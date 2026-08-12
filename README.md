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
├── LICENSE                      # Standalone MIT License file
└── README.md                    # Main project documentation manual

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

This frontend override does not change scheduled execution. For safety, the Windows task runner always uses the fixed local CourtSniper API at `http://127.0.0.1:8000/api` and accepts no host or URL configuration.

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

## Local API Contract

The dashboard and fixed scheduled runner use the following local API routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/status` | Confirm CourtSniper service identity, availability, and armed state. |
| `GET` | `/api/config` | Load the current booking configuration. |
| `POST` | `/api/config` | Save booking configuration and armed status. |
| `POST` | `/api/run-setup` | Open the manual login browser at the internally configured booking conversation. |
| `POST` | `/api/run-sniper` | Start one controlled sniper run when armed. |
| `GET` | `/api/run-sniper/status` | Read the current sniper process lifecycle state. |
| `POST` | `/api/run-sniper/stop` | Stop the currently tracked sniper run. |
| `GET` | `/api/scheduler` | Read the sanitized state of the fixed Windows task. |
| `POST` | `/api/scheduler/config` | Configure selected booking weekdays and warm-up using the existing target time. |
| `POST` | `/api/scheduler/enable` | Enable future triggers for the configured fixed task. |
| `POST` | `/api/scheduler/disable` | Disable future triggers without stopping an active run. |

`POST /api/run-setup` accepts no URL, command, executable path, or script path from the client. It launches only the predefined `backend/src/setup_session.py` entry point, which reads `TARGET_URL` from the backend's internal configuration at runtime. The API request cannot override the login destination.

Setup launch requests are idempotent while login setup is active. The backend serializes simultaneous requests, tracks the child it launched, and checks a project-scoped Windows named mutex to detect setup processes that survived an API restart or were started manually. A duplicate request launches no additional browser and returns a successful response instructing the user to continue in the existing window. The setup script also acquires the mutex before reading configuration or loading Playwright, closing the remaining race between separate API instances.

`POST /api/run-sniper` executes only the predefined `backend/src/sniper.py` entry point. It returns `202 Accepted` when a run starts and rejects disarmed or concurrent requests with `409 Conflict`. The endpoint never accepts commands, script paths, booking URLs, or messages from the request.

`GET /api/run-sniper/status` returns `idle`, `running`, `stopping`, `stopped`, `succeeded`, or `failed`, together with non-sensitive process metadata such as timestamps, PID, and exit code. A successful process exit confirms that the automation finished without a process-level error; it does not independently guarantee Messenger delivery. Run state is held in memory and resets when the FastAPI service restarts.

`POST /api/run-sniper/stop` accepts no PID, command, or path from the client. It targets only the process group created and tracked by the API, requests graceful cancellation first, and uses an exact-PID process-tree fallback if cleanup does not finish within five seconds. It returns `409 Conflict` when no run is active. Cancellation before dispatch prevents the booking message from being sent; cancellation after dispatch closes the browser but cannot retract a message that was already submitted.

The scheduler configuration request accepts only `weekdays` and `warmup_minutes`. It never accepts a task name, command, URL, executable path, or script path. The backend reads `TARGET_HOUR`, `TARGET_MINUTE`, and `TARGET_SECOND` internally and calculates the Windows trigger as target time minus warm-up. Selected weekdays refer to booking days, so a target shortly after midnight can produce a trigger on the preceding weekday.

The first successful scheduler configuration installs the fixed task in a disabled state. Updating a recognized task preserves its current enabled state. Enabling is rejected when the booking target has changed since the task was configured; save the scheduler configuration again to recalculate the trigger. Scheduler enablement remains independent from `STATUS`, and the existing ARMED check still decides whether a scheduled request can start the sniper.

Scheduler errors use sanitized HTTP responses: validation errors return `422`, state conflicts return `409`, permission failures return `403`, unavailable or unsupported scheduler environments return `503`, timeouts return `504`, and other scheduler failures return `500`. The API does not return Windows command output, credentials, principals, task actions, or local paths.

---

## Manual Authentication Phase (`setup_session.py`)

* **Mid-Week Preparation**: Choose **Open Login Browser** in the Session panel, or execute `python src/setup_session.py` from the `backend/` directory, once during the week prior to your booking day.
* **Configured Destination**: The script reads the saved `TARGET_URL` internally and opens that booking conversation when it is an HTTPS URL on `facebook.com`, `messenger.com`, or one of their subdomains.
* **Validation and Fallback**: URLs using another scheme or host, malformed URLs, and URLs containing embedded username or password credentials are rejected. A missing or rejected value falls back to `https://www.facebook.com/messages/`.
* **Private Logging**: Console messages identify whether the configured conversation or fallback inbox is being used without printing the complete conversation URL.
* **Session Persistence**: The script launches a visible Google Chrome window with the existing persistent profile, allowing you to manually log into Facebook Messenger and solve any Two-Factor Authentication (2FA) challenges.
* **Single Setup Window**: Repeated button clicks, simultaneous API requests, API restarts, and manual script launches reuse or defer to the active setup window instead of opening the persistent profile twice.
* **Completion and Cleanup**: Close the login browser after the configured conversation or fallback inbox loads. Closing Chrome finishes setup immediately; otherwise, the window closes after five minutes. The named mutex is released after normal completion, interruption, or failure, and Windows releases it automatically if the setup process crashes.
* **Caching Cookies and Re-authentication**: The persistent profile retains the Facebook login inside the local `user_data/` folder, so setup does not run again automatically. Use **Open Login Browser** again only when you intentionally need to inspect the conversation or re-authenticate after Facebook invalidates the session.

---

## Windows Task Scheduler Automation

### 1. Configure the Schedule

Start FastAPI and open the Scheduler panel in the dashboard. Select one or more booking weekdays, enter the warm-up period in minutes, and choose **Save Schedule**. The default warm-up is five minutes and the supported range is 0 through 1440 minutes. The booking target continues to come from `TARGET_HOUR`, `TARGET_MINUTE`, and `TARGET_SECOND`; the Scheduler panel does not maintain a second target-time setting.

Saving creates or updates only the Windows task named `CourtSniper`. A new task is installed disabled so its calculated trigger can be reviewed before **Enable Schedule** is selected. If an unrelated task already owns that exact name, CourtSniper reports a name conflict and refuses to modify it.

After upgrading from the earlier direct-HTTP task action, choose **Save Schedule** once to replace that action with the fixed runner. A recognized CourtSniper-managed task is updated in place and does not need to be deleted. Saving preserves its enabled state. If the project is moved or its Python environment is recreated later, save again to refresh the internally recorded interpreter and runner locations.

### 2. Enable or Disable Future Runs

Choose **Enable Schedule** after reviewing the trigger. At the scheduled time, Windows launches the fixed `scheduled_runner.py` entry point. The runner reuses a recognized CourtSniper API if one is already running; otherwise, it starts FastAPI locally, sends the fixed request to `POST http://127.0.0.1:8000/api/run-sniper`, and monitors the existing process manager. If CourtSniper is disarmed, the endpoint rejects the request and no sniper process starts.

When the runner started FastAPI, it keeps that API available while the sniper is active so the existing **Stop Sniper** endpoint remains usable. The frontend is not started automatically; open the dashboard if you need its **Stop Sniper** control during a scheduled run. The runner shuts down only the API process it started after the run succeeds, fails, or is stopped. It never shuts down a FastAPI instance that was already running.

Choose **Disable Future Runs** to prevent later triggers. This does not terminate a sniper process that is already running. Use **Stop Sniper** on the dashboard for an active run.

### 3. Critical Scheduler Settings

The adapter applies these fixed settings when it registers the task:

* **Wake the computer to run this task** so a supported sleeping computer can wake for the trigger.
* **Run only when the user is logged on** so the visible persistent Chrome session can run interactively.
* **Run with highest privileges**; Windows may require FastAPI itself to be started from an elevated terminal when configuring the task.
* **Ignore overlapping task instances**. The API process manager also rejects a second sniper run while one is active.
* **No stored password**. The task uses the current interactive Windows token.
* **Fixed local action**. The task launches only the internally selected Python interpreter and `scheduled_runner.py`; scheduler API requests cannot supply an executable, script, command, task name, or URL.
* **Unexpected-service protection**. If port `8000` responds without the CourtSniper service identity, the runner refuses to replace or invoke that service.

### 4. Status Semantics

`GET /api/scheduler` reports whether the fixed task is installed, recognized as CourtSniper-managed, configured, in sync with the booking target, and enabled. It also returns the next run time, last run time, and Windows last-task result when available.

A last-task result of `0` means the scheduled runner observed a successful process exit. Result `1` is a runner, monitoring, timeout, or local API failure; `2` means the existing ARMED/concurrency guard rejected the run; `3` means the sniper process failed; and `4` means it was stopped. A successful process exit does not independently prove that Messenger accepted the booking message.

If monitoring becomes unavailable or exceeds the fixed two-hour safety window while a run may still be active, the runner reports result `1` and leaves an API it started running rather than risk interrupting the booking. A temporary API is stopped when no run was accepted or after the runner confirms an idle or terminal process state.

CourtSniper provides no API route for arbitrary task management or deletion. It does not expose the task action, Windows account, credentials, or sensitive local filesystem paths.

---

## Sleep Mode Pre-Flight Checklist

Windows Task Scheduler's **Wake the computer to run this task** setting is a wake request, not a guarantee that every laptop firmware and sleep model will resume a desktop program. Check the sleep states supported by the computer before relying on a sleeping machine for a time-sensitive booking:

```powershell
powercfg /a
```

* **Traditional S3 sleep**: A listed `Standby (S3)` state can normally use an enabled wake timer, subject to the laptop firmware and active power plan. Test the complete scheduled workflow on the target computer before relying on it.
* **Modern Standby (S0 Low Power Idle)**: A listed `Standby (S0 Low Power Idle)` state may suspend ordinary desktop programs such as Python and Chrome while the lid is closed. On affected systems, Windows remembers the trigger but CourtSniper does not begin until the user opens the lid or otherwise resumes the interactive desktop. Changing the task to **Run whether user is logged on or not** does not fix this behavior and is incompatible with CourtSniper's interactive persistent Chrome session.
* **No supported S3 state**: If `powercfg /a` says S3 is unavailable because the firmware does not support it, do not use registry overrides to force S3. Use only an explicit Legacy S3 option supplied by the computer's BIOS/UEFI vendor.
* **Reliable Modern Standby configuration**: While plugged in, set **When I close the lid** to **Do nothing**, set system sleep to **Never**, and allow only the display to turn off. Keep the Windows user logged in; locking the session with `Win + L` is allowed. Leave normal sleep enabled on battery unless the battery-life tradeoff is intentional.
* **Power and ventilation**: Leave the laptop connected to AC power on a hard, ventilated surface. Never run it awake with the lid closed inside a bag or another enclosed space.
* **Wake timer verification**: Enable wake timers for the active Windows power plan and, from an elevated PowerShell window, run `powercfg /waketimers` to confirm that Windows has exposed an active timer. An empty result means Windows is not currently reporting a timer even if the task's wake checkbox is selected.
* **Interactive desktop**: Keep **Run only when the user is logged on**. CourtSniper uses the existing Windows token and visible persistent Chrome profile; it must not request, transmit, or store the user's Microsoft account password.

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

All automated Windows scheduler tests use injected command, HTTP, clock, and process implementations. They do not create, update, enable, disable, query, or delete a real Windows task, and they do not start a real API or sniper process. Session-setup tests inject configuration, Playwright, browser, page, Win32 mutex, guard, and process objects; they do not read the private `.env`, create a real mutex or process, launch a real browser, or access the persistent `user_data/` profile.

---

## Project History & Legacy Version (v1.0)

* CourtSniper 1.0 was an automated Python script designed to secure time-critical badminton court bookings via Facebook Messenger.
* It relied on a simple three-file terminal architecture (`config.py`, `setup_session.py`, and `sniper.py`).

---

## License & Liability

This project is licensed under the [MIT License](LICENSE).

This software is provided "AS IS", without warranty of any kind. The authors are not legally liable for any account restrictions triggered by Meta's anti-bot algorithms or missed court reservations.
