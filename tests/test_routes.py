"""Route tests for ingest/list mock. TestClient only — no QVAC worker."""

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app


def test_post_remitos_fields_then_list(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        created = client.post(
            "/remitos",
            json={
                "fecha": "2026-08-22",
                "patente": "AB123CD",
                "tonelaje_kg": 12500,
                "origen": "Finca Norte",
                "destino": "Ingenio",
                "producto": "soja",
                "humedad": 14,
                "raw_ocr": "ticket text",
            },
        )
        assert created.status_code == 200
        remito = created.json()["remito"]
        assert remito["tonelaje_kg"] == 12500
        assert remito["patente"] == "AB123CD"

        listed = client.get("/remitos")
        assert listed.status_code == 200
        rows = listed.json()["remitos"]
        assert len(rows) == 1
        assert rows[0]["id"] == remito["id"]
        assert rows[0]["raw_ocr"] == "ticket text"


def test_post_remitos_invalid_kg_returns_422_and_skips_insert(
    tmp_db_path: Path,
) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        for payload in (
            {"tonelaje_kg": "abc", "raw_ocr": "noisy"},
            {"tonelaje_kg": 0, "raw_ocr": "noisy"},
            {"tonelaje_kg": -1, "raw_ocr": "noisy"},
        ):
            response = client.post("/remitos", json=payload)
            assert response.status_code == 422
            body = response.json()
            assert body["form"] is True
            assert body["raw_ocr"] == "noisy"
        assert client.get("/remitos").json()["remitos"] == []


def test_post_photo_saves_uuid_and_does_not_insert(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.post(
            "/remitos",
            files={"photo": ("ticket.jpg", b"fake-bytes", "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["degraded"] is True
        assert body["form"] is True
        assert body["ocr_ready"] is False
        assert body["llm_ready"] is False
        image_path = Path(body["image_path"])
        assert image_path.exists()
        assert image_path.read_bytes() == b"fake-bytes"
        UUID(image_path.name)
        assert client.get("/remitos").json()["remitos"] == []


def test_post_photo_and_fields_saves_image_and_row(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.post(
            "/remitos",
            data={"fecha": "2026-08-22", "tonelaje_kg": "800", "producto": "trigo"},
            files={"photo": ("ticket.jpg", b"img", "image/jpeg")},
        )
        assert response.status_code == 200
        remito = response.json()["remito"]
        assert remito["tonelaje_kg"] == 800
        assert Path(remito["image_path"]).exists()
        listed = client.get("/remitos").json()["remitos"]
        assert len(listed) == 1


def test_extract_only_raw_ocr_does_not_save(tmp_db_path: Path) -> None:
    del tmp_db_path
    raw = '{"fecha":"2026-08-22","tonelaje_kg":999}'
    with TestClient(app) as client:
        response = client.post("/remitos", json={"raw_ocr": raw})
        assert response.status_code == 200
        body = response.json()
        assert body["form"] is True
        assert body["extract"]["tonelaje_kg"] == 999
        assert body["extract"]["raw_ocr"] == raw
        assert client.get("/remitos").json()["remitos"] == []


def test_post_photo_qvac_extract_only_does_not_insert(
    tmp_db_path: Path, fake_qvac
) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        health = client.get("/health").json()
        assert health["ocr_ready"] is True
        assert health["llm_ready"] is True
        response = client.post(
            "/remitos",
            files={"photo": ("ticket.jpg", b"fake-bytes", "image/jpeg")},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["degraded"] is False
        assert body["form"] is True
        assert body["ocr_ready"] is True
        assert body["extract"]["patente"] == "AB123CD"
        assert body["extract"]["tonelaje_kg"] == 1500
        assert body["invoked"] == ["extract_remito"]
        assert fake_qvac.ocr_paths
        assert Path(fake_qvac.ocr_paths[0]).exists()
        assert client.get("/remitos").json()["remitos"] == []


def test_post_photo_qvac_extract_and_save_inserts(
    tmp_db_path: Path, fake_qvac_save
) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.post(
            "/remitos",
            files={"photo": ("ticket.jpg", b"img", "image/jpeg")},
        )
        assert response.status_code == 200
        remito = response.json()["remito"]
        assert remito["tonelaje_kg"] == 1500
        assert remito["patente"] == "AB123CD"
        assert remito["raw_ocr"]
        assert response.json()["turns"] == 2
        assert response.json()["invented"] is False
        assert Path(remito["image_path"]).exists()
        listed = client.get("/remitos").json()["remitos"]
        assert len(listed) == 1
        assert listed[0]["id"] == remito["id"]


def test_post_duplicate_warns_409_then_confirm_saves(tmp_db_path: Path) -> None:
    del tmp_db_path
    body = {"fecha": "2026-08-22", "patente": "AB123CD", "tonelaje_kg": 28740}
    with TestClient(app) as client:
        assert client.post("/remitos", json=body).status_code == 200

        dup = client.post("/remitos", json=body)
        assert dup.status_code == 409
        assert dup.json()["detail"] == "duplicate_remito"
        assert dup.json()["duplicates"][0]["patente"] == "AB123CD"
        # The refused duplicate must not inflate the day total.
        assert client.get("/resumen").json() == {
            "total_kg": 28740,
            "count": 1,
            "fecha": None,
        }

        confirmed = client.post("/remitos", json={**body, "confirm_duplicate": 1})
        assert confirmed.status_code == 200
        assert client.get("/resumen").json()["count"] == 2


def test_post_same_kg_different_patente_is_not_duplicate(
    tmp_db_path: Path,
) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        first = {"fecha": "2026-08-22", "patente": "AB123CD", "tonelaje_kg": 100}
        second = {"fecha": "2026-08-22", "patente": "ZZ999AA", "tonelaje_kg": 100}
        assert client.post("/remitos", json=first).status_code == 200
        assert client.post("/remitos", json=second).status_code == 200
        assert client.get("/resumen").json()["count"] == 2


def test_agent_never_autosaves_a_duplicate(
    tmp_db_path: Path, fake_qvac_save
) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        first = client.post(
            "/remitos",
            files={"photo": ("ticket.jpg", b"img", "image/jpeg")},
        )
        assert first.status_code == 200

        again = client.post(
            "/remitos",
            files={"photo": ("ticket.jpg", b"img", "image/jpeg")},
        )
        assert again.status_code == 409
        assert again.json()["detail"] == "duplicate_remito"
        assert client.get("/resumen").json()["count"] == 1


def test_post_garbage_humedad_returns_422(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        response = client.post(
            "/remitos",
            json={"tonelaje_kg": 100, "humedad": "no-es-numero"},
        )
        assert response.status_code == 422
        assert "humedad" in response.json()["detail"]

        # Comma decimals are how users type it; accept them.
        ok = client.post(
            "/remitos",
            json={"tonelaje_kg": 100, "humedad": "13,4"},
        )
        assert ok.status_code == 200
        assert ok.json()["remito"]["humedad"] == 13.4


def test_degraded_form_still_works_when_qvac_flags_false(tmp_db_path: Path) -> None:
    del tmp_db_path
    with TestClient(app) as client:
        page = client.get("/app", headers={"accept": "text/html"})
        assert page.status_code == 200
        assert "Guardar remito" in page.text
        assert "ocr_ready=false" in page.text
        created = client.post(
            "/remitos",
            json={"fecha": "2026-08-22", "tonelaje_kg": 10, "producto": "maiz"},
        )
        assert created.status_code == 200
        assert created.json()["remito"]["tonelaje_kg"] == 10
