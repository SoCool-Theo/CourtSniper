from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os
import subprocess
import sys

try:
    from .sniper_process import (
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperProcessManager,
        SniperScriptNotFoundError,
    )
except ImportError:
    from sniper_process import (
        SniperAlreadyRunningError,
        SniperLaunchError,
        SniperProcessManager,
        SniperScriptNotFoundError,
    )

# Initialize the FastAPI application
app = FastAPI(title="CourtSniper Web UI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = os.path.dirname(CURRENT_DIR)

ENV_FILE_PATH = os.path.join(ROOT_DIR, ".env")

sniper_process_manager = SniperProcessManager()


def _get_configured_status():
    """Read only the kill-switch value required to authorize a run."""
    if not os.path.exists(ENV_FILE_PATH):
        return None

    with open(ENV_FILE_PATH, "r", encoding="utf-8") as file:
        for line in file:
            stripped_line = line.strip()
            if not stripped_line or stripped_line.startswith("#") or "=" not in stripped_line:
                continue

            key, value = stripped_line.split("=", 1)
            if key.strip() == "STATUS":
                return value.strip().strip("\"'").upper()

    return None

@app.get("/api/status")
def get_status():
    return {"status": "CourtSniper backend is armed and online!"}

@app.get("/api/config")
def get_config():
    """Reads the current .env file and sends it to the frontend as JSON."""
    config = {}
    if os.path.exists(ENV_FILE_PATH):
        with open(ENV_FILE_PATH, "r", encoding="utf-8") as file:
            for line in file:
                # Ignore empty lines and comments
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    # Strip out any extra quotes used in the .env file
                    config[key] = value.strip("\"'")
    return config

@app.post("/api/config")
def update_config(updates: Dict[str, str]):
    """Receives JSON from the frontend and overwrites the .env file."""
    if not os.path.exists(ENV_FILE_PATH):
        return {"error": ".env file missing!"}

    # Read the current file line by line
    with open(ENV_FILE_PATH, "r", encoding="utf-8") as file:
        lines = file.readlines()

    # Rewrite the file, swapping out updated values
    with open(ENV_FILE_PATH, "w", encoding="utf-8") as file:
        for line in lines:
            written = False
            for key, new_value in updates.items():
                if line.startswith(f"{key}="):
                    # Write the new value, wrapped safely in quotes
                    file.write(f'{key}="{new_value}"\n')
                    written = True
                    break
            # If the line wasn't updated, keep it exactly as it was
            if not written:
                file.write(line)

    return {"message": "Configuration successfully updated on the server!"}


@app.post("/api/run-setup")
def trigger_setup():
    """Triggers the manual Facebook login script in the background."""

    # 1. Build the absolute path to setup_session.py (it lives in the same folder as this api.py)
    setup_script_path = os.path.join(CURRENT_DIR, "setup_session.py")

    if not os.path.exists(setup_script_path):
        return {"error": "Could not find setup_session.py!"}

    try:
        # 2. Launch the script as a separate background process.
        subprocess.Popen([sys.executable, setup_script_path], cwd=ROOT_DIR)

        return {"message": "Setup session launched! Check your laptop screen."}

    except Exception as e:
        return {"error": f"Failed to launch script: {str(e)}"}


@app.post("/api/run-sniper", status_code=status.HTTP_202_ACCEPTED)
def trigger_sniper():
    """Start the predefined sniper automation when the kill switch is armed."""
    if _get_configured_status() != "ARMED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="CourtSniper must be armed before starting a run.",
        )

    try:
        run_status = sniper_process_manager.start()
    except SniperAlreadyRunningError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    except (SniperScriptNotFoundError, SniperLaunchError) as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error

    return {
        "message": "CourtSniper run started.",
        "run": run_status.to_dict(),
    }


@app.get("/api/run-sniper/status")
def get_sniper_run_status():
    """Return the current non-sensitive sniper process state."""
    return {"run": sniper_process_manager.get_status().to_dict()}
