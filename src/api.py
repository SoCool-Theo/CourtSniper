from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import os

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