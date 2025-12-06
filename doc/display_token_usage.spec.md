# Display Token Usage in Tab Title (Client-Side Estimation)

## Problem
Users cannot see which model is being used or how many tokens have been consumed relative to the context window.

## Solution
1.  **Client-Side Estimation**:
    -   We will estimate token usage on the client side (in `Agent`) to avoid changing the LLM protocol.
    -   Heuristic: 1 token ~= 4 characters.
    -   We will maintain a `ModelRegistry` with known context window sizes (e.g., `gpt-4o`: 128k, `claude-3-5-sonnet`: 200k).
    -   Configuration in `.simple-agent.toml` can override `context_window` and `model_name`.

2.  **Agent Changes**:
    -   `Agent` will receive `model_name` in `__init__`.
    -   In `llm_responds()`, `Agent` will calculate total characters in `self.context` and the new answer.
    -   Convert characters to tokens.
    -   Retrieve `max_tokens` for the model.
    -   Emit `AssistantRespondedEvent` with additional metadata: `model`, `token_count`, `max_tokens`.

3.  **Event Update**:
    -   Update `AssistantRespondedEvent` dataclass to include:
        ```python
        model: str
        token_count: int
        max_tokens: int
        ```

4.  **Frontend (Textual)**:
    -   Update `TextualDisplay` to subscribe to `AssistantRespondedEvent`.
    -   When received, post a `TokenUsageMessage` (internal UI message) to `TextualApp`.
    -   `TextualApp` updates the tab title: `Title [Model: 50%]`.

## Design Details

### Token Estimation
```python
def estimate_tokens(text: str) -> int:
    return len(text) // 4
```

### Event
```python
@dataclass
class AssistantRespondedEvent(AgentEvent):
    event_name: ClassVar[str] = "assistant_responded"
    response: str
    model: str = ""
    token_count: int = 0
    max_tokens: int = 0
```