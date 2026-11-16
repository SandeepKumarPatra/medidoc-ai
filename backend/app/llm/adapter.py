"""LLM adapters for MediDoc AI.

Provides unified adapter interfaces with:
- GeminiLLMAdapter: Production implementation via langchain-google-genai (ChatGoogleGenerativeAI)
- OpenAILLMAdapter: Configurable OpenAI implementation and stub
Factory function get_llm_adapter() returns the configured adapter instance.
"""

from __future__ import annotations

import concurrent.futures
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional, Type

from backend.app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BaseLLMAdapter(ABC):
    """Abstract base class for LLM completion adapters."""

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate text completion for the supplied prompt string.

        Args:
            prompt: Formatted prompt text.

        Returns:
            Generated model output string.
        """
        pass

    @abstractmethod
    def generate_structured(self, prompt: str, schema: Type[Any]) -> Any:
        """Generate structured output adhering to a Pydantic schema or schema dict.

        Args:
            prompt: Formatted prompt text.
            schema: Target Pydantic BaseModel class or JSON schema.

        Returns:
            Extracted structured object conforming to schema.
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model identifier string."""
        pass


class GeminiLLMAdapter(BaseLLMAdapter):
    """Gemini adapter utilizing langchain-google-genai ChatGoogleGenerativeAI."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        timeout: Optional[float] = None,
        thinking_budget: Optional[int] = None,
    ) -> None:
        self.model_name = (
            model_name
            or os.getenv("LLM_MODEL")
            or settings.llm_model
            or "gemini-2.5-flash"
        )
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
                or settings.gemini_api_key
            )
        self.temperature = temperature
        self.timeout = (
            timeout
            if timeout is not None
            else float(os.getenv("LLM_TIMEOUT", str(settings.llm_timeout)))
        )
        if thinking_budget is not None:
            self.thinking_budget = thinking_budget
        else:
            env_budget = os.getenv("LLM_THINKING_BUDGET")
            if env_budget is not None and env_budget.strip() != "":
                self.thinking_budget = int(env_budget)
            else:
                self.thinking_budget = settings.llm_thinking_budget
        self._llm = None

    def _get_client(self):
        """Lazily initialize ChatGoogleGenerativeAI instance."""
        if self._llm is None:
            if not self.api_key or self.api_key.startswith("your-"):
                raise ValueError(
                    "GEMINI_API_KEY environment variable is required to generate responses with Gemini. "
                    "Please set GEMINI_API_KEY in your .env or environment."
                )

            from langchain_google_genai import ChatGoogleGenerativeAI

            logger.info(
                "Initializing ChatGoogleGenerativeAI with model=%s, timeout=%.1fs, thinking_budget=%s",
                self.model_name,
                self.timeout,
                self.thinking_budget,
            )
            extra_kwargs: dict[str, Any] = {}
            if self.thinking_budget is not None:
                extra_kwargs["thinking_budget"] = self.thinking_budget

            self._llm = ChatGoogleGenerativeAI(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                timeout=self.timeout,
                **extra_kwargs,
            )
        return self._llm

    def _invoke(self, prompt: str) -> str:
        """Internal synchronous call to LLM."""
        client = self._get_client()
        response = client.invoke(prompt)
        content = response.content
        if isinstance(content, list):
            text_parts = [
                part if isinstance(part, str) else str(part.get("text", ""))
                for part in content
            ]
            return "".join(text_parts).strip()
        return str(content).strip()

    def generate(self, prompt: str) -> str:
        """Invoke Gemini LLM with prompt bounded by configurable timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._invoke, prompt)
            try:
                return future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(
                    f"LLM generation timed out after {self.timeout}s (model: {self.model_name})"
                )

    def _invoke_structured(self, prompt: str, schema: Type[Any]) -> Any:
        """Internal synchronous call to Gemini LLM with structured output."""
        client = self._get_client()
        structured_llm = client.with_structured_output(schema)
        return structured_llm.invoke(prompt)

    def generate_structured(self, prompt: str, schema: Type[Any]) -> Any:
        """Invoke Gemini LLM with structured output bounded by configurable timeout."""
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._invoke_structured, prompt, schema)
            try:
                return future.result(timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(
                    f"LLM structured generation timed out after {self.timeout}s (model: {self.model_name})"
                )

    def get_model_name(self) -> str:
        return self.model_name


class OpenAILLMAdapter(BaseLLMAdapter):
    """OpenAI stub adapter switchable by configuration."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: float = 0.0,
        timeout: Optional[float] = None,
    ) -> None:
        self.model_name = (
            model_name
            or os.getenv("LLM_MODEL")
            or "gpt-4o-mini"
        )
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = (
                os.getenv("OPENAI_API_KEY")
                or settings.openai_api_key
            )
        self.temperature = temperature
        self.timeout = (
            timeout
            if timeout is not None
            else float(os.getenv("LLM_TIMEOUT", str(settings.llm_timeout)))
        )
        self._llm = None

    def _invoke(self, prompt: str) -> str:
        from langchain_openai import ChatOpenAI

        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                timeout=self.timeout,
            )
        response = self._llm.invoke(prompt)
        return str(response.content).strip()

    def generate(self, prompt: str) -> str:
        """Invoke OpenAI if configured and keyed, otherwise report stub status."""
        if not self.api_key or self.api_key.startswith("your-") or "placeholder" in self.api_key.lower():
            raise NotImplementedError(
                "OpenAI adapter is currently operating as a stub. "
                "To enable live OpenAI generation, set OPENAI_API_KEY in your environment, "
                "or switch LLM_PROVIDER to 'gemini'."
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._invoke, prompt)
                try:
                    return future.result(timeout=self.timeout)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(
                        f"LLM generation timed out after {self.timeout}s (model: {self.model_name})"
                    )
        except ImportError:
            raise NotImplementedError(
                "langchain-openai is required for OpenAI integration. Please install it or use Gemini."
            )

    def _invoke_structured(self, prompt: str, schema: Type[Any]) -> Any:
        from langchain_openai import ChatOpenAI

        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                timeout=self.timeout,
            )
        structured_llm = self._llm.with_structured_output(schema)
        return structured_llm.invoke(prompt)

    def generate_structured(self, prompt: str, schema: Type[Any]) -> Any:
        """Invoke OpenAI structured output if configured and keyed, otherwise report stub status."""
        if not self.api_key or self.api_key.startswith("your-") or "placeholder" in self.api_key.lower():
            raise NotImplementedError(
                "OpenAI adapter is currently operating as a stub. "
                "To enable live OpenAI generation, set OPENAI_API_KEY in your environment, "
                "or switch LLM_PROVIDER to 'gemini'."
            )

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(self._invoke_structured, prompt, schema)
                try:
                    return future.result(timeout=self.timeout)
                except concurrent.futures.TimeoutError:
                    raise TimeoutError(
                        f"LLM structured generation timed out after {self.timeout}s (model: {self.model_name})"
                    )
        except ImportError:
            raise NotImplementedError(
                "langchain-openai is required for OpenAI integration. Please install it or use Gemini."
            )

    def get_model_name(self) -> str:
        return self.model_name


def get_llm_adapter(
    provider: Optional[str] = None,
    timeout: Optional[float] = None,
) -> BaseLLMAdapter:
    """Factory function returning configured LLM adapter instance.

    Args:
        provider: Optional override for provider ('gemini' or 'openai').
        timeout: Optional timeout in seconds (defaults to config llm_timeout).

    Returns:
        Instance conforming to BaseLLMAdapter.
    """
    chosen_provider = (
        provider
        or os.getenv("LLM_PROVIDER")
        or settings.llm_provider
        or "gemini"
    ).lower()

    if chosen_provider == "gemini":
        return GeminiLLMAdapter(timeout=timeout)
    elif chosen_provider == "openai":
        return OpenAILLMAdapter(timeout=timeout)
    else:
        raise ValueError(
            f"Unsupported LLM provider '{chosen_provider}'. Supported options: 'gemini', 'openai'."
        )
