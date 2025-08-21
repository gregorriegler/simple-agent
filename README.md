# Minimal Agent

## Components

### [`agent.py`](agent.py:1)
Agent that manages chat sessions with Claude AI, integrates tool execution, and coordinates the modernization workflow.

### [`ToolLibrary`](tools/tool_library.py:13)
Central registry and execution engine for all available tools, combining static tools with dynamically discovered tools

### [`SystemPromptGenerator`](system_prompt_generator.py:3)
Dynamically generates system prompts for Claude AI by discovering and documenting available tools.

## Usage

### Basic Modernization Session

```bash
# Start interactive modernization session
./agent.sh --new Modernize Project Xy

# Continue existing session
./agent.sh Optional Message
```

### Direct Tool Usage

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
