from .input import Input
from .llm import LLM, Messages
from .session_storage import SessionStorage
from .tool_library import ToolResult, ContinueResult, ToolLibrary
from .event_bus_protocol import EventBus
from .events import AssistantSaidEvent, AssistantRespondedEvent, ToolCalledEvent, ToolResultEvent, SessionEndedEvent, \
    SessionInterruptedEvent, \
    UserPromptRequestedEvent, UserPromptedEvent, EventType


class Agent:
    def __init__(
        self,
        agent_id: str,
        system_prompt,
        tools: ToolLibrary,
        llm: LLM,
        user_input: Input,
        event_bus: EventBus,
        session_storage: SessionStorage
    ):
        self.agent_id = agent_id
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.tools = tools
        self.user_input = user_input
        self.event_bus = event_bus
        self.session_storage = session_storage

    def start(self, context=Messages()):
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
            while tool_result.do_continue():
                message_and_tools = self.llm_responds(context)
                message = message_and_tools.message
                tools = message_and_tools.tools
                self.notify_about_message(message)

                if self.user_input.escape_requested():
                    self.notify_about_interrupt()
                    prompt = self.read_user_input_and_prompt_it(context)
                    if prompt:
                        break
                if not tools:
                    break
                tool_result = self.execute_tool(tools[0], context)
        except KeyboardInterrupt:
            self.event_bus.publish(EventType.SESSION_INTERRUPTED, SessionInterruptedEvent(self.agent_id))

        return tool_result

    def notify_about_interrupt(self):
        self.event_bus.publish(EventType.SESSION_INTERRUPTED, SessionInterruptedEvent(self.agent_id))
        self.event_bus.publish(EventType.USER_PROMPT_REQUESTED, UserPromptRequestedEvent(self.agent_id))

    def notify_about_message(self, message):
        if message:
            self.event_bus.publish(EventType.ASSISTANT_SAID, AssistantSaidEvent(self.agent_id, message))

    def llm_responds(self, context):
        system_prompt = self.system_prompt(self.tools)
        answer = self.llm(system_prompt, context.to_list())
        context.assistant_says(answer)
        self.event_bus.publish(EventType.ASSISTANT_RESPONDED, AssistantRespondedEvent(self.agent_id, answer))
        return self.tools.parse_message_and_tools(answer)

    def user_prompts(self, context):
        if not self.user_input.has_stacked_messages():
            self.event_bus.publish(EventType.USER_PROMPT_REQUESTED, UserPromptRequestedEvent(self.agent_id))
        prompt = self.read_user_input_and_prompt_it(context)
        return prompt

    def read_user_input_and_prompt_it(self, context):
        prompt = self.user_input.read()
        if prompt:
            context.user_says(prompt)
            self.event_bus.publish(EventType.USER_PROMPTED, UserPromptedEvent(self.agent_id, prompt))
        return prompt

    def execute_tool(self, tool, context):
        self.event_bus.publish(EventType.TOOL_CALLED, ToolCalledEvent(self.agent_id, tool))
        tool_result = self.tools.execute_parsed_tool(tool)
        self.event_bus.publish(EventType.TOOL_RESULT, ToolResultEvent(self.agent_id, str(tool_result)))
        if isinstance(tool_result, ContinueResult):
            context.user_says(f"Result of {tool}\n{tool_result}")
        return tool_result

    def notify_session_ended(self):
        self.event_bus.publish(EventType.SESSION_ENDED, SessionEndedEvent(self.agent_id))
