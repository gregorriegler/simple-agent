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


def test_coverage_tool_with_project_only():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/12345/coverage.cobertura.xml'
    }
    
    coverage_tool = CoverageTool(mock_runcommand)
    result = coverage_tool.execute('MyProject.csproj')
    
    # Should run dotnet test on the project
    mock_runcommand.assert_called_with('dotnet', ['test', 'MyProject.csproj', '--collect:"XPlat Code Coverage"'])


def test_coverage_tool_with_project_and_single_file():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/12345/coverage.cobertura.xml'
    }
    
    mock_xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<coverage>
  <packages>
    <package name="MyProject">
      <classes>
        <class name="Calculator" filename="Calculator.cs">
          <lines>
            <line number="10" hits="0" branch="false"/>
          </lines>
        </class>
        <class name="Helper" filename="Helper.cs">
          <lines>
            <line number="5" hits="0" branch="false"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>'''
    
    coverage_tool = CoverageTool(mock_runcommand)
    coverage_tool._read_coverage_file = Mock(return_value=mock_xml_content)
    
    result = coverage_tool.execute('MyProject.csproj Calculator.cs')
    
    # Should only show coverage for Calculator.cs, not Helper.cs
    assert 'Calculator.cs:' in result['output']
    assert 'Helper.cs:' not in result['output']


def test_coverage_tool_with_project_and_multiple_files():
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/12345/coverage.cobertura.xml'
    }
    
    mock_xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<coverage>
  <packages>
    <package name="MyProject">
      <classes>
        <class name="Calculator" filename="Calculator.cs">
          <lines>
            <line number="10" hits="0" branch="false"/>
          </lines>
        </class>
        <class name="Helper" filename="Helper.cs">
          <lines>
            <line number="5" hits="0" branch="false"/>
          </lines>
        </class>
        <class name="Utils" filename="Utils.cs">
          <lines>
            <line number="15" hits="0" branch="false"/>
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>'''
    
    coverage_tool = CoverageTool(mock_runcommand)
    coverage_tool._read_coverage_file = Mock(return_value=mock_xml_content)
    
    result = coverage_tool.execute('MyProject.csproj Calculator.cs Helper.cs')
    
    # Should show coverage for Calculator.cs and Helper.cs, but not Utils.cs
    assert 'Calculator.cs:' in result['output']
    assert 'Helper.cs:' in result['output']
    assert 'Utils.cs:' not in result['output']


def test_coverage_tool_with_real_xml_structure():
    """Test with actual XML structure from dotnet test coverage output"""
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/12345/coverage.cobertura.xml'
    }
    
    # Real XML structure with <lines> container element
    mock_xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<coverage line-rate="0.75" branch-rate="1" version="1.9" timestamp="1750966760" lines-covered="9" lines-valid="12" branches-covered="0" branches-valid="0">
  <sources>
    <source>C:\\Users\\test\\project\\</source>
  </sources>
  <packages>
    <package name="TestProject" line-rate="0.75" branch-rate="1" complexity="4">
      <classes>
        <class name="TestProject.Domain.Category" filename="Domain\\Category.cs" line-rate="0.75" branch-rate="1" complexity="4">
          <methods>
            <method name="getName" signature="()" line-rate="0" branch-rate="1" complexity="1">
              <lines>
                <line number="9" hits="0" branch="False" />
                <line number="10" hits="0" branch="False" />
                <line number="11" hits="0" branch="False" />
              </lines>
            </method>
            <method name="setName" signature="(System.String)" line-rate="1" branch-rate="1" complexity="1">
              <lines>
                <line number="14" hits="2" branch="False" />
                <line number="15" hits="2" branch="False" />
                <line number="16" hits="2" branch="False" />
              </lines>
            </method>
          </methods>
          <lines>
            <line number="9" hits="0" branch="False" />
            <line number="10" hits="0" branch="False" />
            <line number="11" hits="0" branch="False" />
            <line number="14" hits="2" branch="False" />
            <line number="15" hits="2" branch="False" />
            <line number="16" hits="2" branch="False" />
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>'''
    
    coverage_tool = CoverageTool(mock_runcommand)
    coverage_tool._read_coverage_file = Mock(return_value=mock_xml_content)
    
    result = coverage_tool.execute('test-project')
    
    # Should show uncovered lines from the real XML structure
    assert 'Domain\\Category.cs:' in result['output']
    assert 'Line 9: Not covered' in result['output']
    assert 'Line 10: Not covered' in result['output']
    assert 'Line 11: Not covered' in result['output']
    # Lines 14, 15, 16 should not appear as they are covered (hits > 0)
    assert 'Line 14: Not covered' not in result['output']


def test_coverage_tool_integration_with_file_not_found():
    """Test what happens when coverage file path is found but file doesn't exist"""
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/nonexistent/coverage.cobertura.xml'
    }
    
    coverage_tool = CoverageTool(mock_runcommand)
    # Don't mock _read_coverage_file - let it try to read the actual file
    
    result = coverage_tool.execute('test-project')
    
    # Should show an error message about file not found
    assert 'Error parsing coverage:' in result['output']
    assert result['success'] is True  # The dotnet test succeeded, just parsing failed


def test_coverage_tool_should_not_duplicate_lines():
    """Test that lines are not duplicated when XML has both method and class level line elements"""
    mock_runcommand = Mock()
    mock_runcommand.return_value = {
        'success': True,
        'output': 'Coverage report generated: TestResults/12345/coverage.cobertura.xml'
    }
    
    # XML with both method-level and class-level line elements (like real dotnet coverage)
    mock_xml_content = '''<?xml version="1.0" encoding="utf-8"?>
<coverage line-rate="0.5" branch-rate="1" version="1.9">
  <packages>
    <package name="TestProject">
      <classes>
        <class name="TestProject.Calculator" filename="Calculator.cs">
          <methods>
            <method name="Add" signature="(System.Int32,System.Int32)">
              <lines>
                <line number="10" hits="1" branch="False" />
                <line number="11" hits="0" branch="False" />
              </lines>
            </method>
          </methods>
          <lines>
            <line number="10" hits="1" branch="False" />
            <line number="11" hits="0" branch="False" />
          </lines>
        </class>
      </classes>
    </package>
  </packages>
</coverage>'''
    
    coverage_tool = CoverageTool(mock_runcommand)
    coverage_tool._read_coverage_file = Mock(return_value=mock_xml_content)
    
    result = coverage_tool.execute('test-project')
    
    # Should only show line 11 once, not twice
    output_lines = result['output'].split('\n')
    line_11_count = sum(1 for line in output_lines if 'Line 11: Not covered' in line)
    assert line_11_count == 1, f"Expected line 11 to appear once, but appeared {line_11_count} times"