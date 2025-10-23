import glob
import os


class FileSystemAgentTypeDiscovery:
    def discover_agent_types(self) -> list[str]:
        simple_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pattern = os.path.join(simple_agent_dir, '*.agent.md')
        agent_files = glob.glob(pattern)
        agent_types = []
        for filepath in agent_files:
            basename = os.path.basename(filepath)
            agent_type = basename.replace('.agent.md', '')
            agent_types.append(agent_type)
        return sorted(agent_types)
