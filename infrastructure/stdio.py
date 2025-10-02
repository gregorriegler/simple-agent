import sys
from typing import TextIO

from application.io import IO


class StdIO(IO):

    def input(self, prompt: str) -> str:
        return input(prompt)

    def print(self, message: str, *, file: TextIO | None = None) -> None:
        print(message, file=file)

    def escape_requested(self) -> bool:
        if sys.platform == "win32":
            import msvcrt
            if not msvcrt.kbhit():
                return False
            return msvcrt.getch() == b"\x1b"
        stdin = sys.stdin
        if not stdin.isatty():
            return False
        import select
        import termios
        import tty
        fd = stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            readable, _, _ = select.select([stdin], [], [], 0)
            if not readable:
                return False
            return stdin.read(1) == "\x1b"
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, old_attrs)
