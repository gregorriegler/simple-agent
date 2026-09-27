# The Test Writer's Mindset

When writing a test, put yourself in the shoes of whoever will use the thing you're about to build. You don't know how it is going to work yet, and you don't want to know. You'll figure that out later. For now, focus instead on what it is that you need from it.

So ask yourself:

- **What do I need back?**
- **What do I have to give it?**

This helps you answer the question: what is the simplest interface that meets that need?

This means staying in the **problem space**, where the question is what is needed. The **solution space**, where the question is how, is deliberately ignored, since it isn't the test's concern.

# How a Test Should Read

When writing a test, think about its reader. What do they need to learn from reading it?

They need to understand what the SUT does and what it is responsible for. So the test talks in the language of the **problem space**.

The reader is looking for signals:

- **What is the scenario?**
- **What is relevant for this particular scenario?**
- **What goes into the SUT?**
- **How is the SUT used?**
- **What is the expected outcome?**

Nothing else belongs in the test. Technicalities such as fixture setup code are noise to the reader, so they get moved away from the test. The reader shouldn't have to scroll to find the signals.

But if something matters for the scenario, it stays in the test. A reader should not have to go looking for such a detail. For example:

- the value that triggers the behavior, like an expired date or an empty list
- what a collaborator answers, like a model that replies with an error

| Noise | Signals |
|---|---|
| Technical names like `mock_x`, `tmp_path`, `fixture_3` | Names from the problem space |
| Values that don't matter for this scenario | The values that make this scenario what it is |
| Constructing and wiring collaborators | The SUT being called the way a consumer would call it |
| Temp files, clocks, environment variables | What goes into the SUT |
| Configuring mocks and verifying interactions | The outcome the consumer receives |
| Loops, conditions, logic | The expected outcome, easy to compare |
| Indentation | A flat read from top to bottom, telling the story |
| Assertions on internal state or intermediate steps | A test name that states the scenario |
