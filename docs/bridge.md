# Bridge Documentation

The `bridge.py` script provides a way to interact with the Simple Agent through the file system. It allows you to act as the "LLM" by reading prompts from a file and providing responses in another. It also captures the Terminal User Interface (TUI) state into a readable Markdown file.

## How to Run

From the project root, run:

```bash
uv run bridge.py
```

The script runs in "control mode" by default, where you provide the LLM responses manually.

## Directory Structure

When the bridge is running, it creates a `bridge/` directory:

- `bridge/inbox/message.txt`: The input file where you write your user-facing prompts to the agent.
- `bridge/inbox/llm_response.txt`: Where you provide the agent's next response (including tool calls), pretending to be the LLM.

- `bridge/outbox/state.md`: This is the main output file. It contains the current screen capture (in plain text), chat history, tool logs, and active TODOs. It updates every 0.5 seconds.
- `bridge/outbox/llm_prompt.md`: This file is crucial for using the bridge effectively. It contains the **entire context** that would be sent to an LLM for generating a response. This includes the agent's detailed system prompt, its specific role, the exact tools it has access to, and the full conversation history. Before writing a response in `llm_response.txt`, you should always inspect this file to understand the agent's current capabilities and state.

- `bridge/status`: Contains the current status of the bridge. Common statuses include:
  - `WAITING_FOR_USER_INPUT`: The agent is ready for you to provide a prompt in `inbox/message.txt`.
  - `AGENT_IS_THINKING`: The agent is processing your request.
  - `WAITING_FOR_LLM_RESPONSE`: The agent is paused, waiting for you to provide a manual response in `inbox/llm_response.txt`.

## Interaction Flow

1. **Start the agent**: The agent will start and wait for user input.
2. **Monitor Progress**: Open `bridge/outbox/state.md` in a Markdown-capable viewer (or just a text editor) to watch the agent work.
3. **Provide User Input**: Check `bridge/status`. When it says `WAITING_FOR_USER_INPUT`, create or edit `bridge/inbox/message.txt` with your message. The bridge will detect the file, send the content to the agent, and then delete the file.
4. **Provide LLM Response**: Check `bridge/status`. When it says `WAITING_FOR_LLM_RESPONSE`:
    a. Read the full context from `bridge/outbox/llm_prompt.md`.
    b. Write the agent's next action (text or tool calls) into `bridge/inbox/llm_response.txt`. The bridge will process it and delete the file.
5. **Repeat**: Continue the cycle of providing user input and LLM responses.
6. **Exit**: To stop the bridge, you can write `/exit` into `bridge/inbox/message.txt` or use `Ctrl+C` in the terminal where the bridge is running. You can also use `/cancel` to stop the agent's current task.

## Formatting

The `state.md` file uses the following structure:
- **Screen**: A text-only representation of the TUI.
- **Agent Info**: Current agent name and ID.
- **Chat History**: The full conversation log.
- **Tool Log**: Details of tool executions, including arguments and results.
- **TODOs**: The agent's internal checklist.
- **Current Input**: What is currently typed in the agent's input field.