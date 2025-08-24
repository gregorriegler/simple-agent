import os
from contextlib import contextmanager

from approvaltests import Options, verify
from approvaltests.scrubbers import create_regex_scrubber, combine_scrubbers


def create_temp_file(tmp_path, filename, contents):
    temp_file = tmp_path / filename
    temp_file.write_text(contents)
    return temp_file


@contextmanager
def temp_directory(tmp_path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield
    finally:
        os.chdir(original_cwd)


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
            new_line = scrub_line_with_path(line)
            result_lines.append(new_line)

        return '\n'.join(result_lines)

    return path_replacer


def scrub_line_with_path(line):
    import re

    # Comprehensive pattern to match any path (Windows or Unix)
    # This approach looks for path-like patterns and then validates them

    def replace_path(match):
        path = match.group(0)

        # Skip if it's just a command like /cat, /ls, etc.
        if re.match(r'^/[a-z-]+$', path):
            return path

        # Check if this looks like a file (has an extension)
        if re.search(r'\.[A-Za-z0-9]+$', path):
            # It's a file, extract just the filename
            filename = os.path.basename(path)
            return f'/tmp/test_path/{filename}'
        else:
            # It's a directory, replace with /tmp/test_path
            return '/tmp/test_path'

    # Pattern 1: Windows absolute paths (C:\... or C:/...)
    # Handle paths with spaces by matching until we hit a space followed by a non-path character
    windows_pattern = r'[A-Za-z]:[/\\](?:[^<>:"|?*\n\r]+[/\\])*[^<>:"|?*\n\r\s]*(?:\.[A-Za-z0-9]+)?'
    result = re.sub(windows_pattern, replace_path, line)

    # Pattern 2: Unix absolute paths starting with / (but not single commands)
    # Match /path/to/something or /file.ext but not /command
    unix_pattern = r'/(?:[^/\s<>:"|?*\n\r]+/)+[^/\s<>:"|?*\n\r]*|/[^/\s<>:"|?*\n\r]*\.[A-Za-z0-9]+'
    result = re.sub(unix_pattern, replace_path, result)

    return result


def create_date_scrubber():
    return create_regex_scrubber(
        r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}',
        '[DATE]'
    )


def create_ls_error_scrubber():
    """Normalize ls error messages between Mac and Linux"""

    def ls_error_replacer(text):
        import re
        # Convert Mac format to Linux format
        # Mac: "ls: /path: No such file or directory"
        # Linux: "ls: cannot access '/path': No such file or directory"
        # Only convert if it's NOT already in Linux format
        if "cannot access" not in text:
            pattern = r"ls: ([^:]+): No such file or directory"
            replacement = r"ls: cannot access '\1': No such file or directory"
            return re.sub(pattern, replacement, text)
        return text

    return ls_error_replacer


def all_scrubbers():
    return combine_scrubbers(
        create_path_scrubber(),
        create_date_scrubber(),
        create_ls_error_scrubber()
    )


def verify_tool(library, command):
    tool = library.parse_tool(command)
    result = library.execute_parsed_tool(tool)
    verify(f"Command:\n{command}\n\nResult:\n{result}", options=Options()
           .with_scrubber(all_scrubbers()))
