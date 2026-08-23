# Observer System — Specification

Companion to [observer-requirements.md](observer-requirements.md). The
requirements say *what* the system must do; this document records the decisions
about *how* it is built on top of Simple Agent, and the order in which it is
built.

---

## Decisions

| Question | Decision |
| --- | --- |
| What triggers a checkpoint | Host-side listener on successful write-tool results, gated on "no observer round in flight" |
| How suggestions reach the agent | Injected as a user-role message, drained inside the tool loop |
| Diff and version marker | `git diff` over touched paths; marker is a content hash per target file |
| Which observers run | Listed in the main agent's `.agent.md` front matter |
| Intent | A tool the agent calls; stored in a per-agent file, mirroring todos; rendered in the UI panel that currently shows todos |

### Why a listener and not a tool

A `checkpoint` tool would make the intent slot a required argument, which is
what §6 asks for. It was rejected because a tool can be forgotten: the agent
would silently stop being observed exactly when it is most absorbed in the work.
A listener on write results cannot be skipped.

The cost is that §6's enforcement weakens from a gate to a nag — see
[Intent staleness](#intent-staleness).

### Why the in-flight gate

Firing on every write is too often: a refactor touching five files would produce
five checkpoints, four of them judging half-finished states. A fixed debounce
interval would need tuning and would not know anything about observer cost.

Gating on "the previous round has finished" makes the rate self-tuning. Writes
that arrive during a round accumulate into the pending diff rather than starting
a new one. Fast observers approach continuous observation; slow ones coalesce
bursts. Cost is bounded without a config knob, and §3's backpressure comes for
free.

---

## Architecture

New application-layer objects, all independent of infrastructure:

- `IntentSlot` — whether the intent has been refreshed since the last
  checkpoint. The intent *value* itself lives in a file (see §1), so the slot
  only needs to track freshness.
- ~~`PendingMessages`~~ — not built. `Input` already is that queue, and
  `UserInput` already holds what the UI has typed; both learned to `drain()`
  instead (see §2).
- `CheckpointDetector` — subscribes to `ToolResultEvent`, owns the in-flight gate.
- `ChangeTracker` (port) — touched paths, diff, version markers since the last
  checkpoint.
- `SuggestionMailbox` — holds suggestions between checkpoints, applies the
  staleness filter.
- `ObserverLibrary` — resolves observer names to definitions.

New infrastructure:

- `GitChangeTracker` — implements `ChangeTracker` via
  `git --no-pager diff -- <paths>`.
- ~~`IntentView`~~ — not built as a separate widget; `TodoView` renders the
  intent above the todos (see §1).

Observers themselves are ordinary async subagents, spawned through the existing
`AgentFactory.create_spawner(...)` and `AgentTaskManager`.

---

## 1. Intent slot

The first slice. It ships value on its own — a visible statement of what the
agent thinks it is doing — and is a prerequisite for the observer context packet.

**Status: built — tool, storage and UI panel. Staleness detection is not.**

### The tool

    key:  communicate_intent
    name: communicate-intent
    body: a single short sentence describing the current goal

The intent is **state, not a log**: a second call overwrites the first. The tool
result confirms the new intent (`Intent: <text>`).

The agent is instructed to call it when the goal changes, not on every step. It
is listed first in the coding agent's front matter, ahead of `write_todos`.

### Storage

The intent is written to `.<Agent>.intent.md`, one file per agent, built from
the same `STATE_FILE_PATTERN` in `AgentId` that produces the todo file. It is
overwritten on every call, so the file *is* the current intent.

This mirrors `write_todos` deliberately. Observers are read-only with `ls` and
`cat` (§5), so a file is something they can read directly — no port, no
injection, no projection to keep in sync.

Cleanup follows the todo file exactly: `AgentStateCleanup` removes an agent's
intent file on a fresh session, when a subagent finishes, and on session clear.

### Why no `IntentCommunicatedEvent`

An earlier draft of this document specified
`IntentCommunicatedEvent(agent_id, intent)`, published on every successful call,
so that intent history and `--continue` replay came "for free".

It was dropped, because that persistence already exists. `ToolCalledEvent`
carries the full `RawToolCall` including its body, it is persisted to
`events.jsonl`, and `HistoryReplayer` republishes every stored event onto the
bus on `--continue`. Every `communicate-intent` call is therefore already in the
event log, and anything that wants the current intent can subscribe to
`ToolCalledEvent` and filter on the tool name.

What a dedicated event would add is a *type* to subscribe to instead of a name
to string-match — worth having eventually, but not worth the cost now: tools in
this codebase are pure functions from `RawToolCall` to `ToolResult` and none of
them touch the event bus. Publishing from the tool would introduce that coupling
for a payload the log already holds.

Revisit if the string coupling bites, or if a second producer of intent appears.
Extracting the event later is mechanical, and the log already contains
everything needed to replay it.

### UI

**Built.** The intent appears in the panel that already holds the todo list
(`left-panel-bottom`, rendered by `TodoView`).

`TodoView.load_content` now reads both state files and joins them, intent first:

    **Intent:** Ship the intent panel

    - [ ] write a test

No second widget was needed. Because visibility already keys off
`TodoView.has_content`, the panel automatically shows when *either* file has
content, and the existing refresh on every tool result covers the intent file
too.

History is not shown in the panel. It is available in the event log; a
scrollback view can come later if it turns out to be wanted.

The panel is state, mirroring §6: one intent, always the current one.

The name `TodoView` is now too narrow for what it renders — a rename to
`AgentStateView` is pending, matching `AgentStateCleanup`.

### Intent staleness

Not built yet. `IntentSlot` records whether `communicate_intent` has been called
since the last checkpoint. When a checkpoint fires with a stale slot, the message injected at
the *next* checkpoint leads with a request to restate or confirm the intent.

This is weaker than §6's "a checkpoint cannot complete until…". With an
automatic trigger there is no completion step to block, so the enforcement is a
nag rather than a gate. Whether agents actually respond to it is one of the
things the first runs should reveal.

---

## 2. Mid-loop message queue

**Status: built.**

Also standalone, and worth building for its own sake: a message typed while the
agent was working was not seen until the agent went idle.

`Agent.run_tool_loop()` now drains pending messages on each iteration,
immediately after tool results are appended. Each drained message becomes a user
turn in the context and publishes `UserPromptedEvent`, so it renders in the UI
and lands in the event log like any other prompt.

### Where the messages actually were

`Input._stack` was the wrong place to look. It only ever holds a subagent's
seeded initial message. A message typed in the UI goes into the
`UserInput` adapter's queue, so draining the stack alone would have delivered
nothing in the real app.

So `drain()` was added to the `UserInput` port — "messages already waiting,
without blocking" — defaulting to `[]`, which is the honest answer for
`NonInteractiveUserInput` and `DummyUserInput`. `Input.drain()` returns stacked
messages plus whatever the port has pending, FIFO. `read_async` is untouched and
stays LIFO.

No `PendingMessages` object was introduced. Observers will produce into the same
`Input`, which is already the queue that object would have been.

### QueuedUserInput

Implementing `drain()` exposed that `TextualUserInput` imported nothing from
Textual — it was a `Queue`, a poll, and an escape flag — and that `bridge.py`
already used it as a generic inbox. It is now `QueuedUserInput` in the
application layer. A future web UI reuses it rather than copying the queue.

### Not handled

Slash commands typed mid-loop. `user_prompts()` intercepts them, the mid-loop
drain does not, so a drained `/clear` reaches the LLM as text. Deliberately
ignored for now, on the assumption that nobody does it.

---

## 3. Checkpoint detector

**Status: built — not yet wired into the application.**

`CheckpointDetector` subscribes to `ToolResultEvent`. Fires on successful results from tools that
mutate files (`create_file`, `replace_file_content`), and only when no observer
round is in flight. Publishes `CheckpointReachedEvent`.

Reads (`cat`, `ls`) produce no new state and are ignored.

`ToolResultEvent` carries only a `call_id`, not the tool that produced it, so the
detector also subscribes to `ToolCalledEvent` and remembers the name per call id.
Adding the call to the result event would have been the alternative; it would
have changed the persisted event schema for a lookup that costs one dict.

The gate is released by `round_finished()`, called by whatever runs the observer
round. Until such a consumer exists the detector is deliberately **not wired**
into `main.py`: with nobody releasing the gate it would latch after the first
write.

`bash` is deliberately excluded for now. It can mutate files, but knowing
*which* files means parsing the command; catching it reliably would mean
diffing the working tree on every bash call. Revisit if it proves to be a real
gap.

A second, opt-in detector is worth considering for this repository
specifically: a checkpoint when `bash test.sh` returns green. Under strict TDD
that is the sharpest available definition of a coherent state — but it couples
the mechanism to a project convention, so it is not the default.

---

## 4. Change tracking

Between checkpoints, touched paths accumulate. At a checkpoint:

- **Diff** — `git --no-pager diff` restricted to those paths. When the working
  directory is not a git repository, fall back to full file contents.
- **Version marker** — `sha256` of each touched file's current content. This
  works whether or not anything has been committed, which a commit SHA would
  not.

---

## 5. Observers

Selected in the main agent's front matter:

    observers: [naming, error-handling]

Resolved against `*.observer.md` files by `ObserverLibrary`, mirroring
`FileSystemAgentLibrary`.

**Read-only is enforced in code, not trusted from the file.** An observer's
declared tool keys are intersected with a hardcoded whitelist (`ls`, `cat`), so
a mis-authored definition cannot grant `bash` or a write tool.

Each observer receives, as its task description, the context packet of §4:
intent, diff, version markers. It may read further files through its whitelisted
tools.

Observers report through `complete-task` in a fixed structure carrying the §7
fields: concern, target file and symbol, version marker, proposed change,
reason.

---

## 6. Staleness filter

Before delivering a suggestion, `SuggestionMailbox` re-hashes the suggestion's
target file and compares it to the marker recorded at observation time. On
mismatch the suggestion is discarded and never reaches the LLM.

This is deliberately mechanical. §5 requires that stale suggestions are dropped
silently rather than reasoned about — doing it in code rather than in the prompt
means it costs nothing and cannot be argued with.

---

## Positions on the open questions

These are starting positions, not settled answers.

**Conflicting suggestions.** Do not arbitrate. Deliver both, each labelled with
its observer. Arbitration needs a judge, which is a second system with its own
failure modes.

**Repeatedly ignored suggestions.** Neither escalate nor go quiet, initially.
Record ignore counts as events so the behaviour can be measured before a policy
is designed for it.

**Budget.** Cap concurrent observers per checkpoint (2–3 to start). The
in-flight gate already provides the main cost control: a checkpoint is skipped
entirely while the previous round is still running.

**Intent that has clearly drifted.** Unresolved. The nag described in §1 detects
a slot that was never refreshed, but not one that was confirmed while the work
moved elsewhere. Detecting that would require comparing intent against the diff
— plausibly a job for an observer, which makes it circular. Left open.

---

## Build order

1. Intent slot — ✅ tool, file storage and UI panel; ⬜ staleness nag
2. Mid-loop message queue — ✅
3. Checkpoint detector — ✅ detector and gate; ⬜ wiring (waits for a consumer)
4. Change tracking — diff and version markers — next
5. Observers — library, read-only whitelist, async spawn, suggestion format
6. Staleness filter

The first two ship value before any observer exists, which also means the
injection point gets exercised before anything depends on it.
