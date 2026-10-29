# Architecture & Directory Structure

[Back to README](../README.md)

The project uses a monorepo setup (`backend/` and `frontend/`). The React frontend provides the control dashboard, while the FastAPI and Python backend manage configuration, authentication setup, browser automation, and the single supported Windows scheduled task.

Scheduled execution follows one controlled path:

```text
Scheduler UI
  -> Scheduler API
  -> fixed Windows task named CourtSniper
  -> fixed backend/src/scheduled_runner.py
  -> start or reuse local FastAPI
  -> POST http://127.0.0.1:8000/api/run-sniper
  -> ARMED check
  -> SniperProcessManager
  -> predefined backend/src/sniper.py
```

The Windows task never runs `sniper.py` directly. Its fixed runner reuses FastAPI when it is already available at `127.0.0.1:8000`; otherwise, it starts a temporary local API, monitors the controlled sniper run, and shuts down only the API process it started after the run reaches a terminal state. The dashboard and FastAPI do not need to remain running between configuration and the scheduled trigger.

```text
CourtSniper/
│
├── .run/                        # Ignored launcher PID records and local logs
├── start-courtsniper.ps1        # Starts the native Windows backend and frontend
├── stop-courtsniper.ps1         # Safely stops only launcher-owned processes
│
├── backend/                     # Python Automation & FastAPI Service
│   ├── .venv/                   # Isolated Python virtual environment
│   ├── user_data/               # Cached Facebook/Chrome session cookies (hidden/ignored)
│   ├── src/
│   │   ├── api.py               # Stable FastAPI composition root (`src.api:app`)
│   │   ├── config.py            # Loads configuration variables from .env
│   │   ├── session/             # Login setup, mutex guard, and process manager
│   │   │   ├── setup.py
│   │   │   ├── guard.py
│   │   │   └── process.py
│   │   ├── booking/             # Booking automation and process lifecycle
│   │   │   ├── sniper.py
│   │   │   └── process.py
│   │   ├── scheduler/           # Models, fixed runner, and Windows adapter
│   │   │   ├── models.py
│   │   │   ├── runner.py
│   │   │   └── windows.py
│   │   ├── web/                 # Feature-specific FastAPI route modules
│   │   │   ├── config_routes.py
│   │   │   ├── session_routes.py
│   │   │   ├── sniper_routes.py
│   │   │   └── scheduler_routes.py
│   │   ├── setup_session.py     # Stable manual-login executable wrapper
│   │   ├── sniper.py            # Stable booking executable wrapper
│   │   ├── scheduled_runner.py  # Stable Windows task executable wrapper
│   │   ├── setup_session_guard.py
│   │   ├── setup_session_process.py
│   │   ├── sniper_process.py
│   │   ├── scheduler_models.py
│   │   └── windows_scheduler.py # Stable legacy import wrappers
│   ├── tests/                    # Backend unit and mocked integration tests
│   ├── .env                     # Hidden environment configuration file
│   ├── .env.example             # Safe template file for environment variables
│   ├── .gitignore               # Excludes .env, .venv, and user_data/ from Git
│   └── requirements.txt         # Python dependencies
│
├── frontend/                    # React / Vite Web Dashboard
│   ├── src/                     # React components, sections, and API services
│   ├── public/                  # CourtSniper shuttlecock image assets
│   ├── index.html               # Main HTML entry page
│   ├── package.json             # Node.js dependencies
│   └── vite.config.js           # Vite server configuration
│
├── docs/                        # Detailed project guides linked from README.md
├── LICENSE                      # Standalone MIT License file
└── README.md                    # Project overview, setup, and documentation links

```

* **`backend/src/session/`**: Owns manual authentication, safe target selection, the project-scoped Windows named mutex, and duplicate-resistant setup process management.
* **`backend/src/booking/`**: Owns the precision Messenger workflow and the tracked sniper process lifecycle, including cancellation and cleanup.
* **`backend/src/scheduler/`**: Owns schedule validation, the fixed local scheduled runner, and the adapter for the single managed Windows task.
* **`backend/src/web/`**: Owns configuration, session, sniper, and scheduler route handlers. `api.py` composes these routes while preserving shared manager lifetimes and CORS settings.
* **Stable compatibility entrypoints**: The root modules under `backend/src/` remain supported import and executable paths. Existing scripts may continue importing `setup_session`, `setup_session_guard`, `setup_session_process`, `sniper`, `sniper_process`, `scheduler_models`, `scheduled_runner`, or `windows_scheduler`.
* **Stable executable paths**: Manual setup still uses `backend/src/setup_session.py`, controlled booking runs still use `backend/src/sniper.py`, and installed Windows tasks still use `backend/src/scheduled_runner.py`.
* **`config.py`**: Loads the target configuration without requiring changes to the automation engine.
* **`frontend/src/` directory**: Contains the dashboard components, responsive sections, shared state, and API client.
* **Critical security notice**: The `user_data/` directory stores authenticated browser cookies and tokens. Keep it excluded from version control and never share, upload, or expose it through the frontend or API.
