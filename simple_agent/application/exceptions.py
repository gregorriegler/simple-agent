class SwitchAgent(Exception):
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
