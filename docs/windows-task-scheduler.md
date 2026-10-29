# Windows Task Scheduler Automation

[Back to README](../README.md)

## 1. Configure the Schedule

Start FastAPI and open the Scheduler panel in the dashboard. Select one or more booking weekdays, enter the warm-up period in minutes, and choose **Save Schedule**. The default warm-up is five minutes and the supported range is 0 through 1440 minutes. The booking target continues to come from `TARGET_HOUR`, `TARGET_MINUTE`, and `TARGET_SECOND`; the Scheduler panel does not maintain a second target-time setting.

Saving creates or updates only the Windows task named `CourtSniper`. A new task is installed disabled so its calculated trigger can be reviewed before **Enable Schedule** is selected. If an unrelated task already owns that exact name, CourtSniper reports a name conflict and refuses to modify it.

After upgrading from the earlier direct-HTTP task action, choose **Save Schedule** once to replace that action with the fixed runner. A recognized CourtSniper-managed task is updated in place and does not need to be deleted. Saving preserves its enabled state. If the project is moved or its Python environment is recreated later, save again to refresh the internally recorded interpreter and runner locations.

## 2. Enable or Disable Future Runs

Choose **Enable Schedule** after reviewing the trigger. At the scheduled time, Windows launches the fixed `scheduled_runner.py` entry point. The runner reuses a recognized CourtSniper API if one is already running; otherwise, it starts FastAPI locally, sends the fixed request to `POST http://127.0.0.1:8000/api/run-sniper`, and monitors the existing process manager. If CourtSniper is disarmed, the endpoint rejects the request and no sniper process starts.

When the runner started FastAPI, it keeps that API available while the sniper is active so the existing **Stop Sniper** endpoint remains usable. The frontend is not started automatically; open the dashboard if you need its **Stop Sniper** control during a scheduled run. The runner shuts down only the API process it started after the run succeeds, fails, or is stopped. It never shuts down a FastAPI instance that was already running.

Choose **Disable Future Runs** to prevent later triggers. This does not terminate a sniper process that is already running. Use **Stop Sniper** on the dashboard for an active run.

## 3. Critical Scheduler Settings

The adapter applies these fixed settings when it registers the task:

* **Wake the computer to run this task** so a supported sleeping computer can wake for the trigger.
* **Run only when the user is logged on** so the visible persistent Chrome session can run interactively.
* **Run with highest privileges**; Windows may require FastAPI itself to be started from an elevated terminal when configuring the task.
* **Ignore overlapping task instances**. The API process manager also rejects a second sniper run while one is active.
* **No stored password**. The task uses the current interactive Windows token.
* **Fixed local action**. The task launches only the internally selected Python interpreter and `scheduled_runner.py`; scheduler API requests cannot supply an executable, script, command, task name, or URL.
* **Unexpected-service protection**. If port `8000` responds without the CourtSniper service identity, the runner refuses to replace or invoke that service.

## 4. Status Semantics

`GET /api/scheduler` reports whether the fixed task is installed, recognized as CourtSniper-managed, configured, in sync with the booking target, and enabled. It also returns the next run time, last run time, and Windows last-task result when available.

A last-task result of `0` means the scheduled runner observed a successful process exit. Result `1` is a runner, monitoring, timeout, or local API failure; `2` means the existing ARMED/concurrency guard rejected the run; `3` means the sniper process failed; and `4` means it was stopped. A successful process exit does not independently prove that Messenger accepted the booking message.

If monitoring becomes unavailable or exceeds the fixed two-hour safety window while a run may still be active, the runner reports result `1` and leaves an API it started running rather than risk interrupting the booking. A temporary API is stopped when no run was accepted or after the runner confirms an idle or terminal process state.

CourtSniper provides no API route for arbitrary task management or deletion. It does not expose the task action, Windows account, credentials, or sensitive local filesystem paths.
