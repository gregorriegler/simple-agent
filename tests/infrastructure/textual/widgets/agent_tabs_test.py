from approvaltests import verify


async def test_next_tab_wraps_around_to_the_first(tabs):
    await tabs.start("Agent/Sub")
    await tabs.next_tab()
    await tabs.next_tab()

    verify(tabs.outline())


async def test_previous_tab_wraps_around_to_the_last(tabs):
    await tabs.start("Agent/Sub")
    await tabs.previous_tab()

    verify(tabs.outline())


async def test_a_finished_subagent_leaves_no_tab_behind(tabs):
    await tabs.start("Agent/Naming")

    await tabs.finish("Agent/Naming")

    verify(tabs.outline())


async def test_the_root_agent_keeps_its_tab_when_it_finishes(tabs):
    await tabs.finish("Agent")

    verify(tabs.outline())


async def test_clearing_a_session_empties_its_chat(tabs):
    await tabs.start("Agent/Sub")
    await tabs.say("Agent", "Message")
    await tabs.say("Agent/Sub", "Kept")

    await tabs.clear("Agent")

    verify(tabs.outline())


async def test_closing_a_focused_subagent_returns_to_its_parent(tabs):
    await tabs.start("Agent/Coder")
    await tabs.start("Agent/Coder/Naming")
    await tabs.focus("Agent/Coder")

    await tabs.finish("Agent/Coder")

    verify(tabs.outline())
