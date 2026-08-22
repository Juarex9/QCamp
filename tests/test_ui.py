"""HTMX partials, resumen, and confirm/edit. TestClient — no QVAC worker."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

HX = {"HX-Request": "true"}


def test_landing_pitches_offline_and_links_to_app(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        page = client.get("/", headers={"accept": "text/html"})
        assert page.status_code == 200
        assert 'href="/app"' in page.text
        assert "Qcamp" in page.text
        assert "/static/app.css" in page.text
        assert 'id="theme-toggle"' in page.text
        assert "/static/theme.js" in page.text
        assert 'data-theme="dark"' in page.text
        assert "qcamp-theme" in page.text
        # The landing must not leak app state or the capture form.
        assert 'name="photo"' not in page.text
        assert 'id="list-slot"' not in page.text


def test_app_renders_banner_upload_form_list_resumen(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        page = client.get("/app", headers={"accept": "text/html"})
        assert page.status_code == 200
        assert "ocr_ready=false" in page.text
        assert "llm_ready=false" in page.text
        assert "Guardar remito" in page.text
        assert 'name="photo"' in page.text
        assert "patente" in page.text
        assert "fecha" in page.text
        assert "kg" in page.text
        assert 'id="list-slot"' in page.text
        assert 'id="resumen"' in page.text
        assert 'id="theme-toggle"' in page.text
        assert "/static/app.css" in page.text


def test_hx_list_and_resumen_are_partials(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        created = client.post(
            "/remitos",
            json={
                "fecha": "2026-08-22",
                "patente": "AB123CD",
                "tonelaje_kg": 12500,
                "raw_ocr": "ticket text",
            },
        )
        assert created.status_code == 200

        listed = client.get("/remitos", headers=HX)
        assert listed.status_code == 200
        assert "<html" not in listed.text.lower()
        assert "<table" in listed.text
        assert "AB123CD" in listed.text
        assert "12500" in listed.text

        resumen = client.get("/resumen", headers=HX)
        assert resumen.status_code == 200
        assert "<html" not in resumen.text.lower()
        assert 'id="resumen"' in resumen.text
        assert "12500" in resumen.text


def test_hx_post_remitos_returns_row_partial(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.post(
            "/remitos",
            data={
                "fecha": "2026-08-22",
                "patente": "XX111YY",
                "tonelaje_kg": "80",
                "producto": "trigo",
            },
            headers=HX,
        )
        assert response.status_code == 200
        assert "<html" not in response.text.lower()
        assert "<tr" in response.text
        assert "XX111YY" in response.text
        assert "80" in response.text
        assert response.headers.get("HX-Trigger") == "remitoSaved"
        assert response.headers.get("HX-Retarget") == "#remitos-table-body"


def test_get_resumen_json_is_sum_tonelaje(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        client.post(
            "/remitos",
            json={"fecha": "2026-08-21", "tonelaje_kg": 100, "producto": "soja"},
        )
        client.post(
            "/remitos",
            json={"fecha": "2026-08-22", "tonelaje_kg": 50, "producto": "maiz"},
        )
        total = client.get("/resumen")
        assert total.status_code == 200
        assert total.json()["total_kg"] == 150
        assert total.json()["count"] == 2

        day = client.get("/resumen", params={"fecha": "2026-08-22"})
        assert day.json()["total_kg"] == 50
        assert day.json()["count"] == 1
        assert day.json()["fecha"] == "2026-08-22"


def test_confirm_edit_preserves_raw_ocr(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        created = client.post(
            "/remitos",
            json={
                "fecha": "2026-08-22",
                "patente": "AB123CD",
                "tonelaje_kg": 1000,
                "producto": "soja",
                "raw_ocr": "ORIGINAL OCR TEXT",
            },
        )
        remito_id = created.json()["remito"]["id"]

        edited = client.post(
            f"/remitos/{remito_id}",
            json={
                "fecha": "2026-08-23",
                "patente": "ZZ999AA",
                "tonelaje_kg": 2000,
                "producto": "maiz",
                "raw_ocr": "SHOULD BE IGNORED",
            },
        )
        assert edited.status_code == 200
        body = edited.json()["remito"]
        assert body["fecha"] == "2026-08-23"
        assert body["patente"] == "ZZ999AA"
        assert body["tonelaje_kg"] == 2000
        assert body["producto"] == "maiz"
        assert body["raw_ocr"] == "ORIGINAL OCR TEXT"

        listed = client.get("/remitos").json()["remitos"]
        assert listed[0]["raw_ocr"] == "ORIGINAL OCR TEXT"
        assert listed[0]["patente"] == "ZZ999AA"


def test_hx_confirm_edit_returns_row_and_keeps_raw_ocr(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        created = client.post(
            "/remitos",
            json={
                "fecha": "2026-08-22",
                "patente": "AB123CD",
                "tonelaje_kg": 1000,
                "raw_ocr": "ORIGINAL OCR TEXT",
            },
        )
        remito_id = created.json()["remito"]["id"]
        edited = client.post(
            f"/remitos/{remito_id}",
            data={
                "fecha": "2026-08-23",
                "patente": "ZZ999AA",
                "tonelaje_kg": "2000",
                "raw_ocr": "SHOULD BE IGNORED",
            },
            headers=HX,
        )
        assert edited.status_code == 200
        assert "<tr" in edited.text
        assert "ZZ999AA" in edited.text
        assert "ORIGINAL OCR TEXT" in edited.text
        assert edited.headers.get("HX-Retarget") is None
        stored = client.get("/remitos").json()["remitos"][0]
        assert stored["raw_ocr"] == "ORIGINAL OCR TEXT"


def test_edit_partial_json_preserves_other_fields(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        created = client.post(
            "/remitos",
            json={
                "fecha": "2026-08-22",
                "patente": "AB123CD",
                "tonelaje_kg": 28740,
                "producto": "soja",
                "origen": "Lote 7",
                "humedad": 13.4,
            },
        ).json()["remito"]

        edited = client.post(
            f"/remitos/{created['id']}", json={"tonelaje_kg": 28750}
        ).json()["remito"]
        assert edited["tonelaje_kg"] == 28750
        assert edited["fecha"] == "2026-08-22"
        assert edited["patente"] == "AB123CD"
        assert edited["producto"] == "soja"
        assert edited["origen"] == "Lote 7"
        assert edited["humedad"] == 13.4

        # The day total must keep counting this remito.
        day = client.get("/resumen", params={"fecha": "2026-08-22"}).json()
        assert day["count"] == 1
        assert day["total_kg"] == 28750


def test_edit_explicit_empty_field_clears_it(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        created = client.post(
            "/remitos",
            json={"tonelaje_kg": 100, "destino": "Rosario", "producto": "maiz"},
        ).json()["remito"]
        response = client.post(f"/remitos/{created['id']}", json={"destino": ""})
        edited = response.json()["remito"]
        assert edited["destino"] is None
        assert edited["producto"] == "maiz"
        assert edited["tonelaje_kg"] == 100


def test_duplicate_form_shows_warning_with_confirm_and_discard(
    tmp_db_path: Path,
) -> None:
    del tmp_db_path
    data = {"fecha": "2026-08-22", "patente": "AB123CD", "tonelaje_kg": "28740"}
    with TestClient(app) as client:
        first = client.post("/remitos", data=data, headers={"HX-Request": "true"})
        assert first.status_code == 200

        dup = client.post("/remitos", data=data, headers={"HX-Request": "true"})
        assert dup.status_code == 409
        html = dup.text
        assert "Posible duplicado" in html
        assert 'name="confirm_duplicate" value="1"' in html
        assert "Es otro viaje" in html
        assert "Descartar" in html
        # The warning form keeps what the user typed.
        assert 'value="AB123CD"' in html

        confirmed = client.post(
            "/remitos",
            data={**data, "confirm_duplicate": "1"},
            headers={"HX-Request": "true"},
        )
        assert confirmed.status_code == 200


def test_remitos_nuevo_returns_blank_form(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.get("/remitos/nuevo", headers={"HX-Request": "true"})
        assert response.status_code == 200
        assert "Guardar remito" in response.text
        assert "confirm_duplicate" not in response.text


def test_edit_missing_remito_returns_404(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.post("/remitos/999", json={"tonelaje_kg": 10})
        assert response.status_code == 404
        assert response.json()["detail"] == "remito not found"
