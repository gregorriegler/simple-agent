def message_claude(messages, system_prompt):
    print("\n[MOCK] Claude would have sent this to the API:")
    print(f"System Prompt: {system_prompt[:100]}..." if system_prompt else "No system prompt")
    print(f"Last message: {messages[-1]['content'][:200]}..." if messages else "No messages")
    return "This is a mock response from Claude. No actual API call was made."
