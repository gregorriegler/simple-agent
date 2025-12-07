from approvaltests import verify

from tests.session_test_bed import SessionTestBed


def test_subagent():
    verify_chat(
        ["Create a subagent that says hello", "\n"], [
            "🛠️[subagent coding say hello]",
            "hello\n🛠️[complete-task I successfully said hello]"
        ]
    )


def test_nested_agent_test():
    verify_chat(
        ["Create a subagent that creates another subagent", "\n"], [
            "🛠️[subagent orchestrator create another subagent]",
            "🛠️[subagent coding say nested hello]",
            "nested hello\n🛠️[complete-task I successfully said nested hello]",
            "🛠️[complete-task I successfully created another subagent]",
            "🛠️[complete-task I successfully created a subagent]"
        ]
    )


def test_agent_says_after_subagent():
    verify_chat(
        ["Create a subagent that says hello, then say goodbye", "\n"], [
            "🛠️[subagent coding say hello]",
            "hello\n🛠️[complete-task I successfully said hello]",
            "goodbye"
        ]
    )


def verify_chat(inputs, answers):
    message, *remaining_inputs = inputs

    result = SessionTestBed() \
        .with_llm_responses(answers) \
        .with_user_inputs(message, *remaining_inputs) \
        .run()

    verify(result.as_approval_string())
