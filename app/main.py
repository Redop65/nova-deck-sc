from __future__ import annotations

import argparse
import re
import socket
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from app.config import ButtonConfig
from app.keyboard import KeyboardSender, parse_combo

ROOT = Path(__file__).resolve().parents[1]


class CommandRequest(BaseModel):
    button_id: str
    test_mode: bool = False


class ButtonInput(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=60)
    keys: str = Field(min_length=1, max_length=50)
    color: Literal["cyan", "blue", "violet", "amber", "orange", "green", "red"] = "cyan"
    icon: str | None = Field(default=None, max_length=8)
    disabled: bool = False
    hold_ms: int = Field(default=0, ge=0, le=5000)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError("Usa minúsculas, números y guiones; por ejemplo 'open-comms'.")
        return value

    @field_validator("name", "keys", mode="before")
    @classmethod
    def strip_text(cls, value: str) -> str:
        if not isinstance(value, str):
            return value
        return value.strip()


class ButtonMutation(BaseModel):
    page_id: str = Field(min_length=1, max_length=50)
    button: ButtonInput


def button_payload(payload: ButtonMutation) -> dict:
    button = payload.button.model_dump(exclude_none=True)
    if not button["disabled"]:
        try:
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


def create_app(config_path: Path | None = None, force_test_mode: bool = False) -> FastAPI:
    app = FastAPI(title="Star Citizen Deck", version="1.0.0")
    app.state.config = ButtonConfig(config_path or ROOT / "config" / "buttons.json")
    app.state.keyboard = KeyboardSender()
    app.state.force_test_mode = force_test_mode

    @app.get("/api/status")
    def status(request: Request) -> dict:
        return {
            "ok": True,
            "force_test_mode": request.app.state.force_test_mode,
            "local_ip": local_ip(),
        }

    @app.get("/api/buttons")
    def buttons(request: Request) -> dict:
        try:
            return request.app.state.config.load()
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post("/api/buttons", status_code=201)
    def create_button(payload: ButtonMutation, request: Request) -> dict:
        button = button_payload(payload)
        try:
            created = request.app.state.config.create_button(payload.page_id, button)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"ok": True, "button": created}

    @app.put("/api/buttons/{button_id}")
    def update_button(button_id: str, payload: ButtonMutation, request: Request) -> dict:
        button = button_payload(payload)
        try:
            updated = request.app.state.config.update_button(button_id, payload.page_id, button)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Botón no encontrado.") from exc
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"ok": True, "button": updated}

    @app.delete("/api/buttons/{button_id}")
    def delete_button(button_id: str, request: Request) -> dict:
        try:
            removed = request.app.state.config.delete_button(button_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Botón no encontrado.") from exc
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"ok": True, "button": removed}

    @app.post("/api/commands")
    def command(payload: CommandRequest, request: Request) -> dict:
        try:
            button = request.app.state.config.get_button(payload.button_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        if button is None:
            raise HTTPException(status_code=404, detail="Botón no encontrado.")
        if button.get("disabled", False):
            raise HTTPException(status_code=409, detail="Este botón está deshabilitado en la configuración.")

        combo = button["keys"]
        try:
            hold_ms = int(button.get("hold_ms", 0))
        except (TypeError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="hold_ms debe ser un número entero.") from exc
        if not 0 <= hold_ms <= 5000:
            raise HTTPException(status_code=422, detail="hold_ms debe estar entre 0 y 5000.")
        is_test = payload.test_mode or request.app.state.force_test_mode
        if not is_test:
            try:
                request.app.state.keyboard.send(combo, hold_ms=hold_ms)
            except (ValueError, RuntimeError, OSError) as exc:
                raise HTTPException(status_code=422, detail=f"No se pudo enviar {combo}: {exc}") from exc
        return {
            "ok": True,
            "button": button["name"],
            "keys": combo,
            "hold_ms": hold_ms,
            "test_mode": is_test,
        }

    frontend = ROOT / "frontend"
    app.mount("/assets", StaticFiles(directory=frontend / "assets"), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(frontend / "index.html")

    return app


app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Panel táctil local para Star Citizen")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--config", type=Path, help="Ruta alternativa a buttons.json")
    parser.add_argument("--test-mode", action="store_true", help="Nunca inyectar teclas")
    args = parser.parse_args()
    uvicorn.run(
        create_app(config_path=args.config, force_test_mode=args.test_mode),
        host=args.host,
        port=args.port,
    )
