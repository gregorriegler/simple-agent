from agent import Display


class ConsoleDisplay(Display):

    def assistant_says(self, message):
        print(f"\nClaude: {message}")

    def tool_about_to_execute(self, parsed_tool):
        print(f"\nExecuting {parsed_tool}")

    def tool_result(self, result):
        print(result, end='')

    def input(self):
        return input("\nPress Enter to continue or type a message to add: ")

    def exit(self):
        print("\nExiting...")
