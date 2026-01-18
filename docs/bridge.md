# Bridge Documentation

The `bridge.py` script provides a way to interact with the Simple Agent through the file system. it captures the Terminal User Interface (TUI) state into a readable Markdown file and listens for user input via a text file.

## How to Run

From the project root, run:

```bash
uv run bridge.py
```

By default, it runs with the LLM stub for testing. To use a real LLM, you would need to modify the script or ensure your environment is configured for remote LLM access.

## Directory Structure

When the bridge is running, it creates a `bridge/` directory:

- `bridge/outbox/state.md`: This is the main output file. It contains the current screen capture (in plain text), chat history, tool logs, and active TODOs. It updates every 0.5 seconds.
- `bridge/status`: Contains the current status of the bridge. Common statuses include:
  - `WAITING_FOR_USER_INPUT`: The agent is ready for you to provide a prompt in `inbox/message.txt`.
  - `AGENT_IS_THINKING`: The agent is processing your request (the LLM is working).
  - `WAITING_FOR_LLM_RESPONSE`: (Control Mode Only) The agent is paused, waiting for you to provide a manual response in `inbox/llm_response.txt`.
- `bridge/inbox/message.txt`: The input file where you write your prompts.

### Control Mode (Optional)

If you run the bridge with the `--control` flag:
```bash
uv run bridge.py --control
```
The bridge will also wait for manual LLM responses:
- `bridge/outbox/llm_prompt.md`: This file is crucial for using control mode effectively. It contains the **entire context** sent to the LLM for generating a response. This includes the agent's detailed system prompt, its specific role, the exact tools it has access to, and the full conversation history. Before writing a response, you should always inspect this file to understand the agent's current capabilities and state.
- `bridge/inbox/llm_response.txt`: Where you provide the agent's next response (including tool calls).

## Interaction Flow

1. **Monitor Progress**: Open `bridge/outbox/state.md` in a Markdown-capable viewer (or just a text editor) to watch the agent work.
2. **Wait for Prompt**: Check `bridge/status`. When it says `WAITING`, the agent is ready for your input.
3. **Provide Input**: Create or edit `bridge/inbox/message.txt` with your message. The bridge will detect the file, send the content to the agent, and then delete the file.
4. **Exit**: To stop the bridge, you can write `--exit` into `bridge/inbox/message.txt` or use `Ctrl+C` in the terminal where the bridge is running. You can also use `--help` for in-line instructions.

## Formatting

The `state.md` file uses the following structure:
- **Screen**: A text-only representation of the TUI.
- **Agent Info**: Current agent name and ID.
- **Chat History**: The full conversation log.
- **Tool Log**: Details of tool executions, including arguments and results.
- **TODOs**: The agent's internal checklist.
- **Current Input**: What is currently typed in the agent's input field.