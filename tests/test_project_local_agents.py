import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from simple_agent.infrastructure.system_prompt.agent_definition import load_agent_prompt, _get_project_local_agents_dir


def test_project_local_agents_directory_path():
    with patch('os.getcwd', return_value='/test/path'):
        result = _get_project_local_agents_dir()
        assert result.endswith(os.path.join('.simple-agent', 'agents'))


def test_load_agent_prompt_prefers_project_local():
    with tempfile.TemporaryDirectory() as tmpdir:
        project_agents_dir = os.path.join(tmpdir, '.simple-agent', 'agents')
        os.makedirs(project_agents_dir, exist_ok=True)
        
        project_agent_file = os.path.join(project_agents_dir, 'test.agent.md')
        with open(project_agent_file, 'w', encoding='utf-8') as f:
            f.write("""---
name: ProjectLocal
tools: bash
---
This is a project-local agent.""")
        
        with patch('os.getcwd', return_value=tmpdir):
            prompt = load_agent_prompt('test')
            assert prompt.name == 'ProjectLocal'
            assert 'project-local agent' in prompt.template


def test_load_agent_prompt_falls_back_to_builtin():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('os.getcwd', return_value=tmpdir):
            prompt = load_agent_prompt('coding')
            assert prompt.name == 'Coding'
            assert len(prompt.tool_keys) > 0


def test_load_agent_prompt_handles_missing_project_local_gracefully():
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch('os.getcwd', return_value=tmpdir):
            prompt = load_agent_prompt('orchestrator')
            assert prompt.name == 'Orchestrator'