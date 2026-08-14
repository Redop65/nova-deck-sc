import json
from pathlib import Path

from app.settings import load_app_settings, save_afk_range


def test_debug_and_log_level_are_loaded() -> None:
    path = Path(__file__).parent / "_settings_debug_test.json"
    path.write_text(
        json.dumps({"app": {
            "debug": True, "log_level": "warning", "default_theme": "amber-cockpit"
        }}),
        encoding="utf-8",
    )
    try:
        settings = load_app_settings(path)
        assert settings.debug is True
        assert settings.log_level == "WARNING"
        assert settings.default_theme == "amber-cockpit"
    finally:
        path.unlink(missing_ok=True)


def test_afk_range_is_loaded_and_saved(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps({"app": {}, "obs": {}, "afk": {
            "min_interval_seconds": 120, "max_interval_seconds": 300,
        }}),
        encoding="utf-8",
    )

    loaded = load_app_settings(path)
    assert loaded.afk_min_delay_seconds == 120
    assert loaded.afk_max_delay_seconds == 300
    save_afk_range(path, 60, 180)

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["afk"] == {"min_interval_seconds": 60, "max_interval_seconds": 180}


def test_legacy_afk_average_keeps_its_previous_variation(tmp_path: Path) -> None:
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"afk": {"interval_seconds": 480}}), encoding="utf-8")

    loaded = load_app_settings(path)
    assert loaded.afk_min_delay_seconds == 450
    assert loaded.afk_max_delay_seconds == 510


def test_invalid_settings_fall_back_safely() -> None:
    path = Path(__file__).parent / "_settings_invalid_test.json"
    path.write_text("not-json", encoding="utf-8")
    try:
        settings = load_app_settings(path)
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.default_theme == "dark-default"
    finally:
        path.unlink(missing_ok=True)
