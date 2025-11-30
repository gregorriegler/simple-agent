from simple_agent.application.display import Display


class FakeDisplay(Display):

    def __init__(self):
        self.events: list[dict] = []

    def _record(self, name: str, agent_id: str, payload=None) -> None:
        self.events.append({"event": name, "agent_id": agent_id, "payload": payload})

    def agent_created(self, event) -> None:
        self._record("agent_created", event.agent_id, {"name": getattr(event, "agent_name", None)})

    def start_session(self, event) -> None:
        is_continuation = getattr(event, "is_continuation", False)
        self._record("start_session", event.agent_id, {"is_continuation": is_continuation})

    def wait_for_input(self, event) -> None:
        self._record("wait_for_input", event.agent_id)

    def user_says(self, event) -> None:
        self._record("user_says", event.agent_id, getattr(event, "input_text", None))

    def assistant_says(self, event) -> None:
        self._record("assistant_says", event.agent_id, getattr(event, "message", None))

    def tool_call(self, event) -> None:
        self._record("tool_call", event.agent_id, {"call_id": getattr(event, "call_id", None), "tool": getattr(event, "tool", None)})

    def tool_result(self, event) -> None:
        self._record("tool_result", event.agent_id, {"call_id": getattr(event, "call_id", None), "result": getattr(event, "result", None)})

    def interrupted(self, event) -> None:
        self._record("interrupted", event.agent_id)

    def exit(self, event) -> None:
        self._record("exit", event.agent_id)
