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
- `bridge/status`: Contains the current status of the bridge (`WAITING` when it needs input, `PROCESSING` when the agent is working).
- `bridge/inbox/message.txt`: The input file where you write your prompts.

## Interaction Flow

1. **Monitor Progress**: Open `bridge/outbox/state.md` in a Markdown-capable viewer (or just a text editor) to watch the agent work.
2. **Wait for Prompt**: Check `bridge/status`. When it says `WAITING`, the agent is ready for your input.
3. **Provide Input**: Create or edit `bridge/inbox/message.txt` with your message. The bridge will detect the file, send the content to the agent, and then delete the file.
4. **Exit**: To stop the bridge, you can write `/exit` into `bridge/inbox/message.txt` or use `Ctrl+C` in the terminal where the bridge is running.

## Formatting

The `state.md` file uses the following structure:
- **Screen**: A text-only representation of the TUI.
- **Agent Info**: Current agent name and ID.
- **Chat History**: The full conversation log.
- **Tool Log**: Details of tool executions, including arguments and results.
- **TODOs**: The agent's internal checklist.
- **Current Input**: What is currently typed in the agent's input field.