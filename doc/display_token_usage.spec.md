# Display Token Usage in Tab Title

## Problem
Users cannot see which model is being used or how many tokens have been consumed. 
This information is important for managing costs and avoiding context window limits.

## Solution
1.  **Backend Changes**:
    -   Update `LLM` protocol to return a `LLMResponse` object instead of a string.
    -   `LLMResponse` will contain `content` (str), `model` (str), and `usage` (dict/object with input/output/total tokens).
    -   Update `ClaudeLLM`, `OpenAILLM`, and `GeminiLLM` to extract and return this information.
    -   Update `Agent` to extract content from `LLMResponse` and emit a `TokenUsageEvent`.
    -   `TokenUsageEvent` will contain `agent_id`, `model`, `input_tokens`, `output_tokens`, `total_tokens`.

2.  **Context Window & Percentage**:
    -   To calculate percentage, we need the model's context window limit.
    -   We will implement a `ModelInfo` helper that maps common model names (e.g., `gpt-4o`, `claude-3-5-sonnet`) to their context window sizes.
    -   We will also allow overriding this via `context_window` in `.simple-agent.toml` (optional).
    -   `Agent` or `TextualDisplay` will use this to calculate percentage.

3.  **Frontend (Textual)**:
    -   Update `TextualDisplay` to listen for `TokenUsageEvent`.
    -   Calculate percentage used: `(total_tokens / context_window) * 100`.
    -   Update `TextualApp` to handle `TokenUsageMessage` and update the corresponding tab's title.
    -   Format: `Title [Model: 50%]`.

## Design Details

### LLM Protocol
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
    usage: TokenUsage | None
```

### Event
```python
@dataclass
class TokenUsageEvent:
    agent_id: AgentId
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
```

### UI Update
-   The tab title is currently set once. We need a way to update it.
-   `TabPane` (Textual) has a `label` property or we update the `Tab` widget directly.
-   `TabbedContent` allows accessing tabs.