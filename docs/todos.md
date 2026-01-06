# NOW
- linter
- agent slash command

# NEXT
- proper session storage
- async subagents
- coverage drilldown slow because redoing the whole thing
- the subagent tool description need to allow for a subscription per agent, so we can explain that a test-writer will only ever write a single test

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


###

gemini:
Response missing parts field

2026-01-06 21:51:14 - DEBUG - simple_agent.infrastructure.logging_http_client -
HTTP/1.1 200 OK
Content-Type: application/json; charset=UTF-8
Vary: Origin, X-Origin, Referer
Content-Encoding: gzip
Date: Tue, 06 Jan 2026 20:51:14 GMT
Server: scaffolding on HTTPServer2
X-Xss-Protection: 0
X-Frame-Options: SAMEORIGIN
X-Content-Type-Options: nosniff
Server-Timing: gfet4t7; dur=14147
Alt-Svc: h3=":443"; ma=2592000,h3-29=":443"; ma=2592000
Transfer-Encoding: chunked

{
"candidates": [
{
"content": {},
"finishReason": "STOP",
"index": 0
}
],
"usageMetadata": {
"promptTokenCount": 21505,
"totalTokenCount": 23623,
"cachedContentTokenCount": 16346,
"promptTokensDetails": [
{
"modality": "TEXT",
"tokenCount": 21505
}
],
"cacheTokensDetails": [
{
"modality": "TEXT",
"tokenCount": 16346
}
],
"thoughtsTokenCount": 2118
},
"modelVersion": "gemini-3-flash-preview",
"responseId": "wnVdadmlDpHYxN8Pk7Hg6QE"
}
