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


async def test_subagents_are_shown_under_their_parent(tabs):
    await tabs.start("Agent/Coder")
    await tabs.start("Agent/Coder/Naming")
    await tabs.start("Agent/Reviewer")

    verify(tabs.tree("Agent"))


async def test_every_workspace_shows_the_same_tree_highlighting_its_own_agent(tabs):
    await tabs.start("Agent/Coder")
    await tabs.start("Agent/Reviewer")

    verify(tabs.tree("Agent/Coder"))


async def test_selecting_an_agent_in_the_tree_activates_its_tab(tabs):
    await tabs.start("Agent/Coder")

    await tabs.select("Agent/Coder")

    verify(tabs.outline())


async def test_a_finished_subagent_leaves_the_tree(tabs):
    await tabs.start("Agent/Coder")
    await tabs.start("Agent/Reviewer")

    await tabs.finish("Agent/Coder")

    verify(tabs.tree("Agent"))


async def test_a_subagent_whose_parent_finished_hangs_under_its_nearest_ancestor(
    tabs,
):
    await tabs.start("Agent/Coder")
    await tabs.start("Agent/Coder/Naming")

    await tabs.finish("Agent/Coder")

    verify(tabs.tree("Agent"))


async def test_a_renamed_agent_is_renamed_in_the_tree(tabs):
    await tabs.start("Agent/Coder")

    await tabs.rename("Agent/Coder", "Refactorer")

    verify(tabs.tree("Agent"))


async def test_each_tree_keeps_highlighting_its_own_agent_after_switching(tabs):
    await tabs.start("Agent/Coder")
    await tabs.select("Agent/Coder")

    await tabs.select("Agent")

    verify(tabs.trees())
