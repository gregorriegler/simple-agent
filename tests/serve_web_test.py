from pathlib import Path

from serve_web import resolve_public_url, resolve_templates_path


def test_resolve_public_url_prefers_arg(monkeypatch):
    monkeypatch.setenv("SIMPLE_AGENT_PUBLIC_URL", "http://env-host:8000")

    assert resolve_public_url("http://arg-host:8000") == "http://arg-host:8000"


def test_resolve_public_url_uses_env(monkeypatch):
    monkeypatch.setenv("SIMPLE_AGENT_PUBLIC_URL", "http://env-host:8000")

    assert resolve_public_url(None) == "http://env-host:8000"


def test_resolve_public_url_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("SIMPLE_AGENT_PUBLIC_URL", raising=False)

    assert resolve_public_url(None) is None


def test_resolve_templates_path_prefers_arg(monkeypatch, tmp_path):
    monkeypatch.setenv("SIMPLE_AGENT_TEMPLATES_PATH", str(tmp_path / "from-env"))

    assert resolve_templates_path("/tmp/from-arg") == "/tmp/from-arg"


def test_resolve_templates_path_uses_env(monkeypatch):
    monkeypatch.setenv("SIMPLE_AGENT_TEMPLATES_PATH", "/tmp/from-env")

    assert resolve_templates_path(None, base_dir=Path(".")) == "/tmp/from-env"


def test_resolve_templates_path_uses_repo_default(tmp_path):
    templates_dir = tmp_path / "web" / "templates"
    templates_dir.mkdir(parents=True)

    assert resolve_templates_path(None, base_dir=tmp_path) == str(templates_dir)


def test_resolve_templates_path_returns_none_when_missing(tmp_path):
    assert resolve_templates_path(None, base_dir=tmp_path) is None
