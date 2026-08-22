"""Shared fixtures. Tests keep SQLite/images off data/ and never start a live worker."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from app.qvac_client import AgentResult, CompleteResult, OcrResult


@pytest.fixture(autouse=True)
def disable_live_qvac(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REMITO_QVAC", "0")


@pytest.fixture
def tmp_db_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "remitos.db"
    monkeypatch.setenv("REMITO_DB_PATH", str(path))
    return path


class FakeQvacRuntime:
    """In-memory QVAC stand-in for TestClient. No worker, no models."""

    def __init__(self, *, do_save: bool = False) -> None:
        self.ocr_ready = True
        self.llm_ready = True
        self.do_save = do_save
        self.ocr_paths: list[str] = []
        self.complete_calls: list[tuple[list, list]] = []
        self.ocr_text = "REMITO patente AB123CD 1500 kg soja"
        self.ocr_confidence = 0.91
        self.last_extract: dict | None = None
        self.invent_kg = False

    async def startup(self) -> None:
        return None

    async def shutdown(self) -> None:
        self.ocr_ready = False
        self.llm_ready = False

    async def ocr(self, path: str) -> OcrResult:
        self.ocr_paths.append(path)
        return OcrResult(
            text=self.ocr_text,
            confidence=self.ocr_confidence,
            blocks=[
                {
                    "text": self.ocr_text,
                    "bbox": None,
                    "confidence": self.ocr_confidence,
                }
            ],
        )

    async def complete(self, history: list, tools: list) -> CompleteResult:
        self.complete_calls.append((history, tools))
        names = {tool["name"] for tool in tools}
        handlers = {tool["name"]: tool["handler"] for tool in tools}
        if "extract_remito" in names:
            extracted = await handlers["extract_remito"](
                {
                    "raw_ocr": self.ocr_text,
                    "fecha": "2026-08-22",
                    "patente": "AB123CD",
                    "tonelaje_kg": 1500,
                    "producto": "soja",
                }
            )
            self.last_extract = extracted
            return CompleteResult(
                content_text="",
                extracted=extracted,
                saved=None,
                invoked=["extract_remito"],
                event_types=["toolCall"],
                tool_calls=[
                    SimpleNamespace(
                        name="extract_remito",
                        arguments={"raw_ocr": self.ocr_text, "tonelaje_kg": 1500},
                    )
                ],
            )
        kg = 9999 if self.invent_kg else 1500
        args = {
            **(self.last_extract or {}),
            "tonelaje_kg": kg,
            "patente": "AB123CD",
            "producto": "soja",
            "fecha": "2026-08-22",
        }
        save_call = SimpleNamespace(name="save_remito", arguments=args, invoke=None)
        if "save_remito" not in names or (not self.do_save and not self.invent_kg):
            return CompleteResult(
                content_text="",
                extracted=None,
                saved=None,
                invoked=[],
                event_types=["toolCall"],
                tool_calls=[],
            )
        return CompleteResult(
            content_text="",
            extracted=None,
            saved=None,
            invoked=[],
            event_types=["toolCall"],
            tool_calls=[save_call],
        )

    async def run_document_agent(self, raw_ocr: str, tools: list) -> AgentResult:
        from app.qvac_client import QvacRuntime

        return await QvacRuntime.run_document_agent(self, raw_ocr, tools)


@pytest.fixture
def fake_qvac(monkeypatch: pytest.MonkeyPatch) -> FakeQvacRuntime:
    runtime = FakeQvacRuntime()
    monkeypatch.setattr("app.main.QvacRuntime", lambda: runtime)
    return runtime


@pytest.fixture
def fake_qvac_save(monkeypatch: pytest.MonkeyPatch) -> FakeQvacRuntime:
    runtime = FakeQvacRuntime(do_save=True)
    monkeypatch.setattr("app.main.QvacRuntime", lambda: runtime)
    return runtime
