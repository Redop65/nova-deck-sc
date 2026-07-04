from __future__ import annotations

import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.config import ButtonConfig

BACKUP_FORMAT = "nova-deck-backup"
BACKUP_VERSION = 1


class BackupError(RuntimeError):
    pass


class BackupManager:
    def __init__(self, buttons_path: Path, settings_path: Path, app_version: str) -> None:
        self.buttons_path = buttons_path
        self.settings_path = settings_path
        self.app_version = app_version
        self.backups_dir = buttons_path.parent / "backups"

    def export(self, include_secrets: bool = False) -> dict[str, Any]:
        buttons = ButtonConfig(self.buttons_path)
        try:
            button_data = buttons.export_data()
        except RuntimeError as exc:
            raise BackupError(f"No se puede exportar buttons.json: {exc}") from exc
        settings = self._read_settings()
        password = str(settings.get("obs", {}).get("password", ""))
        if not include_secrets:
            settings.setdefault("obs", {}).pop("password", None)
        return {
            "format": BACKUP_FORMAT,
            "version": BACKUP_VERSION,
            "created_at": datetime.now(UTC).isoformat(),
            "app_version": self.app_version,
            "configuration": {"buttons": button_data, "settings": settings},
            "icon_references": self._icon_references(button_data),
            "secrets": {
                "obs_password_included": bool(include_secrets and password),
            },
        }

    def import_backup(self, payload: dict[str, Any]) -> dict[str, Any]:
        buttons, imported_settings, password_included, legacy = self._unpack(payload)
        self._validate_buttons(buttons)
        if imported_settings is not None:
            self._validate_settings(imported_settings)

        current_settings = self._read_settings()
        settings_to_write = None
        if imported_settings is not None:
            settings_to_write = deepcopy(imported_settings)
            if not password_included:
                existing = str(current_settings.get("obs", {}).get("password", ""))
                settings_to_write.setdefault("obs", {})["password"] = existing

        local_backup = self._save_local_backup()
        old_buttons = self.buttons_path.read_bytes()
        old_settings = self.settings_path.read_bytes() if self.settings_path.exists() else None
        try:
            self._atomic_json_write(self.buttons_path, buttons)
            if settings_to_write is not None:
                self._atomic_json_write(self.settings_path, settings_to_write)
        except OSError as exc:
            self.buttons_path.write_bytes(old_buttons)
            if old_settings is not None:
                self.settings_path.write_bytes(old_settings)
            raise BackupError(f"No se pudo aplicar el backup; se restauró la configuración anterior: {exc}") from exc

        return {
            "local_backup": local_backup.name,
            "legacy_import": legacy,
            "obs_password_restored": password_included,
            "icon_references": self._icon_references(buttons),
        }

    def create_local_backup(self) -> str:
        """Create a full PC-local safety copy and return only its filename."""
        return self._save_local_backup().name

    def _unpack(
        self, payload: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any] | None, bool, bool]:
        if not isinstance(payload, dict):
            raise BackupError("La raíz del archivo debe ser un objeto JSON.")
        if payload.get("format") == BACKUP_FORMAT:
            if payload.get("version") != BACKUP_VERSION:
                raise BackupError(
                    f"Versión de backup no soportada: {payload.get('version')}. Se esperaba {BACKUP_VERSION}."
                )
            configuration = payload.get("configuration")
            if not isinstance(configuration, dict) or not isinstance(configuration.get("buttons"), dict):
                raise BackupError("El backup necesita configuration.buttons.")
            settings = configuration.get("settings")
            if settings is not None and not isinstance(settings, dict):
                raise BackupError("configuration.settings debe ser un objeto.")
            secrets = payload.get("secrets", {})
            password_included = bool(
                isinstance(secrets, dict) and secrets.get("obs_password_included")
            )
            return configuration["buttons"], settings, password_included, False
        if "profiles" in payload or "pages" in payload:
            return payload, None, False, True
        raise BackupError(
            "El archivo no es un backup de NOVA DECK ni una configuración buttons.json compatible."
        )

    def _validate_buttons(self, data: dict[str, Any]) -> None:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        validation_path = self.backups_dir / f".validate-{uuid4().hex}.json"
        try:
            validation_path.write_text(
                json.dumps(data, ensure_ascii=False), encoding="utf-8"
            )
            candidate = ButtonConfig(validation_path)
            candidate.load()
            issues = candidate.issues()
            if issues:
                first = issues[0]
                raise BackupError(
                    f"Botón inválido en {first['path']}: {first['message']}"
                )
        except BackupError:
            raise
        except (OSError, RuntimeError, TypeError, ValueError) as exc:
            raise BackupError(f"Configuración de botones inválida: {exc}") from exc
        finally:
            validation_path.unlink(missing_ok=True)

    @staticmethod
    def _validate_settings(settings: dict[str, Any]) -> None:
        app = settings.get("app", {})
        obs = settings.get("obs", {})
        if not isinstance(app, dict) or not isinstance(obs, dict):
            raise BackupError("settings.app y settings.obs deben ser objetos.")
        if "debug" in app and not isinstance(app["debug"], bool):
            raise BackupError("settings.app.debug debe ser true o false.")
        if "log_level" in app and str(app["log_level"]).upper() not in {
            "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
        }:
            raise BackupError("settings.app.log_level no es válido.")
        if "enabled" in obs and not isinstance(obs["enabled"], bool):
            raise BackupError("settings.obs.enabled debe ser true o false.")
        try:
            port = int(obs.get("port", 4455))
            timeout = int(obs.get("timeout_seconds", 3))
        except (TypeError, ValueError) as exc:
            raise BackupError("Puerto o timeout de OBS inválido.") from exc
        if not 1 <= port <= 65535:
            raise BackupError("settings.obs.port debe estar entre 1 y 65535.")
        if not 1 <= timeout <= 15:
            raise BackupError("settings.obs.timeout_seconds debe estar entre 1 y 15.")
        for field in ("host", "password"):
            if field in obs and not isinstance(obs[field], str):
                raise BackupError(f"settings.obs.{field} debe ser texto.")

    def _read_settings(self) -> dict[str, Any]:
        if not self.settings_path.exists():
            return {"app": {"debug": False, "log_level": "INFO"}, "obs": {}}
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("la raíz debe ser un objeto")
            self._validate_settings(data)
            return deepcopy(data)
        except (OSError, json.JSONDecodeError, ValueError, BackupError) as exc:
            raise BackupError(f"No se puede leer settings.json: {exc}") from exc

    def _save_local_backup(self) -> Path:
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        destination = self.backups_dir / f"before-import-{stamp}.json"
        self._atomic_json_write(destination, self.export(include_secrets=True))
        return destination

    @staticmethod
    def _atomic_json_write(path: Path, data: dict[str, Any]) -> None:
        temporary = path.with_suffix(f"{path.suffix}.tmp")
        try:
            temporary.write_text(
                json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _icon_references(buttons: dict[str, Any]) -> list[str]:
        references: set[str] = set()
        for profile in buttons.get("profiles", []):
            if not isinstance(profile, dict):
                continue
            for page in profile.get("pages", []):
                if not isinstance(page, dict):
                    continue
                for button in page.get("buttons", []):
                    if isinstance(button, dict):
                        icon = button.get("icon")
                        if isinstance(icon, str) and icon.startswith("assets/icons/"):
                            references.add(icon)
        return sorted(references)
