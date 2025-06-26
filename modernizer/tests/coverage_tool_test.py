from unittest.mock import Mock
from modernizer.tools.tool_library import ToolLibrary
from modernizer.tools.coverage_tool import CoverageTool


def test_coverage_tool_is_available():
    tool_library = ToolLibrary()
    assert 'coverage' in tool_library.tool_dict


def test_coverage_tool_runs_dotnet_test_with_coverlet():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {'success': True, 'output': 'Coverage report generated'}
    
    coverage_tool = CoverageTool(mock_runcommand)
    result = coverage_tool.execute('test-project')
    
    mock_runcommand.assert_called_with('dotnet', ['test', 'test-project', '--collect:"XPlat Code Coverage"'])
    assert result['success'] is True


def test_coverage_tool_shows_specific_uncovered_lines():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/12345/coverage.cobertura.xml'
    }
    
    # Mock XML content with specific uncovered lines
    mock_xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<coverage>
  <packages>
    <package name="MyProject">
      <classes>
        <class name="Calculator" filename="Calculator.cs">
          <lines>
            <line number="10" hits="1" branch="false"/>
            <line number="15" hits="0" branch="false"/>
            <line number="20" hits="0" branch="false"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>'''
    
    coverage_tool = CoverageTool(mock_runcommand)
    coverage_tool._read_coverage_file = Mock(return_value=mock_xml_content)
    
    result = coverage_tool.execute('test-project')
    
    assert 'Calculator.cs:' in result['output']
    assert 'Line 15: Not covered' in result['output']
    assert 'Line 20: Not covered' in result['output']
    assert 'Line 10: Not covered' not in result['output']  # This line is covered