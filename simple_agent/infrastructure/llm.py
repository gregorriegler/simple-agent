from simple_agent.application.llm_stub import create_llm_stub
from simple_agent.infrastructure.claude.claude_client import ClaudeLLM
from simple_agent.infrastructure.user_configuration import UserConfiguration
from simple_agent.infrastructure.openai import OpenAILLM


def create_llm(stub_llm, user_config: UserConfiguration):
    model_config = user_config.model_config()
    if stub_llm:
        return create_llm_stub(
            [
                "Starting task\n🛠️ subagent orchestrator Run bash echo hello world and then complete",
                "Subagent1 handling the orchestrator task\n🛠️ subagent coding Run bash echo hello world and then complete",
                "Subagent2 updating todos\n🛠️ write-todos\n- [x] Feature exploration\n- [ ] **Implementing tool**\n- [ ] Initial setup\n🛠️🔚",
                "Subagent2 running a slow bash command\n🛠️ bash sleep .4",
                "Subagent2 running the bash command\n🛠️ bash echo hello world",
                "Subagent2 reading AGENTS.md\n🛠️ cat AGENTS.md",
                "🛠️ create-file newfile.txt\ncontent of newfile.txt\n",
                "🛠️ edit-file newfile.txt replace 1\nnew content of newfile.txt\n",
                "🛠️ bash rm newfile.txt",
                "🛠️ complete-task Subagent2 completed successfully",
                "🛠️ complete-task Subagent1 completed successfully",
                "🛠️ complete-task Main task completed successfully"
            ]
        )

    if model_config.adapter == "openai":
        return OpenAILLM(model_config)

    return ClaudeLLM(model_config)
