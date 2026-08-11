import { useState } from 'react';
import {
  CalendarCheck,
  CalendarDays,
  CheckSquare2,
  Clock3,
  Power,
  PowerOff,
  Save,
  ShieldAlert,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import useCourtSniper from '../context/useCourtSniper';

const weekdays = [
  { value: 'MONDAY', short: 'MON' },
  { value: 'TUESDAY', short: 'TUE' },
  { value: 'WEDNESDAY', short: 'WED' },
  { value: 'THURSDAY', short: 'THU' },
  { value: 'FRIDAY', short: 'FRI' },
  { value: 'SATURDAY', short: 'SAT' },
  { value: 'SUNDAY', short: 'SUN' },
];

const weekdayIndex = new Map(weekdays.map((weekday, index) => [weekday.value, index]));

const requirements = [
  'Wake the computer to run this task',
  'Run only when user is logged on',
  'Run with highest privileges',
];

function formatTime(value) {
  return value || 'Not configured';
}

function formatDateTime(value) {
  if (!value) return 'Not available';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return 'Not available';
  return date.toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

function getTargetSeconds(config) {
  const hour = Number(config.TARGET_HOUR);
  const minute = Number(config.TARGET_MINUTE);
  const second = Number(config.TARGET_SECOND);
  if (
    !Number.isInteger(hour) || hour < 0 || hour > 23
    || !Number.isInteger(minute) || minute < 0 || minute > 59
    || !Number.isInteger(second) || second < 0 || second > 59
  ) return null;
  return (hour * 3600) + (minute * 60) + second;
}

function formatSeconds(seconds) {
  const normalized = ((seconds % 86400) + 86400) % 86400;
  const hour = Math.floor(normalized / 3600);
  const minute = Math.floor((normalized % 3600) / 60);
  const second = normalized % 60;
  return [hour, minute, second]
    .map((value) => String(value).padStart(2, '0'))
    .join(':');
}

function getTriggerPreview(config, selectedWeekdays, warmupMinutes) {
  const targetSeconds = getTargetSeconds(config);
  const warmup = Number(warmupMinutes);
  if (
    targetSeconds === null
    || !Number.isInteger(warmup)
    || warmup < 0
    || warmup > 1440
  ) return null;

  const rawTriggerSeconds = targetSeconds - (warmup * 60);
  const dayShift = Math.floor(rawTriggerSeconds / 86400);
  const triggerWeekdays = [...new Set(selectedWeekdays.map((weekday) => {
    const index = weekdayIndex.get(weekday);
    return weekdays[(index + dayShift + 7) % 7].value;
  }))].sort((left, right) => weekdayIndex.get(left) - weekdayIndex.get(right));

  return {
    time: formatSeconds(rawTriggerSeconds),
    weekdays: triggerWeekdays,
  };
}

function schedulerPresentation(scheduler, loading, error) {
  if (loading) return { label: 'Checking', tone: 'warning' };
  if (error) return { label: 'Unavailable', tone: 'danger' };
  if (!scheduler.installed) return { label: 'Not Installed', tone: 'warning' };
  if (!scheduler.managed) return { label: 'Name Conflict', tone: 'danger' };
  if (!scheduler.configured) return { label: 'Needs Configuration', tone: 'warning' };
  if (scheduler.configuration_in_sync === false) return { label: 'Out of Sync', tone: 'danger' };
  if (scheduler.enabled) return { label: 'Enabled', tone: 'success' };
  return { label: 'Disabled', tone: 'neutral' };
}

const toneClasses = {
  success: 'text-court-green',
  danger: 'text-court-danger',
  warning: 'text-court-warning',
  neutral: 'text-court-cyan',
};

const dotClasses = {
  success: 'bg-court-green shadow-[0_0_8px_rgba(99,255,0,0.75)]',
  danger: 'bg-court-danger shadow-[0_0_8px_rgba(255,55,72,0.7)]',
  warning: 'bg-court-warning shadow-[0_0_8px_rgba(255,213,31,0.7)]',
  neutral: 'bg-court-cyan shadow-[0_0_8px_rgba(0,231,255,0.7)]',
};

export default function Scheduler() {
  const {
    config,
    scheduler,
    schedulerError,
    isLoadingScheduler,
    isSavingScheduler,
    isTogglingScheduler,
    configureSchedule,
    enableSchedule,
    disableSchedule,
  } = useCourtSniper();
  const [draft, setDraft] = useState(null);
  const [feedback, setFeedback] = useState('');
  const [feedbackTone, setFeedbackTone] = useState('success');
  const selectedWeekdays = draft?.weekdays
    ?? scheduler.configuration?.weekdays
    ?? [];
  const warmupMinutes = draft?.warmupMinutes
    ?? String(scheduler.configuration?.warmup_minutes ?? 5);

  const targetSeconds = getTargetSeconds(config);
  const targetTime = targetSeconds === null ? null : formatSeconds(targetSeconds);
  const preview = getTriggerPreview(config, selectedWeekdays, warmupMinutes);
  const presentation = schedulerPresentation(
    scheduler,
    isLoadingScheduler,
    schedulerError,
  );
  const warmup = Number(warmupMinutes);
  const validWarmup = Number.isInteger(warmup) && warmup >= 0 && warmup <= 1440;
  const canManage = !scheduler.installed || scheduler.managed;
  const canSave = canManage
    && !schedulerError
    && targetTime !== null
    && selectedWeekdays.length > 0
    && validWarmup
    && !isLoadingScheduler
    && !isSavingScheduler
    && !isTogglingScheduler;
  const canEnable = scheduler.installed
    && scheduler.managed
    && scheduler.configured
    && scheduler.configuration_in_sync === true
    && !schedulerError
    && !scheduler.enabled
    && !isLoadingScheduler
    && !isSavingScheduler
    && !isTogglingScheduler;
  const canDisable = scheduler.installed
    && scheduler.managed
    && scheduler.enabled
    && !schedulerError
    && !isLoadingScheduler
    && !isSavingScheduler
    && !isTogglingScheduler;

  const toggleWeekday = (weekday) => {
    setDraft({
      weekdays: selectedWeekdays.includes(weekday)
        ? selectedWeekdays.filter((value) => value !== weekday)
        : [...selectedWeekdays, weekday].sort(
          (left, right) => weekdayIndex.get(left) - weekdayIndex.get(right),
        ),
      warmupMinutes,
    });
    setFeedback('');
  };

  const handleSave = async () => {
    setFeedback('');
    try {
      const result = await configureSchedule({
        weekdays: selectedWeekdays,
        warmup_minutes: warmup,
      });
      setDraft(null);
      setFeedbackTone('success');
      setFeedback(result?.message || 'CourtSniper schedule configured.');
    } catch (error) {
      setFeedbackTone('danger');
      setFeedback(error.message || 'Unable to configure the schedule.');
    }
  };

  const handleToggle = async () => {
    setFeedback('');
    try {
      const result = scheduler.enabled
        ? await disableSchedule()
        : await enableSchedule();
      setFeedbackTone(scheduler.enabled ? 'warning' : 'success');
      setFeedback(result?.message || `CourtSniper schedule ${scheduler.enabled ? 'disabled' : 'enabled'}.`);
    } catch (error) {
      setFeedbackTone('danger');
      setFeedback(error.message || 'Unable to change scheduler state.');
    }
  };

  const displayedTrigger = preview?.time
    || scheduler.configuration?.trigger_time
    || null;
  const displayedTriggerWeekdays = preview?.weekdays
    || scheduler.configuration?.trigger_weekdays
    || [];

  return (
    <div className="tactical-panel">
      <SectionHeader icon={CalendarDays} title="Scheduler" />

      <div className="space-y-5 p-4 sm:p-5">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.2fr_0.85fr] lg:items-center lg:gap-0">
          <dl className="grid grid-cols-[auto_1fr] gap-x-7 gap-y-3 lg:pr-7">
            <dt className="text-[0.65rem] font-bold text-court-text/75">Status</dt>
            <dd className={`flex items-center gap-2 text-[0.68rem] font-bold uppercase tracking-wide ${toneClasses[presentation.tone]}`}>
              <span className={`h-2 w-2 rounded-full ${dotClasses[presentation.tone]}`} />
              {presentation.label}
            </dd>
            <dt className="text-[0.65rem] font-bold text-court-text/75">Next Execution</dt>
            <dd className="text-xs font-medium leading-snug text-court-text">
              {scheduler.enabled ? formatDateTime(scheduler.next_run_time) : 'No future run enabled'}
            </dd>
            <dt className="text-[0.65rem] font-bold text-court-text/75">Last Trigger</dt>
            <dd className="text-xs font-medium leading-snug text-court-text">
              {formatDateTime(scheduler.last_run_time)}
              <span className="block text-[0.65rem] text-court-muted">
                Result: {scheduler.last_run_result ?? 'Not available'}
              </span>
            </dd>
            <dt className="text-[0.65rem] font-bold text-court-text/75">Trigger</dt>
            <dd className="font-mono text-xs font-medium text-court-text">
              {formatTime(displayedTrigger)}
              {displayedTriggerWeekdays.length > 0 && (
                <span className="block font-sans text-[0.65rem] text-court-muted">
                  {displayedTriggerWeekdays.map((day) => day.slice(0, 3)).join(', ')}
                </span>
              )}
            </dd>
          </dl>

          <div className="space-y-3 border-court-line-soft/70 lg:border-x lg:px-7">
            {requirements.map((requirement) => (
              <div key={requirement} className="flex items-center gap-3 text-xs font-medium text-court-text/90">
                <CheckSquare2 aria-hidden="true" className="h-4 w-4 shrink-0 text-court-cyan" />
                <span>{requirement}</span>
              </div>
            ))}
          </div>

          <div className="space-y-3 lg:pl-7">
            <button
              type="button"
              onClick={handleToggle}
              disabled={scheduler.enabled ? !canDisable : !canEnable}
              className={`tactical-button min-h-11 w-full px-4 disabled:cursor-not-allowed disabled:opacity-50 ${
                scheduler.enabled
                  ? 'border-court-danger bg-court-danger/10 text-court-danger'
                  : 'tactical-button--primary'
              }`}
            >
              {scheduler.enabled
                ? <PowerOff aria-hidden="true" className="h-4 w-4" />
                : <Power aria-hidden="true" className="h-4 w-4" />}
              {isTogglingScheduler
                ? 'Updating...'
                : scheduler.enabled
                  ? 'Disable Future Runs'
                  : 'Enable Schedule'}
            </button>
            <p className="text-center text-[0.62rem] font-medium leading-relaxed text-court-muted">
              {scheduler.enabled
                ? 'Disabling does not stop an active sniper run.'
                : scheduler.configuration_in_sync === false
                  ? 'Save the schedule again for the current booking target.'
                  : scheduler.configured
                    ? 'The saved schedule is ready to enable.'
                    : 'Save a valid schedule before enabling future runs.'}
            </p>
          </div>
        </div>

        <div className="grid gap-5 rounded-md border border-court-line-soft/75 bg-court-inset/40 p-4 lg:grid-cols-[1.3fr_0.7fr]">
          <fieldset disabled={!canManage || isSavingScheduler || isTogglingScheduler}>
            <legend className="tactical-label mb-3">Booking Weekdays</legend>
            <div className="grid grid-cols-4 gap-2 sm:grid-cols-7">
              {weekdays.map((weekday) => {
                const selected = selectedWeekdays.includes(weekday.value);
                return (
                  <button
                    key={weekday.value}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => toggleWeekday(weekday.value)}
                    className={`min-h-10 rounded border px-2 font-mono text-[0.68rem] font-bold transition ${
                      selected
                        ? 'border-court-green bg-court-green/15 text-court-green shadow-green-strong'
                        : 'border-court-line bg-court-void/45 text-court-muted hover:border-court-cyan hover:text-court-cyan'
                    }`}
                  >
                    {weekday.short}
                  </button>
                );
              })}
            </div>
            {selectedWeekdays.length === 0 && (
              <p className="mt-2 text-[0.65rem] font-medium text-court-warning">
                Select at least one booking weekday.
              </p>
            )}
          </fieldset>

          <div>
            <label htmlFor="scheduler-warmup" className="tactical-label mb-2 block">
              Warm-up Period
            </label>
            <div className="flex items-center gap-3">
              <input
                id="scheduler-warmup"
                type="number"
                min="0"
                max="1440"
                step="1"
                value={warmupMinutes}
                onChange={(event) => {
                  setDraft({
                    weekdays: selectedWeekdays,
                    warmupMinutes: event.target.value,
                  });
                  setFeedback('');
                }}
                disabled={!canManage || isSavingScheduler || isTogglingScheduler}
                className="tactical-input h-10 w-full px-3 font-mono text-sm"
              />
              <span className="text-xs font-medium text-court-muted">minutes</span>
            </div>
            {!validWarmup && (
              <p className="mt-2 text-[0.65rem] font-medium text-court-danger">
                Enter a whole number from 0 to 1440.
              </p>
            )}
          </div>

          <div className="grid gap-3 rounded border border-court-line-soft/70 bg-court-void/35 p-3 sm:grid-cols-2 lg:col-span-2">
            <div className="flex items-center gap-3">
              <Clock3 aria-hidden="true" className="h-4 w-4 text-court-cyan" />
              <div>
                <p className="text-[0.6rem] font-bold uppercase tracking-label text-court-muted">Booking Target</p>
                <p className="mt-1 font-mono text-xs text-court-text">{targetTime || 'Invalid or missing'}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <CalendarCheck aria-hidden="true" className="h-4 w-4 text-court-green" />
              <div>
                <p className="text-[0.6rem] font-bold uppercase tracking-label text-court-muted">Calculated Trigger</p>
                <p className="mt-1 font-mono text-xs text-court-text">{preview?.time || 'Complete the schedule'}</p>
              </div>
            </div>
          </div>

          <div className="flex justify-center lg:col-span-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={!canSave}
              className="tactical-button min-h-10 w-full max-w-[24rem] px-6 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Save aria-hidden="true" className="h-4 w-4" />
              {isSavingScheduler ? 'Saving Schedule...' : 'Save Schedule'}
            </button>
          </div>
        </div>

        {(scheduler.configuration_in_sync === false || !scheduler.managed || schedulerError) && (
          <div className="flex items-start gap-3 rounded-md border border-court-danger/45 bg-court-danger/5 px-4 py-3">
            <ShieldAlert aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-court-danger" />
            <p className="text-[0.7rem] font-medium leading-relaxed text-court-text/80">
              {schedulerError
                || (!scheduler.managed && scheduler.installed
                  ? 'A different Windows task already uses the CourtSniper name. It will not be modified.'
                  : 'The booking target changed. Save the schedule again before enabling future runs.')}
            </p>
          </div>
        )}

        <div className="flex items-start gap-3 rounded-md border border-court-warning/45 bg-court-inset/75 px-4 py-3">
          <CalendarCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-court-cyan" />
          <p className="text-[0.7rem] font-medium leading-relaxed text-court-text/80">
            The Windows task triggers the local FastAPI service. CourtSniper still starts only when
            execution status is ARMED. Use Stop Sniper for an active run; disabling here affects only
            future triggers.
          </p>
        </div>

        {(feedback || schedulerError) && (
          <p className={`text-center text-xs font-semibold ${toneClasses[schedulerError ? 'danger' : feedbackTone]}`}>
            {schedulerError || feedback}
          </p>
        )}
      </div>
    </div>
  );
}
