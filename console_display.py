from agent import Display


class ConsoleDisplay(Display):

    def assistant_says(self, message):
        print(f"\nClaude: {message}")

    def tool_result(self, result):
        print(result, end='')

    def exit(self):
        print("\nExiting...")
