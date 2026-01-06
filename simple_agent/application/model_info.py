class ModelInfo:
    KNOWN_MODELS = {
        # OpenAI GPT-5.1 Codex family
        "gpt-5.1-codex": 400_000,
        "gpt-5.1-codex-mini": 400_000,
        "gpt-5.1-codex-max": 400_000,
        # Anthropic Claude 4.5 models
        "claude-sonnet-4-5-20250929": 200_000,
        "claude-opus-4-5-20251101": 200_000,
        "claude-haiku-4-5-20251001": 200_000,
        # Google Gemini models
        "gemini-2.5-pro": 1_048_576,
        "gemini-3-pro-preview": 1_048_576,
    }

    @staticmethod
    def get_context_window(model_name: str) -> int:
        if not model_name:
            return 0

        # Direct lookup first
        if model_name in ModelInfo.KNOWN_MODELS:
            return ModelInfo.KNOWN_MODELS[model_name]

        # Fuzzy matching for models with version suffixes
        for known_model, context_window in ModelInfo.KNOWN_MODELS.items():
            # Match if the model_name starts with the known pattern (without date suffix)
            if model_name.startswith(known_model.rsplit("-", 1)[0]):
                return context_window

        return 0
