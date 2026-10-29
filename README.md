# CourtSniper 2.0

![Frontend: React + Vite](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-149ECA?style=for-the-badge&logo=react&logoColor=white)
![Backend: FastAPI + Python](https://img.shields.io/badge/Backend-FastAPI%20%2B%20Python-009688?style=for-the-badge&logo=fastapi&logoColor=white)
<br />
![Automation: Playwright + Chrome](https://img.shields.io/badge/Automation-Playwright%20%2B%20Chrome-2EAD33?style=for-the-badge&logo=googlechrome&logoColor=white)
![Scheduler: Windows Task Scheduler](https://img.shields.io/badge/Scheduler-Windows%20Task%20Scheduler-0078D4?style=for-the-badge)

CourtSniper is a local automation application designed to secure time-critical badminton court bookings through Facebook Messenger. It combines a Python automation service with a responsive React dashboard and separates manual login authentication from high-speed execution.

The automation engine uses a persistent local browser session to avoid repeating login and Two-Factor Authentication (2FA) prompts on booking day. A precision countdown coordinates message dispatch with the configured booking time.

---

## Documentation

| Guide | Contents |
| --- | --- |
| [Architecture & Directory Structure](docs/architecture.md) | System design, execution flow, and repository layout. |
| [Local API Contract](docs/local-api-contract.md) | API routes, request constraints, lifecycle states, and errors. |
| [Manual Authentication Phase (`setup_session.py`)](docs/manual-authentication.md) | Manual login, session persistence, and re-authentication. |
| [Windows Task Scheduler Automation](docs/windows-task-scheduler.md) | Schedule configuration, task settings, and run results. |
| [Sleep Mode Pre-Flight Checklist](docs/sleep-mode-checklist.md) | Sleep states, wake timers, and power settings. |

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

### 4. One-Command Local Startup

After installing the backend and frontend dependencies, run the following command from the repository root:

```powershell
.\start-courtsniper.ps1
```

The launcher starts FastAPI and Vite as hidden native Windows processes, waits for both local services to become ready, and opens no network ports beyond `127.0.0.1`. It records the exact process IDs, executable paths, and fixed command identities in the ignored `.run/` directory. Runtime logs are also written there without moving or copying `.env` or `user_data/`.

Open the dashboard at `http://127.0.0.1:5173`. To safely stop only the processes created by the launcher, run:

```powershell
.\stop-courtsniper.ps1
```

The stop script validates each recorded PID against the expected Python or Node executable and command before terminating it. A backend or frontend process started manually is reused when recognized but is not claimed or stopped by the launcher.

---

## Configuration Setup (`.env`)

Copy the safe `.env.example` template to create a private `.env` file in the `backend/` directory. Configure these target variables in the new `.env` file:

* **`TARGET_URL`**: The specific Facebook Messenger chat thread URL for the badminton club.
* **`BOOKING_MESSAGE`**: Your customized booking message text (e.g., "Hi, I would like to book badminton court at 4 - 5pm").
* **`TARGET_HOUR`, `TARGET_MINUTE`, `TARGET_SECOND`**: Your target execution timestamp in 24-hour format (for example, `8`, `0`, `0` for 8:00 AM).
* **`STATUS`**: Set this to `"ARMED"` or `"DISARMED"` to authorize or reject every request to `POST /api/run-sniper`, including requests made by the Windows task.

Never commit `.env`, `user_data/`, browser profiles, cookies, tokens, or account credentials.

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
