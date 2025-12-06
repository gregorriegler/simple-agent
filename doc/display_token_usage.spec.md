# Display Token Usage in Tab Title (API Data)

## Problem
Users cannot see which model is being used or how many tokens have been consumed.

## Solution
1.  **LLM Protocol Update**:
    -   Update `LLM` protocol to return a `LLMResponse` object instead of a string.
    -   `LLMResponse` contains `content` (str), `model` (str), and `usage` (dict).
    -   Update `ClaudeLLM`, `OpenAILLM`, and `GeminiLLM` to return this object.

2.  **Agent Changes**:
    -   Update `Agent.llm_responds` to handle `LLMResponse`.
    -   Extract `token_count` (total tokens) and `model`.
    -   Emit `AssistantRespondedEvent` with `model`, `token_count`, and `max_tokens` (looked up via helper).

3.  **Event Update**:
    -   Update `AssistantRespondedEvent` dataclass to include:
        ```python
        model: str
        token_count: int
        max_tokens: int
        ```

4.  **Frontend (Textual)**:
    -   Update `TextualDisplay` to subscribe to `AssistantRespondedEvent`.
    -   Update `TextualApp` to update the tab title.

## Design Details

### LLM Response
```python
@dataclass
class TokenUsage:
    input_tokens: int
    output_tokens: int
    total_tokens: int

@dataclass
class LLMResponse:
    content: str
    model: str
    usage: TokenUsage
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

### Model Info Helper
```python
class ModelInfo:
    KNOWN_MODELS = {
        "gpt-4o": 128000,
        "claude-3-5-sonnet-20240620": 200000,
        # ... others
    }
    
    @staticmethod
    def get_context_window(model_name: str) -> int:
        # Fuzzy matching or direct lookup
        return ModelInfo.KNOWN_MODELS.get(model_name, 0)
# Slices

## [ ] Slice 1: End-to-End Walking Skeleton
- [ ] **Core Types**: Update `LLM` protocol and introduce `LLMResponse`, `TokenUsage`.
- [ ] **Agent Logic**: Update `Agent` to handle `LLMResponse` and emit enriched event.
- [ ] **Infrastructure**: Update `OpenAILLM` to return real usage data; update other providers with dummy data.
- [ ] **UI**: Update Textual app to display token usage in tab title.
```