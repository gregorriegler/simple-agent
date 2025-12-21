from simple_agent.application.model_info import ModelInfo


def test_empty_model_returns_zero():
    assert ModelInfo.get_context_window("") == 0


def test_exact_model_returns_context_window():
    assert ModelInfo.get_context_window("gpt-5.1-codex") == 400_000


def test_fuzzy_model_prefix_match_returns_context_window():
    assert ModelInfo.get_context_window("claude-sonnet-4-5-20260101") == 200_000


def test_unknown_model_returns_zero():
    assert ModelInfo.get_context_window("unknown-model") == 0
