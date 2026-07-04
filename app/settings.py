from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

THEMES = {
    "dark-default", "space-blue", "amber-cockpit", "red-alert", "industrial-mining"
}

@dataclass(frozen=True)
class AppSettings:
    debug: bool = False
    log_level: str = "INFO"
    default_theme: str = "dark-default"


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
        return AppSettings(
            debug=bool(app.get("debug", False)), log_level=level, default_theme=theme
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return AppSettings()
