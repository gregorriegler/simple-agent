# NOW 
- fix logs. nicely human readable request and response log
- other markdown debug logs add noise
- are we sending proper tool result responses to the llms?
- coverage
- token usage % counter not going up
- haiku still not zeroed in
- /clear

# NEXT
- add files via @

# LATER
- rag for code
- say as a tool (too much noise in root)
- add review agent
- shutdown responsibilities should be singular. Proof: the SessionEnded event already calls AllDisplays.exit → TextualDisplay.exit →
TextualApp.shutdown, yet run_session invokes display.exit() again (application/session.py:64-65), causing double shutdown and mixed ownership of lifecycle.
- Hypothesis: subagents should not share input buffers. Proof: main.py:108 returns the same Input for every subagent, and SubagentTool pushes the task
description onto that shared stack (tools/subagent_tool.py:47-49), so nested agents can steal each other’s queued prompts and are unnecessarily coupled.
- ModelConfig does validation and ModelConfig, belongs to application
- --version
- better feedback that we are still waiting for a http response
- tdd loop
- api key via env var
- Login with Claude Max subscription (We need to ask for a OAuth ClientId)
- Refactoring opportunity in edit_file_tool.py
- Simpler switching between models
