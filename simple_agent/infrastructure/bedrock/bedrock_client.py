import json
import logging
from typing import Any

import boto3
from botocore.exceptions import ClientError

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig
import asyncio

logger = logging.getLogger(__name__)

class BedrockClientError(RuntimeError):
    pass

class BedrockClaudeLLM(LLM):
    def __init__(self, config: ModelConfig):
        self._config = config
        self._ensure_bedrock_adapter()
        self._client = boto3.client("bedrock-runtime", region_name=self._config.api_key) # Assuming api_key field holds region for now or environment variable

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        return await self._call_async(messages)

    async def _call_async(self, messages: ChatMessages) -> LLMResponse:
        model_id = self._config.model

        # Prepare messages for Bedrock Claude 3
        payload_messages = list(messages)
        system_prompt = (
            payload_messages.pop(0).get("content", "")
            if payload_messages and payload_messages[0].get("role") == "system"
            else None
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "messages": payload_messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        try:
            # boto3 is synchronous, so we run it in a thread to avoid blocking the loop
            response = await asyncio.to_thread(
                self._client.invoke_model,
                body=json.dumps(body),
                modelId=model_id,
                accept="application/json",
                contentType="application/json"
            )

            response_body = json.loads(response.get("body").read())

        except ClientError as e:
            raise BedrockClientError(f"Bedrock API request failed: {e}") from e
        except Exception as e:
            raise BedrockClientError(f"Unexpected error: {e}") from e

        content_list = response_body.get("content", [])
        content = ""
        if content_list:
            first_content = content_list[0]
            if "text" in first_content:
                content = first_content["text"]

        usage_data = response_body.get("usage", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        usage = TokenUsage(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

        return LLMResponse(content=content, model=model_id, usage=usage)

    def _ensure_bedrock_adapter(self) -> None:
        if self._config.adapter != "bedrock":
            raise BedrockClientError(
                "Configured adapter is not 'bedrock'; cannot use Bedrock client"
            )
