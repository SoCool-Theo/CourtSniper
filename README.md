# CourtSniper 2.0

CourtSniper is a local automation application designed to secure time-critical badminton court bookings through Facebook Messenger. It combines a Python automation service with a responsive React dashboard and separates manual login authentication from high-speed execution.

The automation engine uses a persistent local browser session to avoid repeating login and Two-Factor Authentication (2FA) prompts on booking day. A precision countdown coordinates message dispatch with the configured booking time.

---

## Architecture & Directory Structure

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
├── backend/                     # Python Automation & FastAPI Service
│   ├── .venv/                   # Isolated Python virtual environment
│   ├── user_data/               # Cached Facebook/Chrome session cookies (hidden/ignored)
│   ├── src/                     
│   │   ├── api.py               # FastAPI backend server and guarded API routes
│   │   ├── config.py            # Loads configuration variables from .env
│   │   ├── scheduled_runner.py  # Fixed scheduled API bootstrap and run monitor
│   │   ├── scheduler_models.py  # Schedule validation and next-run calculation
│   │   ├── setup_session.py     # Manual login script for caching session cookies
│   │   ├── sniper.py            # High-precision Playwright execution engine
│   │   └── windows_scheduler.py # Fixed Windows Task Scheduler adapter
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
├── LICENSE                      # Standalone MIT License file
└── README.md                    # Main project documentation manual

```

* **`backend/src/` directory**: Contains the API, configuration, session setup, and automation logic.
* **`config.py`**: Loads the target configuration without requiring changes to the automation engine.
* **`setup_session.py`**: Handles manual authentication and creates the persistent browser profile.
* **`sniper.py`**: Runs the precision booking workflow.
* **`scheduled_runner.py`**: Safely starts or reuses the local API for a scheduled run and monitors the existing process manager.
* **`scheduler_models.py`**: Validates selected booking weekdays and warm-up values and calculates local trigger times.
* **`windows_scheduler.py`**: Manages only the fixed, adapter-owned `CourtSniper` Windows task.
* **`frontend/src/` directory**: Contains the dashboard components, responsive sections, shared state, and API client.
* **Critical security notice**: The `user_data/` directory stores authenticated browser cookies and tokens. Keep it excluded from version control and never share, upload, or expose it through the frontend or API.

---

## Web Dashboard

The responsive CourtSniper dashboard includes:

* A live system clock and countdown to the next configured booking time.
* Armed and disarmed execution-state controls.
* Booking URL, message, and target-time configuration.
* Backend connection and session-setup controls.
* Scheduler, system-status, and execution-console panels.
* Desktop, tablet, and mobile layouts with accessible navigation.

The **Start Sniper** control uses the guarded backend API and is enabled only while the backend is online, the configuration is armed, and no run is active. While automation is running, the control becomes **Stop Sniper** and requests graceful cancellation. The dashboard reports `stopping` until browser cleanup completes and then reports `stopped`.

The **Scheduler** panel configures booking weekdays and a warm-up period, reports the installed and enabled state of the Windows task, and displays next-run and last-run information when Windows provides it. Scheduler enablement controls future triggers only. It does not replace the `ARMED` kill switch and disabling it does not stop an active run. The frontend never executes local programs or Python files directly.

---

## Installation & Dependencies

### 1. Backend Virtual Environment Setup

Navigate into the `backend/` directory. Create and activate an isolated Python virtual environment (`.venv`) in your terminal to keep project dependencies cleanly separated from your system Python:

```bash
cd backend
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

```

### 2. Backend Package & Driver Installation

Install the required Python libraries by running `pip install -r requirements.txt` in your terminal. Then, download the mandatory core browser automation drivers needed to establish the Chrome DevTools Protocol pipeline by running `playwright install chromium`.

```bash
pip install -r requirements.txt
playwright install chromium

```

Start the local API from the `backend/` directory whenever you want to use the dashboard or change the saved schedule:

```powershell
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

After saving and enabling the Windows task, you may close both development servers. The scheduled task will start FastAPI automatically when its trigger fires. Saving the schedule again is required after moving the project or recreating its Python environment because the fixed task action records the current interpreter and runner locations.

Windows may require the terminal hosting FastAPI to run with elevated permission when the dashboard first creates or updates the highest-privilege scheduled task. The API returns a sanitized permission error if Windows denies the operation.

### 3. Frontend Setup

Navigate into the `frontend/` directory, install the Node dependencies, and start the Vite development server:

```bash
cd ../frontend
npm install
npm run dev

```

The frontend connects to `http://127.0.0.1:8000/api` by default. To use a different backend address, create `frontend/.env.local` and set:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

Before opening a pull request, verify the frontend with:

```bash
npm run lint
npm run build
```

---

## Configuration Setup (`.env`)

Copy the safe `.env.example` template to create a private `.env` file in the `backend/` directory. Configure these target variables in the new `.env` file:

* **`TARGET_URL`**: The specific Facebook Messenger chat thread URL for the badminton club.
* **`BOOKING_MESSAGE`**: Your customized booking message text (e.g., "Hi, I would like to book badminton court at 4 - 5pm").
* **`TARGET_HOUR`, `TARGET_MINUTE`, `TARGET_SECOND`**: Your target execution timestamp in 24-hour format (for example, `8`, `0`, `0` for 8:00 AM).
* **`STATUS`**: Set this to `"ARMED"` or `"DISARMED"` to authorize or reject every request to `POST /api/run-sniper`, including requests made by the Windows task.

Never commit `.env`, `user_data/`, browser profiles, cookies, tokens, or account credentials.

---

## Frontend API Contract

The current frontend uses the following API routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/status` | Check backend availability and the current armed state. |
| `GET` | `/api/config` | Load the current booking configuration. |
| `POST` | `/api/config` | Save booking configuration and armed status. |
| `POST` | `/api/run-setup` | Request the manual login/session setup browser. |
| `POST` | `/api/run-sniper` | Start one controlled sniper run when armed. |
| `GET` | `/api/run-sniper/status` | Read the current sniper process lifecycle state. |
| `POST` | `/api/run-sniper/stop` | Stop the currently tracked sniper run. |
| `GET` | `/api/scheduler` | Read the sanitized state of the fixed Windows task. |
| `POST` | `/api/scheduler/config` | Configure selected booking weekdays and warm-up using the existing target time. |
| `POST` | `/api/scheduler/enable` | Enable future triggers for the configured fixed task. |
| `POST` | `/api/scheduler/disable` | Disable future triggers without stopping an active run. |

`POST /api/run-sniper` executes only the predefined `backend/src/sniper.py` entry point. It returns `202 Accepted` when a run starts and rejects disarmed or concurrent requests with `409 Conflict`. The endpoint never accepts commands, script paths, booking URLs, or messages from the request.

`GET /api/run-sniper/status` returns `idle`, `running`, `stopping`, `stopped`, `succeeded`, or `failed`, together with non-sensitive process metadata such as timestamps, PID, and exit code. A successful process exit confirms that the automation finished without a process-level error; it does not independently guarantee Messenger delivery. Run state is held in memory and resets when the FastAPI service restarts.

`POST /api/run-sniper/stop` accepts no PID, command, or path from the client. It targets only the process group created and tracked by the API, requests graceful cancellation first, and uses an exact-PID process-tree fallback if cleanup does not finish within five seconds. It returns `409 Conflict` when no run is active. Cancellation before dispatch prevents the booking message from being sent; cancellation after dispatch closes the browser but cannot retract a message that was already submitted.

The scheduler configuration request accepts only `weekdays` and `warmup_minutes`. It never accepts a task name, command, URL, executable path, or script path. The backend reads `TARGET_HOUR`, `TARGET_MINUTE`, and `TARGET_SECOND` internally and calculates the Windows trigger as target time minus warm-up. Selected weekdays refer to booking days, so a target shortly after midnight can produce a trigger on the preceding weekday.

The first successful scheduler configuration installs the fixed task in a disabled state. Updating a recognized task preserves its current enabled state. Enabling is rejected when the booking target has changed since the task was configured; save the scheduler configuration again to recalculate the trigger. Scheduler enablement remains independent from `STATUS`, and the existing ARMED check still decides whether a scheduled request can start the sniper.

Scheduler errors use sanitized HTTP responses: validation errors return `422`, state conflicts return `409`, permission failures return `403`, unavailable or unsupported scheduler environments return `503`, timeouts return `504`, and other scheduler failures return `500`. The API does not return Windows command output, credentials, principals, task actions, or local paths.

---

## Manual Authentication Phase (`setup_session.py`)

* **Mid-Week Preparation**: Execute `python src/setup_session.py` in your terminal once during the week prior to your booking day. Make sure you are in the `backend/` directory.
* **Session Persistence**: This script launches a visible Google Chrome window, allowing you to manually log into Facebook Messenger and solve any Two-Factor Authentication (2FA) challenges.
* **Caching Cookies**: Once your inbox loads completely, close the browser window to permanently cache your session cookies inside the local `user_data/` folder.

---

## Windows Task Scheduler Automation

### 1. Configure the Schedule

Start FastAPI and open the Scheduler panel in the dashboard. Select one or more booking weekdays, enter the warm-up period in minutes, and choose **Save Schedule**. The default warm-up is five minutes and the supported range is 0 through 1440 minutes. The booking target continues to come from `TARGET_HOUR`, `TARGET_MINUTE`, and `TARGET_SECOND`; the Scheduler panel does not maintain a second target-time setting.

Saving creates or updates only the Windows task named `CourtSniper`. A new task is installed disabled so its calculated trigger can be reviewed before **Enable Schedule** is selected. If an unrelated task already owns that exact name, CourtSniper reports a name conflict and refuses to modify it.

### 2. Enable or Disable Future Runs

Choose **Enable Schedule** after reviewing the trigger. At the scheduled time, Windows launches the fixed `scheduled_runner.py` entry point. The runner reuses a recognized CourtSniper API if one is already running; otherwise, it starts FastAPI locally, sends the fixed request to `POST http://127.0.0.1:8000/api/run-sniper`, and monitors the existing process manager. If CourtSniper is disarmed, the endpoint rejects the request and no sniper process starts.

When the runner started FastAPI, it keeps that API available while the sniper is active so the existing **Stop Sniper** endpoint remains usable. It shuts down only that owned API after the run succeeds, fails, or is stopped. It never shuts down a FastAPI instance that was already running. If monitoring becomes unavailable while a run may still be active, the runner leaves its API running rather than risk interrupting the booking.

Choose **Disable Future Runs** to prevent later triggers. This does not terminate a sniper process that is already running. Use **Stop Sniper** on the dashboard for an active run.

### 3. Critical Scheduler Settings

The adapter applies these fixed settings when it registers the task:

* **Wake the computer to run this task** so a supported sleeping computer can wake for the trigger.
* **Run only when the user is logged on** so the visible persistent Chrome session can run interactively.
* **Run with highest privileges**; Windows may require FastAPI itself to be started from an elevated terminal when configuring the task.
* **Ignore overlapping task instances**. The API process manager also rejects a second sniper run while one is active.
* **No stored password**. The task uses the current interactive Windows token.

### 4. Status Semantics

`GET /api/scheduler` reports whether the fixed task is installed, recognized as CourtSniper-managed, configured, in sync with the booking target, and enabled. It also returns the next run time, last run time, and Windows last-task result when available.

A last-task result of `0` means the scheduled runner observed a successful process exit. Result `1` is a runner or local API failure, `2` means the existing ARMED/concurrency guard rejected the run, `3` means the sniper process failed, and `4` means it was stopped. A successful process exit does not independently prove that Messenger accepted the booking message.

CourtSniper provides no API route for arbitrary task management or deletion. It does not expose the task action, Windows account, credentials, or sensitive local filesystem paths.

---

## Sleep Mode Pre-Flight Checklist

* **Continuous Power**: Leave your PC or laptop plugged into an AC power outlet overnight.
* **Sleep Mode Over Hibernate**: On laptops utilizing Modern Standby (S0 Low Power Idle)—such as ASUS TUF gaming laptops—you must use standard Sleep mode rather than Hibernate overnight.
* **Power Plan Settings**: Verify that wake timers are strictly enabled inside your Windows Advanced Power Plan settings.
* **Interactive Desktop**: Confirm that the logged-in desktop and visible Chrome session remain available after wake. Do not weaken device sign-in security solely for automation.

---

## Verification

Run the backend suite from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m unittest discover -s backend\tests -v
cd backend
.\.venv\Scripts\python.exe -m pip check
```

Run the frontend checks from `frontend/`:

```powershell
npm.cmd run lint
npm.cmd run build
```

All automated Windows scheduler tests use injected command, HTTP, clock, and process implementations. They do not create, update, enable, disable, query, or delete a real Windows task, and they do not start a real API or sniper process.

---

## Project History & Legacy Version (v1.0)

* CourtSniper 1.0 was an automated Python script designed to secure time-critical badminton court bookings via Facebook Messenger.
* It relied on a simple three-file terminal architecture (`config.py`, `setup_session.py`, and `sniper.py`).

---

## License & Liability

This project is licensed under the [MIT License](LICENSE).

This software is provided "AS IS", without warranty of any kind. The authors are not legally liable for any account restrictions triggered by Meta's anti-bot algorithms or missed court reservations.
