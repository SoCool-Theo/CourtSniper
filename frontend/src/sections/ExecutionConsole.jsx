import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Crosshair,
  LoaderCircle,
  TerminalSquare,
} from 'lucide-react';
import { assetUrl } from '../assets';
import SectionHeader from '../components/SectionHeader';
import useCourtSniper from '../context/useCourtSniper';

function formatTimestamp(timestamp) {
  if (!timestamp) return '--:--:--.---';

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '--:--:--.---';

  return date.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    fractionalSecondDigits: 3,
  });
}

function getRunLogs(run) {
  if (run.state === 'running') {
    return [
      { time: formatTimestamp(run.started_at), message: `CourtSniper process ${run.pid ?? ''} started.` },
      { time: formatTimestamp(run.started_at), message: 'Automation is running. Waiting for completion...', tone: 'success' },
    ];
  }

  if (run.state === 'succeeded') {
    return [
      { time: formatTimestamp(run.started_at), message: `CourtSniper process ${run.pid ?? ''} started.` },
      { time: formatTimestamp(run.finished_at), message: 'CourtSniper process completed successfully.', tone: 'strong', checked: true },
    ];
  }

  if (run.state === 'failed') {
    return [
      { time: formatTimestamp(run.started_at), message: `CourtSniper process ${run.pid ?? ''} started.` },
      { time: formatTimestamp(run.finished_at), message: `Process failed with exit code ${run.exit_code ?? 'unknown'}.`, tone: 'danger' },
    ];
  }

  return [
    { time: '--:--:--.---', message: 'No sniper run has been started in this API session.' },
  ];
}

function ConsoleLog({ log }) {
  const messageTone = log.tone === 'strong'
    ? 'font-bold text-court-green'
    : log.tone === 'success'
      ? 'text-court-green'
      : log.tone === 'danger'
        ? 'text-court-danger'
      : 'text-court-text/80';

  return (
    <div className="grid grid-cols-1 gap-0 leading-[1.55] sm:grid-cols-[6.4rem_minmax(0,1fr)] sm:gap-3">
      <span className="font-semibold text-court-cyan">[{log.time}]</span>
      <span className={`min-w-0 ${messageTone}`}>
        {log.message}
        {log.checked && (
          <span className="ml-2 inline-flex h-4 w-4 translate-y-0.5 items-center justify-center rounded-sm bg-court-green text-court-void">
            <Check aria-hidden="true" className="h-3 w-3" strokeWidth={3} />
          </span>
        )}
      </span>
    </div>
  );
}

function RunStatePanel({ state }) {
  const stateContent = {
    idle: {
      icon: Crosshair,
      title: 'Standing By',
      message: 'Arm the system and start a run when ready.',
      tone: 'text-court-cyan',
    },
    running: {
      icon: LoaderCircle,
      title: 'Targeting',
      message: 'CourtSniper automation is currently running.',
      tone: 'text-court-cyan',
    },
    succeeded: {
      icon: CheckCircle2,
      title: 'Run Complete',
      message: 'The automation process exited successfully.',
      tone: 'text-court-green',
    },
    failed: {
      icon: AlertTriangle,
      title: 'Run Failed',
      message: 'Review the backend terminal for execution details.',
      tone: 'text-court-danger',
    },
  };
  const content = stateContent[state] || stateContent.idle;
  const StateIcon = content.icon;

  return (
    <div className="relative flex min-h-[18rem] flex-col items-center justify-center overflow-hidden rounded-md border border-court-line-soft bg-[radial-gradient(circle_at_center,rgba(0,154,190,0.24),rgba(1,18,8,0.96)_65%)] px-5 py-4 text-center">
      <img
        src={assetUrl('shuttlecock-hit')}
        alt=""
        className={`relative h-36 w-full shrink-0 object-contain ${state === 'idle' ? 'opacity-35' : ''}`}
      />

      <h3 className={`relative mt-1 text-3xl font-bold uppercase tracking-tactical sm:text-4xl ${content.tone}`}>
        {content.title}
      </h3>
      <p className={`relative mt-2 text-sm font-semibold ${content.tone}`}>
        {content.message}
      </p>
      <StateIcon
        aria-hidden="true"
        className={`relative mt-3 h-8 w-8 ${content.tone} ${state === 'running' ? 'animate-spin' : ''}`}
      />
    </div>
  );
}

export default function ExecutionConsole() {
  const { sniperRun } = useCourtSniper();
  const logs = getRunLogs(sniperRun);

  return (
    <div className="tactical-panel">
      <SectionHeader icon={TerminalSquare} title="Execution Console" />

      <div className="grid gap-4 p-4 lg:grid-cols-[1.55fr_0.75fr]">
        <div className="min-h-[18rem] overflow-auto rounded-md border border-court-line-soft/85 bg-[#01070d] p-4 font-mono text-[0.68rem] shadow-inner sm:p-5 sm:text-[0.72rem]">
          {logs.map((log) => (
            <ConsoleLog key={`${log.time}-${log.message}`} log={log} />
          ))}
        </div>

        <RunStatePanel state={sniperRun.state} />
      </div>
    </div>
  );
}
