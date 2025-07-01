import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modernizer.tools.tool_library import ToolLibrary
from .test_helpers import verifyTool

library = ToolLibrary()

def test_create_tool_single_character_name(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, "/create a")
        
        # Verify file was created
        assert os.path.exists("a"), "File 'a' should have been created"
        assert os.path.getsize("a") == 0, "File 'a' should be empty"
    finally:
        os.chdir(original_cwd)

def test_create_tool_simple_name_with_extension(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, "/create test.txt")
        
        # Verify file was created
        assert os.path.exists("test.txt"), "File 'test.txt' should have been created"
        assert os.path.getsize("test.txt") == 0, "File 'test.txt' should be empty"
    finally:
        os.chdir(original_cwd)

def test_create_tool_single_character_content(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, "/create test.txt a")
        
        # Verify file was created with correct content
        assert os.path.exists("test.txt"), "File 'test.txt' should have been created"
        with open("test.txt", "r") as f:
            content = f.read()
        assert content == "a", f"File 'test.txt' should contain 'a', but contains '{content}'"
    finally:
        os.chdir(original_cwd)

def test_create_tool_simple_text_content(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, "/create readme.txt Hello World")
        
        # Verify file was created with correct content
        assert os.path.exists("readme.txt"), "File 'readme.txt' should have been created"
        with open("readme.txt", "r") as f:
            content = f.read()
        assert content == "Hello World", f"File 'readme.txt' should contain 'Hello World', but contains '{content}'"
    finally:
        os.chdir(original_cwd)

def test_create_tool_newline_content(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, '/create multi.txt "Line 1\\nLine 2"')
        
        # Verify file was created with correct content
        assert os.path.exists("multi.txt"), "File 'multi.txt' should have been created"
        with open("multi.txt", "r") as f:
            content = f.read()
        assert content == "Line 1\nLine 2", f"File 'multi.txt' should contain 'Line 1\\nLine 2', but contains '{repr(content)}'"
    finally:
        os.chdir(original_cwd)

def test_create_tool_json_content(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, '/create config.json {"name": "test"}')
        
        # Verify file was created with correct content
        assert os.path.exists("config.json"), "File 'config.json' should have been created"
        with open("config.json", "r") as f:
            content = f.read()
        assert content == '{"name": "test"}', f"File 'config.json' should contain JSON content, but contains '{repr(content)}'"
    finally:
        os.chdir(original_cwd)

def test_create_tool_explicit_empty_content(tmp_path):
    # Change to temp directory for test
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        verifyTool(library, '/create empty.txt ""')
        
        # Verify file was created with empty content
        assert os.path.exists("empty.txt"), "File 'empty.txt' should have been created"
        with open("empty.txt", "r") as f:
            content = f.read()
        assert content == "", f"File 'empty.txt' should be empty, but contains '{repr(content)}'"
    finally:
        os.chdir(original_cwd)