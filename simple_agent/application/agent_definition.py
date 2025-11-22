import logging
from typing import Any

import yaml

from simple_agent.application.agent_id import AgentId
from simple_agent.application.ground_rules import GroundRules
from simple_agent.application.system_prompt import AgentPrompt

logger = logging.getLogger(__name__)

class AgentDefinition:
    def __init__(self, agent_id: AgentId, content: str, ground_rules: GroundRules):
        self._prompt = None
        self._agent_id = agent_id
        self._content = content
        self.ground_rules = ground_rules

    def agent_id(self) -> AgentId:
        return self._agent_id

    def agent_name(self):
        return self.prompt().agent_name

    def tool_keys(self):
        return self.prompt().tool_keys

    def prompt(self):
        if not self._prompt:
            self._prompt = self.load_prompt()
        return self._prompt

    def load_prompt(self) -> AgentPrompt:
        metadata, template = self._parse_front_matter(self._content)
        name = metadata.get('name', str(self._agent_id).capitalize())
        tool_keys = self._read_tool_keys(metadata.get('tools'))
        ground_rules = self.ground_rules.read()
        return AgentPrompt(name, template, tool_keys, ground_rules)

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

