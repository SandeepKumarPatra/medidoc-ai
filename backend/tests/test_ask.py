"""Tests for POST /ask endpoint and LLM adapters with mocked model inference."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from backend.app.llm.adapter import GeminiLLMAdapter, OpenAILLMAdapter, get_llm_adapter
from backend.app.main import app

client = TestClient(app)


class MockLLMAdapter:
    """Mock LLM adapter simulating grounded clinical generation without live API calls."""

    def __init__(self, response_text: str = ""):
        self.response_text = response_text or (
            "Standard precautions require hand hygiene before and after patient contact "
            "[sop_infection_control.pdf, pp. 2-3]. Sharps injuries must be reported within 1 hour "
            "[sop_infection_control.pdf, p. 4]."
        )
        self.last_prompt = None

    def generate(self, prompt: str) -> str:
        self.last_prompt = prompt
        return self.response_text

    def get_model_name(self) -> str:
        return "mock-gemini-test"


def test_llm_adapter_factory():
    """Assert get_llm_adapter returns the correct adapter type based on provider."""
    gemini_adapter = get_llm_adapter("gemini")
    assert isinstance(gemini_adapter, GeminiLLMAdapter)
    assert gemini_adapter.get_model_name() is not None

    openai_adapter = get_llm_adapter("openai")
    assert isinstance(openai_adapter, OpenAILLMAdapter)
    assert openai_adapter.get_model_name() is not None

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        get_llm_adapter("unknown_provider")


def test_openai_stub_raises():
    """Assert OpenAI stub raises NotImplementedError when invoked without API key."""
    stub = OpenAILLMAdapter(api_key="")
    with pytest.raises(NotImplementedError, match="stub"):
        stub.generate("Test prompt")


@patch("backend.app.retrieval.qa.get_llm_adapter")
def test_ask_endpoint_success(mock_get_adapter):
    """Test POST /ask generates answers, structured citations, timings, and prompt provenance."""
    mock_adapter = MockLLMAdapter()
    mock_get_adapter.return_value = mock_adapter

    payload = {
        "question": "What are the standard infection control precautions?",
        "mode": "hybrid_rerank",
        "top_k": 3,
    }

    response = client.post("/ask", json=payload)
    assert response.status_code == 200, f"POST /ask failed: {response.text}"

    data = response.json()

    # 1. Assert Answer
    assert data["answer"] == mock_adapter.response_text

    # 2. Assert Citations and Sources
    assert "sources" in data
    assert len(data["sources"]) <= 3
    for source in data["sources"]:
        assert source["document"].endswith(".pdf")
        assert "p." in source["pages"] or "pp." in source["pages"]
        assert source["citation"].startswith("[") and source["citation"].endswith("]")
        assert isinstance(source["score"], float)

    # 3. Assert Retrieved IDs
    assert len(data["retrieved_ids"]) == len(data["sources"])
    for rid in data["retrieved_ids"]:
        assert isinstance(rid, str)

    # 4. Assert Timings Breakdown
    timings = data["timings"]
    assert "embed_ms" in timings
    assert "dense_search_ms" in timings
    assert "generation_ms" in timings
    assert "llm_model" in timings
    assert timings["llm_model"] == "mock-gemini-test"
    assert "total_ms" in timings
    assert timings["total_ms"] > 0

    # 5. Assert Prompt hidden by default and Prompt Version always present
    assert "prompt" not in data or data["prompt"] is None
    assert data["prompt_version"] == "rag-clinical-v1.0"


@patch("backend.app.retrieval.qa.get_llm_adapter")
def test_ask_debug_flag_controls_prompt(mock_get_adapter):
    """Assert debug=true exposes the prompt while debug=false hides it."""
    mock_adapter = MockLLMAdapter()
    mock_get_adapter.return_value = mock_adapter

    # 1. debug=false (default): prompt omitted
    res_default = client.post(
        "/ask",
        json={"question": "What are infection precautions?", "mode": "naive", "debug": False},
    )
    assert res_default.status_code == 200
    data_default = res_default.json()
    assert "prompt" not in data_default or data_default["prompt"] is None
    assert data_default["prompt_version"] == "rag-clinical-v1.0"

    # 2. debug=true: prompt included
    res_debug = client.post(
        "/ask",
        json={"question": "What are infection precautions?", "mode": "naive", "debug": True},
    )
    assert res_debug.status_code == 200
    data_debug = res_debug.json()
    assert "prompt" in data_debug and data_debug["prompt"] is not None
    assert "QUESTION: What are infection precautions?" in data_debug["prompt"]
    assert data_debug["prompt_version"] == "rag-clinical-v1.0"


@patch("backend.app.retrieval.qa.get_llm_adapter")
def test_ask_never_returns_duplicate_parent_sources(mock_get_adapter):
    """Assert a single /ask request never returns two sources with the same parent_id (fails on duplicates)."""
    mock_adapter = MockLLMAdapter()
    mock_get_adapter.return_value = mock_adapter

    for mode in ["parent_child", "hybrid", "hybrid_rerank"]:
        res = client.post(
            "/ask",
            json={
                "question": "What are hospital policies for hand hygiene and sharps disposal?",
                "mode": mode,
                "top_k": 5,
            },
        )
        assert res.status_code == 200
        sources = res.json()["sources"]
        assert len(sources) > 0

        parent_ids = [s["parent_id"] for s in sources if s.get("parent_id")]
        # Assert strictly distinct parents
        assert len(parent_ids) == len(set(parent_ids)), (
            f"Mode '{mode}' returned duplicate parent_id in sources: {parent_ids}"
        )


@patch("backend.app.retrieval.qa.get_llm_adapter")
@pytest.mark.parametrize("retrieval_mode", ["naive", "parent_child", "hybrid", "hybrid_rerank"])
def test_ask_all_retrieval_modes(mock_get_adapter, retrieval_mode):
    """Assert POST /ask functions reliably across all four retrieval strategies."""
    mock_adapter = MockLLMAdapter("Grounded answer [sop_infection_control.pdf, p. 2].")
    mock_get_adapter.return_value = mock_adapter

    payload = {
        "question": "What is the procedure for hand hygiene?",
        "mode": retrieval_mode,
        "top_k": 2,
    }

    response = client.post("/ask", json=payload)
    assert response.status_code == 200, f"Mode {retrieval_mode} failed: {response.text}"
    data = response.json()
    assert data["answer"] == mock_adapter.response_text
    assert len(data["sources"]) <= 2


@patch("backend.app.retrieval.qa.get_llm_adapter")
def test_ask_not_found_handling(mock_get_adapter):
    """Assert /ask handles queries where context does not contain the answer."""
    not_found_text = "The answer was not found in the provided hospital documentation."
    mock_adapter = MockLLMAdapter(not_found_text)
    mock_get_adapter.return_value = mock_adapter

    payload = {
        "question": "What is the policy for nuclear reactor shutdowns?",
        "mode": "hybrid",
        "top_k": 3,
    }

    response = client.post("/ask", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == not_found_text


def test_ask_validation_errors():
    """Assert POST /ask validates inputs according to Pydantic constraints."""
    # Invalid mode
    res_mode = client.post("/ask", json={"question": "Test", "mode": "invalid_mode"})
    assert res_mode.status_code == 422

    # Empty question
    res_q = client.post("/ask", json={"question": "", "mode": "naive"})
    assert res_q.status_code == 422

    # Out-of-bounds top_k
    res_k = client.post("/ask", json={"question": "Test", "top_k": 0})
    assert res_k.status_code == 422

    res_k_max = client.post("/ask", json={"question": "Test", "top_k": 50})
    assert res_k_max.status_code == 422


@patch("backend.app.retrieval.qa.get_llm_adapter")
def test_ask_llm_timeout_handling(mock_get_adapter):
    """Assert POST /ask returns HTTP 504 with a clear error message when LLM times out."""
    mock_adapter = MagicMock()
    mock_adapter.get_model_name.return_value = "timeout-model-test"
    mock_adapter.generate.side_effect = TimeoutError("LLM generation timed out after 30.0s (model: timeout-model-test)")
    mock_get_adapter.return_value = mock_adapter

    response = client.post(
        "/ask",
        json={"question": "What are the rules?", "mode": "naive"},
    )
    assert response.status_code == 504
    detail = response.json()["detail"]
    assert "LLM request timed out" in detail
    assert "timeout-model-test" in detail


def test_gemini_adapter_timeout_enforced():
    """Assert GeminiLLMAdapter raises TimeoutError when generation exceeds timeout."""
    import time

    def slow_invoke(prompt):
        time.sleep(0.5)
        return "slow response"

    adapter = GeminiLLMAdapter(api_key="fake-key-for-test", timeout=0.05)
    with patch.object(adapter, "_invoke", side_effect=slow_invoke):
        with pytest.raises(TimeoutError, match="LLM generation timed out after 0.05s"):
            adapter.generate("Test prompt")
