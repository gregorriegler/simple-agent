import os

import pytest

from simple_agent.infrastructure.env_file import load_env_files, parse_env_file


@pytest.fixture(autouse=True)
def restore_environment():
    original = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original)


def test_parse_simple_assignment():
    assert parse_env_file("KEY=value\n") == {"KEY": "value"}


def test_parse_ignores_blank_lines_and_comments():
    content = """
# a comment
KEY=value

   # indented comment
OTHER=second
""".lstrip()

    assert parse_env_file(content) == {"KEY": "value", "OTHER": "second"}


def test_parse_strips_export_prefix_and_surrounding_whitespace():
    assert parse_env_file("export  KEY = value \n") == {"KEY": "value"}


def test_parse_strips_matching_quotes():
    content = "SINGLE='single value'\nDOUBLE=\"double value\"\n"

    assert parse_env_file(content) == {
        "SINGLE": "single value",
        "DOUBLE": "double value",
    }


def test_parse_keeps_hash_inside_quoted_value_but_strips_inline_comment():
    content = 'QUOTED="value # not a comment"\nPLAIN=value # a comment\n'

    assert parse_env_file(content) == {
        "QUOTED": "value # not a comment",
        "PLAIN": "value",
    }


def test_parse_unescapes_double_quoted_newlines():
    assert parse_env_file('KEY="first\\nsecond"\n') == {"KEY": "first\nsecond"}


def test_parse_keeps_equals_sign_inside_value():
    assert parse_env_file("KEY=a=b\n") == {"KEY": "a=b"}


def test_parse_ignores_lines_without_assignment():
    assert parse_env_file("NOT_AN_ASSIGNMENT\nKEY=value\n") == {"KEY": "value"}


def test_parse_allows_empty_value():
    assert parse_env_file("KEY=\n") == {"KEY": ""}


def test_load_env_files_sets_variables_from_cwd(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("SOME_KEY", raising=False)
    (tmp_path / ".env").write_text("SOME_KEY=from-cwd\n")

    load_env_files(str(tmp_path))

    assert os.environ["SOME_KEY"] == "from-cwd"


def test_load_env_files_does_not_override_existing_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.setenv("SOME_KEY", "from-environment")
    (tmp_path / ".env").write_text("SOME_KEY=from-file\n")

    load_env_files(str(tmp_path))

    assert os.environ["SOME_KEY"] == "from-environment"


def test_load_env_files_prefers_cwd_over_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    cwd = tmp_path / "project"
    cwd.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv("HOME_ONLY", raising=False)
    monkeypatch.delenv("SHARED", raising=False)
    (home / ".env").write_text("SHARED=from-home\nHOME_ONLY=home-value\n")
    (cwd / ".env").write_text("SHARED=from-cwd\n")

    load_env_files(str(cwd))

    assert os.environ["SHARED"] == "from-cwd"
    assert os.environ["HOME_ONLY"] == "home-value"


def test_load_env_files_is_noop_without_files(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))

    assert load_env_files(str(tmp_path)) == {}


def test_load_env_files_ignores_byte_order_mark(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("USERPROFILE", str(tmp_path / "home"))
    monkeypatch.delenv("BOM_KEY", raising=False)
    (tmp_path / ".env").write_text("BOM_KEY=value\n", encoding="utf-8-sig")

    load_env_files(str(tmp_path))

    assert os.environ["BOM_KEY"] == "value"
