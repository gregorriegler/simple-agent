import os
import subprocess
import sys


def test_system_prompt_generator_outputs_prompt_without_args():
    script_path = os.path.join(os.path.dirname(__file__), '..', 'system_prompt_generator.py')

    result = subprocess.run([sys.executable, script_path],
                          capture_output=True, text=True)

    assert result.returncode == 0, f"Expected script to run successfully, but got return code {result.returncode}"
    assert len(result.stdout) > 0, "Expected system prompt output, but got empty stdout"
    assert "DYNAMIC_TOOLS_PLACEHOLDER" not in result.stdout, \
        "Expected placeholder to be replaced, but it's still present"

