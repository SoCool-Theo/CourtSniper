import { useMemo, useState } from 'react';
import {
  CalendarDays,
  Clock3,
  Crosshair,
  FlaskConical,
  Info,
  Send,
  Target,
} from 'lucide-react';
import Countdown from '../components/Countdown';

function getNextBookingDate() {
  const now = new Date();
  const target = new Date(now);
  target.setHours(9, 0, 0, 0);

  if (target <= now) target.setDate(target.getDate() + 1);
  return target;
}

function TargetGraphic() {
  return (
    <div className="pointer-events-none absolute inset-y-0 right-0 hidden w-[58%] overflow-hidden lg:block" aria-hidden="true">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_42%,rgba(0,231,255,0.13),transparent_34%)]" />
      <div className="absolute right-[-5rem] top-[-3rem] h-[22rem] w-[22rem] rounded-full border border-court-line/20" />
      <div className="absolute right-[-1.5rem] top-[0.5rem] h-[15rem] w-[15rem] rounded-full border border-court-line/35" />

      <div className="absolute right-[7%] top-1/2 h-48 w-48 -translate-y-1/2">
        <span className="absolute left-1/2 top-0 h-full w-px bg-gradient-to-b from-transparent via-court-cyan to-transparent" />
        <span className="absolute left-0 top-1/2 h-px w-full bg-gradient-to-r from-transparent via-court-cyan to-transparent" />
        <div className="absolute inset-4 rounded-full border border-court-cyan shadow-cyan" />
        <div className="absolute inset-[3.75rem] rounded-full border border-court-cyan/65" />
        <Target className="absolute left-1/2 top-1/2 h-20 w-20 -translate-x-1/2 -translate-y-1/2 rotate-[-22deg] text-court-cyan drop-shadow-[0_0_15px_rgba(0,231,255,0.45)]" strokeWidth={1.15} />
      </div>

      {Array.from({ length: 7 }).map((_, index) => (
        <span
          key={index}
          className="absolute right-[9%] h-px origin-right bg-gradient-to-l from-court-cyan/70 to-transparent"
          style={{
            top: `${25 + index * 7}%`,
            width: `${14 + index * 2}%`,
            transform: `rotate(${index * 4 - 12}deg)`,
          }}
        />
      ))}
    </div>
  );
}

export default function Dashboard() {
  const [isArmed, setIsArmed] = useState(true);
  const targetDate = useMemo(() => getNextBookingDate(), []);

  const formattedDate = targetDate.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const formattedTime = targetDate.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: true,
  });
  const precisionTime = formattedTime.replace(' ', '.000 ');

  return (
    <div className="tactical-panel">
      <div className="absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-court-cyan/70 to-transparent" />

      <div className="grid lg:grid-cols-12">
        <div className="relative z-10 p-6 sm:p-7 lg:col-span-7 lg:p-8 xl:p-9">
          <h1 className="text-sm font-bold uppercase tracking-label text-court-cyan sm:text-base">
            Next Booking
          </h1>

          <Countdown targetDate={targetDate} />

          <div className="mt-7 sm:mt-8">
            <div className="mb-3 flex items-center gap-2">
              <h2 className="text-xs font-bold uppercase tracking-label text-court-cyan">
                Execution Status
              </h2>
              <Info aria-hidden="true" className="h-3.5 w-3.5 text-court-muted" />
            </div>

            <div className="grid max-w-[31rem] grid-cols-2 rounded-full border border-court-green/60 bg-court-inset/90 p-0.5">
              <button
                type="button"
                aria-pressed={isArmed}
                onClick={() => setIsArmed(true)}
                className={`flex min-h-10 items-center justify-center gap-2 rounded-full text-sm font-bold tracking-wide transition-all ${
                  isArmed
                    ? 'border border-court-green bg-court-green/15 text-court-green shadow-green-strong'
                    : 'text-court-muted hover:text-court-text'
                }`}
              >
                <Crosshair aria-hidden="true" className="h-5 w-5" />
                ARMED
              </button>
              <button
                type="button"
                aria-pressed={!isArmed}
                onClick={() => setIsArmed(false)}
                className={`min-h-10 rounded-full text-sm font-bold tracking-wide transition-all ${
                  !isArmed
                    ? 'border border-court-danger bg-court-danger/10 text-court-danger shadow-[0_0_18px_rgba(255,55,72,0.24)]'
                    : 'text-court-muted hover:text-court-text'
                }`}
              >
                DISARMED
              </button>
            </div>

            <p className="mt-3 max-w-[31rem] rounded-md border border-court-green/45 bg-court-inset/80 px-4 py-3 text-center text-xs font-medium leading-relaxed text-court-text/80">
              Task runs daily; booking executes only when{' '}
              <strong className="font-mono text-court-green">STATUS = ARMED</strong>{' '}
              (from <span className="font-mono">.env</span>).
            </p>
          </div>
        </div>

        <div className="relative min-h-[17rem] overflow-hidden border-t border-court-line-soft/70 p-6 sm:p-7 lg:col-span-5 lg:min-h-0 lg:border-l lg:border-t-0 lg:p-8">
          <TargetGraphic />

          <div className="relative z-10 max-w-xs">
            <h2 className="mb-6 text-xs font-bold uppercase tracking-label text-court-cyan">
              Target Booking
            </h2>

            <div className="space-y-5 text-sm font-medium text-court-text">
              <div className="flex items-center gap-3">
                <Crosshair aria-hidden="true" className="h-5 w-5 text-court-cyan" />
                <span>Court Booking</span>
              </div>
              <div className="flex items-center gap-3">
                <CalendarDays aria-hidden="true" className="h-5 w-5 text-court-text/80" />
                <span>{formattedDate}</span>
              </div>
              <div className="flex items-center gap-3">
                <Clock3 aria-hidden="true" className="h-5 w-5 text-court-text/80" />
                <span className="font-mono text-xs">{precisionTime}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 grid gap-3 border-t border-court-line-soft/70 bg-court-void/20 p-4 sm:grid-cols-[minmax(0,1fr)_minmax(17rem,1.3fr)_minmax(11rem,0.8fr)] sm:items-center sm:p-5 lg:px-7">
        <div>
          <div className={`inline-flex items-center gap-2 rounded border px-2.5 py-1 text-[0.67rem] font-bold tracking-label ${
            isArmed
              ? 'border-court-green/45 text-court-green'
              : 'border-court-danger/45 text-court-danger'
          }`}>
            <span className={`h-2 w-2 rounded-full ${
              isArmed ? 'bg-court-green shadow-[0_0_8px_#63ff00]' : 'bg-court-danger shadow-[0_0_8px_#ff3748]'
            }`} />
            {isArmed ? 'ARMED & READY' : 'DISARMED'}
          </div>
          <p className="mt-2 text-[0.7rem] font-medium text-court-muted">
            Target time: {precisionTime}
          </p>
        </div>

        <button type="button" className="tactical-button tactical-button--primary min-h-[4rem] px-5">
          <Crosshair aria-hidden="true" className="h-8 w-8" />
          <span className="text-left">
            <span className="block text-lg leading-none">Start Sniper</span>
            <span className="mt-1 block text-[0.55rem] tracking-label">Send booking message</span>
          </span>
          <Send aria-hidden="true" className="h-4 w-4 opacity-70" />
        </button>

        <button type="button" className="tactical-button min-h-[3.3rem] px-5">
          <FlaskConical aria-hidden="true" className="h-5 w-5" />
          Test Run
        </button>
      </div>
    </div>
  );
}
