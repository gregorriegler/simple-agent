import subprocess
from pathlib import Path

from simple_agent.application.change_reporter import ChangeReporter


class GitChangeReporter(ChangeReporter):
    def __init__(self, working_directory: Path):
        self._working_directory = working_directory

    def diff(self) -> str:
        diffs = [self._git("--no-pager", "diff")]
        diffs += [self._diff_of_new_file(path) for path in self._new_files()]
        return "".join(diff for diff in diffs if diff)

    def _new_files(self) -> list[str]:
        return self._git("ls-files", "--others", "--exclude-standard").splitlines()

    def _diff_of_new_file(self, path: str) -> str:
        return self._git("--no-pager", "diff", "--no-index", "--", "/dev/null", path)

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=self._working_directory,
            capture_output=True,
            text=True,
        )
        return result.stdout
