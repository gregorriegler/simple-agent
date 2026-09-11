# Native tool calls: making the Gemini path right

## Intent

Every LLM chat API has native tool calling, so the emoji text syntax will die
at some point. The structured tool call (name, argument dict, provider state)
must become the source of truth, and the emoji syntax one adapter over that
shape that can be deleted as a unit. The user stays in charge of context: no
compaction, no skills, agents only.

Scope of this story: only the path that consumes the Gemini adapter, done in
small steps that break nothing, each step tests first and its own commit.
Native calling for Claude and OpenAI is a later story; it will map the same
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
- `RawToolCall` carries `named_arguments`, `native_id`, `thought_signature`
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
- `RawToolCall` is the name, the dict and the provider ids. Bound to its
  tool it carries the `ToolArguments` declaration and renders the header
  and body from the dict; the text fields are gone. The emoji parser
  yields `EmojiToolCall`, which binds its positional text to the declared
  names; the resolver calls `bind` on whichever call it got. Persistence
  stores the dict only, and a session continued from disk binds every
  loaded call against the factory's declarations before replaying it, so
  the transcript and the text adapters render the same header as live.
  The last declared positional argument is written unquoted, since it
  absorbs leftover tokens when bound, so `say hello` round-trips as
  written; a value with quotes in it is shell-quoted

## Next steps

Leftovers from this story, small:
- values from Gemini are not coerced to the declared type; a non-string where
  a tool expects text fails the turn with a generic error (typed arguments
  object, needed once a second native adapter exists)
- Ctrl+C (KeyboardInterrupt) ends the session without recording results;
  only ESC (CancelledError) is covered
- `thought_signature` and `native_id` are Gemini-shaped; fold into one
  `provider_state` when a second native adapter needs its own

The next story: native tool calling for Claude and OpenAI. Each adapter maps
the core call (name, dict, id) to its wire format and back, declares tools
from `ToolArguments`, and drops the emoji parsing. The Gemini adapter and its
acceptance tests are the template. After that the header/body split in
`ToolArguments`, `text_messages.py`, `text_response.py` and the emoji module
are the deletable remainder.
