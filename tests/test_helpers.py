import os

from approvaltests import Options, verify
from approvaltests.scrubbers import create_regex_scrubber, combine_scrubbers


def create_temp_file(tmp_path, filename, contents):
    temp_file = tmp_path / filename
    temp_file.write_text(contents)
    return temp_file

def create_temp_directory_structure(tmp_path):
    file1 = tmp_path / "file1.txt"
    file1.write_text("Hello world\nLine 2\nLine 3")

    file2 = tmp_path / "file2.py"
    file2.write_text("def hello():\n    print('Hello')\n    return 42")

    subdir = tmp_path / "subdir"
    subdir.mkdir()
    subfile = subdir / "subfile.txt"
    subfile.write_text("Subdirectory file content")

    return tmp_path, file1, file2, subdir, subfile

def create_path_scrubber():
    def path_replacer(text):

        lines = text.split('\n')
        result_lines = []

        for line in lines:
            new_line = scrub_line(line)
            result_lines.append(new_line)

        return '\n'.join(result_lines)
    return path_replacer


def scrub_line(line):
    if '/cat ' in line:
        parts = line.split('/cat ')
        filename = os.path.basename(parts[1].strip())
        return parts[0] + '/cat /tmp/test_path/' + filename
    elif '/ls ' in line:
        parts = line.split('/ls ')
        return parts[0] + '/ls /tmp/test_path'
    else:
        return line


def create_date_scrubber():
    return create_regex_scrubber(
        r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}',
        '[DATE]'
    )

def create_ls_error_scrubber():
    """Normalize ls error messages between Mac and Windows"""
    def ls_error_replacer(text):
        import re
        pattern = r"ls: cannot access '([^']+)': No such file or directory"
        replacement = r"ls: \1: No such file or directory"
        return re.sub(pattern, replacement, text)
    return ls_error_replacer

def all_scrubbers():
    return combine_scrubbers(
        create_path_scrubber(),
        create_date_scrubber(),
        create_ls_error_scrubber()
    )


def verify_tool(framework, command):
    result = framework.parse_and_execute(command)
    verify(f"Command:\n{command}\n\nResult:\n{result}", options=Options()
           .with_scrubber(all_scrubbers()))

