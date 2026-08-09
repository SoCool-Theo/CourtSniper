import {
  Check,
  CheckCircle2,
  Crosshair,
  Target,
  TerminalSquare,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';

const logs = [
  { time: '08:57:40.123', message: 'CourtSniper initialized successfully.' },
  { time: '08:57:40.456', message: 'Configuration loaded.' },
  { time: '08:57:40.789', message: 'Session loaded and authenticated.' },
  { time: '08:57:41.012', message: 'Browser ready. Navigated to target chat.' },
  { time: '08:57:41.789', message: 'Synchronizing with target time...' },
  { time: '08:57:42.123', message: 'Countdown started. Target: 09:00:00.000' },
  { time: '08:59:58.250', message: 'T - 00:01.750' },
  { time: '08:59:59.500', message: 'T - 00:00.500' },
  { time: '08:59:59.900', message: 'Final sync...', tone: 'success' },
  { time: '09:00:00.000', message: '>>> BOOKING MESSAGE DISPATCHED <<<', tone: 'strong' },
  { time: '09:00:00.230', message: 'Message sent successfully!', tone: 'success', checked: true },
];

function ConsoleLog({ log }) {
  const messageTone = log.tone === 'strong'
    ? 'font-bold text-court-green'
    : log.tone === 'success'
      ? 'text-court-green'
      : 'text-court-text/80';

  return (
    <div className="grid grid-cols-[6.4rem_minmax(0,1fr)] gap-3 leading-[1.55]">
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

function TargetHitPanel() {
  return (
    <div className="relative flex min-h-[18rem] flex-col items-center justify-center overflow-hidden rounded-md border border-court-green bg-[radial-gradient(circle_at_center,rgba(31,117,5,0.42),rgba(1,18,8,0.96)_65%)] px-5 text-center shadow-green-strong">
      <div className="absolute inset-0 bg-tactical-grid bg-tactical-grid opacity-25" />
      <div className="absolute left-1/2 top-1/2 h-44 w-44 -translate-x-1/2 -translate-y-[64%] rounded-full border border-court-green/15" />
      <div className="absolute left-1/2 top-1/2 h-32 w-32 -translate-x-1/2 -translate-y-[70%] rounded-full border border-court-green/35" />

      <div className="relative mb-5 flex h-24 w-24 items-center justify-center text-court-green">
        <span className="absolute left-1/2 top-0 h-full w-px bg-gradient-to-b from-transparent via-court-green to-transparent" />
        <span className="absolute left-0 top-1/2 h-px w-full bg-gradient-to-r from-transparent via-court-green to-transparent" />
        <Target aria-hidden="true" className="h-20 w-20 drop-shadow-[0_0_14px_rgba(99,255,0,0.55)]" strokeWidth={1.2} />
        <Crosshair aria-hidden="true" className="absolute h-9 w-9" strokeWidth={1.5} />
      </div>

      <h3 className="relative text-3xl font-bold uppercase tracking-tactical text-court-green drop-shadow-[0_0_12px_rgba(99,255,0,0.6)] sm:text-4xl">
        Target Hit!
      </h3>
      <p className="relative mt-2 text-base font-semibold text-court-green">Booking request sent.</p>
      <CheckCircle2 aria-hidden="true" className="relative mt-3 h-8 w-8 text-court-green" />
    </div>
  );
}

export default function ExecutionConsole() {
  return (
    <div className="tactical-panel">
      <SectionHeader icon={TerminalSquare} title="Execution Console" />

      <div className="grid gap-4 p-4 lg:grid-cols-[1.55fr_0.75fr]">
        <div className="min-h-[18rem] overflow-auto rounded-md border border-court-line-soft/85 bg-[#01070d] p-4 font-mono text-[0.68rem] shadow-inner sm:p-5 sm:text-[0.72rem]">
          {logs.map((log) => (
            <ConsoleLog key={`${log.time}-${log.message}`} log={log} />
          ))}
        </div>

        <TargetHitPanel />
      </div>
    </div>
  );
}
