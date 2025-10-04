# Simple Agent

[![Tests](https://github.com/gregorriegler/simple-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/gregorriegler/simple-agent/actions/workflows/tests.yml)

## Components

### [`agent.py`](agent.py:1)
Agent that manages chat sessions with Claude AI, integrates tool execution, and coordinates the modernization workflow.

### [`ToolLibrary`](tools/tool_library.py:13)
Central registry and execution engine for all available tools, combining static tools with dynamically discovered tools

### [`SystemPromptGenerator`](system_prompt_generator.py:3)
Dynamically generates system prompts for Claude AI by discovering and documenting available tools.

## Installation and Usage

### Method 1: Using the shell script (recommended for development)
```bash
./agent.sh "your message here"
./agent.sh --help
./agent.sh --continue  # continue previous session
```

### Method 2: Using uv directly
```bash
uv run agent "your message here"
uv run agent --help
uv run agent --continue  # continue previous session
```

### Method 3: Install globally with uv
```bash
uv tool install .
agent "your message here"
```

### Examples
```bash
# Start interactive session
./agent.sh "say hello"

# Continue existing session
./agent.sh --continue "Optional Message"
```

## Configuration

Create an `simple-agent.toml` file in the directory where you run the agent:

```toml
[claude]
api_key = "your-claude-api-key-here"
model = "claude-sonnet-4-5-20250929"

[paths]
refactoring_tools_path = "/path/to/your/tools"
```

The agent will look for this file in the current working directory and exit with an error if not found.

## Direct Tool Usage

```bash
./list_tools.sh

./run_tool.sh ls .
```

## Development

```bash
# Run tests
./test.sh

# Approve received files
./approve.sh

# Test the System Prompt
./system_prompt.sh
```

## Text-to-Speech Setup

The `say.py` script requires a Piper TTS voice model to function. Download the required model:

```bash
# Download the voice model (61MB)
curl -L -o en_US-lessac-medium.onnx "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx"
curl -L -o en_US-lessac-medium.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json"
```

Or use the provided script:
```bash
./download_voice_model.sh
```

Then use:
```bash
./say.py "Hello world"
# or
./say.sh "Hello world"
```
