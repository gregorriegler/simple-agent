import sys


class ConsoleEscapeDetector:

    def __call__(self) -> bool:
        if sys.platform == "win32":
            import msvcrt
            if msvcrt.kbhit():
                return msvcrt.getch() == b"\x1b"
            return False
        import select
        import termios
        import tty
        stdin = sys.stdin
        if not stdin.isatty():
            return False
        fd = stdin.fileno()
        old_attrs = termios.tcgetattr(fd)
        try:
            tty.setcbreak(fd)
            readable, _, _ = select.select([stdin], [], [], 0)
            if not readable:
                return False
            return stdin.read(1) == "\x1b"
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_attrs)
