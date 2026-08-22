"""QVAC facade matching the JS contract: ocr(path) and complete(history, tools).

Python mapping (official SDK): Client() + client.transport;
load_model(t, model_src=OCR_LATIN | LLAMA_3_2_1B_INST_Q4_0);
ocr_stream + OcrStreamRequest image {type:filePath,value}
(JS wraps a string; Python does not);
completion(..., tools=...); drain run.events then await run.final;
toolCall.invoke(). Fail to load → ocr_ready / llm_ready stay false.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tetherto.qvac_sdk import (
    Client,
    OcrStreamRequest,
    completion,
    load_model,
    ocr_stream,
    unload_model,
)
from tetherto.qvac_sdk.models import LLAMA_3_2_1B_INST_Q4_0, OCR_LATIN

logger = logging.getLogger("qcamp.qvac")

OCR_MODEL_CONFIG = {
    "langList": ["en"],
    "magRatio": 1.5,
    "defaultRotationAngles": [90, 180, 270],
    "contrastRetry": False,
    "lowConfidenceThreshold": 0.5,
    "recognizerBatchSize": 1,
}
LLM_MODEL_CONFIG = {"ctx_size": 2048, "temp": 0.1, "tools": True}
LLM_GENERATION_PARAMS = {"temp": 0.1, "seed": 42}
AGENT_SYSTEM = (
    "You are a local back-office agent. Read the remito OCR. "
    "Turn 1: call extract_remito only. Never invent tonelaje_kg. "
    "Turn 2: after you see the extract result, call save_remito with "
    "the same fecha, patente, and tonelaje_kg. Do not change numbers. "
    "If kg is missing or not a number, do not call save_remito."
)
LOCKED_FIELDS = ("tonelaje_kg", "patente", "fecha")


def live_qvac_enabled() -> bool:
    """Live worker/models stay off in pytest unless REMITO_QVAC=1."""
    raw = os.environ.get("REMITO_QVAC", "").strip().lower()
    if raw in {"0", "false", "off", "no"}:
        return False
    if raw in {"1", "true", "on", "yes"}:
        return True
    return "PYTEST_CURRENT_TEST" not in os.environ


def _kg_positive(payload: dict[str, Any] | None) -> bool:
    if not payload:
        return False
    try:
        return float(payload.get("tonelaje_kg")) > 0  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False


@dataclass
class OcrResult:
    text: str
    confidence: float | None
    blocks: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class CompleteResult:
    content_text: str
    extracted: dict[str, Any] | None
    saved: dict[str, Any] | None
    invoked: list[str]
    event_types: list[str]
    tool_calls: list[Any] = field(default_factory=list)


@dataclass
class AgentResult:
    """Two-turn document agent: extract → use result → save. Track QVAC 1°+2°."""

    extracted: dict[str, Any] | None
    saved: dict[str, Any] | None
    invoked: list[str]
    turns: int
    invented: bool
    needs_judgment: bool
    event_types: list[str]


class QvacRuntime:
    """JS-like singleton: startup/shutdown once; ocr(path); complete(history, tools)."""

    def __init__(self) -> None:
        self.ocr_ready = False
        self.llm_ready = False
        self._client: Client | None = None
        self._ocr_model_id: str | None = None
        self._llm_model_id: str | None = None

    @property
    def _transport(self):
        if self._client is None:
            raise RuntimeError("QVAC client is not connected")
        return self._client.transport

    async def startup(self) -> None:
        if not live_qvac_enabled():
            return
        try:
            self._client = Client()
            await self._client.connect()
        except Exception:
            logger.exception("QVAC worker connect failed; OCR and LLM stay disabled")
            self._client = None
            self.ocr_ready = False
            self.llm_ready = False
            return

        transport = self._client.transport
        try:
            self._ocr_model_id = await load_model(
                transport,
                model_src=OCR_LATIN,
                model_config=OCR_MODEL_CONFIG,
            )
            self.ocr_ready = True
        except Exception:
            logger.exception("OCR model load failed (OCR_LATIN)")
            self._ocr_model_id = None
            self.ocr_ready = False

        try:
            self._llm_model_id = await load_model(
                transport,
                model_src=LLAMA_3_2_1B_INST_Q4_0,
                model_config=LLM_MODEL_CONFIG,
            )
            self.llm_ready = True
        except Exception:
            logger.exception("LLM model load failed (LLAMA_3_2_1B_INST_Q4_0)")
            self._llm_model_id = None
            self.llm_ready = False

    async def shutdown(self) -> None:
        transport = None
        try:
            if self._client is not None:
                transport = self._client.transport
        except Exception:
            transport = None
        if transport is not None:
            for model_id in (self._ocr_model_id, self._llm_model_id):
                if model_id:
                    try:
                        await unload_model(transport, model_id)
                    except Exception:
                        logger.debug("unload_model(%s) failed", model_id, exc_info=True)
        if self._client is not None:
            try:
                await self._client.close()
            except Exception:
                logger.debug("client close failed", exc_info=True)
        self._client = None
        self._ocr_model_id = None
        self._llm_model_id = None
        self.ocr_ready = False
        self.llm_ready = False

    async def ocr(self, path: str) -> OcrResult:
        if not self.ocr_ready or not self._ocr_model_id:
            raise RuntimeError("OCR is not ready")
        resolved = str(Path(path).resolve())
        request = OcrStreamRequest.model_validate(
            {
                "type": "ocrStream",
                "modelId": self._ocr_model_id,
                "image": {"type": "filePath", "value": resolved},
                "options": {"paragraph": False},
            }
        )
        texts: list[str] = []
        confidences: list[float] = []
        blocks: list[dict[str, Any]] = []
        async for response in ocr_stream(self._transport, request):
            error = getattr(response, "error", None)
            if error:
                raise RuntimeError(str(error))
            for block in response.blocks or []:
                text = getattr(block, "text", "") or ""
                texts.append(text)
                confidence = getattr(block, "confidence", None)
                if confidence is not None:
                    confidences.append(float(confidence))
                blocks.append(
                    {
                        "text": text,
                        "bbox": getattr(block, "bbox", None),
                        "confidence": confidence,
                    }
                )
        joined = "\n".join(part for part in texts if part)
        mean = sum(confidences) / len(confidences) if confidences else None
        return OcrResult(text=joined, confidence=mean, blocks=blocks)

    async def complete(
        self,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> CompleteResult:
        if not self.llm_ready or not self._llm_model_id:
            raise RuntimeError("LLM is not ready")
        run = completion(
            self._transport,
            model_id=self._llm_model_id,
            history=history,
            tools=tools,
            generation_params=LLM_GENERATION_PARAMS,
        )
        event_types: list[str] = []
        async for event in run.events:
            event_types.append(getattr(event, "type", ""))
        final = await run.final

        extracted: dict[str, Any] | None = None
        saved: dict[str, Any] | None = None
        invoked: list[str] = []
        extracts = [call for call in final.tool_calls if call.name == "extract_remito"]
        saves = [call for call in final.tool_calls if call.name == "save_remito"]
        for call in extracts:
            extracted = await call.invoke()
            invoked.append("extract_remito")
        if extracted and _kg_positive(extracted):
            for call in saves:
                saved = await call.invoke()
                invoked.append("save_remito")
                break
        return CompleteResult(
            content_text=final.content_text,
            extracted=extracted,
            saved=saved,
            invoked=invoked,
            event_types=event_types,
            tool_calls=list(final.tool_calls or []),
        )

    async def run_document_agent(
        self,
        raw_ocr: str,
        tools: list[dict[str, Any]],
    ) -> AgentResult:
        """Force extract then save. Ignore skipped steps; reject invented kg.

        Aligns to track.md: 1–4B must chain tools without forgetting a step
        or inventing an answer. Host never persists a kg the extract did not
        produce.
        """
        extract_tools = [tool for tool in tools if tool["name"] == "extract_remito"]
        save_tools = [tool for tool in tools if tool["name"] == "save_remito"]
        history: list[dict[str, Any]] = [
            {"role": "system", "content": AGENT_SYSTEM},
            {"role": "user", "content": f"OCR remito:\n{raw_ocr}"},
        ]
        event_types: list[str] = []
        invoked: list[str] = []

        first = await self.complete(history, extract_tools)
        event_types.extend(first.event_types)
        extracted = first.extracted
        if extracted:
            invoked.append("extract_remito")
        if not extracted or not _kg_positive(extracted):
            return AgentResult(
                extracted=extracted,
                saved=None,
                invoked=invoked,
                turns=1,
                invented=False,
                needs_judgment=True,
                event_types=event_types,
            )

        history = [
            *history,
            {
                "role": "assistant",
                "content": first.content_text or "extract_remito",
            },
            {
                "role": "user",
                "content": (
                    "extract_remito returned this JSON. Call save_remito "
                    "with the same fecha, patente, tonelaje_kg. "
                    "Do not invent or change numbers.\n"
                    f"{json.dumps(extracted, ensure_ascii=False)}"
                ),
            },
        ]
        second = await self.complete(history, save_tools)
        event_types.extend(second.event_types)
        saved = None
        invented = False
        save_calls = [
            call
            for call in second.tool_calls
            if getattr(call, "name", "") == "save_remito"
        ]
        if not save_calls:
            return AgentResult(
                extracted=extracted,
                saved=None,
                invoked=invoked,
                turns=2,
                invented=False,
                needs_judgment=True,
                event_types=event_types,
            )

        call = save_calls[0]
        args = _tool_args(call)
        if _invents_locked_fields(extracted, args):
            invented = True
        else:
            merged = {**args, **_locked_subset(extracted)}
            handler = _tool_handler(save_tools)
            if handler is not None and _kg_positive(merged):
                saved = await handler(merged)
                invoked.append("save_remito")
            elif hasattr(call, "invoke") and call.invoke and _kg_positive(merged):
                saved = await call.invoke()
                invoked.append("save_remito")

        return AgentResult(
            extracted=extracted,
            saved=saved,
            invoked=invoked,
            turns=2,
            invented=invented,
            needs_judgment=saved is None,
            event_types=event_types,
        )


def _tool_args(call: Any) -> dict[str, Any]:
    raw = getattr(call, "arguments", None) or getattr(call, "args", None) or {}
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        return loaded if isinstance(loaded, dict) else {}
    return dict(raw) if isinstance(raw, dict) else {}


def _tool_handler(save_tools: list[dict[str, Any]]):
    if not save_tools:
        return None
    return save_tools[0].get("handler")


def _locked_subset(extracted: dict[str, Any]) -> dict[str, Any]:
    return {
        key: extracted[key]
        for key in LOCKED_FIELDS
        if extracted.get(key) not in (None, "")
    }


def _invents_locked_fields(
    extracted: dict[str, Any], proposed: dict[str, Any]
) -> bool:
    if proposed.get("tonelaje_kg") in (None, ""):
        return False
    if not _kg_positive(extracted):
        return True
    try:
        proposed_kg = float(proposed["tonelaje_kg"])
        extracted_kg = float(extracted["tonelaje_kg"])
        return abs(proposed_kg - extracted_kg) > 1e-6
    except (TypeError, ValueError):
        return True
