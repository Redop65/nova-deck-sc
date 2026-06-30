from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import sleep


ALIASES = {
    "ALT": "alt",
    "CTRL": "ctrl",
    "CONTROL": "ctrl",
    "SHIFT": "shift",
    "WIN": "cmd",
    "WINDOWS": "cmd",
    "ENTER": "enter",
    "RETURN": "enter",
    "ESC": "esc",
    "ESCAPE": "esc",
    "SPACE": "space",
    "TAB": "tab",
    "BACKSPACE": "backspace",
    "DELETE": "delete",
    "DEL": "delete",
    "INSERT": "insert",
    "HOME": "home",
    "END": "end",
    "PAGEUP": "page_up",
    "PAGEDOWN": "page_down",
    "UP": "up",
    "DOWN": "down",
    "LEFT": "left",
    "RIGHT": "right",
}


@dataclass(frozen=True)
class ParsedKey:
    name: str
    is_special: bool


def parse_combo(combo: str) -> list[ParsedKey]:
    parts = [part.strip() for part in combo.split("+")]
    if not parts or any(not part for part in parts):
        raise ValueError("La combinación contiene una tecla vacía.")
    if len(parts) > 5:
        raise ValueError("La combinación admite un máximo de 5 teclas.")

    parsed: list[ParsedKey] = []
    for raw in parts:
        upper = raw.upper()
        if upper in ALIASES:
            parsed.append(ParsedKey(ALIASES[upper], True))
        elif upper.startswith("F") and upper[1:].isdigit() and 1 <= int(upper[1:]) <= 24:
            parsed.append(ParsedKey(upper.lower(), True))
        elif len(raw) == 1:
            parsed.append(ParsedKey(raw.lower(), False))
        else:
            raise ValueError(f"Tecla no soportada: {raw}")
    return parsed


class KeyboardSender:
    def __init__(self) -> None:
        self._lock = Lock()

    def send(self, combo: str, hold_ms: int = 0) -> None:
        parsed = parse_combo(combo)
        try:
            from pynput.keyboard import Controller, Key
        except ImportError as exc:
            raise RuntimeError("pynput no está instalado.") from exc

        keys = []
        for item in parsed:
            if item.is_special:
                try:
                    keys.append(getattr(Key, item.name))
                except AttributeError as exc:
                    raise ValueError(f"Tecla no disponible: {item.name}") from exc
            else:
                keys.append(item.name)

        keyboard = Controller()
        pressed = []
        with self._lock:
            try:
                for index, key in enumerate(keys):
                    keyboard.press(key)
                    pressed.append(key)
                    if index < len(keys) - 1:
                        sleep(0.025)
                sleep(max(0.025, hold_ms / 1000))
            finally:
                for key in reversed(pressed):
                    keyboard.release(key)
