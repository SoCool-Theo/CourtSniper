import time
import os
from playwright.sync_api import sync_playwright

def create_persistent_session():
    print("Launching Google Chrome to save your Facebook login...")
    with sync_playwright() as p:

        script_dir = os.path.dirname(os.path.abspath(__file__))
        backend_dir = os.path.dirname(script_dir)
        user_data_path = os.path.join(backend_dir, "user_data")

        browser = p.chromium.launch_persistent_context(
            user_data_dir=user_data_path,
            channel="chrome",
            headless=False,
            viewport={"width": 1280, "height": 720}
        )

        page = browser.new_page()
        page.goto("https://www.facebook.com/messages/")

        print("\n--- ACTION REQUIRED ---")
        print("1. Log into your Facebook account in the browser window.")
        print("2. Handle any Two-Factor Authentication (2FA) prompts.")
        print(
            "3. Once you can see your Messenger inbox, return to this terminal and press Ctrl+C, or simply close the browser window.")

        # Keep the script open for 5 minutes to give you plenty of time to log in
        time.sleep(300)
        browser.close()


if __name__ == "__main__":
    create_persistent_session()