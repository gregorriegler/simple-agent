import os

ENV_FILE_NAME = ".env"

_ESCAPES = {"n": "\n", "r": "\r", "t": "\t", '"': '"', "\\": "\\"}


def load_env_files(cwd: str) -> dict[str, str]:
    home_values = _read_env_file(os.path.join(os.path.expanduser("~"), ENV_FILE_NAME))
    cwd_values = _read_env_file(os.path.join(cwd, ENV_FILE_NAME))
    values = {**home_values, **cwd_values}

    for key, value in values.items():
        os.environ.setdefault(key, value)

    return values


def parse_env_file(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in content.splitlines():
        entry = _parse_line(line)
        if entry:
            key, value = entry
            values[key] = value
    return values


def _read_env_file(path: str) -> dict[str, str]:
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return parse_env_file(handle.read())


def _parse_line(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    key, separator, value = stripped.partition("=")
    if not separator:
        return None

    key = _parse_key(key)
    if not key:
        return None

    return key, _parse_value(value)


def _parse_key(key: str) -> str:
    key = key.strip()
    if key.startswith("export "):
        key = key[len("export ") :].strip()
    return key


def _parse_value(value: str) -> str:
    value = value.strip()
    quote = value[:1]
    if quote in ('"', "'"):
        return _parse_quoted_value(value, quote)
    return _strip_inline_comment(value)


def _parse_quoted_value(value: str, quote: str) -> str:
    result = []
    index = 1
    while index < len(value):
        character = value[index]
        if character == quote:
            return "".join(result)
        if character == "\\" and quote == '"' and index + 1 < len(value):
            index += 1
            result.append(_ESCAPES.get(value[index], "\\" + value[index]))
        else:
            result.append(character)
        index += 1
    return "".join(result)


def _strip_inline_comment(value: str) -> str:
    comment_start = value.find(" #")
    if comment_start != -1:
        value = value[:comment_start]
    return value.strip()
