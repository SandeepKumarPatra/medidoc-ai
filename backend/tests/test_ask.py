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
    assert data["prompt_version"] == "rag-clinical-v1.1"


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
    assert data_default["prompt_version"] == "rag-clinical-v1.1"

    # 2. debug=true: prompt included
    res_debug = client.post(
        "/ask",
        json={"question": "What are infection precautions?", "mode": "naive", "debug": True},
    )
    assert res_debug.status_code == 200
    data_debug = res_debug.json()
    assert "prompt" in data_debug and data_debug["prompt"] is not None
    assert "QUESTION: What are infection precautions?" in data_debug["prompt"]
    assert data_debug["prompt_version"] == "rag-clinical-v1.1"


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


def test_format_page_label_ranges():
    """Assert page labels format single pages as 'p. X' and multi-page ranges as 'pp. X-Y'."""
    from backend.app.retrieval.qa import format_page_label

    assert format_page_label(1, 1) == "p. 1"
    assert format_page_label(5, 5) == "p. 5"
    assert format_page_label(2, 3) == "pp. 2-3"
    assert format_page_label(1, 7) == "pp. 1-7"


def test_replace_source_citations_unit():
    """Unit test deterministic citation mapping: [S1], [S1, S4], invalid [S9] dropped/flagged, and CitedSource list."""
    from backend.app.retrieval.qa import SourceCitation, replace_source_citations

    dummy_sources = [
        SourceCitation(
            document="sop_infection_control.pdf",
            pages="pp. 2-3",
            page_start=2,
            page_end=3,
            citation="[sop_infection_control.pdf, pp. 2-3]",
            section_title="Precautions",
            score=0.95,
        ),
        SourceCitation(
            document="sop_medication_safety.pdf",
            pages="p. 4",
            page_start=4,
            page_end=4,
            citation="[sop_medication_safety.pdf, p. 4]",
            section_title="High Alert Meds",
            score=0.88,
        ),
        SourceCitation(
            document="sop_blood_transfusion.pdf",
            pages="pp. 1-2",
            page_start=1,
            page_end=2,
            citation="[sop_blood_transfusion.pdf, pp. 1-2]",
            section_title="Verification",
            score=0.75,
        ),
        SourceCitation(
            document="sop_discharge_process.pdf",
            pages="pp. 5-7",
            page_start=5,
            page_end=7,
            citation="[sop_discharge_process.pdf, pp. 5-7]",
            section_title="Checklist",
            score=0.70,
        ),
    ]

    # 1. Single and multiple valid citations
    raw = "Wash hands before contact [S1]. Verify ID and high-alert labels [S1, S4]."
    ans, cited, dropped = replace_source_citations(raw, dummy_sources)

    assert "[S1]" not in ans
    assert "[S4]" not in ans
    assert "[sop_infection_control.pdf, pp. 2-3]" in ans
    assert "[sop_discharge_process.pdf, pp. 5-7]" in ans
    assert len(dropped) == 0
    assert len(cited) == 2
    assert cited[0].source_index == 1
    assert cited[0].document == "sop_infection_control.pdf"
    assert cited[0].pages == "pp. 2-3"
    assert cited[1].source_index == 4
    assert cited[1].document == "sop_discharge_process.pdf"
    assert cited[1].pages == "pp. 5-7"

    # 2. Out-of-bounds citation [S9] is dropped and flagged
    raw_invalid = "Routine cleaning schedule [S9]. Sharps disposal protocol [S2]."
    ans_inv, cited_inv, dropped_inv = replace_source_citations(raw_invalid, dummy_sources)

    assert "[S9]" not in ans_inv
    assert "S9" in dropped_inv
    assert "[sop_medication_safety.pdf, p. 4]" in ans_inv
    assert len(cited_inv) == 1
    assert cited_inv[0].source_index == 2
    # Ensure dropped [S9] left clean sentence punctuation without trailing space before period
    assert "Routine cleaning schedule." in ans_inv

    # 3. Mixed valid and invalid inside same bracket: [S1, S9]
    raw_mixed = "Policy guidance [S1, S9]."
    ans_mix, cited_mix, dropped_mix = replace_source_citations(raw_mixed, dummy_sources)
    assert ans_mix == "Policy guidance [sop_infection_control.pdf, pp. 2-3]."
    assert "S9" in dropped_mix
    assert len(cited_mix) == 1
    assert cited_mix[0].source_index == 1


@patch("backend.app.retrieval.qa.get_llm_adapter")
def test_ask_endpoint_deterministic_citations_replacement(mock_get_adapter):
    """Integration test POST /ask deterministic citation replacement with mocked LLM outputting [S1], [S1, S2], [S9]."""
    mock_text = (
        "Staff must sanitize hands upon room entry [S1]. "
        "Medications require double verification [S1, S2]. "
        "Unverified external guidance [S9]."
    )
    mock_adapter = MockLLMAdapter(response_text=mock_text)
    mock_get_adapter.return_value = mock_adapter

    payload = {
        "question": "What are infection control and medication safety protocols?",
        "mode": "hybrid",
        "top_k": 3,
    }

    response = client.post("/ask", json=payload)
    assert response.status_code == 200, f"/ask failed: {response.text}"
    data = response.json()

    # 1. Assert [S1], [S2] replaced with real [document, pages]
    assert "[S1]" not in data["answer"]
    assert "[S2]" not in data["answer"]
    assert "[S9]" not in data["answer"]
    assert ".pdf" in data["answer"]
    assert ("p." in data["answer"] or "pp." in data["answer"])

    # 2. Assert [S9] was dropped and flagged
    assert "dropped_citations" in data
    assert "S9" in data["dropped_citations"]

    # 3. Assert citations list contains actual cited sources with expected attributes
    assert "citations" in data
    assert len(data["citations"]) >= 1
    for c in data["citations"]:
        assert c["source_index"] in (1, 2)
        assert c["document"].endswith(".pdf")
        assert ("p." in c["pages"] or "pp." in c["pages"])

    # 4. Assert sources list includes full page ranges for all retrieved candidates
    assert "sources" in data
    assert len(data["sources"]) >= len(data["citations"])
    for s in data["sources"]:
        assert s["page_start"] >= 1
        assert s["page_end"] >= s["page_start"]
        assert ("p." in s["pages"] or "pp." in s["pages"])
        assert s["citation"].startswith("[") and s["citation"].endswith("]")


def test_gemini_adapter_thinking_budget_configuration():
    """Assert GeminiLLMAdapter respects LLM_THINKING_BUDGET configuration."""
    adapter = GeminiLLMAdapter(api_key="fake-key-test", thinking_budget=0)
    assert adapter.thinking_budget == 0

