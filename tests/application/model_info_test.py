from simple_agent.application.model_info import ModelInfo


def test_empty_model_returns_zero():
    assert ModelInfo.get_context_window("") == 0


def test_exact_model_returns_context_window():
    assert ModelInfo.get_context_window("gpt-5.1-codex") == 400_000


def test_fuzzy_model_prefix_match_returns_context_window():
    assert ModelInfo.get_context_window("claude-sonnet-4-5-20260101") == 200_000


def test_current_gemini_models_return_context_window():
    for model in [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.1-pro-preview",
        "gemini-3.1-flash-lite",
        "gemini-3-flash-preview",
    ]:
        assert ModelInfo.get_context_window(model) == 1_048_576


def test_gemini_latest_aliases_return_context_window():
    for model in [
        "gemini-pro-latest",
        "gemini-flash-latest",
        "gemini-flash-lite-latest",
    ]:
        assert ModelInfo.get_context_window(model) == 1_048_576


def test_unknown_model_returns_zero():
    assert ModelInfo.get_context_window("unknown-model") == 0
