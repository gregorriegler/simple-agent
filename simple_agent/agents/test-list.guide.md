# The Test List

The TEST_LIST_FILE is `test-list.md` in the root directory of the project.
It lists the scenarios the code has to handle, before they become tests.
It is shared by everyone working on the project and lives with the code.

## Format

A markdown checklist, one scenario per line, grouped by the problem it solves:

```markdown
## Cart total
- [x] an empty cart has a total of zero
- [x] a cart with one item totals the price of that item
- [ ] a cart with many items totals the sum of their prices

## Discount codes
- [ ] a cart without a discount code keeps its total
- [ ] a discount code reduces the total
- [ ] an unknown discount code is rejected
```

- Describe what the code has to do, not how it does it.
- Cross a scenario off with `- [x]` once its test passes.

## One Problem at a Time

Solve one problem at a time.
Triangulate it, sometimes with multiple tests, until it is completely covered.
Only then tackle the next problem.

This decides the order of the TEST_LIST_FILE and where new scenarios go:
- A scenario for a problem goes into that problem's group.
- A new problem gets its own group, after the one you are working on.

## ZOMBIES

Use ZOMBIES to decide which scenarios a problem needs and how to sort them:
- **Z**ero: nothing, empty, none
- **O**ne: a single item
- **M**any: more than one
- **B**oundary behaviors: the edges where behavior changes
- **I**nterface definition: what you give it and what you get back
- **E**xceptional behavior: errors and invalid input
- **S**imple scenarios, simple solutions: start with the simplest

Zero, One, Many sets the order within a problem.
Boundaries and exceptional behavior come once the happy paths are covered.

## A Living File

The TEST_LIST_FILE changes throughout the work, whenever we learn something new.
Add scenarios as you discover them, reorder them, and remove the ones that turn out to be irrelevant.
When there is no TEST_LIST_FILE yet, create it.
