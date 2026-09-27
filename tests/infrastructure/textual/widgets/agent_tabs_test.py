from approvaltests import verify


async def test_closing_a_focused_subagent_returns_to_its_parent(tabs):
    await tabs.start("Agent/Coder")
    await tabs.start("Agent/Coder/Naming")
    await tabs.focus("Agent/Coder")

    await tabs.finish("Agent/Coder")

    verify(tabs.outline())
