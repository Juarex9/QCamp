"""Config helpers for local vs cloud bind."""

from __future__ import annotations

import pytest

from app.config import bind_host, bind_port, cors_origins, seed_demo_on_empty


def test_bind_host_defaults_local() -> None:
    assert bind_host() == "127.0.0.1"


def test_bind_host_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REMITO_HOST", "0.0.0.0")
    assert bind_host() == "0.0.0.0"


def test_bind_port_prefers_port_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PORT", "10000")
    monkeypatch.delenv("REMITO_PORT", raising=False)
    assert bind_port() == 10000


def test_cors_origins_splits_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "REMITO_CORS_ORIGINS", "https://a.vercel.app, https://b.vercel.app"
    )
    assert cors_origins() == [
        "https://a.vercel.app",
        "https://b.vercel.app",
    ]


def test_seed_demo_on_empty_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("REMITO_SEED_DEMO", raising=False)
    assert seed_demo_on_empty() is False
    monkeypatch.setenv("REMITO_SEED_DEMO", "1")
    assert seed_demo_on_empty() is True
