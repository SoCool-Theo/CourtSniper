import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import config

import sys
from dotenv import load_dotenv

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ENV_PATH = os.path.join(ROOT_DIR, ".env")

load_dotenv(dotenv_path=ENV_PATH)

# --- THE KILL SWITCH ---
# If the Web UI set the status to anything other than "ARMED", shut down immediately.
if os.getenv("STATUS") != "ARMED":
    print("CourtSniper is DISARMED. Going back to sleep.")
    sys.exit(0)
# -----------------------

def run_sniper():
    print("Initializing CourtSniper...")

    with sync_playwright() as p:
        script_dir = os.path.dirname(os.path.abspath(__file__))

        user_data_path = os.path.join(script_dir, "../..", "user_data")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 720}
        )

        page = browser.new_page()
        print(f"Navigating to chat: {config.TARGET_URL}")
        page.goto(config.TARGET_URL)

        # Target the Facebook Messenger input box using functional accessibility roles
        print("Waiting for chat interface and text box to render...")
        input_box = page.get_by_role("textbox").first
        input_box.wait_for(state="visible", timeout=30000)
        print("Chat loaded! Armed and waiting for target timestamp...")

        # --- PRECISION TIMING ENGINE ---
        while True:
            now = datetime.now()

            # Check if we have reached or passed the target time (8:00:00 AM)
            if (now.hour == config.TARGET_HOUR and
                    now.minute == config.TARGET_MINUTE and
                    now.second >= config.TARGET_SECOND):
                break

            # Calculate remaining time to decide how aggressively to poll
            target_time = now.replace(
                hour=config.TARGET_HOUR,
                minute=config.TARGET_MINUTE,
                second=config.TARGET_SECOND,
                microsecond=0
            )
            seconds_left = (target_time - now).total_seconds()

            # If more than 10 seconds left, sleep briefly to save CPU
            # During the last 10 seconds, enter a tight polling loop without sleeping
            if seconds_left > 10:
                time.sleep(0.5)
            elif seconds_left > 1:
                time.sleep(0.01)

        # --- EXECUTION STRIKE ---
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] Firing booking message!")

        # Focus the box, insert text, and hit Enter instantly
        input_box.focus()
        input_box.fill(config.BOOKING_MESSAGE)
        page.keyboard.press("Enter")

        print("Message dispatched successfully! Good luck on the court.")

        # Leave the browser open for 15 seconds so you can visually verify the message sent
        time.sleep(15)
        browser.close()


if __name__ == "__main__":
    run_sniper()