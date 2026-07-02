from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    debug: bool = False
    log_level: str = "INFO"


def load_app_settings(path: Path) -> AppSettings:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        app = raw.get("app", {})
        level = str(app.get("log_level", "INFO")).upper()
        if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            level = "INFO"
        return AppSettings(debug=bool(app.get("debug", False)), log_level=level)
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return AppSettings()
