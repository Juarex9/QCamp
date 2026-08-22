"""Pydantic models for remito extract/save. Save requires tonelaje_kg > 0."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RemitoFields(BaseModel):
    fecha: str | None = None
    patente: str | None = None
    tonelaje_kg: float | None = None
    origen: str | None = None
    destino: str | None = None
    producto: str | None = None
    humedad: float | None = None


class ExtractResult(RemitoFields):
    raw_ocr: str
    confidence: float | None = None


class RemitoIn(RemitoFields):
    raw_ocr: str | None = None
    image_path: str | None = None
    confidence: float | None = None


class RemitoSave(RemitoIn):
    tonelaje_kg: float = Field(gt=0)


class RemitoOut(RemitoIn):
    id: int
    created_at: str


class HarvestSummary(BaseModel):
    total_kg: float
    count: int
    fecha: str | None = None
