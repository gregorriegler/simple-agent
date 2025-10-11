from .llm import LLM
from .session_storage import SessionStorage
from .tool_library_protocol import ToolLibrary
from .tool_result import ToolResult, ContinueResult
from .event_bus_protocol import EventBus
from .events import AssistantSaidEvent, ToolResultEvent, SessionEndedEvent, UserPromptRequestedEvent, UserPromptedEvent, \
    EventType


class Agent:
    def __init__(
        self,
        agent_id: str,
        llm: LLM,
        system_prompt,
        user_input,
        tools: ToolLibrary,
        event_bus: EventBus,
        session_storage: SessionStorage
    ):
        self.agent_id = agent_id
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.user_input = user_input
        self.event_bus = event_bus
        self.tools = tools
        self.session_storage = session_storage

    def start(self, context):
        try:
            tool_result: ToolResult = ContinueResult()

            while self.user_prompts(context):
                tool_result = self.run_tool_loop(context)

            self.event_bus.publish(EventType.SESSION_ENDED, SessionEndedEvent(self.agent_id))
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self.event_bus.publish(EventType.SESSION_ENDED, SessionEndedEvent(self.agent_id))
            return ContinueResult()

    def run_tool_loop(self, context):
        tool_result: ToolResult = ContinueResult()

        try:
            while isinstance(tool_result, ContinueResult):
                llm_answer = self.llm_answers(context)
                tool = self.tools.parse_tool(llm_answer)
                if not tool or self.user_input.escape_requested():
                    break
                tool_result = self.execute_tool(tool, context)
        except KeyboardInterrupt:
            pass

        return tool_result

    def user_prompts(self, context):
        self.event_bus.publish(EventType.USER_PROMPT_REQUESTED, UserPromptRequestedEvent(self.agent_id))
        prompt = self.user_input.read()
        if prompt:
            context.user_says(prompt)
            self.event_bus.publish(EventType.USER_PROMPTED, UserPromptedEvent(self.agent_id, prompt))
        return prompt

    def llm_answers(self, context):
        system_prompt = self.system_prompt(self.tools)
        answer = self.llm(system_prompt, context.to_list())
        self.event_bus.publish(EventType.ASSISTANT_SAID, AssistantSaidEvent(self.agent_id, answer))
        context.assistant_says(answer)
        return answer

    def execute_tool(self, tool, context):
        tool_result = self.tools.execute_parsed_tool(tool)
        self.event_bus.publish(EventType.TOOL_RESULT, ToolResultEvent(self.agent_id, str(tool_result)))
        if isinstance(tool_result, ContinueResult):
            context.user_says(f"Result of {tool}\n{tool_result}")
        return tool_result
