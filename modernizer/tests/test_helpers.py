import pytest
from approvaltests import verify
from approvaltests.reporters.report_with_beyond_compare import ReportWithWinMerge
from approvaltests import set_default_reporter
from approvaltests.scrubbers import create_regex_scrubber, combine_scrubbers

@pytest.fixture(scope="session", autouse=True)
def set_default_reporter_for_all_tests() -> None:
    set_default_reporter(ReportWithWinMerge())

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
        import re
        import os
        
        lines = text.split('\n')
        result_lines = []
        
        for line in lines:
            if '/cat ' in line:
                parts = line.split('/cat ')
                if len(parts) > 1:
                    path_part = parts[1].strip()
                    filename = os.path.basename(path_part)
                    new_line = parts[0] + '/cat /tmp/test_path/' + filename
                    result_lines.append(new_line)
                else:
                    result_lines.append(line)
            elif '/ls ' in line:
                parts = line.split('/ls ')
                if len(parts) > 1:
                    new_line = parts[0] + '/ls /tmp/test_path'
                    result_lines.append(new_line)
                else:
                    result_lines.append(line)
            else:
                result_lines.append(line)
        
        return '\n'.join(result_lines)
    
    return path_replacer

def create_date_scrubber():
    return create_regex_scrubber(
        r'\w{3}\s+\d{1,2}\s+\d{1,2}:\d{2}|\d{1,2}\s+\w{3}\s+\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2}\s+\d{1,2}:\d{2}', 
        '[DATE]'
    )

def create_multi_scrubber(path_scrubber=None, date_scrubber=None):
    if path_scrubber is None:
        path_scrubber = create_path_scrubber()
    if date_scrubber is None:
        date_scrubber = create_date_scrubber()
    return combine_scrubbers(path_scrubber, date_scrubber)

multi_scrubber = create_multi_scrubber()
