import os
import sys
import subprocess

from system_prompt_generator import SystemPromptGenerator

def test_system_prompt_generator_outputs_prompt_without_args():
    script_path = os.path.join(os.path.dirname(__file__), '..', 'system_prompt_generator.py')

    result = subprocess.run([sys.executable, script_path],
                          capture_output=True, text=True)

    assert result.returncode == 0, f"Expected script to run successfully, but got return code {result.returncode}"
    assert len(result.stdout) > 0, "Expected system prompt output, but got empty stdout"
    assert "DYNAMIC_TOOLS_PLACEHOLDER" not in result.stdout, \
        "Expected placeholder to be replaced, but it's still present"

def test_system_prompt_shows_detailed_arguments():
    generator = SystemPromptGenerator()
    system_prompt = generator.generate_system_prompt()

    assert "project_path: string" in system_prompt, "Should show specific argument details like 'project_path: string'"
    assert "file_name: string" in system_prompt, "Should show specific argument details like 'file_name: string'"
    assert "selection: CodeSelection" in system_prompt, "Should show specific argument details like 'selection: CodeSelection'"
    assert "newMethodName: String" in system_prompt, "extract-method should show its specific newMethodName argument"
    assert "startLine:startColumn-endLine:endColumn" in system_prompt, "Should show CodeSelection format as startLine:startColumn-endLine:endColumn"
    assert "(e.g., 5:10-8:25)" in system_prompt, "Should show CodeSelection example as (e.g., 5:10-8:25)"
    assert "line:column" in system_prompt, "Should show Cursor format as line:column"
    assert "(e.g., 12:5)" in system_prompt, "Should show Cursor example as (e.g., 12:5)"
