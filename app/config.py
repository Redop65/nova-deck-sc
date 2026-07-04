from __future__ import annotations

import json
import re
import unicodedata
from copy import deepcopy
from pathlib import Path
from threading import RLock
from typing import Any

from pydantic import ValidationError

from app.keyboard import parse_combo
from app.models import ButtonInput


class ButtonConfig:
    """Loads and validates the editable button catalogue."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()
        self._mtime_ns = -1
        self._data: dict[str, Any] = {}
        self._source_data: dict[str, Any] = {}
        self._buttons: dict[str, dict[str, dict[str, Any]]] = {}
        self._issues: list[dict[str, str]] = []

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

            source = self._normalize(raw)
            normalized = deepcopy(source)
            profiles = normalized["profiles"]
            profile_ids: set[str] = set()
            buttons: dict[str, dict[str, dict[str, Any]]] = {}
            issues: list[dict[str, str]] = []
            for profile_index, profile in enumerate(profiles):
                if not isinstance(profile, dict) or not profile.get("id") or not profile.get("name"):
                    raise RuntimeError(f"profiles[{profile_index}]: cada perfil necesita 'id' y 'name'.")
                if profile["id"] in profile_ids:
                    raise RuntimeError(f"profiles[{profile_index}]: ID de perfil duplicado '{profile['id']}'.")
                profile_ids.add(profile["id"])
                pages = profile.get("pages")
                if not isinstance(pages, list) or not pages:
                    raise RuntimeError(f"El perfil {profile['id']} necesita una lista 'pages'.")
                profile_buttons: dict[str, dict[str, Any]] = {}
                source_profile = source["profiles"][profile_index]
                page_ids: set[str] = set()
                for page_index, page in enumerate(pages):
                    self._validate_page(
                        page, source_profile["pages"][page_index], profile["id"],
                        profile_buttons, page_ids, issues,
                    )
                buttons[profile["id"]] = profile_buttons

            self._data = normalized
            self._source_data = source
            self._buttons = buttons
            self._issues = issues
            self._mtime_ns = mtime_ns
            return self._data

    @classmethod
    def _normalize(cls, raw: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(raw, dict):
            raise RuntimeError("La raíz de la configuración debe ser un objeto JSON.")

        if "profiles" not in raw:
            pages = raw.get("pages")
            if not isinstance(pages, list) or not pages:
                raise RuntimeError("La configuración debe contener 'profiles' o una lista legacy 'pages'.")
            return {
                **{key: value for key, value in raw.items() if key != "pages"},
                "profiles": [
                    {"id": "default", "name": "Default", "pages": pages}
                ],
            }

        profiles = raw["profiles"]
        if isinstance(profiles, dict):
            converted = []
            for name, value in profiles.items():
                if not isinstance(value, dict):
                    raise RuntimeError(f"El perfil {name} debe ser un objeto.")
                pages = value.get("pages", [])
                if isinstance(pages, dict):
                    pages = [
                        {"id": cls._slug(page_name), "name": page_name, "buttons": page_buttons}
                        for page_name, page_buttons in pages.items()
                    ]
                converted.append(
                    {
                        **value,
                        "id": value.get("id", cls._slug(name)),
                        "name": value.get("name", name),
                        "pages": pages,
                    }
                )
            profiles = converted
        if not isinstance(profiles, list) or not profiles:
            raise RuntimeError("'profiles' debe ser una lista u objeto con al menos un perfil.")
        return {**raw, "profiles": profiles}

    @staticmethod
    def _validate_page(
        page: dict[str, Any], source_page: dict[str, Any], profile_id: str,
        buttons: dict[str, dict[str, Any]], page_ids: set[str],
        issues: list[dict[str, str]],
    ) -> None:
        if not isinstance(page, dict) or not page.get("id") or not page.get("name"):
            raise RuntimeError(f"Perfil '{profile_id}': cada página necesita 'id' y 'name'.")
        if page["id"] in page_ids:
            raise RuntimeError(f"Perfil '{profile_id}': ID de página duplicado '{page['id']}'.")
        page_ids.add(page["id"])
        if not isinstance(page.get("buttons"), list):
            raise RuntimeError(f"La página {page['id']} necesita una lista 'buttons'.")
        for index, button in enumerate(page["buttons"]):
            path = f"profiles.{profile_id}.pages.{page['id']}.buttons[{index}]"
            error = None
            try:
                action = ButtonInput.model_validate(button)
                if not action.disabled and action.action_type == "hotkey" and action.keys:
                    parse_combo(action.keys)
                elif not action.disabled and action.action_type == "macro" and action.macro:
                    for step in action.macro:
                        parse_combo(step.keys)
                if action.id in buttons:
                    raise ValueError(f"ID de botón duplicado '{action.id}'.")
            except ValidationError as exc:
                item = exc.errors(include_url=False)[0]
                location = ".".join(str(part) for part in item.get("loc", ()))
                error = f"{location + ': ' if location else ''}{item['msg']}"
            except ValueError as exc:
                error = str(exc)

            if error:
                issues.append({"path": path, "message": error})
                original = source_page["buttons"][index]
                fallback_id = original.get("id") if isinstance(original, dict) else None
                fallback_name = original.get("name") if isinstance(original, dict) else None
                page["buttons"][index] = {
                    **(button if isinstance(button, dict) else {}),
                    "id": fallback_id or f"invalid-{profile_id}-{page['id']}-{index + 1}",
                    "name": fallback_name or "Botón con error",
                    "disabled": True,
                    "_config_error": f"{path}: {error}",
                }
                continue
            buttons[action.id] = button

    @staticmethod
    def _slug(value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
        return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-") or "profile"

    def list_profiles(self) -> list[dict[str, str]]:
        data = self.load()
        return [{"id": profile["id"], "name": profile["name"]} for profile in data["profiles"]]

    def issues(self) -> list[dict[str, str]]:
        self.load()
        return deepcopy(self._issues)

    def export_data(self) -> dict[str, Any]:
        """Return the original editable data without runtime warning markers."""
        self.load()
        return deepcopy(self._source_data)

    def invalidate(self) -> None:
        with self._lock:
            self._mtime_ns = -1

    def get_profile(self, profile_id: str) -> dict[str, Any] | None:
        data = self.load()
        return next((profile for profile in data["profiles"] if profile["id"] == profile_id), None)

    def get_button(self, profile_id: str, button_id: str) -> dict[str, Any] | None:
        self.load()
        return self._buttons.get(profile_id, {}).get(button_id)

    def create_button(
        self, profile_id: str, page_id: str, button: dict[str, Any]
    ) -> dict[str, Any]:
        with self._lock:
            self.load()
            data = deepcopy(self._source_data)
            if button["id"] in self._buttons.get(profile_id, {}):
                raise ValueError(f"Ya existe un botón con el ID '{button['id']}'.")
            profile = self._find_profile(data, profile_id)
            page = self._find_page(profile, page_id)
            page["buttons"].append(button)
            self._write(data)
            return button

    def update_button(
        self, profile_id: str, button_id: str, page_id: str, button: dict[str, Any],
        target_profile_id: str | None = None, position: int | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self.load()
            data = deepcopy(self._source_data)
            source_profile = self._find_profile(data, profile_id)
            source_page, source_position = self._find_button(source_profile, button_id)
            if source_page is None or source_position is None:
                raise KeyError(button_id)
            destination_id = target_profile_id or profile_id
            destination_profile = self._find_profile(data, destination_id)
            existing = self._buttons.get(destination_id, {}).get(button["id"])
            same_button = destination_id == profile_id and button["id"] == button_id
            if existing is not None and not same_button:
                raise ValueError(f"Ya existe un botón con el ID '{button['id']}'.")

            source_page["buttons"].pop(source_position)
            target_page = self._find_page(destination_profile, page_id)
            target_position = len(target_page["buttons"]) if position is None else position
            target_position = max(0, min(target_position, len(target_page["buttons"])))
            target_page["buttons"].insert(target_position, button)
            self._write(data)
            return button

    def delete_button(self, profile_id: str, button_id: str) -> dict[str, Any]:
        with self._lock:
            self.load()
            data = deepcopy(self._source_data)
            profile = self._find_profile(data, profile_id)
            page, position = self._find_button(profile, button_id)
            if page is None or position is None:
                raise KeyError(button_id)
            removed = page["buttons"].pop(position)
            self._write(data)
            return removed

    @staticmethod
    def _find_profile(data: dict[str, Any], profile_id: str) -> dict[str, Any]:
        for profile in data["profiles"]:
            if profile["id"] == profile_id:
                return profile
        raise ValueError(f"El perfil '{profile_id}' no existe.")

    @staticmethod
    def _find_page(profile: dict[str, Any], page_id: str) -> dict[str, Any]:
        for page in profile["pages"]:
            if page["id"] == page_id:
                return page
        raise ValueError(f"La página '{page_id}' no existe.")

    @staticmethod
    def _find_button(
        profile: dict[str, Any], button_id: str
    ) -> tuple[dict[str, Any] | None, int | None]:
        for page in profile["pages"]:
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
