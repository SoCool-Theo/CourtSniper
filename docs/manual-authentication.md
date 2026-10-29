# Manual Authentication Phase (`setup_session.py`)

[Back to README](../README.md)

* **Mid-Week Preparation**: Choose **Open Login Browser** in the Session panel, or execute `python src/setup_session.py` from the `backend/` directory, once during the week prior to your booking day.
* **Configured Destination**: The script reads the saved `TARGET_URL` internally and opens that booking conversation when it is an HTTPS URL on `facebook.com`, `messenger.com`, or one of their subdomains.
* **Validation and Fallback**: URLs using another scheme or host, malformed URLs, and URLs containing embedded username or password credentials are rejected. A missing or rejected value falls back to `https://www.facebook.com/messages/`.
* **Private Logging**: Console messages identify whether the configured conversation or fallback inbox is being used without printing the complete conversation URL.
* **Session Persistence**: The script launches a visible Google Chrome window with the existing persistent profile, allowing you to manually log into Facebook Messenger and solve any Two-Factor Authentication (2FA) challenges.
* **Single Setup Window**: Repeated button clicks, simultaneous API requests, API restarts, and manual script launches reuse or defer to the active setup window instead of opening the persistent profile twice.
* **Completion and Cleanup**: Close the login browser after the configured conversation or fallback inbox loads. Closing Chrome finishes setup immediately; otherwise, the window closes after five minutes. The named mutex is released after normal completion, interruption, or failure, and Windows releases it automatically if the setup process crashes.
* **Caching Cookies and Re-authentication**: The persistent profile retains the Facebook login inside the local `user_data/` folder, so setup does not run again automatically. Use **Open Login Browser** again only when you intentionally need to inspect the conversation or re-authenticate after Facebook invalidates the session.
