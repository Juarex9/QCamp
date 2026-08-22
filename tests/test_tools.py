"""Unit tests for remito tools. No QVAC worker."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.db import connect, init_schema
from app.models import RemitoIn
from app.tools import (
    DuplicateRemitoError,
    RemitoNotFoundError,
    RemitoValidationError,
    extract_remito,
    list_remitos,
    save_remito,
    summarize_harvest,
    update_remito,
)


@pytest.fixture
def conn(tmp_path: Path):
    connection = connect(tmp_path / "remitos.db")
    init_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


def test_extract_remito_parses_json_without_io(tmp_path: Path, conn) -> None:
    raw = (
        '{"fecha":"2026-08-22","patente":"AB123CD","tonelaje_kg":1500,'
        '"origen":"Finca Norte","destino":"Ingenio","producto":"soja","humedad":14.5}'
    )
    result = extract_remito(raw)
    assert result.fecha == "2026-08-22"
    assert result.patente == "AB123CD"
    assert result.tonelaje_kg == 1500
    assert result.origen == "Finca Norte"
    assert result.destino == "Ingenio"
    assert result.producto == "soja"
    assert result.humedad == 14.5
    assert result.raw_ocr == raw
    assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 0
    assert not any(path.is_dir() for path in tmp_path.iterdir())


def test_extract_remito_keeps_garbage_raw_ocr(conn) -> None:
    raw = "??? ticket ilegible ???"
    result = extract_remito(raw)
    assert result.tonelaje_kg is None
    assert result.fecha is None
    assert result.raw_ocr == raw
    assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 0


def test_extract_remito_parses_labeled_ticket_text() -> None:
    raw = (
        "REMITO / TICKET DE BALANZA\n"
        "SINTETICO - NO ES UN TICKET REAL\n"
        "FECHA: 2026-08-20\n"
        "PATENTE: AB123CD\n"
        "TONELAJE: 18500 KG\n"
        "ORIGEN: TUCUMAN\n"
        "DESTINO: ROSARIO\n"
        "PRODUCTO: SOJA\n"
        "HUMEDAD: 13.5\n"
    )
    result = extract_remito(raw)
    assert result.fecha == "2026-08-20"
    assert result.patente == "AB123CD"
    assert result.tonelaje_kg == 18500
    assert result.origen == "TUCUMAN"
    assert result.destino == "ROSARIO"
    assert result.producto == "SOJA"
    assert result.humedad == 13.5


def test_extract_remito_parses_balanza_neto_over_bruto_tara() -> None:
    raw = (
        "BALANZA LA MERCED - TUCUMAN\n"
        "TICKET NRO 004821   FECHA 22/08/2026\n"
        "PATENTE AB123CD   CHOFER J. PEREZ\n"
        "PRODUCTO SOJA\n"
        "BRUTO   41.200 KG\n"
        "TARA    12.460 KG\n"
        "NETO    28.740 KG\n"
        "HUMEDAD 13,4 %\n"
    )
    result = extract_remito(raw)
    assert result.tonelaje_kg == 28740
    assert result.fecha == "2026-08-22"
    assert result.patente == "AB123CD"
    assert result.producto == "SOJA"
    assert result.humedad == 13.4


def test_extract_remito_refuses_ambiguous_unlabeled_kg() -> None:
    raw = "carga 41200 kg y despues 12460 kg sin etiquetas"
    assert extract_remito(raw).tonelaje_kg is None


def test_extract_remito_single_unlabeled_kg_is_used() -> None:
    raw = "REMITO patente AB123CD 1500 kg soja"
    result = extract_remito(raw)
    assert result.tonelaje_kg == 1500
    assert result.patente == "AB123CD"
    assert result.producto == "soja"


def test_save_remito_inserts_when_kg_positive(conn) -> None:
    saved = save_remito(
        conn,
        RemitoIn(
            fecha="2026-08-22",
            patente="AB123CD",
            tonelaje_kg=12500,
            producto="maiz",
            raw_ocr="ocr text",
        ),
    )
    assert saved.id >= 1
    assert saved.tonelaje_kg == 12500
    assert saved.raw_ocr == "ocr text"
    rows = list_remitos(conn)
    assert len(rows) == 1
    assert rows[0].patente == "AB123CD"


def test_save_remito_rejects_non_positive_kg(conn) -> None:
    for kg in (0, -3, None):
        with pytest.raises(RemitoValidationError):
            save_remito(conn, RemitoIn(tonelaje_kg=kg, raw_ocr="keep me"))
    assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 0


def test_list_remitos_filters_and_summarize_harvest(conn) -> None:
    save_remito(conn, RemitoIn(fecha="2026-08-21", tonelaje_kg=100, producto="soja"))
    save_remito(conn, RemitoIn(fecha="2026-08-22", tonelaje_kg=250, producto="maiz"))
    save_remito(conn, RemitoIn(fecha="2026-08-22", tonelaje_kg=50, producto="soja"))

    by_fecha = list_remitos(conn, fecha="2026-08-22")
    assert len(by_fecha) == 2
    by_producto = list_remitos(conn, producto="soja")
    assert len(by_producto) == 2

    total = summarize_harvest(conn)
    assert total.total_kg == 400
    assert total.count == 3
    day = summarize_harvest(conn, fecha="2026-08-22")
    assert day.total_kg == 300
    assert day.count == 2


def test_save_remito_duplicate_raises_then_confirm_inserts(conn) -> None:
    payload = RemitoIn(fecha="2026-08-22", patente="AB123CD", tonelaje_kg=28740)
    save_remito(conn, payload)
    with pytest.raises(DuplicateRemitoError) as excinfo:
        save_remito(conn, payload)
    assert excinfo.value.duplicates[0].tonelaje_kg == 28740
    assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 1
    save_remito(conn, payload, allow_duplicate=True)
    assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 2


def test_save_remito_same_kg_other_patente_is_not_duplicate(conn) -> None:
    save_remito(conn, RemitoIn(fecha="2026-08-22", patente="AB123CD", tonelaje_kg=100))
    save_remito(conn, RemitoIn(fecha="2026-08-22", patente="ZZ999AA", tonelaje_kg=100))
    save_remito(conn, RemitoIn(fecha="2026-08-23", patente="AB123CD", tonelaje_kg=100))
    assert conn.execute("SELECT COUNT(*) FROM remitos").fetchone()[0] == 3


def test_update_remito_preserves_raw_ocr(conn) -> None:
    saved = save_remito(
        conn,
        RemitoIn(
            fecha="2026-08-22",
            patente="AB123CD",
            tonelaje_kg=1000,
            producto="soja",
            raw_ocr="ORIGINAL OCR",
        ),
    )
    updated = update_remito(
        conn,
        saved.id,
        RemitoIn(
            fecha="2026-08-23",
            patente="ZZ999AA",
            tonelaje_kg=2000,
            producto="maiz",
            raw_ocr="SHOULD BE IGNORED",
        ),
    )
    assert updated.patente == "ZZ999AA"
    assert updated.tonelaje_kg == 2000
    assert updated.producto == "maiz"
    assert updated.raw_ocr == "ORIGINAL OCR"
    assert list_remitos(conn)[0].raw_ocr == "ORIGINAL OCR"


def test_update_remito_missing_id_raises(conn) -> None:
    with pytest.raises(RemitoNotFoundError):
        update_remito(conn, 999, RemitoIn(tonelaje_kg=10))


def test_update_remito_partial_provided_preserves_other_fields(conn) -> None:
    saved = save_remito(
        conn,
        RemitoIn(
            fecha="2026-08-22",
            patente="AB123CD",
            tonelaje_kg=28740,
            producto="soja",
            origen="Lote 7",
            humedad=13.4,
            raw_ocr="OCR",
        ),
    )
    updated = update_remito(
        conn,
        saved.id,
        RemitoIn(tonelaje_kg=28750),
        provided={"tonelaje_kg"},
    )
    assert updated.tonelaje_kg == 28750
    assert updated.fecha == "2026-08-22"
    assert updated.patente == "AB123CD"
    assert updated.producto == "soja"
    assert updated.origen == "Lote 7"
    assert updated.humedad == 13.4


def test_update_remito_provided_empty_field_clears_it(conn) -> None:
    saved = save_remito(
        conn,
        RemitoIn(tonelaje_kg=100, destino="Rosario", producto="maiz"),
    )
    updated = update_remito(
        conn,
        saved.id,
        RemitoIn(tonelaje_kg=100, destino=None),
        provided={"tonelaje_kg", "destino"},
    )
    assert updated.destino is None
    assert updated.producto == "maiz"
