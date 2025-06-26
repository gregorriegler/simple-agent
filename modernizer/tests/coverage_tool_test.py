import unittest
from unittest.mock import Mock
from modernizer.tools.tool_library import ToolLibrary
from modernizer.tools.coverage_tool import CoverageTool

class CoverageToolTest(unittest.TestCase):
    
    def test_coverage_tool_is_available(self):
        tool_library = ToolLibrary()
        self.assertIn('coverage', tool_library.tool_dict)
    
    def test_coverage_tool_runs_dotnet_test_with_coverlet(self):
        mock_runcommand = Mock()
        mock_runcommand.return_value = {'success': True, 'output': 'Coverage report generated'}
        
        coverage_tool = CoverageTool(mock_runcommand)
        result = coverage_tool.execute('test-project')
        
        mock_runcommand.assert_called_with('dotnet', ['test', 'test-project', '--collect:"XPlat Code Coverage"'])
        self.assertTrue(result['success'])

if __name__ == '__main__':
    unittest.main()