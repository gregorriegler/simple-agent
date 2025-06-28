from unittest.mock import Mock
from modernizer.tools.tool_library import ToolLibrary
from modernizer.tools.mutation_tool import MutationTool


def test_mutation_tool_is_available():
    tool_library = ToolLibrary()
    assert 'mutation' in tool_library.tool_dict


def test_mutation_tool_executes_successfully():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {'success': True, 'output': 'Stryker.NET mutation testing completed'}
    
    mutation_tool = MutationTool(mock_runcommand)
    result = mutation_tool.execute('test-project')
    
    assert result['success'] is True