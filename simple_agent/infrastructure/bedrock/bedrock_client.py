import json
import logging
import asyncio
from typing import Any

import boto3
from botocore.exceptions import ClientError

from simple_agent.application.llm import LLM, ChatMessages, LLMResponse, TokenUsage
from simple_agent.infrastructure.model_config import ModelConfig

logger = logging.getLogger(__name__)


class BedrockClientError(RuntimeError):
    pass


class BedrockClaudeLLM(LLM):
    def __init__(self, config: ModelConfig):
        self._config = config
        self._ensure_bedrock_adapter()
        # Initialize boto3 client. We assume credentials are provided via env vars or ~/.aws/credentials
        self._client = boto3.client("bedrock-runtime", region_name=self._config.api_key if self._config.api_key and self._config.api_key != "bedrock" else None)
        # Note: ModelConfig requires api_key. For Bedrock, we can abuse it to pass region,
        # or just ignore it if it's a dummy value.
        # Let's assume if api_key looks like a region (e.g., us-east-1), use it, otherwise let boto3 decide.
        # Actually, to be safe and consistent with "api_key" semantics, maybe we shouldn't use it for region.
        # But the user might put "AWS_ACCESS_KEY" there?
        # Better: Rely on standard AWS env vars (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION).
        # We will just instantiate the client.

    @property
    def model(self) -> str:
        return self._config.model

    async def call_async(self, messages: ChatMessages) -> LLMResponse:
        return await asyncio.to_thread(self._call_sync, messages)

    def _call_sync(self, messages: ChatMessages) -> LLMResponse:
        model_id = self._config.model

        payload_messages = list(messages)
        system_prompt = None

        # Extract system prompt if present (Claude 3 supports top-level system parameter)
        if payload_messages and payload_messages[0].get("role") == "system":
            system_prompt = payload_messages.pop(0).get("content", "")

        # Format messages for Claude 3 on Bedrock
        # Bedrock Claude 3 expects "messages": [{"role": "user", "content": "..."}]
        # content can be string or list of blocks.
        # simple-agent messages are simple dicts.

        formatted_messages = []
        for msg in payload_messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "messages": formatted_messages,
        }

        if system_prompt:
            body["system"] = system_prompt

        try:
            response = self._client.invoke_model(
                modelId=model_id,
                body=json.dumps(body)
            )

            response_body = json.loads(response.get("body").read())

        except ClientError as e:
            raise BedrockClientError(f"Bedrock API failed: {e}") from e
        except Exception as e:
            raise BedrockClientError(f"Unexpected error: {e}") from e

        # Parse response
        # Claude 3 response body:
        # {
        #   "type": "message",
        #   "role": "assistant",
        #   "content": [{"type": "text", "text": "..."}],
        #   "usage": {"input_tokens": 10, "output_tokens": 20}
        # }

        content = ""
        if "content" in response_body:
            for block in response_body["content"]:
                if block.get("type") == "text":
                    content += block.get("text", "")

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
