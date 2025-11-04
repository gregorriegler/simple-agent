import glob
import os

from simple_agent.infrastructure.agent_file_conventions import (
    get_project_local_agents_dir,
    agent_type_from_filename
)


class FileSystemAgentTypeDiscovery:
    def discover_agent_types(self) -> list[str]:
        agent_types = []
        
        simple_agent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pattern = os.path.join(simple_agent_dir, '*.agent.md')
        agent_files = glob.glob(pattern)
        
        for filepath in agent_files:
            basename = os.path.basename(filepath)
            agent_type = agent_type_from_filename(basename)
            agent_types.append(agent_type)
        
        project_local_dir = get_project_local_agents_dir()
        if os.path.isdir(project_local_dir):
            project_pattern = os.path.join(project_local_dir, '*.agent.md')
            project_agent_files = glob.glob(project_pattern)
            
            for filepath in project_agent_files:
                basename = os.path.basename(filepath)
                agent_type = agent_type_from_filename(basename)
                agent_types.append(agent_type)
        
        return sorted(agent_types)