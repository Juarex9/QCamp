"""QvacRuntime unit tests. Mock Client / transport — no live worker."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from tetherto.qvac_sdk import CompletionFinal, ToolCall

from app.qvac_client import QvacRuntime, live_qvac_enabled


def test_live_qvac_disabled_by_default_in_pytest() -> None:
    assert live_qvac_enabled() is False


def test_startup_skips_client_when_disabled() -> None:
    runtime = QvacRuntime()
    asyncio.run(runtime.startup())
    assert runtime.ocr_ready is False
    assert runtime.llm_ready is False
    assert runtime._client is None


def test_startup_flags_false_when_client_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REMITO_QVAC", "1")

    class BoomClient:
        def __init__(self, **kwargs) -> None:
            raise RuntimeError("no worker")

    monkeypatch.setattr("app.qvac_client.Client", BoomClient)
    runtime = QvacRuntime()
    asyncio.run(runtime.startup())
    assert runtime.ocr_ready is False
    assert runtime.llm_ready is False


def test_startup_ocr_fail_leaves_llm_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("REMITO_QVAC", "1")

    class DummyClient:
        def __init__(self, **kwargs) -> None:
            self.transport = object()

        async def connect(self, **kwargs):
            return self

        async def close(self) -> None:
            return None

    async def fake_load(transport, *, model_src=None, **kwargs) -> str:
        name = getattr(model_src, "name", str(model_src))
        if name == "OCR_LATIN":
            raise RuntimeError("ocr download failed")
        return "llm-model-1"

    monkeypatch.setattr("app.qvac_client.Client", DummyClient)
    monkeypatch.setattr("app.qvac_client.load_model", fake_load)
    runtime = QvacRuntime()
    asyncio.run(runtime.startup())
    assert runtime.ocr_ready is False
    assert runtime.llm_ready is True
    assert runtime._llm_model_id == "llm-model-1"


def test_ocr_uses_filepath_chunk_and_concats_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    captured: list = []

    async def fake_stream(transport, request):
        captured.append(request)
        yield SimpleNamespace(
            blocks=[
                SimpleNamespace(text="linea A", bbox=[1, 2, 3, 4], confidence=0.8)
            ],
            error=None,
        )
        yield SimpleNamespace(
            blocks=[SimpleNamespace(text="linea B", bbox=None, confidence=0.6)],
            error=None,
        )

    monkeypatch.setattr("app.qvac_client.ocr_stream", fake_stream)
    image = tmp_path / "ticket.png"
    image.write_bytes(b"img")
    runtime = QvacRuntime()
    runtime.ocr_ready = True
    runtime._ocr_model_id = "ocr-1"
    runtime._client = SimpleNamespace(transport="t")
    result = asyncio.run(runtime.ocr(str(image)))
    assert result.text == "linea A\nlinea B"
    assert result.confidence == pytest.approx(0.7)
    assert len(result.blocks) == 2
    request = captured[0]
    image_chunk = request.image
    assert image_chunk.type == "filePath"
    assert image_chunk.value == str(image.resolve())


def test_complete_invokes_extract_not_save_when_extract_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_calls: list[dict] = []

    async def extract_handler(args: dict) -> dict:
        return {"raw_ocr": args["raw_ocr"], "tonelaje_kg": 1500, "patente": "AB123CD"}

    async def save_handler(args: dict) -> dict:
        saved_calls.append(args)
        return {"id": 1, **args}

    extract_call = ToolCall(
        id="1",
        name="extract_remito",
        arguments={"raw_ocr": "ticket"},
        _handler=extract_handler,
    )
    final = CompletionFinal(content_text="ok", tool_calls=[extract_call])

    class FakeRun:
        @property
        def events(self):
            async def gen():
                yield SimpleNamespace(type="toolCall")
                yield SimpleNamespace(type="completionDone")

            return gen()

        @property
        def final(self):
            async def resolve():
                return final

            return resolve()

    def fake_completion(transport, **kwargs):
        assert kwargs["tools"][0]["name"] == "extract_remito"
        assert kwargs["generation_params"]["temp"] == 0.1
        return FakeRun()

    monkeypatch.setattr("app.qvac_client.completion", fake_completion)
    runtime = QvacRuntime()
    runtime.llm_ready = True
    runtime._llm_model_id = "llm-1"
    runtime._client = SimpleNamespace(transport="t")
    tools = [
        {"name": "extract_remito", "handler": extract_handler},
        {"name": "save_remito", "handler": save_handler},
    ]
    result = asyncio.run(runtime.complete([{"role": "user", "content": "x"}], tools))
    assert result.extracted["tonelaje_kg"] == 1500
    assert result.saved is None
    assert result.invoked == ["extract_remito"]
    assert result.event_types == ["toolCall", "completionDone"]
    assert saved_calls == []


def test_complete_invokes_save_only_after_valid_extract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def extract_handler(args: dict) -> dict:
        return {"raw_ocr": args["raw_ocr"], "tonelaje_kg": 800}

    async def save_handler(args: dict) -> dict:
        return {"id": 9, "tonelaje_kg": args["tonelaje_kg"]}

    extract_call = ToolCall(
        id="1",
        name="extract_remito",
        arguments={"raw_ocr": "ocr"},
        _handler=extract_handler,
    )
    save_call = ToolCall(
        id="2",
        name="save_remito",
        arguments={"tonelaje_kg": 800},
        _handler=save_handler,
    )
    final = CompletionFinal(
        content_text="",
        tool_calls=[save_call, extract_call],  # save listed first — still extract first
    )

    class FakeRun:
        @property
        def events(self):
            async def gen():
                yield SimpleNamespace(type="toolCall")

            return gen()

        @property
        def final(self):
            async def resolve():
                return final

            return resolve()

    monkeypatch.setattr("app.qvac_client.completion", lambda *a, **k: FakeRun())
    runtime = QvacRuntime()
    runtime.llm_ready = True
    runtime._llm_model_id = "llm-1"
    runtime._client = SimpleNamespace(transport="t")
    result = asyncio.run(
        runtime.complete(
            [],
            [
                {"name": "extract_remito", "handler": extract_handler},
                {"name": "save_remito", "handler": save_handler},
            ],
        )
    )
    assert result.invoked == ["extract_remito", "save_remito"]
    assert result.saved["id"] == 9


def test_complete_skips_save_without_extract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked_save = []

    async def save_handler(args: dict) -> dict:
        invoked_save.append(args)
        return args

    save_call = ToolCall(
        id="2",
        name="save_remito",
        arguments={"tonelaje_kg": 800},
        _handler=save_handler,
    )
    final = CompletionFinal(content_text="", tool_calls=[save_call])

    class FakeRun:
        @property
        def events(self):
            async def gen():
                if False:
                    yield None

            return gen()

        @property
        def final(self):
            async def resolve():
                return final

            return resolve()

    monkeypatch.setattr("app.qvac_client.completion", lambda *a, **k: FakeRun())
    runtime = QvacRuntime()
    runtime.llm_ready = True
    runtime._llm_model_id = "llm-1"
    runtime._client = SimpleNamespace(transport="t")
    result = asyncio.run(
        runtime.complete([], [{"name": "save_remito", "handler": save_handler}])
    )
    assert result.saved is None
    assert result.invoked == []
    assert invoked_save == []


def _fake_run(final: CompletionFinal):
    class FakeRun:
        @property
        def events(self):
            async def gen():
                yield SimpleNamespace(type="toolCall")

            return gen()

        @property
        def final(self):
            async def resolve():
                return final

            return resolve()

    return FakeRun()


def test_document_agent_two_turns_then_save(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved_payloads: list[dict] = []

    async def extract_handler(args: dict) -> dict:
        return {
            "raw_ocr": args.get("raw_ocr", "ocr"),
            "tonelaje_kg": 800,
            "patente": "AB123CD",
            "fecha": "2026-08-22",
        }

    async def save_handler(args: dict) -> dict:
        saved_payloads.append(args)
        return {"id": 3, **args}

    extract_call = ToolCall(
        id="1",
        name="extract_remito",
        arguments={"raw_ocr": "ocr", "tonelaje_kg": 800},
        _handler=extract_handler,
    )
    save_call = ToolCall(
        id="2",
        name="save_remito",
        arguments={"tonelaje_kg": 800, "patente": "AB123CD"},
        _handler=save_handler,
    )
    calls = {"n": 0}

    def fake_completion(transport, **kwargs):
        calls["n"] += 1
        names = [tool["name"] for tool in kwargs["tools"]]
        if calls["n"] == 1:
            assert names == ["extract_remito"]
            final = CompletionFinal(content_text="", tool_calls=[extract_call])
            return _fake_run(final)
        assert names == ["save_remito"]
        return _fake_run(CompletionFinal(content_text="", tool_calls=[save_call]))

    monkeypatch.setattr("app.qvac_client.completion", fake_completion)
    runtime = QvacRuntime()
    runtime.llm_ready = True
    runtime._llm_model_id = "llm-1"
    runtime._client = SimpleNamespace(transport="t")
    result = asyncio.run(
        runtime.run_document_agent(
            "ticket",
            [
                {"name": "extract_remito", "handler": extract_handler},
                {"name": "save_remito", "handler": save_handler},
            ],
        )
    )
    assert result.turns == 2
    assert result.invoked == ["extract_remito", "save_remito"]
    assert result.saved["id"] == 3
    assert result.invented is False
    assert result.needs_judgment is False
    assert saved_payloads[0]["tonelaje_kg"] == 800
    assert calls["n"] == 2


def test_document_agent_rejects_invented_kg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    save_hits: list[dict] = []

    async def extract_handler(args: dict) -> dict:
        return {"raw_ocr": "ocr", "tonelaje_kg": 800, "patente": "AB123CD"}

    async def save_handler(args: dict) -> dict:
        save_hits.append(args)
        return args

    extract_call = ToolCall(
        id="1",
        name="extract_remito",
        arguments={"raw_ocr": "ocr"},
        _handler=extract_handler,
    )
    save_call = ToolCall(
        id="2",
        name="save_remito",
        arguments={"tonelaje_kg": 9999},
        _handler=save_handler,
    )
    calls = {"n": 0}

    def fake_completion(transport, **kwargs):
        calls["n"] += 1
        final = (
            CompletionFinal(content_text="", tool_calls=[extract_call])
            if calls["n"] == 1
            else CompletionFinal(content_text="", tool_calls=[save_call])
        )
        return _fake_run(final)

    monkeypatch.setattr("app.qvac_client.completion", fake_completion)
    runtime = QvacRuntime()
    runtime.llm_ready = True
    runtime._llm_model_id = "llm-1"
    runtime._client = SimpleNamespace(transport="t")
    result = asyncio.run(
        runtime.run_document_agent(
            "ticket",
            [
                {"name": "extract_remito", "handler": extract_handler},
                {"name": "save_remito", "handler": save_handler},
            ],
        )
    )
    assert result.saved is None
    assert result.invented is True
    assert result.needs_judgment is True
    assert "save_remito" not in result.invoked
    assert save_hits == []


def test_document_agent_stops_without_kg(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def extract_handler(args: dict) -> dict:
        return {"raw_ocr": args.get("raw_ocr", ""), "tonelaje_kg": None}

    extract_call = ToolCall(
        id="1",
        name="extract_remito",
        arguments={"raw_ocr": "ilegible"},
        _handler=extract_handler,
    )

    def fake_completion(transport, **kwargs):
        return _fake_run(CompletionFinal(content_text="", tool_calls=[extract_call]))

    monkeypatch.setattr("app.qvac_client.completion", fake_completion)
    runtime = QvacRuntime()
    runtime.llm_ready = True
    runtime._llm_model_id = "llm-1"
    runtime._client = SimpleNamespace(transport="t")
    result = asyncio.run(
        runtime.run_document_agent(
            "ilegible",
            [
                {"name": "extract_remito", "handler": extract_handler},
                {"name": "save_remito", "handler": lambda a: a},
            ],
        )
    )
    assert result.turns == 1
    assert result.needs_judgment is True
    assert result.saved is None
    assert result.invoked == ["extract_remito"]
