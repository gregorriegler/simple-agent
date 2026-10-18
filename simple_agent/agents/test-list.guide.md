# The Test List

The TEST_LIST_FILE is `test-list.md` in the root directory of the project.
It lists the scenarios the code has to handle, before they become tests.
It is shared by everyone working on the project and lives with the code.

## Format

A markdown checklist, one scenario per line, grouped by what the consumer wants to do or see:

```markdown
## Cart pricing
- [x] calculates price of an empty cart
- [x] calculates price of a cart with a single item
- [ ] calculates price of a cart with multiple items
```

- Write each scenario from the outermost consumer's view (player, caller, user), in their words. The subject is the system as a whole, never one of its parts.
- Name groups after what the consumer wants to do or see, not after components.
- Would the consumer recognize every noun in the line? A noun only the implementation knows (board, renderer, grid) means you are inside the box.
- Describe what the system does, not how it does it.
- Focus on actions and observable transformations, not empty containers or internal state.
- Keep the list focused on the current problem; add new problems only when you reach them.
- Cross a scenario off with `- [x]` once its test passes.

## Where to Start: Behavior Over Structure

- **Start with core domain behavior**: Focus on the simplest action that produces an observable outcome. Do not begin with scaffolding, empty containers, board dimensions, or passive data structures. Data structures emerge to support behavior, not before it.
- **Start with a thin slice**: Do not pre-plan an exhaustive list of all problems and edge cases upfront. Start with the simplest slice of actual behavior, make it pass, and expand the test list incrementally as you learn.

## One Problem at a Time

Solve one problem at a time.
Triangulate it, sometimes with multiple tests, until it is completely covered.
Only then tackle the next problem.

This decides the order of the TEST_LIST_FILE and where new scenarios go:
- A scenario for a problem goes into that problem's group.
- A new problem gets its own group, after the one you are working on.

## ZOMBIES

Use ZOMBIES to decide which scenarios a problem needs and how to sort them:
- **Z**ero: nothing, empty, none (e.g. no action taken, neutral state)
- **O**ne: a single item or single step
- **M**any: more than one
- **B**oundary behaviors: the edges where behavior changes
- **I**nterface definition: express through verbs and actions, not state inspection or passive getters
- **E**xceptional behavior: errors and invalid input
- **S**imple scenarios, simple solutions: start with the simplest

Zero, One, Many sets the order within a problem.
Boundaries and exceptional behavior come once the happy paths are covered.

## A Living File

The TEST_LIST_FILE changes throughout the work, whenever we learn something new.
Add scenarios as you discover them, reorder them, and remove the ones that turn out to be irrelevant.
When there is no TEST_LIST_FILE yet, create it.
