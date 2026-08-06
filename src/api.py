from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize the FastAPI application
app = FastAPI(title="CourtSniper Web UI")

# Set up CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows any local Tailscale IP to connect
    allow_credentials=True,
    allow_methods=["*"],  # Allows GET (read) and POST (write) requests
    allow_headers=["*"],
)

@app.get("/api/status")
def get_status():
    return {"status": "CourtSniper backend is armed and online!"}