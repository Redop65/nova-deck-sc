from __future__ import annotations

import re
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CommandRequest(BaseModel):
    button_id: str
    profile_id: str = "default"
    test_mode: bool = False


class MacroStep(BaseModel):
    keys: str = Field(min_length=1, max_length=50)
    hold_ms: int = Field(default=0, ge=0, le=5000)
    delay_after_ms: int = Field(default=0, ge=0, le=10000)

    @field_validator("keys", mode="before")
    @classmethod
    def strip_keys(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value


class ButtonInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=60)
    action_type: Literal["hotkey", "macro", "obs"] | None = Field(default=None, alias="type")
    keys: str | None = Field(default=None, min_length=1, max_length=50)
    macro: list[MacroStep] | None = Field(default=None, min_length=1, max_length=20)
    obs_action: Literal[
        "start_recording", "stop_recording", "toggle_recording", "pause_recording",
        "resume_recording", "set_scene", "toggle_mute", "set_source_visibility",
    ] | None = Field(default=None, alias="obsAction")
    scene_name: str | None = Field(default=None, alias="sceneName", max_length=200)
    input_name: str | None = Field(default=None, alias="inputName", max_length=200)
    source_name: str | None = Field(default=None, alias="sourceName", max_length=200)
    visible: bool | None = None
    color: Literal["cyan", "blue", "violet", "amber", "orange", "green", "red"] = "cyan"
    icon: str | None = Field(default=None, max_length=200)
    disabled: bool = False
    hold_ms: int = Field(default=0, ge=0, le=5000)

    @field_validator("id")
    @classmethod
    def valid_id(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
            raise ValueError("Usa minúsculas, números y guiones; por ejemplo 'open-comms'.")
        return value

    @field_validator("name", "keys", "scene_name", "input_name", "source_name", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="before")
    @classmethod
    def infer_legacy_type(cls, data: object) -> object:
        if isinstance(data, dict) and not data.get("type") and not data.get("action_type"):
            data = dict(data)
            data["type"] = "macro" if data.get("macro") else "hotkey"
        return data

    @model_validator(mode="after")
    def exactly_one_action(self) -> Self:
        if self.action_type == "hotkey" and (not self.keys or self.macro or self.obs_action):
            raise ValueError("Un botón hotkey necesita 'keys' y no admite macro u obsAction.")
        if self.action_type == "macro" and (not self.macro or self.keys or self.obs_action):
            raise ValueError("Un botón macro necesita 'macro' y no admite keys u obsAction.")
        if self.action_type == "obs" and (not self.obs_action or self.keys or self.macro):
            raise ValueError("Un botón OBS necesita 'obsAction' y no admite keys o macro.")
        if self.action_type == "macro" and self.macro:
            total_ms = sum(step.hold_ms + step.delay_after_ms for step in self.macro)
            if total_ms > 60000:
                raise ValueError("La macro no puede superar 60000 ms en total.")
        required = {
            "set_scene": ("scene_name",),
            "toggle_mute": ("input_name",),
            "set_source_visibility": ("scene_name", "source_name", "visible"),
        }.get(self.obs_action, ())
        missing = [field for field in required if getattr(self, field) is None]
        if missing:
            raise ValueError(f"La acción OBS {self.obs_action} requiere: {', '.join(missing)}.")
        return self


class ButtonMutation(BaseModel):
    profile_id: str = Field(default="default", min_length=1, max_length=50)
    target_profile_id: str | None = Field(default=None, min_length=1, max_length=50)
    page_id: str = Field(min_length=1, max_length=50)
    position: int | None = Field(default=None, ge=0, le=500)
    button: ButtonInput
