from agent import Display


class ConsoleDisplay(Display):

    def assistant_says(self, message):
        lines = str(message).split('\n')
        if lines:
            print(f"\nAgent: {lines[0]}")
            for line in lines[1:]:
                print(f"       {line}")

    def tool_about_to_execute(self, parsed_tool):
        print(f"\n{parsed_tool}")

    def tool_result(self, result):
        result = self._indent_lines(result, "       ")
        print(f"\n\n{result}", end='')

    def input(self):
        return input("\nPress Enter to continue or type a message to add: ")

    def exit(self):
        print("\nExiting...")

    def _indent_lines(self, text, prefix="    "):
        lines = str(text).split('\n')
        return '\n'.join(f"{prefix}{line}" for line in lines)
