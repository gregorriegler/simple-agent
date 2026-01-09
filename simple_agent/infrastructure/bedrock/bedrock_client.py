import json
import os
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig

_CLIENT_UNSET = object()


class BedrockClaudeClientError(RuntimeError):
    pass


class BedrockClaudeLLM(LLM):
    def __init__(self, config: ModelConfig, client: Any = _CLIENT_UNSET):
        self._config = config
        if client is None:
            raise BedrockClaudeClientError("Bedrock client cannot be None")
        self._client = self._build_client() if client is _CLIENT_UNSET else client
        self._ensure_bedrock_adapter()

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        return await self._call_async(messages)

    async def _call_async(self, messages: ChatMessages) -> LLMResponse:
        payload_messages = list(messages)
        system_prompt = (
            payload_messages.pop(0).get("content", "")
            if payload_messages and payload_messages[0].get("role") == "system"
            else None
        )

        data = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": payload_messages,
            **({"system": system_prompt} if system_prompt else {}),
        }

        try:
            response = self._client.invoke_model(
                modelId=self._config.model,
                body=json.dumps(data),
                contentType="application/json",
                accept="application/json",
            )
        except (BotoCoreError, ClientError) as error:
            raise BedrockClaudeClientError(f"API request failed: {error}") from error

        response_data = json.loads(response["body"].read().decode("utf-8"))

        if "content" not in response_data:
            raise BedrockClaudeClientError("API response missing 'content' field")

        content_list = response_data["content"]
        content = ""
        if content_list:
            first_content = content_list[0]
            if "text" not in first_content:
                raise BedrockClaudeClientError(
                    "API response content missing 'text' field"
                )
            content = first_content["text"]

        usage_data = response_data.get("usage", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        return LLMResponse(content=content, model=self._config.model, usage=usage)

    def _build_client(self):
        base_url = self._config.base_url
        endpoint_url = None
        region = (
            os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )

        if base_url:
            if base_url.startswith(("http://", "https://")):
                endpoint_url = base_url
            else:
                region = base_url

        config = Config(
            read_timeout=self._config.request_timeout,
            connect_timeout=self._config.request_timeout,
        )
        return boto3.client(
            "bedrock-runtime",
            region_name=region,
            endpoint_url=endpoint_url,
            config=config,
        )

    def _ensure_bedrock_adapter(self) -> None:
        if self._config.adapter != "bedrock":
            raise BedrockClaudeClientError(
                "Configured adapter is not 'bedrock'; cannot use Bedrock client"
            )
