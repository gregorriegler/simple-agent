from simple_agent.application.agent_definition import AgentDefinition

READ_ONLY_TOOLS = ["ls", "cat"]
REPORTING_TOOLS = ["suggest", "complete_task"]


class ObserverDefinition(AgentDefinition):
    def tool_keys(self) -> list[str]:
        declared = super().tool_keys() or READ_ONLY_TOOLS
        allowed = [key for key in declared if key in READ_ONLY_TOOLS]
        return allowed + REPORTING_TOOLS
