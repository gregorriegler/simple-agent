# Simple Agent

[![Tests](https://github.com/gregorriegler/simple-agent/actions/workflows/tests.yml/badge.svg)](https://github.com/gregorriegler/simple-agent/actions/workflows/tests.yml)
[![Coverage](docs/coverage.svg)](#generate-coverage-locally)
[![LoC](docs/loc.svg)](#generate-coverage-locally)

Simple Agent aims to be a simple, extensible, and transparent general-purpose agent system.

![Simple Agent Screenshot](docs/screenshot.png)

## Features

- Transparency: observe every tool call and agent decision with ease
- Markdown-driven subagents: build modular agents from simple markdown files
- Token-efficient tool calling: optimized tool execution to reduce overhead
- CLI-first design: built for command-line use, with optional non-interactive mode
- API integration: works with OpenAI, Anthropic, and Google Gemini APIs

## Installation and Usage

### Quick install (recommended)
```bash
./install.sh
```

### Usage method 1: shell wrapper (recommended for development)
```bash
./agent.sh "your message here"
./agent.sh --agent <agent-type>  # defines the starting agent
./agent.sh --continue            # continue previous session
./agent.sh --user-interface console
./agent.sh --system-prompt       # print rendered system prompt
./agent.sh --stub                # run against the built-in LLM stub
./agent.sh --non-interactive     # suppress interactive prompts
```

### Usage method 2: invoke the script with uv
```bash
uv run --project . --script simple_agent/main.py "your message here"
uv run --project . --script simple_agent/main.py --help
```

### Install globally with uv
```bash
uv tool install .
agent "your message here"
```

### Examples
```bash
# Start an interactive session using the default textual UI
./agent.sh "say hello"

# Run in the console UI and continue the previous session
./agent.sh --user-interface console --continue
```

## Configuration

Create a `.simple-agent.toml` file either in your home directory or in the directory where you run the agent. Values from the current directory override those from `~`.

```toml
[model]
default = "claude"  # Which model configuration to use by default

[models.claude]
model = "claude-sonnet-4-5-20250929"
adapter = "claude"
api_key = "${ANTHROPIC_API_KEY}"  # Or use a literal API key
```

The `[model]` section specifies which model to use by default. Define one or more models under `[models.*]` sections. API keys can reference environment variables using `${VAR_NAME}` syntax.

### Multiple models

You can define multiple model configurations and switch between them:

```toml
[model]
default = "claude"

[models.claude]
model = "claude-sonnet-4-5-20250929"
adapter = "claude"
api_key = "${ANTHROPIC_API_KEY}"

[models.openai]
model = "gpt-4o"
adapter = "openai"
api_key = "${OPENAI_API_KEY}"
# base_url = "https://openrouter.ai/api/v1"  # Optional: for OpenRouter, etc.

[models.gemini]
model = "gemini-2.5-pro"
adapter = "gemini"
api_key = "${GOOGLE_API_KEY}"
```

### Adapter-specific configuration

**OpenAI adapter:** You can point the client at a compatible provider by overriding `base_url`, e.g. set it to `https://openrouter.ai/api/v1` for OpenRouter.

**Gemini adapter:** Configure with a Google AI API key and model name (e.g., `gemini-2.5-pro`, `gemini-1.5-flash`).

### Custom agent definitions

Agent definition files (`*.agent.md`) are discovered from the built-in `simple_agent` package and from `.simple-agent/agents` in your project directory. To point the agent at a different directory, add `agent_definitions_dir = "/path/to/agents"` under the `[paths]` section of `.simple-agent.toml`. When configured, only the files from that directory are used for type discovery and prompt loading.

To change which agent starts first, set it via the `[agents]` section:

```toml
[agents]
path = "/path/to/custom/agents"
start = "orchestrator"
```

## Development

```bash
# Run tests
./test.sh                    # Run all tests (stops on first failure)
./test.sh test_foo.py        # Run a specific test file
./test.sh test_foo           # Run tests matching a pattern
./test.sh -v                 # Verbose mode with full tracebacks
./test.sh -h                 # Show help

# Approve received files
./approve.sh

# Generate coverage locally and refresh the badges
./coverage.sh               # generate code coverage report
./coverage.sh foo.py        # show coverage of a specific file
./coverage.sh --badge       # update the coverage badge
```

Running the coverage script with `--badge` creates `docs/coverage.svg`, and `loc_badge.py` generates `docs/loc.svg`, keeping the badges self-hosted.

Badge updates run automatically on `main` via the [`Coverage Badge` workflow](.github/workflows/coverage-badge.yml), which commits refreshed coverage and LoC badges after each push.

## Components

- [`simple_agent/main.py`](simple_agent/main.py): CLI entry point that wires the event bus, user interface, Claude client, and tool library before running a session.
- [`simple_agent/application/session.py`](simple_agent/application/session.py): Orchestrates the lifecycle of a chat session, including streaming assistant output, tool execution, and persistence.
- [`simple_agent/application/agent.py`](simple_agent/application/agent.py): Core chat loop that gathers user input, streams Claude responses, and coordinates tool execution.
- [`simple_agent/tools/all_tools.py`](simple_agent/tools/all_tools.py): Registers built-in tools (bash, cat, edit_file, etc.), parses tool calls, and executes them.
- [`simple_agent/infrastructure/system_prompt/agent_definition.py`](simple_agent/infrastructure/system_prompt/agent_definition.py): Loads agent definitions and renders prompts that describe available tools to Claude.

## Text-to-Speech setup

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
