import logging
from typing import Any

import yaml

from simple_agent.application.agent_type import AgentType
from simple_agent.application.ground_rules import GroundRules
from simple_agent.application.system_prompt import AgentPrompt

logger = logging.getLogger(__name__)

class AgentDefinition:
    def __init__(self, agent_type: AgentType, content: str, ground_rules: GroundRules):
        self._agent_type = agent_type
        self._content = content
        self.ground_rules = ground_rules
        self._metadata: dict[str, Any] | None = None
        self._template: str | None = None
        self._prompt: AgentPrompt | None = None

    def agent_name(self):
        return self.prompt().agent_name

    def tool_keys(self):
        metadata, _ = self._load()
        return self._read_tool_keys(metadata.get('tools'))

    def model(self) -> str | None:
        metadata, _ = self._load()
        model_value = metadata.get('model')
        return str(model_value).strip() if model_value is not None else None

    def prompt(self) -> AgentPrompt:
        if not self._prompt:
            self._prompt = self._build_prompt()
        return self._prompt

    def _load(self) -> tuple[dict[str, Any], str]:
        if self._metadata is None:
            self._metadata, self._template = self._parse_front_matter(self._content)
        return self._metadata, self._template

    def _build_prompt(self) -> AgentPrompt:
        metadata, template = self._load()
        name = metadata.get('name', str(self._agent_type).capitalize())
        ground_rules = self.ground_rules.read()
        return AgentPrompt(name, template, ground_rules)

    def _parse_front_matter(self, content: str) -> tuple[dict[str, Any], str]:
        if not content:
            return {}, content

        leading_trimmed = content.lstrip()
        leading_prefix = content[: len(content) - len(leading_trimmed)]
        working = leading_trimmed

        if not working.startswith('---'):
            return {}, content

        working = working[3:]

        if working.startswith('\r\n'):
            newline = '\r\n'
            working = working[2:]
        elif working.startswith('\n'):
            newline = '\n'
            working = working[1:]
        else:
            return {}, content

        closing = f"{newline}---"
        end_index = working.find(closing)
        if end_index == -1:
            return {}, content

        front_matter_text = working[:end_index]
        remainder = working[end_index + len(closing):]
        if newline and remainder.startswith(newline):
            remainder = remainder[len(newline):]

        metadata = self._load_front_matter(front_matter_text)
        return metadata, leading_prefix + remainder


    @staticmethod
    def _load_front_matter(front_matter_text: str) -> dict[str, Any]:
        try:
            loaded = yaml.safe_load(front_matter_text) or {}
        except yaml.YAMLError:
            return {}

        if isinstance(loaded, dict):
            return loaded

        return {}


    @staticmethod
    def _read_tool_keys(raw_tools: Any) -> list[str]:
        if raw_tools is None:
            return []

        if isinstance(raw_tools, str):
            parts = [item.strip() for item in raw_tools.split(',')]
            return [item for item in parts if item]

        if isinstance(raw_tools, list):
            normalized = []
            for item in raw_tools:
                if isinstance(item, str):
                    stripped = item.strip()
                    if stripped:
                        normalized.append(stripped)
            return normalized

        return []

