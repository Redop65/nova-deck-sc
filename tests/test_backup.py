import json
from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.backup import BackupError, BackupManager
from app.main import create_app


ROOT = Path(__file__).resolve().parents[1]
SOURCE_BUTTONS = ROOT / "config" / "buttons.json"


def make_manager() -> tuple[BackupManager, Path, Path]:
    buttons = Path(__file__).parent / "_backup_buttons_test.json"
    settings = Path(__file__).parent / "_backup_settings_test.json"
    buttons.write_text(SOURCE_BUTTONS.read_text(encoding="utf-8"), encoding="utf-8")
    settings.write_text(
        json.dumps({
            "app": {"debug": False, "log_level": "INFO"},
            "obs": {
                "enabled": True, "host": "127.0.0.1", "port": 4455,
                "password": "local-secret", "timeout_seconds": 3,
            },
        }),
        encoding="utf-8",
    )
    return BackupManager(buttons, settings, "test"), buttons, settings


def cleanup(buttons: Path, settings: Path) -> None:
    buttons.unlink(missing_ok=True)
    settings.unlink(missing_ok=True)
    backups = buttons.parent / "backups"
    if backups.exists():
        for item in backups.iterdir():
            item.unlink(missing_ok=True)
        backups.rmdir()


def test_safe_export_omits_obs_password_and_lists_icons() -> None:
    manager, buttons, settings = make_manager()
    try:
        backup = manager.export()
        assert backup["format"] == "nova-deck-backup"
        assert backup["version"] == 1
        assert "password" not in backup["configuration"]["settings"]["obs"]
        assert backup["secrets"]["obs_password_included"] is False
        assert "assets/icons/landing-gear.svg" in backup["icon_references"]
    finally:
        cleanup(buttons, settings)


def test_import_creates_local_backup_and_preserves_local_password() -> None:
    manager, buttons, settings = make_manager()
    try:
        backup = manager.export()
        backup["configuration"]["buttons"]["title"] = "Restored Deck"
        result = manager.import_backup(backup)

        saved_buttons = json.loads(buttons.read_text(encoding="utf-8"))
        saved_settings = json.loads(settings.read_text(encoding="utf-8"))
        safety_copy = buttons.parent / "backups" / result["local_backup"]
        local_backup = json.loads(safety_copy.read_text(encoding="utf-8"))

        assert saved_buttons["title"] == "Restored Deck"
        assert saved_settings["obs"]["password"] == "local-secret"
        assert local_backup["secrets"]["obs_password_included"] is True
        assert local_backup["configuration"]["settings"]["obs"]["password"] == "local-secret"
    finally:
        cleanup(buttons, settings)


def test_invalid_import_does_not_overwrite_current_files() -> None:
    manager, buttons, settings = make_manager()
    original_buttons = buttons.read_bytes()
    original_settings = settings.read_bytes()
    try:
        backup = manager.export()
        invalid = deepcopy(backup)
        invalid["configuration"]["buttons"]["profiles"][0]["pages"][0]["buttons"][0]["keys"] = "Mouse99"
        with pytest.raises(BackupError, match="Botón inválido"):
            manager.import_backup(invalid)
        assert buttons.read_bytes() == original_buttons
        assert settings.read_bytes() == original_settings
    finally:
        cleanup(buttons, settings)


def test_backup_api_download_and_malformed_import() -> None:
    with TestClient(create_app(SOURCE_BUTTONS, force_test_mode=True)) as client:
        exported = client.get("/api/backup/export")
        malformed = client.post(
            "/api/backup/import",
            content="{not-json",
            headers={"Content-Type": "application/json"},
        )
    assert exported.status_code == 200
    assert "attachment" in exported.headers["content-disposition"]
    assert "password" not in exported.json()["configuration"]["settings"]["obs"]
    assert malformed.status_code == 422
    assert "JSON mal formado" in malformed.json()["detail"]
