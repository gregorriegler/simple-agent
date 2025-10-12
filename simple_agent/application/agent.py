from .llm import LLM, Messages
from .session_storage import SessionStorage
from .tool_library import ToolResult, ContinueResult, ToolLibrary
from .event_bus_protocol import EventBus
from .events import AssistantSaidEvent, ToolCalledEvent, ToolResultEvent, SessionEndedEvent, UserPromptRequestedEvent, UserPromptedEvent, \
    EventType


class Agent:
    def __init__(self, agent_id: str, system_prompt, tools: ToolLibrary, llm: LLM, user_input, event_bus: EventBus,
                 session_storage: SessionStorage):
        self.agent_id = agent_id
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.tools = tools
        self.user_input = user_input
        self.event_bus = event_bus
        self.session_storage = session_storage

    def start(self, context = Messages()):
        try:
            tool_result: ToolResult = ContinueResult()

            while self.user_prompts(context):
                tool_result = self.run_tool_loop(context)

            self.notify_session_ended()
            return tool_result
        except (EOFError, KeyboardInterrupt):
            self.notify_session_ended()
            return ContinueResult()

    def run_tool_loop(self, context):
        tool_result: ToolResult = ContinueResult()

        try:
            while isinstance(tool_result, ContinueResult):
                llm_answer = self.llm_answers(context)
                message_and_tools = self.tools.parse_tool(llm_answer)
                if not message_and_tools.tools or self.user_input.escape_requested():
                    break
                tool_result = self.execute_tool(message_and_tools.tools[0], context)
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
        self.event_bus.publish(EventType.TOOL_CALLED, ToolCalledEvent(self.agent_id, tool))
        tool_result = self.tools.execute_parsed_tool(tool)
        self.event_bus.publish(EventType.TOOL_RESULT, ToolResultEvent(self.agent_id, str(tool_result)))
        if isinstance(tool_result, ContinueResult):
            context.user_says(f"Result of {tool}\n{tool_result}")
        return tool_result

    def notify_session_ended(self):
        self.event_bus.publish(EventType.SESSION_ENDED, SessionEndedEvent(self.agent_id))
