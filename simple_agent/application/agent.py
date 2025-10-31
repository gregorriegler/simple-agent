from .input import Input
from .llm import LLM, Messages
from .session_storage import SessionStorage
from .tool_library import ToolResult, ContinueResult, ToolLibrary, MessageAndParsedTools, ParsedTool
from .event_bus_protocol import EventBus
from .events import AssistantSaidEvent, AssistantRespondedEvent, ToolCalledEvent, ToolResultEvent, SessionEndedEvent, \
    SessionInterruptedEvent, \
    UserPromptRequestedEvent, UserPromptedEvent


class Agent:
    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        system_prompt: str,
        tools: ToolLibrary,
        llm: LLM,
        user_input: Input,
        event_bus: EventBus,
        session_storage: SessionStorage
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.llm: LLM = llm
        self.system_prompt = system_prompt
        self.tools = tools
        self.user_input = user_input
        self.event_bus = event_bus
        self.session_storage = session_storage
        self._tool_call_counter = 0

    def start(self, context: Messages = Messages()):
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
                message, tools  = self.llm_responds(context)
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
            self.event_bus.publish(SessionInterruptedEvent(self.agent_id))

        return tool_result

    def notify_about_interrupt(self):
        self.event_bus.publish(SessionInterruptedEvent(self.agent_id))
        self.event_bus.publish(UserPromptRequestedEvent(self.agent_id))

    def notify_about_message(self, message):
        if message:
            self.event_bus.publish(AssistantSaidEvent(self.agent_id, message))

    def llm_responds(self, context) -> MessageAndParsedTools:
        answer = self.llm(self.system_prompt, context.to_list())
        context.assistant_says(answer)
        self.event_bus.publish(AssistantRespondedEvent(self.agent_id, answer))
        return self.tools.parse_message_and_tools(answer)

    def user_prompts(self, context):
        if not self.user_input.has_stacked_messages():
            self.event_bus.publish(UserPromptRequestedEvent(self.agent_id))
        prompt = self.read_user_input_and_prompt_it(context)
        return prompt

    def read_user_input_and_prompt_it(self, context):
        prompt = self.user_input.read()
        if prompt:
            context.user_says(prompt)
            self.event_bus.publish(UserPromptedEvent(self.agent_id, prompt))
        return prompt

    def execute_tool(self, tool: ParsedTool, context):
        self._tool_call_counter += 1
        call_id = f"{self.agent_id}::tool_call::{self._tool_call_counter}"
        self.event_bus.publish(ToolCalledEvent(self.agent_id, call_id, tool))
        tool_result = self.tools.execute_parsed_tool(tool)
        self.event_bus.publish(ToolResultEvent(self.agent_id, call_id, tool_result))
        if isinstance(tool_result, ContinueResult):
            context.user_says(f"Result of {tool}\n{tool_result}")
        return tool_result

    def notify_session_ended(self):
        self.event_bus.publish(SessionEndedEvent(self.agent_id))
