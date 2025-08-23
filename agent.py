from chat import save_chat
from tools import ToolLibrary


class Agent:

    def __init__(self, system_prompt, message_claude, save_chat=save_chat):
        self.system_prompt = system_prompt
        self.message_claude = message_claude
        self.save_chat = save_chat

    def start(self, chat, rounds=999999):
        tools = ToolLibrary()

        for _ in range(rounds):
            answer = self.message_claude(chat.to_list(), self.system_prompt)
            print(f"\nClaude: {answer}")
            chat = chat.assistantSays(answer)

            try:
                user_input = input("\nPress Enter to continue or type a message to add: ")
                if user_input.strip():
                    chat = chat.userSays(user_input)
                    continue
            except EOFError:
                print("\nExiting...")
                break
            except KeyboardInterrupt:
                print("\nExiting...")
                break

            _, tool_result = tools.parse_and_execute(answer)
            print(tool_result, end='')

            if tool_result:
                chat = chat.userSays(tool_result)

            self.save_chat(chat)
