import pytest
from tool_framework import ToolFramework

def test_ls_lists_directory_contents(tmp_path):
    file1 = tmp_path / "file1.txt"
    file2 = tmp_path / "file2.txt"
    subdir = tmp_path / "subdir"
    file1.write_text("hello")
    file2.write_text("world")
    subdir.mkdir()

    framework = ToolFramework()
    
    content, tool_result = framework.parse_and_execute("/ls " + str(tmp_path))
    
    assert "file1.txt" in tool_result
    assert "file2.txt" in tool_result
    assert "subdir" in tool_result


def test_cat_shows_contents(tmp_path):
    # Setup: create some files and directories
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello")
    
    framework = ToolFramework()

    content, tool_result = framework.parse_and_execute("/cat " + str(file1))

    assert "1\thello" == tool_result
    
    
def xtest_extract_method():
    framework = ToolFramework()
    
    content, tool_result = framework.parse_and_execute("/extract-method \"C:/Users/riegl/code/Parrot-Refactoring-Kata/CSharp/Parrot/Parrot.csproj\" Parrot.cs 23:0-33:14 ComputeSpeed")
    
    print(content)
    print(tool_result)
    assert "x" is tool_result