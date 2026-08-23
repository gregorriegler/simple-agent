from simple_agent.application.agent_definition import AgentDefinition

READ_ONLY_TOOLS = ["ls", "cat"]


class ObserverDefinition(AgentDefinition):
    def tool_keys(self) -> list[str]:
        declared = super().tool_keys()
        if not declared:
            return list(READ_ONLY_TOOLS)
        return [key for key in declared if key in READ_ONLY_TOOLS]
