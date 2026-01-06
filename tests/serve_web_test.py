import os

from serve_web import resolve_public_url


def test_resolve_public_url_prefers_arg(monkeypatch):
    monkeypatch.setenv("SIMPLE_AGENT_PUBLIC_URL", "http://env-host:8000")

    assert resolve_public_url("http://arg-host:8000") == "http://arg-host:8000"


def test_resolve_public_url_uses_env(monkeypatch):
    monkeypatch.setenv("SIMPLE_AGENT_PUBLIC_URL", "http://env-host:8000")

    assert resolve_public_url(None) == "http://env-host:8000"


def test_resolve_public_url_returns_none_when_missing(monkeypatch):
    monkeypatch.delenv("SIMPLE_AGENT_PUBLIC_URL", raising=False)

    assert resolve_public_url(None) is None
