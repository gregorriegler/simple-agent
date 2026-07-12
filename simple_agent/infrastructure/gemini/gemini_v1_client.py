from .gemini_client import GeminiLLM


class GeminiV1ClientError(Exception):
    pass


class GeminiV1LLM(GeminiLLM):
    client_label = "Gemini V1 client"
    adapter_name = "gemini_v1"
    default_base_url = "https://generativelanguage.googleapis.com/v1"
    error_class = GeminiV1ClientError
    max_retries = 0

    def _generate_content_request(
        self, base_url: str, model: str, api_key: str
    ) -> tuple[str, dict[str, str]]:
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        return url, {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        }
