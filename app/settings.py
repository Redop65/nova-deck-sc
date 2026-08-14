from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

THEMES = {
    "dark-default", "space-blue", "amber-cockpit", "red-alert", "industrial-mining"
}
MIN_AFK_INTERVAL_SECONDS = 60
MAX_AFK_INTERVAL_SECONDS = 1800
DEFAULT_AFK_MIN_DELAY_SECONDS = 210
DEFAULT_AFK_MAX_DELAY_SECONDS = 270

@dataclass(frozen=True)
class AppSettings:
    debug: bool = False
    log_level: str = "INFO"
    default_theme: str = "dark-default"
    afk_min_delay_seconds: int = DEFAULT_AFK_MIN_DELAY_SECONDS
    afk_max_delay_seconds: int = DEFAULT_AFK_MAX_DELAY_SECONDS

    @property
    def afk_interval_seconds(self) -> int:
        """Promedio legado del rango AFK, para consumidores antiguos."""
        return round((self.afk_min_delay_seconds + self.afk_max_delay_seconds) / 2)


def _valid_afk_seconds(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, int)
        and MIN_AFK_INTERVAL_SECONDS <= value <= MAX_AFK_INTERVAL_SECONDS
    )


def _afk_range(afk: object) -> tuple[int, int]:
    """Load the explicit range, falling back to the previous average format."""
    if not isinstance(afk, dict):
        return DEFAULT_AFK_MIN_DELAY_SECONDS, DEFAULT_AFK_MAX_DELAY_SECONDS

    minimum = afk.get("min_interval_seconds")
    maximum = afk.get("max_interval_seconds")
    if _valid_afk_seconds(minimum) and _valid_afk_seconds(maximum) and minimum <= maximum:
        return minimum, maximum

    # v1.2.6 stored only an average and applied a 30 second variation at runtime.
    # Preserve that behavior for existing local settings files.
    interval = afk.get("interval_seconds")
    if _valid_afk_seconds(interval):
        return (
            max(MIN_AFK_INTERVAL_SECONDS, interval - 30),
            min(MAX_AFK_INTERVAL_SECONDS, interval + 30),
        )
    return DEFAULT_AFK_MIN_DELAY_SECONDS, DEFAULT_AFK_MAX_DELAY_SECONDS


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
        afk_min_delay, afk_max_delay = _afk_range(raw.get("afk", {}))
        return AppSettings(
            debug=bool(app.get("debug", False)), log_level=level, default_theme=theme,
            afk_min_delay_seconds=afk_min_delay,
            afk_max_delay_seconds=afk_max_delay,
        )
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return AppSettings()


def save_afk_range(path: Path, min_interval_seconds: int, max_interval_seconds: int) -> None:
    """Persist the explicit AFK random range without altering OBS data."""
    if not _valid_afk_seconds(min_interval_seconds) or not _valid_afk_seconds(max_interval_seconds):
        raise ValueError(
            f"El rango AFK debe estar entre {MIN_AFK_INTERVAL_SECONDS} y {MAX_AFK_INTERVAL_SECONDS} segundos."
        )
    if min_interval_seconds > max_interval_seconds:
        raise ValueError("El mínimo del rango AFK no puede ser mayor que el máximo.")
    try:
        raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"No se puede leer settings.json: {exc}") from exc
    if not isinstance(raw, dict):
        raise ValueError("settings.json debe contener un objeto JSON.")
    afk = raw.setdefault("afk", {})
    if not isinstance(afk, dict):
        raise ValueError("settings.afk debe ser un objeto.")
    afk["min_interval_seconds"] = min_interval_seconds
    afk["max_interval_seconds"] = max_interval_seconds
    # Remove the legacy average so a subsequent edit remains unambiguous.
    afk.pop("interval_seconds", None)
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise ValueError(f"No se puede guardar settings.json: {exc}") from exc
