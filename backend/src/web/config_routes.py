"""Configuration and service-status routes."""

import os
from typing import Callable, Dict

from fastapi import HTTPException


def read_config_values(
    env_file_path: str,
    allowed_keys: set[str],
) -> dict[str, str]:
    values = {}
    if not os.path.exists(env_file_path):
        return values

    with open(env_file_path, "r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
                continue

            key, value = stripped_line.split("=", 1)
            key = key.strip()
            if key in allowed_keys:
                values[key] = value.strip().strip("\"'")
    return values


def update_config_file(
    updates: Dict[str, str],
    *,
    env_file_path: str,
    editable_keys: set[str],
) -> dict[str, str]:
    if any(key not in editable_keys for key in updates):
        raise HTTPException(
            status_code=422,
            detail="The request contains an unsupported configuration field.",
        )

    if not os.path.exists(env_file_path):
        return {"error": ".env file missing!"}

    with open(env_file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(env_file_path, "w", encoding="utf-8") as file:
        for line in lines:
            written = False
            for key, new_value in updates.items():
                if line.startswith(f"{key}="):
                    file.write(f'{key}="{new_value}"\n')
                    written = True
                    break
            if not written:
                file.write(line)

    return {"message": "Configuration successfully updated on the server!"}


def register_config_routes(
    app,
    *,
    get_configured_status: Callable[[], str | None],
    read_public_config: Callable[[], dict[str, str]],
    update_configuration: Callable[[Dict[str, str]], dict[str, str]],
):
    @app.get("/api/status")
    def get_status():
        execution_status = get_configured_status() or "UNKNOWN"
        return {
            "service": "CourtSniper",
            "status": "online",
            "execution_status": execution_status,
            "armed": execution_status == "ARMED",
        }

    @app.get("/api/config")
    def get_config():
        """Return only the configuration fields required by the dashboard."""
        return read_public_config()

    @app.post("/api/config")
    def update_config(updates: Dict[str, str]):
        """Receive dashboard configuration and update the fixed env file."""
        return update_configuration(updates)

    return get_status, get_config, update_config
