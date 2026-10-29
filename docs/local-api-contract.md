# Local API Contract

[Back to README](../README.md)

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
