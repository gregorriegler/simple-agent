from simple_agent.application.agent_switch import AgentSwitch


async def clear_handler(args, agent):
    await agent.clear_session()


async def model_handler(args, agent):
    if not args:
        await agent.notify_error("Usage: /model <model-name>")
        return
    await agent.update_model(args)


async def quit_handler(args, agent):
    agent.quit()


async def exit_handler(args, agent):
    agent.quit()


def create_agent_handler(available_agents: list[str]):
    async def agent_handler(args, agent):
        if not args:
            await agent.notify_error("Usage: /agent <agent-type>")
            return

        agent_type = args
        if agent_type not in available_agents:
            await agent.notify_error(f"Unknown agent type: {agent_type}")
            return

        return AgentSwitch(agent_type)

    return agent_handler
