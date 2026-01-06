import shlex


def create_lexer(text):
    lexer = shlex.shlex(text, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = ""
    return lexer


def split_arguments(text):
    lexer = create_lexer(text)
    return list(lexer)
