import asyncio
from pathlib import Path

from simple_agent.application.change_reporter import ChangeReporter

TIMEOUT = 30


class GitChangeReporter(ChangeReporter):
    def __init__(self, working_directory: Path):
        self._working_directory = working_directory

    async def diff(self) -> str:
        try:
            diffs = [await self._git("--no-pager", "diff")]
            for path in await self._new_files():
                diffs.append(await self._diff_of_new_file(path))
        except TimeoutError:
            return ""
        return "".join(diff for diff in diffs if diff)

    async def _new_files(self) -> list[str]:
        new_files = await self._git(
            "ls-files", "--others", "--exclude-standard", "--exclude=.*"
        )
        return new_files.splitlines()

    async def _diff_of_new_file(self, path: str) -> str:
        return await self._git(
            "--no-pager", "diff", "--no-index", "--", "/dev/null", path
        )

    async def _git(self, *args: str) -> str:
        process = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=self._working_directory,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), TIMEOUT)
        except (TimeoutError, asyncio.CancelledError):
            process.kill()
            await process.wait()
            raise
        return stdout.decode("utf-8", errors="replace")
