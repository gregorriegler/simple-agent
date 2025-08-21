from chat import Chat, load_chat, save_chat
from tools import ToolLibrary


def start_chat(system_prompt, start_message, new, message_claude, rounds=999999, save_chat=save_chat):
    tools = ToolLibrary()

    chat = Chat() if new else load_chat("claude-session.json")
    print("Starting new session" if new else "Continuing session")

    if start_message:
        chat = chat.userSays(start_message)

    for _ in range(rounds):
        answer = message_claude(chat.to_list(), system_prompt)
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

        save_chat(chat)
