# Simple Agent - Architectural Overview

Simple Agent is a general-purpose, extensible, transparent agent system designed for command-line use. It emphasizes modularity through markdown-defined agents and follows a Ports and Adapters architecture.

## 🏗️ Architecture

The codebase follows a minimal **Ports and Adapters** (Hexagonal) architecture:

- **`simple_agent/main.py`**: The entry point. Wires up dependencies (adapters) and starts the session. [Main Entry Point](../simple_agent/main.py)
- **`simple_agent/application/`**: Contains the core logic and domain model. This layer is independent of infrastructure.
    - `session.py`: Orchestrates the chat session and maintains high-level flow.
    - `agent.py`: Core chat loop, tool execution coordination, and interaction logic.
    - `events.py` & `event_bus.py`: Implements an event-driven architecture to decouple core logic from side effects like UI updates.
    - `tool_library.py`: Defines protocols and logic for tool parsing and execution.
    - `session_storage.py`: Protocol for saving and loading conversation history.
- **`simple_agent/infrastructure/`**: Implementation of ports (e.g., file system, LLM clients, user interface).
    - `display_hub.py`: Central hub that subscribes to events and delegates rendering to specific display implementations (e.g., Textual).
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