from dataclasses import dataclass

SystemPrompt = str


@dataclass
class AgentPrompt:
    agent_name: str
    template: str
    tool_keys: list[str]
    agents_content: str

    def render(self, tools_documentation: str) -> SystemPrompt:
        result = self.template.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_documentation)
        if not self.agents_content:
            return result.replace("{{AGENTS.MD}}", "")

        if "{{AGENTS.MD}}" in result:
            return result.replace("{{AGENTS.MD}}", self.agents_content)

        return self.agents_content + "\n\n" + result
