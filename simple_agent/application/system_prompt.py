from dataclasses import dataclass
from simple_agent.application.tree_display import generate_tree

SystemPrompt = str


@dataclass
class AgentPrompt:
    agent_name: str
    template: str
    agents_content: str

    def render(self, tools_documentation: str) -> SystemPrompt:
        tree_output = generate_tree(max_depth=2)
        project_structure = f"# Project Structure\n\n```\n{tree_output}```\n"

        result = self.template.replace("{{DYNAMIC_TOOLS_PLACEHOLDER}}", project_structure + tools_documentation)
        if not self.agents_content:
            return result.replace("{{AGENTS.MD}}", "")

        if "{{AGENTS.MD}}" in result:
            return result.replace("{{AGENTS.MD}}", self.agents_content)

        return self.agents_content + "\n\n" + result
