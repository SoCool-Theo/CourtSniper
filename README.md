# CourtSniper

CourtSniper is an automated reservation script designed to secure time-critical badminton court bookings the exact second registration opens, all without triggering Meta's automated anti-bot alarms. By separating your manual login authentication from high-speed execution, the script acts like an ultra-fast human already sitting at the keyboard.

## Project Overview

* **The Core Strategy**: CourtSniper bypasses Meta's automated anti-bot algorithms by separating manual login authentication from high-speed execution.
* **The Two-Stage Architecture**: The script uses a persistent local browser session to bypass login screens and Two-Factor Authentication (2FA) prompts on booking day. It combines this pre-authenticated profile with a high-precision microsecond countdown loop that dispatches your customized booking message the exact second registration opens.

---

## Directory Structure

```
courtsniper/
│
├── .venv/                # Isolated Python virtual environment
├── user_data/            # Local directory storing persistent browser sessions
├── src/                  # Core execution scripts
│   ├── config.py         # Stores booking targets, URL, and timestamps
│   ├── setup_session.py  # Script to log in manually and save browser cookies
│   └── sniper.py         # Precision engine that polls the OS clock and fires
├── .env                  # Hidden environment variables (Target URL, Message, Time)
├── .env.example          # Safe template for GitHub
├── .gitignore            # Excludes sensitive data from version control
├── README.md             # Project documentation
└── requirements.txt      # Python dependencies
```

* **`src/` Directory**: Contains the core logic.
* **`config.py`**: Isolates and stores your target configuration variables so you never have to edit core automation logic.
* **`setup_session.py`**: Handles the manual authentication phase to generate and cache your active browser profile.
* **`sniper.py`**: The active precision execution engine that runs on booking day to snipe the court.
* **CRITICAL SECURITY NOTICE**: The `user_data/` directory stores your active, authenticated browser session cookies and tokens. You must keep this folder excluded from version control via `.gitignore`, as uploading it would allow anyone to access your personal Facebook account without needing your password or 2FA.

---

## Installation & Dependencies

### 1. Virtual Environment Setup

Create and activate an isolated Python virtual environment (`.venv`) in your terminal to keep project dependencies cleanly separated from your system Python:

```bash
# Create the virtual environment
python -m venv .venv

# Activate on Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate on Windows (Command Prompt)
.\.venv\Scripts\activate.bat
```

### 2. Package Installation

Install the required Python libraries by running this command in your terminal:

```bash
pip install -r requirements.txt
```

### 3. Browser Driver Installation

Download the mandatory core browser automation drivers needed to establish the Chrome DevTools Protocol pipeline by running:

```bash
playwright install chromium
```

---

## Configuration Setup (`config.py`)

* **Environment Variables**: Copy the safe `.env.example` template file to create your own hidden `.env` file in the project root directory.
* **Target Mapping**: Open `src/config.py` (or your new `.env` file) and configure these three critical target variables:
  * **`TARGET_URL`**: The specific Facebook Messenger chat thread URL for the badminton club.
  * **`BOOKING_MESSAGE`**: Your customized booking message text (e.g., `"Hi, I would like to book badminton court at 4 - 5pm"`).
  * **`TARGET_HOUR`, `TARGET_MINUTE`, `TARGET_SECOND`**: Your target execution timestamp set in 24-hour format (e.g., `8`, `0`, `0` for an 8:00 AM booking).

---

## Manual Authentication Phase (`setup_session.py`)

* **Mid-Week Preparation**: Execute `python src/setup_session.py` in your terminal once during the week prior to your booking day.
* **Session Persistence**: This script launches a visible Google Chrome window, allowing you to manually log into Facebook Messenger and solve any Two-Factor Authentication (2FA) challenges.
* **Caching Cookies**: Once your inbox loads completely, close the browser window to permanently cache your session cookies inside the local `user_data/` folder.

---

## Windows Task Scheduler Automation

### 1. Unattended Execution

Configure Windows Task Scheduler to launch `sniper.py` automatically at **few minutes before the target time to book**. This gives the browser a minute warm-up buffer before registration.

### 2. Absolute System Paths

Because Windows Task Scheduler runs in the background, you must provide absolute system paths for both your Python executable (`python.exe`) and your script directory:

* **Program/script**: `C:\Users\YourName\Desktop\CourtSniper\.venv\Scripts\python.exe`
* **Add arguments**: `src\sniper.py`
* **Start in**: `C:\Users\YourName\Desktop\CourtSniper` *(CRITICAL: This must stay as your root directory, otherwise Python cannot locate your `.env` or `user_data` folders).*

### 3. Critical Scheduler Settings

* **Hardware Alarm Clock**: Under the **Conditions** tab, you must enable the checkbox labeled **"Wake the computer to run this task"** to command your motherboard to physically power on from sleep mode.
* **Security Options**: Under the **General** tab, select **"Run only when user is logged on"** so Windows allows your active user desktop to render the visible Google Chrome UI.

---

## Sleep Mode Pre-Flight Checklist

* **Continuous Power**: Leave your PC or laptop plugged into an AC power outlet overnight. Windows power management policies actively suppress hardware wake timers when running on battery power.
* **Sleep Mode Over Hibernate**: On laptops utilizing Modern Standby (S0 Low Power Idle)—such as ASUS TUF gaming laptops—you **must** use standard Sleep mode rather than Hibernate overnight. Modern laptop firmware physically severs the hardware wake circuit during deep hibernation. Sleep mode keeps a low-power idle state active, preserving RAM and allowing the Windows System Events Broker to reliably trigger the alarm.
* **Power Plan Settings**: Verify that wake timers are strictly enabled inside your Windows Advanced Power Plan settings (`Edit Power Plan -> Change advanced power settings -> Sleep -> Allow wake timers -> Enable`).
* **Lock Screen Rules**: Adjust your Windows sign-in requirements to **Never** require a password when waking from sleep so Playwright can render cleanly without getting blocked by a locked desktop.
* **Laptop Lid Rules**: If you close your laptop screen overnight, set your "When I close the lid" action in Control Panel to **Do nothing** when plugged in. Otherwise, Windows will force the system back to sleep the exact second Task Scheduler attempts to wake it.

---

## License & Liability

This project is licensed under the [MIT License](LICENSE).
