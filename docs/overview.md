# Simple Agent - Architectural Overview

Simple Agent is a general-purpose, extensible, transparent agent system designed for command-line use. It emphasizes modularity through markdown-defined agents and follows a Ports and Adapters architecture.

## 🏗️ Architecture

The codebase follows a minimal **Ports and Adapters** (Hexagonal) architecture:

- **`simple_agent/main.py`**: The entry point. Wires up dependencies (adapters) and starts the session. [Main Entry Point](../simple_agent/main.py)
- **`simple_agent/application/`**: Contains the core logic and domain model. This layer is independent of infrastructure.
    - `session.py`: Orchestrates the chat session and maintains high-level flow.
    - `agent.py`: Core chat loop, tool execution coordination, and interaction logic.
    - `events.py` & `event_bus.py`: Implements an event-driven architecture to decouple core logic from side effects like UI updates.
    - `tool_library.py`: Defines the `ToolCall` shape, tool declarations, and the protocols for resolving and executing calls.
    - `session_storage.py`: Protocol for saving and loading conversation history.
- **`simple_agent/infrastructure/`**: Implementation of ports (e.g., file system, LLM clients, user interface).
    - `textual/`: The Textual-based TUI implementation.
    - `claude/`, `openai/`, `gemini/`: LLM client adapters.
    - `system_prompt/`: System prompt generation logic.
- **`simple_agent/tools/`**: Built-in tool implementations available to agents.
    - `all_tools.py`: Tool registration and factory logic.

## 🧩 Key Concepts

- **Markdown-Driven Agents**: Agents are defined in `*.agent.md` files. These define the agent's persona, capabilities, and system prompt.
- **Event-Driven UI**: The UI reacts to events (e.g., `AssistantSaidEvent`, `ToolCalledEvent`) emitted by the application layer, ensuring separation of concerns.
- **Subagents**: Agents can spawn subagents to handle specific tasks, promoting modularity.
- **Transparency**: The system is designed to make tool calls and agent reasoning visible to the user.

## 🔧 Tool Calling

Every LLM adapter calls tools natively through its API; no text syntax is parsed.

- **One core shape**: a `ToolCall` is the tool's name, its arguments as a typed dict coerced through the tool's declaration (flags to `bool`, numbers to `int`/`float`, the rest text), and an opaque `provider_state` dict. The core persists that state in the `ToolCalledEvent` without reading it.
- **Adapters map the shape to their wire format**: each adapter declares the tools from the same `ToolArguments`, reads the API's calls into `ToolCall`s, and renders the history back through a `MessageRenderer`, one method per message kind. Every adapter keeps the call id it was given as `native_id` in the provider state, so a result is replayed under the id the model used; a call made under another adapter gets a synthetic id matched to its result by order.
- **Gemini also keeps a thought signature**: Gemini rejects a function call on replay unless it is led by the thought that produced it. Calls Gemini made itself carry that signature in the provider state; calls made by another adapter or before a model switch have none and are replayed as text describing the call and its result (`Called bash command="ls"`). The other adapters need no such fallback.
- **The UI tab title** renders a call as one line of command text through `call_header`, which needs the tool declarations; they are a required argument of the app.

## 🛠️ Development & Process

The project follows a strict TDD and process-driven workflow.

- **Tests**: Run `./test.sh` to execute tests. Infrastructure is tested via integration tests; application logic is unit tested.
- **Coverage**: Run `./coverage.sh` to check code coverage.

## 📂 Important Directories

- `simple_agent/`: Source code.
- `tests/`: Test suite.
- `process/`: Documentation of the development processes.
- `custom_agents/`: Example or custom agent definitions.
- `docs/`: Documentation and diagrams.

For more details on usage and configuration, see the [README](../README.md).
