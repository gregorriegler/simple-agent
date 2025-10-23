from dataclasses import dataclass

SystemPrompt = str


@dataclass
class AgentPrompt:
    template: str
    tool_keys: list[str]
    agents_content: str

    def render(self, tools_documentation: str) -> SystemPrompt:
        result = self.template.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", tools_documentation)
        if not self.agents_content:
            return result
        return result + "\n\n" + self.agents_content
