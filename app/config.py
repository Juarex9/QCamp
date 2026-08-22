"""Runtime settings: local demo vs cloud (Render / Vercel)."""

from __future__ import annotations

import os


def bind_host() -> str:
    """127.0.0.1 locally; 0.0.0.0 on Render when REMITO_HOST is set."""
    return os.environ.get("REMITO_HOST", "127.0.0.1")


def bind_port() -> int:
    return int(os.environ.get("PORT", os.environ.get("REMITO_PORT", "8000")))


def cors_origins() -> list[str]:
    raw = os.environ.get("REMITO_CORS_ORIGINS", "")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def public_banner_label() -> str:
    """Short line in the status banner (host + privacy hint)."""
    if label := os.environ.get("REMITO_PUBLIC_LABEL"):
        return label
    if os.environ.get("RENDER"):
        return "Render · QVAC off en cloud · datos en disco del servicio"
    return "127.0.0.1 · nada sale del equipo"


def seed_demo_on_empty() -> bool:
    raw = os.environ.get("REMITO_SEED_DEMO", "").strip().lower()
    return raw in {"1", "true", "on", "yes"}


def backend_public_url() -> str | None:
    """Canonical backend URL (Render). Used in docs and Vercel landing build."""
    url = os.environ.get("REMITO_BACKEND_URL", "").strip()
    return url.rstrip("/") if url else None
