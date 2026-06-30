import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


CONFIG = Path(__file__).resolve().parents[1] / "config" / "buttons.json"


def test_reads_button_pages() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        response = client.get("/api/buttons")
    assert response.status_code == 200
    assert [page["id"] for page in response.json()["pages"]] == [
        "flight", "mobiglas", "combat", "mining", "fps", "camera-obs"
    ]
    flight_ids = [
        button["id"]
        for button in response.json()["pages"][0]["buttons"]
    ]
    assert "cruise-control" not in flight_ids
    assert "wing-configuration" in flight_ids
    assert "open-all-doors" in flight_ids
    assert "star-map" not in flight_ids
    assert "mobiglas" not in flight_ids
    mobiglas_ids = [
        button["id"]
        for button in response.json()["pages"][1]["buttons"]
    ]
    assert "mobiglas-open" in mobiglas_ids
    assert "star-map" in mobiglas_ids


def test_command_is_simulated_in_forced_test_mode() -> None:
    app = create_app(CONFIG, force_test_mode=True)
    with TestClient(app) as client:
        response = client.post("/api/commands", json={"button_id": "landing-gear"})
    assert response.status_code == 200
    assert response.json()["test_mode"] is True
    assert response.json()["keys"] == "N"


def test_quantum_drive_uses_one_second_hold() -> None:
    app = create_app(CONFIG)
    sent: dict = {}

    def capture(combo: str, hold_ms: int = 0) -> None:
        sent.update(combo=combo, hold_ms=hold_ms)

    app.state.keyboard.send = capture
    with TestClient(app) as client:
        response = client.post("/api/commands", json={"button_id": "quantum-drive"})

    assert response.status_code == 200
    assert response.json()["hold_ms"] == 1000
    assert sent == {"combo": "B", "hold_ms": 1000}


def test_unknown_and_disabled_buttons_are_rejected() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        missing = client.post("/api/commands", json={"button_id": "unknown"})
        disabled = client.post("/api/commands", json={"button_id": "missile-mode"})
    assert missing.status_code == 404
    assert disabled.status_code == 409


def test_create_update_move_and_delete_button() -> None:
    editable_config = Path(__file__).parent / "_buttons_crud_test.json"
    editable_config.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    payload = {
        "page_id": "flight",
        "button": {
            "id": "test-action",
            "name": "Test Action",
            "keys": "Ctrl+F12",
            "icon": "TST",
            "color": "cyan",
            "disabled": False,
        },
    }

    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            created = client.post("/api/buttons", json=payload)
            assert created.status_code == 201

            payload["page_id"] = "fps"
            payload["button"]["id"] = "test-action-updated"
            payload["button"]["name"] = "Updated Action"
            updated = client.put("/api/buttons/test-action", json=payload)
            assert updated.status_code == 200

            config = client.get("/api/buttons").json()
            fps = next(page for page in config["pages"] if page["id"] == "fps")
            assert any(button["id"] == "test-action-updated" for button in fps["buttons"])
            assert not any(
                button["id"] == "test-action"
                for page in config["pages"]
                for button in page["buttons"]
            )

            deleted = client.delete("/api/buttons/test-action-updated")
            assert deleted.status_code == 200

        saved = json.loads(editable_config.read_text(encoding="utf-8"))
        assert not any(
            button["id"].startswith("test-action")
            for page in saved["pages"]
            for button in page["buttons"]
        )
    finally:
        editable_config.unlink(missing_ok=True)


def test_editor_rejects_duplicate_id_and_invalid_enabled_key() -> None:
    editable_config = Path(__file__).parent / "_buttons_validation_test.json"
    editable_config.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    duplicate = {
        "page_id": "flight",
        "button": {"id": "landing-gear", "name": "Duplicate", "keys": "K"},
    }
    invalid = {
        "page_id": "flight",
        "button": {"id": "bad-key", "name": "Bad Key", "keys": "Mouse99"},
    }

    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            assert client.post("/api/buttons", json=duplicate).status_code == 409
        response = client.post("/api/buttons", json=invalid)
        assert response.status_code == 422
        assert "Tecla no soportada" in response.json()["detail"]
        blank_name = {
            "page_id": "flight",
            "button": {"id": "blank-name", "name": "   ", "keys": "K"},
        }
        assert client.post("/api/buttons", json=blank_name).status_code == 422
    finally:
        editable_config.unlink(missing_ok=True)
