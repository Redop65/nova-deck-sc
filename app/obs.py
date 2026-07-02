from __future__ import annotations

import json
from pathlib import Path
from threading import RLock
from typing import Any


class ObsError(RuntimeError):
    """Error de OBS seguro para mostrar al usuario."""


class ObsController:
    def __init__(self, settings_path: Path) -> None:
        self.settings_path = settings_path
        self._lock = RLock()

    def public_status(self) -> dict[str, Any]:
        try:
            obs = self._settings()["obs"]
        except ObsError as exc:
            return {"enabled": False, "configured": False, "error": str(exc)}
        return {
            "enabled": obs["enabled"],
            "host": obs["host"],
            "port": obs["port"],
            "configured": bool(obs["password"]),
        }

    def execute(self, action: str, **params: Any) -> dict[str, Any]:
        with self._lock:
            settings = self._settings()["obs"]
            if not settings["enabled"]:
                raise ObsError("La integración OBS está deshabilitada en config/settings.json.")
            try:
                import obsws_python as obs

                client = obs.ReqClient(
                    host=settings["host"], port=settings["port"],
                    password=settings["password"], timeout=settings["timeout_seconds"],
                )
                return {"action": action, **self._dispatch(client, action, params)}
            except ObsError:
                raise
            except Exception as exc:
                raise ObsError(
                    "OBS no respondió. Comprueba que esté abierto, WebSocket habilitado y los datos de settings.json sean correctos."
                ) from exc

    @staticmethod
    def _dispatch(client: Any, action: str, params: dict[str, Any]) -> dict[str, Any]:
        if action == "start_recording": client.start_record()
        elif action == "stop_recording": client.stop_record()
        elif action == "toggle_recording":
            status = client.get_record_status()
            client.stop_record() if status.output_active else client.start_record()
        elif action == "pause_recording": client.pause_record()
        elif action == "resume_recording": client.resume_record()
        elif action == "set_scene": client.set_current_program_scene(params["scene_name"])
        elif action == "toggle_mute": client.toggle_input_mute(params["input_name"])
        elif action == "set_source_visibility":
            scene = params["scene_name"]
            item = client.get_scene_item_id(scene, params["source_name"])
            client.set_scene_item_enabled(scene, item.scene_item_id, params["visible"])
        else: raise ObsError(f"Acción OBS no soportada: {action}")
        return {key: value for key, value in params.items() if value is not None}

    def _settings(self) -> dict[str, Any]:
        try:
            raw = json.loads(self.settings_path.read_text(encoding="utf-8"))
            obs = raw.get("obs", {})
            return {"obs": {
                "enabled": bool(obs.get("enabled", False)),
                "host": str(obs.get("host", "127.0.0.1")),
                "port": int(obs.get("port", 4455)),
                "password": str(obs.get("password", "")),
                "timeout_seconds": max(1, min(int(obs.get("timeout_seconds", 3)), 15)),
            }}
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise ObsError(f"Configuración OBS inválida en {self.settings_path.name}: {exc}") from exc
