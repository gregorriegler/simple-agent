import unittest
from modernizer.tools.tool_library import ToolLibrary

class CoverageToolTest(unittest.TestCase):
    
    def test_coverage_tool_is_available(self):
        tool_library = ToolLibrary()
        self.assertIn('coverage', tool_library.tool_dict)

if __name__ == '__main__':
    unittest.main()