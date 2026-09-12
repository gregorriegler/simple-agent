# Native tool calls: making the Gemini path right

## Intent

Every LLM chat API has native tool calling, so the emoji text syntax will die
at some point. The structured tool call (name, argument dict, provider state)
must become the source of truth, and the emoji syntax one adapter over that
shape that can be deleted as a unit. The user stays in charge of context: no
compaction, no skills, agents only.

Scope of this story: only the path that consumes the Gemini adapter, done in
small steps that break nothing, each step tests first and its own commit.
Native calling for Claude and OpenAI was a later story; it will map the same
core shape to their wire formats.

## Where we started (commit c2dfca1b)

Gemini was the only native adapter and it was bolted onto a text-shaped core.
A native call was flattened into the positional emoji string the moment it
arrived and rebuilt by re-splitting that string on every later request.
Three different parsers touched one call: a space-join in the adapter, shlex
in the tool, a plain whitespace split on replay. Concretely, a cat call on
`my notes.md` read the file `my`, lost the line-numbers flag, and was replayed
to Gemini as a different call than it had made.

Other findings from the first review:
- `tool_syntax = "native"` on a non-Gemini adapter silently removed all tools
- declared integer/boolean types were erased to strings
- calls and results were paired by two independent counters
- an ESC during a tool left a function call with no result in the history
- on `--continue` the history was rebuilt as plain text with no tool turns
- switching from Gemini to a text model dropped the calls entirely
- the thought signature was not persisted

## Achieved

Acceptance tests in `tests/agent/gemini_native_tool_calls_test.py` drive the
real Gemini client behind a scripted transport with real tools, and approve
both the session transcript and the exact request bodies sent back. Four
scenarios: a filename with a space, a continued session, an interrupted call,
a mid-session switch to a text model.

The core shape:
- the call (then `RawToolCall`, now `ToolCall`) carries `named_arguments` and
  the provider state (first as `native_id` and `thought_signature`)
- Gemini reads a function call into name, dict, id and signature only; it
  knows nothing about the emoji syntax or the tool declarations any more
- Gemini replays the dict verbatim, under the ids it sent, thought first
- tool-called events persist the dict, id and signature; old files still load

The emoji syntax as one adapter (binding happens once, at resolve time in
`AllTools.resolve_tool_calls`; see the cleanup section for the final shape):
- text call: positional header bound to declared names (single argument takes
  the whole text, shlex split otherwise, leftovers into the last argument,
  bool arguments are flags matched by name)
- native call: header text and body rendered from the dict, the inverse
  (`ToolArguments.render_header`: shell quoting, true flags by name)
- text adapters render a native assistant turn as emoji text when they see it

Tools read only `named_arguments` (first cat, create-file,
replace-file-content and subagent; the rest followed in the cleanup). The
positional parser module is deleted.

Session behaviour:
- `events_to_messages` rebuilds structured assistant turns and tool messages
  from tool-called and tool-result events, so `--continue` replays natively
- `ToolsExecutor` records results as they arrive; on ESC every call of the
  turn, started or not, gets an interrupted result, live and on replay
- model config rejects native syntax on adapters that only speak emoji, and
  unknown syntax names
- bool arguments are declared to Gemini as JSON booleans

Test bed: `with_llm_provider`, `cancelling_when(event)`, persists tool-called
events and subscribes persistence after replay, both as production does.

## Cleanup after the story

A second review found the seams the story had left, each fixed in its own
commit with the tests green:
- `ToolArguments` answers which header arguments are flags, which are
  positional, and whether one argument takes the whole text; the syntax no
  longer computes that twice
- `ToolArgument` answers its JSON type and whether it is a flag, under both
  the `bool` and `boolean` spellings; cat's `with_line_numbers` is declared
  as the flag it is, so a native call renders it by name, not as `true`
- a tool reads a flag through `RawToolCall.flag`, one truth test instead of
  one per tool
- the call carries no syntax marker: `str(call)` is `name arguments body`,
  the "Result of 🛠️" label is rendered by the emoji syntax, and the UI adds
  its own icon
- every assistant turn, with or without calls, is an `AssistantMessage`, and
  a tool's output is a `ToolResultMessage` carrying the call it answers; the
  Gemini adapter and the text renderer dispatch on the type
- the Gemini adapter asks a turn whether it signed it, rather than walking
  message keys
- `ChatMessage` is a union of four typed messages: `SystemMessage`,
  `UserMessage`, `AssistantMessage`, `ToolResultMessage`. The role-keyed
  wire dict exists only inside `to_text_messages`, where the text adapters
  ask for it; `split_system_prompt` hands Claude and Bedrock their system
  prompt, and Gemini flattens unsigned turns through `to_text_turn`, which
  stays typed
- a message renders itself through a `MessageRenderer`, one method per
  kind, so no adapter asks a message what it is. The text renderer and the
  Gemini `InteractionSteps` builder are the two renderers; a native Claude
  or OpenAI adapter is a third, and a new message kind fails at the
  protocol instead of falling through a chain
- every tool reads its arguments by name; none reads the header or body
  text
- the call is the name, the dict and the provider ids; the text fields are
  gone. The last declared positional argument is rendered unquoted, since
  it absorbs leftover tokens when bound, so `say hello` round-trips as
  written; a value with quotes in it is shell-quoted

## Binding belongs to the adapters

A third review asked who should bind and coerce a call. The answer: the
adapter, because it already holds the tool declarations it sent out, and
the consumer of an adapter wants finished calls, not half-products. Each
step its own commit, tests green:
- `ToolArguments.coerce` types a dict per the declaration: a flag from its
  spellings to a bool, everything else to text. Tools read a flag straight
  from the dict; `RawToolCall.flag` and the per-tool `str()`/`is_true` went
- the Gemini reader `to_tool_calls(steps, tools)` binds each function call
  to the tool it names and refuses an undeclared name (`UndeclaredTool`)
- `EmojiToolCallsLLM` wraps any client that still speaks emoji. The provider
  builds it with the tools; it renders the history to text turns before the
  inner call and binds the emoji calls in the answer afterwards, leaving the
  whole answer as text when a call names an unknown tool. Clients return
  plain text and know nothing about the emoji syntax; Gemini native binds
  inside and is handed out bare. `emoji_response` is gone
- `LLMResponse.tool_calls` carries bound calls. `AllTools.resolve_tool_calls`
  only pairs each call with the tool that runs it
- the pairing is `ToolInvocation(call, tool)` with `execute()`; the executor
  and the results container hold invocations and read `.call`
- `RawToolCall` is `ToolCall`: name, typed `named_arguments`, provider ids,
  nothing else. It has no `bind`, no `declaration`, no `header`/`body`/`str`
- `EmojiBracketToolSyntax(declarations)` renders a call's header, body and
  result label by looking the tool up; a call to a tool it does not know
  renders its values in order. `to_text_messages(messages, syntax)` and
  `to_text_turn` take the syntax; clients call `to_wire_messages`, a plain
  role mapping that raises on an unrendered tool turn. Gemini native builds
  a syntax from its declarations for unsigned turns; the UI receives one
  from `main.py` for the tab label
- loaded events need no binding: a persisted call is typed JSON and is
  replayed as it is. `bind_call` and `bind_tool_calls` are gone; the
  replayer's legacy text recovery uses `bind_emoji_calls`, the same routine
  as the wrapper. Only `EmojiToolCall.bind(tool)` binds, positional text to
  typed names, and it never takes `None`

Known smell left in place: `library.execute_tool_call(invocation)` stays as
the executor's seam because the test bed injects Ctrl+C there.

## Next steps

The Ctrl+C and provider-state leftovers are done: a `KeyboardInterrupt`
during a tool records the cancelled event and an interrupted result like ESC
does, and `ToolCall.provider_state` is an opaque dict the core persists
without reading; only the Gemini adapter knows its `thought_signature` and
`native_id` keys. Persisted tool-called events written before this carry
the two keys at the top level and load without them.

## OpenAI native

The second native adapter, on the chat completions API, shapes verified
against the types in `openai/openai-python`. `tool_syntax = "native"` on an
openai model hands `OpenAILLM(config, tools)` out bare. Acceptance tests in
`tests/agent/openai_native_tool_calls_test.py`: a filename with a space, a
continued session, an interrupted call.
- `openai_tools.py` declares each tool as `{"type": "function", "function":
  {name, description, parameters}}` and reads a message's `tool_calls` into
  `ToolCall`s: the JSON argument string decoded and coerced through the
  declaration, the call id as `provider_state["native_id"]`. An undeclared
  name or a malformed argument string is refused with the tool named
- `openai_messages.py` is the third `MessageRenderer`: an assistant turn
  carries its calls as `tool_calls` (arguments re-encoded as JSON, content
  `null` when there is none), a tool result is a `tool` message under the
  call's id. A call made without an id, under emoji or by another adapter,
  is replayed under a synthetic `call_N` matched to its result by order;
  chat completions needs no signature, so no text fallback
- `NATIVE_ADAPTERS` lists openai; the provider's native branch dispatches on
  the adapter

## Claude native

The third native adapter, on the Messages API, shapes checked against the
tool use reference. `tool_syntax = "native"` on a claude model hands
`ClaudeLLM(config, tools)` out bare. Acceptance tests in
`tests/agent/claude_native_tool_calls_test.py`: a filename with a space, a
continued session, an interrupted call.
- `claude_tools.py` declares each tool as `{name, description, input_schema}`
  and reads a response's `tool_use` blocks into `ToolCall`s: the input dict
  coerced through the declaration, the block id as
  `provider_state["native_id"]`. An undeclared name is refused with the tool
  named; the input is already JSON, so nothing to decode
- `claude_messages.py` is the fourth `MessageRenderer`: an assistant turn
  carries its calls as `tool_use` blocks after its text block (none when the
  text is empty), a tool result is a `tool_result` block under the call's id
  in a user turn, and the results of one turn share a single user message,
  as the API wants them. A call made without an id is replayed under a
  synthetic `toolu_N` matched to its result by order. A system message has
  no place in the history; the client splits it off as before
- the client renders every history through the block renderer, emoji or
  native, and joins a response's text blocks; the "first block must be text"
  reading is gone. `NATIVE_ADAPTERS` lists claude; the provider's native
  branch dispatches on the adapter

## Native by adapter

With all three API adapters native, the `tool_syntax` config key is gone.
The provider hands Claude, OpenAI and Gemini out bare with the tools;
`ModelConfig.tool_syntax` derives the name from the adapter, so the system
prompt still knows whether to document the tools as text. A `tool_syntax`
key left in an old config is ignored.

## Bedrock

Bedrock's `invoke_model` takes the Messages API shapes, so the Bedrock
adapter reuses the Claude adapter's block renderer, tool declarations and
`tool_use` reader as they are. The provider hands it out bare with the
tools like the other three; every adapter is native now.

## The emoji syntax is test-only

No model speaks emoji any more, so the syntax left production: the emoji
module, `EmojiToolCallsLLM` and the text-turn rendering live under
`tests/` (`emoji_syntax.py`, `emoji_llm.py`), where the stub LLMs are
still scripted as emoji text and the transcripts render calls back into
it. The system prompt documents no tools as text, `tool_syntax` is gone
from the provider and the config, and the stub provider answers with
structured calls. A call is rendered as one line of command text through
`call_header`/`call_body` where production still needs text: the UI's
tool title, and Gemini's replay of unsigned turns. History replay of a
log older than the granular events keeps the assistant text but no longer
recovers its calls.

## The emoji syntax is gone

The test bed scripts the stub LLM the way the adapters answer: a scripted
turn is a plain string, a bare `ToolCall`, or `says(text, *calls)` when
the model speaks before it calls. `tests/tool_calls.py` builds the calls
the tests make often (`cat`, `create_file`, `complete_task`, `subagent`
and the like); the rest use `ToolCall` directly. The provider hands the
stub out bare, a tool test executes a `ToolCall` through
`resolve_tool_calls`, and a persisted fixture carries the assistant's
words only, as production writes them now.

Transcripts render from the structure: an `assistant:` line carries the
words, each call is indented under it as its name and named arguments
(`cat filename="my notes.md" with_line_numbers=true`), and each result is
a `tool_result:` line, in the session transcript and in what a captured
model received.
The Gemini switch scenario now switches to another native model, which
receives the call as structured history.

Deleted: the emoji syntax and wrapper modules under `tests/`, their tests,
and the emoji parsing tests; the emoji text example left in
`replace-file-content`. What stays: `call_header` and `call_body` in
`ToolArguments`, because production still renders a call as one line of
command text for the UI tab title and for Gemini's replay of unsigned
turns; the transcripts show the named dict instead. One legacy-log test keeps
an emoji string in an old `assistant_responded` event to show that such
text is replayed as text.

## Leftovers closed

- Integer and number arguments are coerced to `int` and `float` like flags
  are to `bool`; a value that is no number stays text. No tool declares
  them yet, but a native adapter no longer promises a type it does not
  deliver
- Gemini replays an unsigned turn as the call's name and named arguments
  (`Called bash command="ls"`, `Result of bash command="ls":`), the same
  line the test transcripts use, through `describe_call`. It needs no
  declarations for that; `call_body` and `render_body` are gone
- The UI tab title still reads as command text through `call_header`, but
  the declarations are now a required argument of `TextualApp` and
  `AgentTabs`; the silent empty fallback is gone and every test passes
  the real `TOOL_DECLARATIONS`
