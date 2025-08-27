# Refactoring Process

STARTER_SYMBOL=🧹

The goal is to identify a small step towards an improvement in the design. 
Aim for better maintainability but avoid overengineering. 
Move called functions below their calling functions.
Favor polymorphism over repeated conditions.
Favor value objects over tuples and other primitive data types and data structures.
Favor tell don't ask over properties.
Avoid interfaces for stable dependencies.

To increase Cohesion:
- Move variable declarations as close as possible to their first use — ideally just one line above.

To Reduce Coupling:
- Avoid booleans as arguments.
- Avoid redundant parameters and making callers provide information the method can derive itself.
- When a parameter receives a complex object where only a small portion of it is actually used, replace the parameter with the specific data needed.

When refactoring tests, remember that Readability trumps code reuse!!

1. Before anything, create a new subtask with the prompt: "Read and follow `process/eliminate-dead-code.md`"
1. Initiate a new subtask to analyze the given code and find a small step that improves the design. Don't implement the change, just report back the result of the analysis.
2. Initiate a new subtask to decompose the proposed design improvement to a plan of many small refactoring steps. don't execute yet, just close the task reporting back the plan.
3. Execute the planned refactoring steps, creating a new subtask for each step where you run the tests before and after the changes using `./test.sh` and commit the changes using a commit message "r <message>"
