from dataclasses import dataclass

from simple_agent.application.embedded_content import EmbeddedContent, embed_content
from simple_agent.application.project_tree import ProjectTree

SystemPrompt = str


@dataclass
class AgentPrompt:
    agent_name: str
    template: str
    agents_content: str
    embedded_content: EmbeddedContent

    def render(self, project_tree: ProjectTree) -> SystemPrompt:
        tree_output = project_tree.render(max_depth=2)
        project_structure = f"# Project Structure\n\n```\n{tree_output}```\n"

        result = embed_content(self.template, self.embedded_content).replace(
            "{{DYNAMIC_TOOLS_PLACEHOLDER}}", project_structure
        )
        if not self.agents_content:
            return result.replace("{{AGENTS.MD}}", "")

        if "{{AGENTS.MD}}" in result:
            return result.replace("{{AGENTS.MD}}", self.agents_content)

        return self.agents_content + "\n\n" + result
