import httpx

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.application.tool_library import Tool
from simple_agent.infrastructure.gemini.gemini_tools import (
    to_function_declarations,
    to_raw_tool_calls,
)
from simple_agent.infrastructure.llm_http import post_with_retry
from simple_agent.infrastructure.model_config import ModelConfig

API_REVISION = "2026-05-20"
SUCCESS_STATUSES = ("completed", "incomplete")


class GeminiClientError(Exception):
    pass


class GeminiLLM(LLM):
    client_label = "Gemini client"
    adapter_name = "gemini"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"
    error_class: type[Exception] = GeminiClientError

    def __init__(
        self,
        config: ModelConfig,
        tools: list[Tool] | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self._config = config
        self._tools = tools or []
        self._transport = transport
        self._ensure_adapter()

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        response = await post_with_retry(
            self._interactions_url(),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._config.api_key,
                "Api-Revision": API_REVISION,
            },
            json=self._build_request(messages),
            timeout=self._config.request_timeout,
            error_class=self.error_class,
            transport=self._transport,
        )

        interaction = response.json()
        self._raise_on_error(interaction)

        steps = interaction.get("steps")
        if not steps:
            raise self.error_class("API response has no steps")
        tool_calls = to_raw_tool_calls(steps, self._tools)

        return LLMResponse(
            content=self._output_text(interaction, tool_calls),
            tool_calls=tool_calls,
            model=interaction.get("model") or self._config.model,
            usage=self._usage(interaction),
        )

    def _interactions_url(self) -> str:
        base_url = self._config.base_url or self.default_base_url
        return f"{base_url.rstrip('/')}/interactions"

    def _build_request(self, messages: ChatMessages) -> dict:
        system_instruction, steps = self._convert_messages(messages)
        request = {
            "model": self._config.model,
            "input": steps,
            "store": False,
        }
        if self._tools:
            request["tools"] = [
                {"function_declarations": to_function_declarations(self._tools)}
            ]
        else:
            request["generation_config"] = {"tool_choice": "none"}
        if system_instruction:
            request["system_instruction"] = system_instruction
        return request

    def _convert_messages(self, messages: ChatMessages) -> tuple[str, list[dict]]:
        """
        Convert standard chat messages to Interactions API input steps.

        System messages become the interaction's system_instruction, user
        messages become 'user_input' steps and assistant messages become
        'model_output' steps.
        """
        system_prompts = []
        steps = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "system":
                system_prompts.append(content)
            elif role == "user":
                steps.append(self._step("user_input", content))
            elif role == "assistant":
                steps.append(self._step("model_output", content))

        return "\n\n".join(system_prompts), steps

    def _step(self, step_type: str, text: str) -> dict:
        return {"type": step_type, "content": [{"type": "text", "text": text}]}

    def _raise_on_error(self, interaction: dict) -> None:
        status = interaction.get("status")
        if status not in SUCCESS_STATUSES:
            raise self.error_class(
                f"Gemini interaction {status}: {self._error_message(interaction)}"
            )

    def _error_message(self, interaction: dict) -> str:
        for error in interaction.get("errors") or []:
            details = [
                str(part) for part in (error.get("code"), error.get("message")) if part
            ]
            if details:
                return ": ".join(details)
        return "no error message"

    def _output_text(self, interaction: dict, tool_calls: list) -> str:
        """
        Collect the text of the trailing run of 'model_output' steps.

        Steps of other types are skipped until the run starts and the echoed
        input of an earlier turn ends the run, as in the Gemini SDK. Unlike
        the SDK we keep text that surrounds non-text content rather than
        stopping at it, since this client only ever asks for text.
        """
        steps = interaction.get("steps") or []

        texts: list[str] = []
        output_error = None
        for step in reversed(steps):
            step_type = step.get("type")
            if step_type == "user_input":
                break
            if step_type != "model_output":
                if texts:
                    break
                continue

            output_error = output_error or step.get("error")
            for content in reversed(step.get("content") or []):
                if content.get("type") == "text":
                    texts.append(content.get("text", ""))

        text = "".join(reversed(texts))
        if not text and not tool_calls:
            self._raise_output_error(output_error)
        return text

    def _raise_output_error(self, output_error: dict | None) -> None:
        if output_error:
            code = output_error.get("code", "")
            message = output_error.get("message", "Unknown error")
            raise self.error_class(f"Gemini model output error [{code}]: {message}")
        raise self.error_class("API response contains no model output text")

    def _usage(self, interaction: dict) -> TokenUsage:
        usage = interaction.get("usage") or {}
        return TokenUsage(
            input_tokens=usage.get("total_input_tokens", 0),
            output_tokens=(usage.get("total_output_tokens") or 0)
            + (usage.get("total_thought_tokens") or 0),
            total_tokens=usage.get("total_tokens", 0),
        )

    def _ensure_adapter(self) -> None:
        if self._config.adapter != self.adapter_name:
            raise self.error_class(
                f"Configured adapter is not '{self.adapter_name}'; "
                f"cannot use {self.client_label}"
            )
