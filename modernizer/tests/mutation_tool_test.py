from unittest.mock import Mock
import json
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


def test_parse_stryker_output():
    # Mock Stryker JSON output
    stryker_json = {
        "files": {
            "Calculator.cs": {
                "mutants": [
                    {
                        "id": "1",
                        "mutatorName": "ArithmeticOperator",
                        "replacement": "a - b",
                        "location": {
                            "start": {"line": 15, "column": 12},
                            "end": {"line": 15, "column": 17}
                        },
                        "status": "Survived"
                    },
                    {
                        "id": "2",
                        "mutatorName": "ArithmeticOperator",
                        "replacement": "a * b",
                        "location": {
                            "start": {"line": 20, "column": 8},
                            "end": {"line": 20, "column": 13}
                        },
                        "status": "Killed"
                    }
                ]
            }
        },
        "thresholds": {
            "high": 80,
            "low": 60
        }
    }
    
    mock_runcommand = Mock()
    mock_runcommand.return_value = {'success': True, 'output': json.dumps(stryker_json)}
    
    mutation_tool = MutationTool(mock_runcommand)
    result = mutation_tool.execute('test-project')
    
    assert result['success'] is True
    
    # Parse the output as JSON
    output_data = json.loads(result['output'])
    
    # Verify structure matches expected format
    assert 'success' in output_data
    assert 'summary' in output_data
    assert 'survived_mutants' in output_data
    
    # Verify summary statistics
    summary = output_data['summary']
    assert summary['total_mutants'] == 2
    assert summary['killed'] == 1
    assert summary['survived'] == 1
    assert summary['mutation_score'] == 50.0
    
    # Verify survived mutants details
    survived = output_data['survived_mutants']
    assert len(survived) == 1
    assert survived[0]['file'] == 'Calculator.cs'
    assert survived[0]['line'] == 15
    assert survived[0]['column'] == 12
    assert survived[0]['mutation_type'] == 'arithmetic_operator'
    assert survived[0]['mutated'] == 'a - b'


def test_stryker_not_installed():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': False,
        'output': 'Could not execute because the specified command or file was not found.'
    }
    
    mutation_tool = MutationTool(mock_runcommand)
    result = mutation_tool.execute('test-project')
    
    assert result['success'] is False
    assert 'Stryker.NET is not installed' in result['output']