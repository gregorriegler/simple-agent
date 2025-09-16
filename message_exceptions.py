class ChatError(Exception):
    pass


class ChatRequestError(ChatError):
    pass


class ChatResponseError(ChatError):
    pass


class ChatInterruptError(ChatError):
    pass
