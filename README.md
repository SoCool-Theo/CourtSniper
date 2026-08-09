# CourtSniper 2.0

CourtSniper is a local automation application designed to secure time-critical badminton court bookings through Facebook Messenger. It combines a Python automation service with a responsive React dashboard and separates manual login authentication from high-speed execution.

The automation engine uses a persistent local browser session to avoid repeating login and Two-Factor Authentication (2FA) prompts on booking day. A precision countdown coordinates message dispatch with the configured booking time.

---

## Architecture & Directory Structure

The project uses a monorepo setup (`backend/` and `frontend/`). The React frontend provides the control dashboard, while the FastAPI and Python backend manage configuration, authentication setup, and browser automation.

```text
CourtSniper/
│
├── backend/                     # Python Automation & FastAPI Service
│   ├── .venv/                   # Isolated Python virtual environment
│   ├── user_data/               # Cached Facebook/Chrome session cookies (hidden/ignored)
│   ├── src/                     
│   │   ├── api.py               # FastAPI backend server (control wrapper)
│   │   ├── config.py            # Loads configuration variables from .env
│   │   ├── setup_session.py     # Manual login script for caching session cookies
│   │   └── sniper.py            # High-precision Playwright execution engine
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

The **Start Sniper**, **Test Run**, and scheduler controls remain disabled until dedicated backend endpoints are implemented. The frontend does not execute local Python files directly.

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
* **`STATUS`**: Set this to `"ARMED"` or `"DISARMED"` to remotely control whether the Task Scheduler script actually fires.

Never commit `.env`, `user_data/`, browser profiles, cookies, tokens, or account credentials.

---

## Frontend API Contract

The current frontend uses the following API routes:

| Method | Route | Purpose |
| --- | --- | --- |
| `GET` | `/api/status` | Check whether the backend is available. |
| `GET` | `/api/config` | Load the current booking configuration. |
| `POST` | `/api/config` | Save booking configuration and armed status. |
| `POST` | `/api/run-setup` | Request the manual login/session setup browser. |

Running the automation from the dashboard is planned for a separate change. It should use a controlled endpoint such as `POST /api/run-sniper`, execute only the predefined automation script, reject concurrent runs, and return a clear run status. It must never accept arbitrary commands or script paths from the browser.

---

## Manual Authentication Phase (`setup_session.py`)

* **Mid-Week Preparation**: Execute `python src/setup_session.py` in your terminal once during the week prior to your booking day. Make sure you are in the `backend/` directory.
* **Session Persistence**: This script launches a visible Google Chrome window, allowing you to manually log into Facebook Messenger and solve any Two-Factor Authentication (2FA) challenges.
* **Caching Cookies**: Once your inbox loads completely, close the browser window to permanently cache your session cookies inside the local `user_data/` folder.

---

## Windows Task Scheduler Automation

### 1. Unattended "Cheat Code" Execution

Configure Windows Task Scheduler to run `sniper.py` automatically **every single day** at 7:55 AM, giving the browser a 5-minute warm-up buffer before registration opens. Because of the `STATUS` variable in your `.env` file, the script will instantly close itself if disarmed via the Web UI, saving you from fighting Windows Administrator permissions.

### 2. Absolute System Paths

Task Scheduler runs in the background and requires absolute system paths for both their Python executable (`python.exe`) and their script directory:

* **Program/script**: `C:\Users\YourName\Desktop\CourtSniper\backend\.venv\Scripts\python.exe`
* **Add arguments**: `src\sniper.py`
* **Start in**: `C:\Users\YourName\Desktop\CourtSniper\backend`

### 3. Critical Scheduler Settings

* **Hardware Alarm Clock**: Under the Conditions tab, you must enable the checkbox labeled "Wake the computer to run this task" to command your motherboard to physically power on from sleep mode.
* **Security Options**: Under the General tab, select "Run only when user is logged on" so Windows allows your active user desktop to render the visible Google Chrome UI.

---

## Sleep Mode Pre-Flight Checklist

* **Continuous Power**: Leave your PC or laptop plugged into an AC power outlet overnight.
* **Sleep Mode Over Hibernate**: On laptops utilizing Modern Standby (S0 Low Power Idle)—such as ASUS TUF gaming laptops—you must use standard Sleep mode rather than Hibernate overnight.
* **Power Plan Settings**: Verify that wake timers are strictly enabled inside your Windows Advanced Power Plan settings.
* **Lock Screen Rules**: Adjust your Windows sign-in requirements to Never require a password when waking from sleep so Playwright can render cleanly without getting blocked by a locked desktop.

---

## Project History & Legacy Version (v1.0)

* CourtSniper 1.0 was an automated Python script designed to secure time-critical badminton court bookings via Facebook Messenger.
* It relied on a simple three-file terminal architecture (`config.py`, `setup_session.py`, and `sniper.py`).

---

## License & Liability

This project is licensed under the [MIT License](LICENSE).

This software is provided "AS IS", without warranty of any kind. The authors are not legally liable for any account restrictions triggered by Meta's anti-bot algorithms or missed court reservations.
