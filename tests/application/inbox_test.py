from simple_agent.application.inbox import Inbox


def test_new_inbox_is_empty():
    assert Inbox().is_empty()


def test_put_message_makes_inbox_non_empty():
    inbox = Inbox()

    inbox.put("hello")

    assert not inbox.is_empty()


def test_take_returns_newest_message_first():
    inbox = Inbox()
    inbox.put("first")
    inbox.put("second")

    assert inbox.take() == "second"
    assert inbox.take() == "first"
    assert inbox.is_empty()


def test_drain_returns_all_messages_oldest_first_and_empties_inbox():
    inbox = Inbox()
    inbox.put("first")
    inbox.put("second")

    assert inbox.drain() == ["first", "second"]
    assert inbox.is_empty()
