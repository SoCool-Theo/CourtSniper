# Sleep Mode Pre-Flight Checklist

[Back to README](../README.md)

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
