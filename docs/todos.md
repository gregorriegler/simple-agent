# NOW
- failing test in pipeline
- warnings in tests
- slash command registry does not include the handler
- slash command autocomplete is not as nice
- plan agent vs slicer agent

# NEXT
- /clear does not reset token usage %
- add files via @
- coverage drilldown slow because redoing the whole thing
- the subagent tool description need to allow for a subscription per agent, so we can explain that a test-writer will only ever write a single test

# LATER
- token usage % counter not going up for gemini
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
