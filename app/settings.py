from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

THEMES = {
    "dark-default", "space-blue", "amber-cockpit", "red-alert", "industrial-mining"
}
DEFAULT_AFK_INTERVAL_SECONDS = 240
MIN_AFK_INTERVAL_SECONDS = 60
MAX_AFK_INTERVAL_SECONDS = 1800

@dataclass(frozen=True)
class AppSettings:
    debug: bool = False
    log_level: str = "INFO"
    default_theme: str = "dark-default"
    afk_interval_seconds: int = DEFAULT_AFK_INTERVAL_SECONDS


def load_app_settings(path: Path) -> AppSettings:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        app = raw.get("app", {})
        level = str(app.get("log_level", "INFO")).upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            level = "INFO"
        theme = str(app.get("default_theme", "dark-default"))
        if theme not in THEMES:
            theme = "dark-default"
        afk = raw.get("afk", {})
        interval = afk.get("interval_seconds", DEFAULT_AFK_INTERVAL_SECONDS) if isinstance(afk, dict) else DEFAULT_AFK_INTERVAL_SECONDS
        if isinstance(interval, bool) or not isinstance(interval, int) or not MIN_AFK_INTERVAL_SECONDS <= interval <= MAX_AFK_INTERVAL_SECONDS:
            interval = DEFAULT_AFK_INTERVAL_SECONDS
        return AppSettings(
            debug=bool(app.get("debug", False)), log_level=level, default_theme=theme,
            afk_interval_seconds=interval,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return AppSettings()


def save_afk_interval(path: Path, interval_seconds: int) -> None:
    """Persist the AFK average interval without exposing or altering OBS data."""
    if isinstance(interval_seconds, bool) or not MIN_AFK_INTERVAL_SECONDS <= interval_seconds <= MAX_AFK_INTERVAL_SECONDS:
        raise ValueError(
            f"El intervalo AFK debe estar entre {MIN_AFK_INTERVAL_SECONDS} y {MAX_AFK_INTERVAL_SECONDS} segundos."
        )
    try:
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se puede leer settings.json: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("settings.json debe contener un objeto JSON.")
    afk = raw.setdefault("afk", {})
    if not isinstance(afk, dict):
        raise ValueError("settings.afk debe ser un objeto.")
    afk["interval_seconds"] = interval_seconds
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"No se puede guardar settings.json: {exc}") from exc
