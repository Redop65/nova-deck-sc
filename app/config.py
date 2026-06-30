from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any


class ButtonConfig:
    """Loads and validates the editable button catalogue."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()
        self._mtime_ns = -1
        self._data: dict[str, Any] = {}
        self._buttons: dict[str, dict[str, Any]] = {}

    def load(self) -> dict[str, Any]:
        with self._lock:
            try:
                mtime_ns = self.path.stat().st_mtime_ns
            except OSError as exc:
                raise RuntimeError(f"No se pudo leer {self.path}: {exc}") from exc
            if mtime_ns == self._mtime_ns:
                return self._data

            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise RuntimeError(f"Configuración inválida: {exc}") from exc

            pages = raw.get("pages")
            if not isinstance(pages, list) or not pages:
                raise RuntimeError("La configuración debe contener una lista 'pages'.")

            buttons: dict[str, dict[str, Any]] = {}
            for page in pages:
                if not isinstance(page, dict) or not page.get("id") or not page.get("name"):
                    raise RuntimeError("Cada página necesita 'id' y 'name'.")
                if not isinstance(page.get("buttons"), list):
                    raise RuntimeError(f"La página {page['id']} necesita una lista 'buttons'.")
                for button in page["buttons"]:
                    required = ("id", "name", "keys")
                    if not isinstance(button, dict) or not all(button.get(k) for k in required):
                        raise RuntimeError(f"Botón inválido en la página {page['id']}.")
                    if button["id"] in buttons:
                        raise RuntimeError(f"ID de botón duplicado: {button['id']}")
                    buttons[button["id"]] = button

            self._data = raw
            self._buttons = buttons
            self._mtime_ns = mtime_ns
            return self._data

    def get_button(self, button_id: str) -> dict[str, Any] | None:
        self.load()
        return self._buttons.get(button_id)

    def create_button(self, page_id: str, button: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            data = deepcopy(self.load())
            if button["id"] in self._buttons:
                raise ValueError(f"Ya existe un botón con el ID '{button['id']}'.")
            page = self._find_page(data, page_id)
            page["buttons"].append(button)
            self._write(data)
            return button

    def update_button(
        self, button_id: str, page_id: str, button: dict[str, Any]
    ) -> dict[str, Any]:
        with self._lock:
            data = deepcopy(self.load())
            source_page, position = self._find_button(data, button_id)
            if source_page is None or position is None:
                raise KeyError(button_id)
            if button["id"] != button_id and button["id"] in self._buttons:
                raise ValueError(f"Ya existe un botón con el ID '{button['id']}'.")

            target_page = self._find_page(data, page_id)
            if source_page is target_page:
                source_page["buttons"][position] = button
            else:
                source_page["buttons"].pop(position)
                target_page["buttons"].append(button)
            self._write(data)
            return button

    def delete_button(self, button_id: str) -> dict[str, Any]:
        with self._lock:
            data = deepcopy(self.load())
            page, position = self._find_button(data, button_id)
            if page is None or position is None:
                raise KeyError(button_id)
            removed = page["buttons"].pop(position)
            self._write(data)
            return removed

    @staticmethod
    def _find_page(data: dict[str, Any], page_id: str) -> dict[str, Any]:
        for page in data["pages"]:
            if page["id"] == page_id:
                return page
        raise ValueError(f"La página '{page_id}' no existe.")

    @staticmethod
    def _find_button(
        data: dict[str, Any], button_id: str
    ) -> tuple[dict[str, Any] | None, int | None]:
        for page in data["pages"]:
            for position, button in enumerate(page["buttons"]):
                if button["id"] == button_id:
                    return page, position
        return None, None

    def _write(self, data: dict[str, Any]) -> None:
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        try:
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            temporary.replace(self.path)
        except OSError as exc:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise RuntimeError(f"No se pudo guardar {self.path}: {exc}") from exc
        self._mtime_ns = -1
        self.load()
