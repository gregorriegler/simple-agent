# Slash Model Command

## Problem

There's no way to switch LLM models mid-session. Users must restart the application with a different configuration to use a different model.

## Solution

When the user types `/model <name>` in the chat input:
1. Switch `self.llm` to the new model via `llm_provider.get(name)`
2. Preserve conversation history
3. Continue chatting with the new model

When the user types `/model` without a name:
- Show error: "Usage: /model <model-name>"

Invalid model names fall back to the registry's default behavior (no special handling).

### Design Change

Currently `Agent` receives an instantiated `LLM`. Change to:
- Pass `LLMProvider` + initial model name (string) to `Agent`
- `Agent` instantiates its own LLM via `llm_provider.get(model_name)`
- `Agent` can switch models by calling `self.llm = self.llm_provider.get(new_name)`

### Relevant Code

- [simple_agent/application/agent.py](../../simple_agent/application/agent.py) - Agent class, `/clear` handling in `user_prompts()`
- [simple_agent/application/llm.py](../../simple_agent/application/llm.py) - `LLMProvider` protocol
- [simple_agent/application/agent_factory.py](../../simple_agent/application/agent_factory.py) - Creates Agent with LLM (line 83-92)
- [simple_agent/infrastructure/llm.py](../../simple_agent/infrastructure/llm.py) - `RemoteLLMProvider` implementation