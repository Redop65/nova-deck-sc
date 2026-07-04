import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import create_app


CONFIG = Path(__file__).resolve().parents[1] / "config" / "buttons.json"


def profile_pages(data: dict, profile_id: str = "default") -> list[dict]:
    profile = next(item for item in data["profiles"] if item["id"] == profile_id)
    return profile["pages"]


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


def test_exposes_profiles_and_profile_pages() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        profiles = client.get("/api/profiles")
        prospector = client.get("/api/profiles/prospector")

    assert profiles.status_code == 200
    assert profiles.json()["profiles"] == [
        {"id": "default", "name": "Default"},
        {"id": "prospector", "name": "Prospector"},
        {"id": "vulture", "name": "Vulture"},
    ]
    assert prospector.status_code == 200
    assert [page["id"] for page in prospector.json()["profile"]["pages"]] == [
        "flight", "mining"
    ]


def test_profile_specific_command_lookup() -> None:
    app = create_app(CONFIG)
    sent: dict = {}
    app.state.keyboard.send = lambda combo, hold_ms=0: sent.update(
        combo=combo, hold_ms=hold_ms
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/commands",
            json={"profile_id": "vulture", "button_id": "salvage-mode"},
        )
        missing = client.post(
            "/api/commands",
            json={"profile_id": "prospector", "button_id": "salvage-mode"},
        )

    assert response.status_code == 200
    assert sent == {"combo": "M", "hold_ms": 0}
    assert missing.status_code == 404


def test_serves_custom_icon_assets() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        icon = client.get("/assets/icons/landing-gear.svg")
        missing = client.get("/assets/icons/does-not-exist.svg")

    assert icon.status_code == 200
    assert icon.headers["content-type"].startswith("image/svg+xml")
    assert b"<svg" in icon.content
    assert missing.status_code == 404


def test_serves_mobile_app_manifest_and_favicon() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        manifest = client.get("/manifest.webmanifest")
        favicon = client.get("/favicon.ico")
    assert manifest.status_code == 200
    assert manifest.json()["display"] == "fullscreen"
    assert manifest.json()["start_url"] == "/"
    assert favicon.status_code == 200
    assert favicon.headers["content-type"].startswith("image/svg+xml")


def test_frontend_assets_revalidate_after_updates() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        index = client.get("/")
        javascript = client.get("/assets/app.js?v=test")
        stylesheet = client.get("/assets/styles.css?v=test")
        themes = client.get("/assets/themes.css?v=test")
    assert "app.js?v=1.1.0-afk" in index.text
    assert "styles.css?v=1.1.0-afk" in index.text
    assert "themes.css?v=1.1.0-afk" in index.text
    assert javascript.headers["cache-control"] == "no-cache, must-revalidate"
    assert stylesheet.headers["cache-control"] == "no-cache, must-revalidate"
    assert themes.headers["cache-control"] == "no-cache, must-revalidate"


def test_command_is_simulated_in_forced_test_mode() -> None:
    app = create_app(CONFIG, force_test_mode=True)
    with TestClient(app) as client:
        response = client.post("/api/commands", json={"button_id": "landing-gear"})
    assert response.status_code == 200
    assert response.json()["test_mode"] is True
    assert response.json()["keys"] == "N"


def test_obs_command_is_simulated_without_connecting() -> None:
    app = create_app(CONFIG, force_test_mode=True)
    app.state.obs.execute = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("OBS no debe conectarse en modo prueba")
    )
    with TestClient(app) as client:
        response = client.post("/api/commands", json={"button_id": "obs-record"})
    assert response.status_code == 200
    assert response.json()["action_type"] == "obs"
    assert response.json()["obs_action"] == "toggle_recording"
    assert response.json()["test_mode"] is True


def test_obs_disabled_returns_clear_error() -> None:
    with TestClient(create_app(CONFIG)) as client:
        response = client.post("/api/commands", json={"button_id": "obs-record"})
    assert response.status_code == 503
    assert "deshabilitada" in response.json()["detail"]


def test_status_never_exposes_obs_password() -> None:
    with TestClient(create_app(CONFIG, force_test_mode=True)) as client:
        status = client.get("/api/status")
    assert status.status_code == 200
    assert status.json()["obs"]["enabled"] is False
    assert "password" not in status.json()["obs"]


def test_invalid_button_is_isolated_and_reported() -> None:
    invalid_config = Path(__file__).parent / "_buttons_partial_error_test.json"
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    flight = profile_pages(data)[0]
    flight["buttons"].append(
        {"id": "broken-action", "name": "Broken Action", "keys": "Mouse99"}
    )
    invalid_config.write_text(json.dumps(data), encoding="utf-8")
    try:
        app = create_app(invalid_config, force_test_mode=True)
        with TestClient(app) as client:
            profiles = client.get("/api/profiles")
            profile = client.get("/api/profiles/default")
            valid = client.post("/api/commands", json={"button_id": "landing-gear"})
            invalid = client.post("/api/commands", json={"button_id": "broken-action"})

        assert profiles.status_code == 200
        assert profiles.json()["warnings"][0]["path"].endswith("buttons[7]")
        broken = profile_pages(
            {"profiles": [profile.json()["profile"]]}
        )[0]["buttons"][-1]
        assert broken["disabled"] is True
        assert "Tecla no soportada" in broken["_config_error"]
        assert valid.status_code == 200
        assert invalid.status_code == 404
    finally:
        invalid_config.unlink(missing_ok=True)


def test_structural_config_error_is_clear_in_status() -> None:
    invalid_config = Path(__file__).parent / "_buttons_structure_error_test.json"
    invalid_config.write_text('{"profiles": []}', encoding="utf-8")
    try:
        with TestClient(create_app(invalid_config, force_test_mode=True)) as client:
            status = client.get("/api/status")
            profiles = client.get("/api/profiles")
        assert status.status_code == 200
        assert status.json()["configuration"]["ok"] is False
        assert "profiles" in status.json()["configuration"]["error"]
        assert profiles.status_code == 500
        assert "profiles" in profiles.json()["detail"]
    finally:
        invalid_config.unlink(missing_ok=True)


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


def test_macro_dispatches_ordered_steps() -> None:
    app = create_app(CONFIG)
    executed: dict = {}

    def capture(steps: list[dict]) -> None:
        executed["steps"] = steps

    app.state.keyboard.send_sequence = capture
    with TestClient(app) as client:
        response = client.post("/api/commands", json={"button_id": "mobiglas-to-map"})

    assert response.status_code == 200
    assert response.json()["action_type"] == "macro"
    assert response.json()["steps"] == 2
    assert executed["steps"] == [
        {"keys": "F1", "hold_ms": 0, "delay_after_ms": 500},
        {"keys": "F2", "hold_ms": 0, "delay_after_ms": 0},
    ]


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
            "icon": "assets/icons/quantum.svg",
            "color": "cyan",
            "disabled": False,
        },
    }

    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            created = client.post("/api/buttons", json=payload)
            assert created.status_code == 201
            assert created.json()["button"]["icon"] == "assets/icons/quantum.svg"

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
            for page in profile_pages(saved)
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
        both_actions = {
            "page_id": "flight",
            "button": {
                "id": "two-actions",
                "name": "Two Actions",
                "keys": "K",
                "macro": [{"keys": "F1"}],
            },
        }
        assert client.post("/api/buttons", json=both_actions).status_code == 422
        invalid_macro = {
            "page_id": "flight",
            "button": {
                "id": "bad-macro",
                "name": "Bad Macro",
                "macro": [{"keys": "Mouse99", "delay_after_ms": 500}],
            },
        }
        assert client.post("/api/buttons", json=invalid_macro).status_code == 422
    finally:
        editable_config.unlink(missing_ok=True)


def test_macro_is_persisted_to_json() -> None:
    editable_config = Path(__file__).parent / "_buttons_macro_test.json"
    editable_config.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    payload = {
        "page_id": "mobiglas",
        "button": {
            "id": "saved-macro",
            "name": "Saved Macro",
            "color": "violet",
            "macro": [
                {"keys": "F1", "delay_after_ms": 500},
                {"keys": "F2", "hold_ms": 100},
            ],
        },
    }

    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            response = client.post("/api/buttons", json=payload)
        assert response.status_code == 201

        saved = json.loads(editable_config.read_text(encoding="utf-8"))
        button = next(
            item
            for page in profile_pages(saved)
            for item in page["buttons"]
            if item["id"] == "saved-macro"
        )
        assert "keys" not in button
        assert button["macro"] == [
            {"keys": "F1", "hold_ms": 0, "delay_after_ms": 500},
            {"keys": "F2", "hold_ms": 100, "delay_after_ms": 0},
        ]
    finally:
        editable_config.unlink(missing_ok=True)


def test_legacy_pages_are_migrated_to_default_profile() -> None:
    legacy_config = Path(__file__).parent / "_buttons_legacy_test.json"
    legacy_config.write_text(
        json.dumps(
            {
                "title": "Legacy Deck",
                "pages": [
                    {
                        "id": "flight",
                        "name": "Flight",
                        "buttons": [
                            {"id": "legacy-key", "name": "Legacy Key", "keys": "K"}
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    try:
        with TestClient(create_app(legacy_config, force_test_mode=True)) as client:
            profiles = client.get("/api/profiles")
            profile = client.get("/api/profiles/default")
        assert profiles.json()["profiles"] == [{"id": "default", "name": "Default"}]
        assert profile.json()["profile"]["pages"][0]["buttons"][0]["id"] == "legacy-key"
    finally:
        legacy_config.unlink(missing_ok=True)


def test_same_button_id_can_exist_in_different_profiles() -> None:
    editable_config = Path(__file__).parent / "_buttons_profiles_test.json"
    editable_config.write_text(CONFIG.read_text(encoding="utf-8"), encoding="utf-8")
    button = {"id": "shared-custom", "name": "Shared Custom", "keys": "K"}

    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            prospector = client.post(
                "/api/buttons",
                json={"profile_id": "prospector", "page_id": "mining", "button": button},
            )
            vulture = client.post(
                "/api/buttons",
                json={"profile_id": "vulture", "page_id": "salvage", "button": button},
            )
            deleted = client.delete(
                "/api/buttons/shared-custom?profile_id=vulture"
            )
            prospector_config = client.get("/api/profiles/prospector").json()["profile"]
            vulture_config = client.get("/api/profiles/vulture").json()["profile"]

        assert prospector.status_code == 201
        assert vulture.status_code == 201
        assert deleted.status_code == 200
        assert any(
            item["id"] == "shared-custom"
            for page in prospector_config["pages"]
            for item in page["buttons"]
        )
        assert not any(
            item["id"] == "shared-custom"
            for page in vulture_config["pages"]
            for item in page["buttons"]
        )
    finally:
        editable_config.unlink(missing_ok=True)


def test_editor_moves_button_between_profiles_and_creates_backup() -> None:
    editable_config = Path(__file__).parent / "_buttons_move_profile_test.json"
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    editable_config.write_text(json.dumps(data), encoding="utf-8")
    landing = next(
        button
        for page in profile_pages(data)
        for button in page["buttons"]
        if button["id"] == "landing"
    )
    payload = {
        "profile_id": "default",
        "target_profile_id": "vulture",
        "page_id": "flight",
        "position": 0,
        "button": landing,
    }
    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            moved = client.put("/api/buttons/landing", json=payload)
            default = client.get("/api/profiles/default").json()["profile"]
            vulture = client.get("/api/profiles/vulture").json()["profile"]
        assert moved.status_code == 200
        assert moved.json()["local_backup"].startswith("before-import-")
        assert not any(
            button["id"] == "landing"
            for page in default["pages"] for button in page["buttons"]
        )
        vulture_flight = next(page for page in vulture["pages"] if page["id"] == "flight")
        assert vulture_flight["buttons"][0]["id"] == "landing"
    finally:
        editable_config.unlink(missing_ok=True)


def test_editor_reorders_button_in_page() -> None:
    editable_config = Path(__file__).parent / "_buttons_reorder_test.json"
    data = json.loads(CONFIG.read_text(encoding="utf-8"))
    editable_config.write_text(json.dumps(data), encoding="utf-8")
    lights = next(
        button for button in profile_pages(data)[0]["buttons"] if button["id"] == "lights"
    )
    try:
        with TestClient(create_app(editable_config, force_test_mode=True)) as client:
            response = client.put(
                "/api/buttons/lights",
                json={
                    "profile_id": "default", "target_profile_id": "default",
                    "page_id": "flight", "position": 0, "button": lights,
                },
            )
            flight = client.get("/api/profiles/default").json()["profile"]["pages"][0]
        assert response.status_code == 200
        assert flight["buttons"][0]["id"] == "lights"
    finally:
        editable_config.unlink(missing_ok=True)
