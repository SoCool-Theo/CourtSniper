# CourtSniper 2.0

CourtSniper is an automated Python script designed to secure time-critical badminton court bookings via Facebook Messenger. It separates manual login authentication from high-speed execution to avoid triggering Meta's automated anti-bot alarms. 

The script uses a persistent local browser session to bypass login screens and Two-Factor Authentication (2FA) prompts on booking day, combined with a high-precision microsecond countdown loop that dispatches your message the exact second registration opens.

---

## Architecture & Directory Structure

The project uses a monorepo setup (`backend/` and `frontend/`). The React frontend provides a Tailscale-accessible Web UI, while the Python backend handles the heavy lifting.

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
│   ├── index.html               # Main HTML entry page
│   ├── package.json             # Node.js dependencies
│   └── vite.config.js           # Vite server configuration
│
├── LICENSE                      # Standalone MIT License file
└── README.md                    # Main project documentation manual

```

* **`backend/src/` Directory**: Contains the core logic.
* **`config.py`**: Isolates and stores your target configuration variables so you never have to edit core automation logic.
* **`setup_session.py`**: Handles the manual authentication phase to generate and cache your active browser profile.
* **`sniper.py`**: The active precision execution engine that runs on booking day to snipe the court.
* **CRITICAL SECURITY NOTICE**: The `user_data/` directory stores your active, authenticated browser session cookies and tokens. You must keep this folder excluded from version control via `.gitignore`, as uploading it would allow anyone to access your personal Facebook account without needing your password or 2FA.

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

---

## Configuration Setup (`.env`)

Copy the safe `.env.example` template file to create your own hidden `.env` file in the `backend/` directory. Open `config.py` (or your new `.env` file) and configure these critical target variables:

* **`TARGET_URL`**: The specific Facebook Messenger chat thread URL for the badminton club.
* **`BOOKING_MESSAGE`**: Your customized booking message text (e.g., "Hi, I would like to book badminton court at 4 - 5pm").
* **`TARGET_HOUR`, `TARGET_MINUTE`, `TARGET_SECOND**`: Your target execution timestamp set in 24-hour format (e.g., 8, 0, 0 for an 8:00 AM booking).
* **`STATUS`**: Set this to `"ARMED"` or `"DISARMED"` to remotely control whether the Task Scheduler script actually fires.

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