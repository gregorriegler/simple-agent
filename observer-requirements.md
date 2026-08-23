# Observer System — High-Level Requirements

## Purpose

A coding agent tends to fall back on its reflexes, which often conflict with
project-specific rules. This system adds small, focused **observers** that watch
the main agent's work and suggest corrections, without taking control of it.

Each observer owns one narrow concern (naming, error handling, test structure,
etc.) and carries its own detailed guidelines for that concern.

---

## 1. Observers

- An observer is a separate agent with its own system prompt and its own
  guidelines file for a single concern.
- Observers are **read-only**. They may read the codebase to inform a decision.
  They may not write, edit, or run anything that mutates state.
- Observers produce **suggestions**, never commands. The main agent decides
  whether to act.
- Multiple observers may run at once. They do not talk to each other.

## 2. Trigger: checkpoints

- Observers do not run continuously. They run at **checkpoints** — a completed
  unit of work (file written, task finished, pre-commit).
- The checkpoint is defined by the host system, not by the observer.

**Why not continuous:** mid-work code is half-finished. Something that looks
wrong early is often correct by the time the agent is done, so a continuous
observer spends most of its output on problems that fix themselves — noise for
the agent, cost for the operator. A checkpoint marks the code as being in a
state worth judging.

**Granularity:** checkpoints should be **small and frequent** — the target is
"continuous, snapped to the nearest coherent state," not batched review. The
smaller the checkpoint, the less work gets built on top of a flaw before the
lagging suggestion arrives (see §3). Start fine-grained and coarsen only if
observer cost becomes a problem.

## 3. Timing: lagging, not blocking

- The main agent does **not** wait for an observer. It continues working while
  the observer reads and thinks.
- An observer's output is delivered at the **next** checkpoint, one step late.
- Consequence: any suggestion may arrive after the code it refers to has moved
  on. This must be handled (see §5).

## 4. Observer context packet

Observers do not receive the full conversation transcript. They receive a small
curated packet:

- **Intent** — the current high-level goal (see §6).
- **Diff** — changes since the last checkpoint.
- **Version marker** — a git SHA or file hash identifying the state observed.
- **Read access** — the observer may pull any additional files it needs.

## 5. Staleness handling

- Every suggestion carries the version marker of the state it was based on,
  plus the specific target (file, symbol).
- On receiving a suggestion, the main agent first checks whether that marker
  still matches the current state.
- If it does not match, the suggestion is **dropped silently**. It is not
  reasoned about, argued with, or partially applied.

## 6. Intent slot

- The main agent maintains a single short, current statement of what it is
  trying to do. It is overwritten when the goal changes — it is state, not a log.
- Observers read this slot instead of reconstructing intent from history.
- **Enforcement:** a checkpoint cannot complete until the agent either writes a
  new intent or explicitly confirms the existing one is unchanged. Keeping the
  slot fresh is a required field, not a habit.

## 7. Suggestion format

Each suggestion should carry:

- The concern it came from (which observer).
- The target: file and symbol.
- The version marker it was based on.
- The proposed change, and a short reason grounded in the observer's guidelines.

---

## Open questions

- What happens when the agent reports "intent unchanged" but the work has
  clearly drifted.
- How the main agent should handle conflicting suggestions from two observers.
- Whether repeatedly ignored suggestions should escalate or go quiet.
- Budget: how many observers can run per checkpoint before cost outweighs value.
