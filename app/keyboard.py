from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from time import sleep


ALIASES = {
    "ALT": "alt",
    # AltGr is exposed by pynput as a separate key. Star Citizen commonly
    # labels the Spanish Ñ key as a semicolon, so both need explicit handling.
    "ALTGR": "alt_gr",
    "ALT_GR": "alt_gr",
    "ALT GR": "alt_gr",
    "ALTRIGHT": "alt_gr",
    "ALT_RIGHT": "alt_gr",
    "RIGHTALT": "alt_gr",
    "RIGHT ALT": "alt_gr",
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

# Star Citizen reads the physical US-semicolon position (scan code 0x27)
# instead of the localized character. On Spanish keyboards that position is Ñ.
PHYSICAL_KEY_ALIASES = {
    "Ñ": ("oem_semicolon", 0x27),
    "SEMICOLON": ("oem_semicolon", 0x27),
}


@dataclass(frozen=True)
class ParsedKey:
    name: str
    is_special: bool
    scan_code: int | None = None


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
        elif upper in PHYSICAL_KEY_ALIASES:
            name, scan_code = PHYSICAL_KEY_ALIASES[upper]
            parsed.append(ParsedKey(name, False, scan_code))
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
        with self._lock:
            self._send_locked(combo, hold_ms)

    def send_sequence(self, steps: list[dict]) -> None:
        with self._lock:
            for index, step in enumerate(steps):
                self._send_locked(step["keys"], int(step.get("hold_ms", 0)))
                if index < len(steps) - 1:
                    delay_ms = int(step.get("delay_after_ms", 0))
                    if delay_ms > 0:
                        sleep(delay_ms / 1000)

    @staticmethod
    def _send_locked(combo: str, hold_ms: int = 0) -> None:
        parsed = parse_combo(combo)
        try:
            from pynput.keyboard import Controller, Key, KeyCode
        except ImportError as exc:
            raise RuntimeError("pynput no está instalado.") from exc

        keys = []
        for item in parsed:
            if item.scan_code is not None:
                # KEYEVENTF_SCANCODE (0x0008) makes SendInput use the physical
                # key position. VK_OEM_1 is supplied only as descriptive data;
                # Windows ignores it while the scan-code flag is present.
                keys.append(KeyCode.from_vk(0xBA, _scan=item.scan_code, _flags=0x0008))
            elif item.is_special:
                try:
                    keys.append(getattr(Key, item.name))
                except AttributeError as exc:
                    raise ValueError(f"Tecla no disponible: {item.name}") from exc
            else:
                keys.append(item.name)

        keyboard = Controller()
        pressed = []
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
