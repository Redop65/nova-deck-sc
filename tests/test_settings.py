import json
from pathlib import Path

from app.settings import load_app_settings


def test_debug_and_log_level_are_loaded() -> None:
    path = Path(__file__).parent / "_settings_debug_test.json"
    path.write_text(
        json.dumps({"app": {"debug": True, "log_level": "warning"}}),
        encoding="utf-8",
    )
    try:
        settings = load_app_settings(path)
        assert settings.debug is True
        assert settings.log_level == "WARNING"
    finally:
        path.unlink(missing_ok=True)


def test_invalid_settings_fall_back_safely() -> None:
    path = Path(__file__).parent / "_settings_invalid_test.json"
    path.write_text("not-json", encoding="utf-8")
    try:
        settings = load_app_settings(path)
        assert settings.debug is False
        assert settings.log_level == "INFO"
    finally:
        path.unlink(missing_ok=True)
