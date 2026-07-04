from __future__ import annotations

import argparse
import json
import logging
import socket
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.backup import BackupError, BackupManager
from app.config import ButtonConfig
from app.keyboard import KeyboardSender, parse_combo
from app.models import ButtonInput, ButtonMutation, CommandRequest
from app.obs import ObsController, ObsError
from app.settings import load_app_settings

ROOT = Path(__file__).resolve().parents[1]
APP_VERSION = "1.1.0"
LOGGER = logging.getLogger("nova_deck")


def button_payload(payload: ButtonMutation) -> dict:
    button = payload.button.model_dump(exclude_none=True, by_alias=True)
    if not button["disabled"]:
        try:
            if button["type"] == "macro":
                for step in button["macro"]:
                    parse_combo(step["keys"])
            elif button["type"] == "hotkey":
                parse_combo(button["keys"])
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
    return button


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("192.0.2.1", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def create_app(
    config_path: Path | None = None,
    force_test_mode: bool = False,
    debug_override: bool | None = None,
) -> FastAPI:
    settings_path = ROOT / "config" / "settings.json"
    runtime = load_app_settings(settings_path)
    debug = runtime.debug if debug_override is None else debug_override
    log_level = "DEBUG" if debug else runtime.log_level
    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    LOGGER.setLevel(getattr(logging, log_level))
    # Debug aumenta los logs, pero no expone tracebacks HTTP a la red local.
    app = FastAPI(title="Star Citizen Deck", version=APP_VERSION, debug=False)
    buttons_path = config_path or ROOT / "config" / "buttons.json"
    app.state.config = ButtonConfig(buttons_path)
    app.state.backup = BackupManager(buttons_path, settings_path, APP_VERSION)
    app.state.keyboard = KeyboardSender()
    app.state.obs = ObsController(settings_path)
    app.state.force_test_mode = force_test_mode
    app.state.debug_mode = debug

    @app.middleware("http")
    async def request_log(request: Request, call_next):
        try:
            response = await call_next(request)
        except Exception:
            LOGGER.exception("Fallo no controlado en %s %s", request.method, request.url.path)
            raise
        LOGGER.debug("%s %s -> %s", request.method, request.url.path, response.status_code)
        if request.url.path in {
            "/assets/app.js", "/assets/styles.css", "/assets/themes.css",
            "/manifest.webmanifest"
        }:
            response.headers["Cache-Control"] = "no-cache, must-revalidate"
        return response

    @app.get("/api/status")
    def status(request: Request) -> dict:
        try:
            request.app.state.config.load()
            config_status = {
                "ok": True,
                "warnings": request.app.state.config.issues(),
            }
        except RuntimeError as exc:
            config_status = {"ok": False, "error": str(exc), "warnings": []}
        return {
            "ok": True,
            "force_test_mode": request.app.state.force_test_mode,
            "debug": request.app.state.debug_mode,
            "default_theme": runtime.default_theme,
            "local_ip": local_ip(),
            "obs": request.app.state.obs.public_status(),
            "configuration": config_status,
        }

    @app.get("/api/buttons")
    def buttons(request: Request) -> dict:
        try:
            data = request.app.state.config.load()
            profile = request.app.state.config.get_profile("default") or data["profiles"][0]
            return {
                "title": data.get("title", "NOVA DECK // SC"),
                "pages": profile["pages"],
                "warnings": request.app.state.config.issues(),
            }
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/profiles")
    def profiles(request: Request) -> dict:
        try:
            data = request.app.state.config.load()
            return {
                "title": data.get("title", "NOVA DECK // SC"),
                "profiles": request.app.state.config.list_profiles(),
                "warnings": request.app.state.config.issues(),
            }
        except RuntimeError as exc:
            LOGGER.error("No se pudo cargar la configuración: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.get("/api/profiles/{profile_id}")
    def profile(profile_id: str, request: Request) -> dict:
        try:
            selected = request.app.state.config.get_profile(profile_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if selected is None:
            raise HTTPException(status_code=404, detail="Perfil no encontrado.")
        warnings = [
            issue for issue in request.app.state.config.issues()
            if issue["path"].startswith(f"profiles.{profile_id}.")
        ]
        return {"profile": selected, "warnings": warnings}

    @app.post("/api/buttons", status_code=201)
    def create_button(payload: ButtonMutation, request: Request) -> dict:
        button = button_payload(payload)
        try:
            safety_backup = request.app.state.backup.create_local_backup()
            created = request.app.state.config.create_button(
                payload.profile_id, payload.page_id, button
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"ok": True, "button": created, "local_backup": safety_backup}

    @app.put("/api/buttons/{button_id}")
    def update_button(button_id: str, payload: ButtonMutation, request: Request) -> dict:
        button = button_payload(payload)
        try:
            safety_backup = request.app.state.backup.create_local_backup()
            updated = request.app.state.config.update_button(
                payload.profile_id, button_id, payload.page_id, button,
                target_profile_id=payload.target_profile_id,
                position=payload.position,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Botón no encontrado.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"ok": True, "button": updated, "local_backup": safety_backup}

    @app.delete("/api/buttons/{button_id}")
    def delete_button(button_id: str, request: Request, profile_id: str = "default") -> dict:
        try:
            safety_backup = request.app.state.backup.create_local_backup()
            removed = request.app.state.config.delete_button(profile_id, button_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Botón no encontrado.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"ok": True, "button": removed, "local_backup": safety_backup}

    @app.get("/api/backup/export")
    def export_backup(request: Request) -> Response:
        try:
            backup = request.app.state.backup.export(include_secrets=False)
        except BackupError as exc:
            LOGGER.error("No se pudo exportar el backup: %s", exc)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        filename = f"nova-deck-backup-{datetime.now():%Y%m%d-%H%M%S}.json"
        LOGGER.info("Backup seguro exportado sin contraseña OBS")
        return Response(
            content=json.dumps(backup, ensure_ascii=False, indent=2) + "\n",
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
            },
        )

    @app.post("/api/backup/import")
    async def import_backup(request: Request) -> dict:
        body = await request.body()
        if len(body) > 2 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="El backup supera el límite de 2 MB.")
        try:
            payload = json.loads(body.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise HTTPException(status_code=422, detail=f"JSON mal formado: {exc}") from exc
        try:
            result = request.app.state.backup.import_backup(payload)
            request.app.state.config.invalidate()
            request.app.state.config.load()
        except BackupError as exc:
            LOGGER.warning("Importación rechazada: %s", exc)
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except RuntimeError as exc:
            LOGGER.exception("El backup fue escrito pero no se pudo recargar")
            raise HTTPException(status_code=500, detail=f"Backup importado, pero falló la recarga: {exc}") from exc
        LOGGER.info("Backup importado; respaldo local: %s", result["local_backup"])
        return {"ok": True, **result}

    @app.post("/api/commands")
    def command(payload: CommandRequest, request: Request) -> dict:
        try:
            button = request.app.state.config.get_button(payload.profile_id, payload.button_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if button is None:
            raise HTTPException(status_code=404, detail="Botón no encontrado.")
        if button.get("disabled", False):
            raise HTTPException(status_code=409, detail="Este botón está deshabilitado en la configuración.")

        try:
            action = ButtonInput.model_validate(button)
            if not action.disabled:
                if action.action_type == "macro":
                    for step in action.macro:
                        parse_combo(step.keys)
                elif action.action_type == "hotkey" and action.keys:
                    parse_combo(action.keys)
        except (ValidationError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=f"Acción inválida: {exc}") from exc

        is_test = payload.test_mode or request.app.state.force_test_mode
        if not is_test:
            try:
                if action.action_type == "macro":
                    request.app.state.keyboard.send_sequence(
                        [step.model_dump() for step in action.macro]
                    )
                elif action.action_type == "hotkey":
                    request.app.state.keyboard.send(action.keys, hold_ms=action.hold_ms)
                else:
                    request.app.state.obs.execute(
                        action.obs_action,
                        scene_name=action.scene_name,
                        input_name=action.input_name,
                        source_name=action.source_name,
                        visible=action.visible,
                    )
            except (ValueError, RuntimeError, OSError, ObsError) as exc:
                LOGGER.warning(
                    "Falló acción %s/%s (%s): %s",
                    payload.profile_id, payload.button_id, action.action_type, exc,
                )
                raise HTTPException(
                    status_code=503 if action.action_type == "obs" else 422,
                    detail=f"No se pudo ejecutar la acción: {exc}",
                ) from exc

        LOGGER.info(
            "Acción %s/%s (%s) %s",
            payload.profile_id, payload.button_id, action.action_type,
            "simulada" if is_test else "ejecutada",
        )

        if action.action_type == "macro":
            return {
                "ok": True,
                "button": action.name,
                "action_type": "macro",
                "steps": len(action.macro),
                "macro": [step.model_dump() for step in action.macro],
                "test_mode": is_test,
            }
        if action.action_type == "obs":
            return {
                "ok": True,
                "button": action.name,
                "action_type": "obs",
                "obs_action": action.obs_action,
                "test_mode": is_test,
            }
        return {
            "ok": True,
            "button": action.name,
            "action_type": "hotkey",
            "keys": action.keys,
            "hold_ms": action.hold_ms,
            "test_mode": is_test,
        }

    frontend = ROOT / "frontend"
    app.mount(
        "/assets/icons",
        StaticFiles(directory=ROOT / "assets" / "icons"),
        name="button-icons",
    )
    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend / "index.html")

    @app.get("/manifest.webmanifest", include_in_schema=False)
    def manifest() -> FileResponse:
        return FileResponse(frontend / "manifest.webmanifest", media_type="application/manifest+json")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(ROOT / "assets" / "icons" / "nova-deck.svg", media_type="image/svg+xml")

    return app


app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Panel táctil local para Star Citizen")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--config", type=Path, help="Ruta alternativa a buttons.json")
    parser.add_argument("--test-mode", action="store_true", help="Nunca inyectar teclas")
    parser.add_argument("--debug", action="store_true", help="Logs detallados para diagnóstico")
    args = parser.parse_args()
    runtime = load_app_settings(ROOT / "config" / "settings.json")
    debug_enabled = args.debug or runtime.debug
    uvicorn.run(
        create_app(
            config_path=args.config,
            force_test_mode=args.test_mode,
            debug_override=debug_enabled,
        ),
        host=args.host,
        port=args.port,
        log_level="debug" if debug_enabled else runtime.log_level.lower(),
    )
