import { useEffect, useState } from 'react';
import {
  CalendarClock,
  Menu,
  Settings,
  ShieldCheck,
} from 'lucide-react';
import { assetUrl } from '../assets';
import useCourtSniper from '../context/useCourtSniper';

function StatusBlock({ icon: Icon, label, children, dot = true, dotClassName = 'bg-court-green shadow-[0_0_9px_rgba(99,255,0,0.85)]' }) {
  return (
    <div className="flex min-h-[4.25rem] min-w-0 flex-1 items-center border-l border-court-line-soft/70 px-4 first:border-l-0 xl:px-5">
      <div className="min-w-0">
        <div className="mb-2 flex items-center gap-1.5 text-[0.65rem] font-bold uppercase tracking-label text-court-cyan">
          {Icon && <Icon aria-hidden="true" className="h-3.5 w-3.5" />}
          <span className="truncate">{label}</span>
        </div>
        <div className="flex items-center gap-2 whitespace-nowrap text-sm font-semibold tracking-wide text-court-text">
          {dot && <span className={`h-2 w-2 shrink-0 rounded-full ${dotClassName}`} aria-hidden="true" />}
          {children}
        </div>
      </div>
    </div>
  );
}

export default function Header({ onMenuToggle }) {
  const [time, setTime] = useState(() => new Date());
  const {
    connectionStatus,
    scheduler,
    schedulerError,
    isLoadingScheduler,
  } = useCourtSniper();

  useEffect(() => {
    const timer = window.setInterval(() => setTime(new Date()), 40);
    return () => window.clearInterval(timer);
  }, []);

  const formattedTime = time.toLocaleTimeString('en-US', {
    hour12: false,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
  const milliseconds = time.getMilliseconds().toString().padStart(3, '0');
  const formattedDate = time.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });
  const connectionLabel = connectionStatus === 'online'
    ? 'API ONLINE'
    : connectionStatus === 'offline'
      ? 'API OFFLINE'
      : 'CHECKING';
  const connectionDot = connectionStatus === 'online'
    ? 'bg-court-green shadow-[0_0_9px_rgba(99,255,0,0.85)]'
    : connectionStatus === 'offline'
      ? 'bg-court-danger shadow-[0_0_9px_rgba(255,55,72,0.75)]'
      : 'bg-court-warning shadow-[0_0_9px_rgba(255,213,31,0.7)]';
  const schedulerLabel = isLoadingScheduler
    ? 'CHECKING'
    : schedulerError
      ? 'UNAVAILABLE'
      : !scheduler.installed
        ? 'NOT INSTALLED'
        : !scheduler.managed
          ? 'NAME CONFLICT'
          : !scheduler.configured
            ? 'NEEDS CONFIG'
            : scheduler.configuration_in_sync === false
              ? 'OUT OF SYNC'
              : scheduler.enabled
                ? 'ENABLED'
                : 'DISABLED';
  const schedulerDot = schedulerError
    || (scheduler.installed && !scheduler.managed)
    || scheduler.configuration_in_sync === false
    ? 'bg-court-danger shadow-[0_0_9px_rgba(255,55,72,0.75)]'
    : scheduler.enabled
      ? 'bg-court-green shadow-[0_0_9px_rgba(99,255,0,0.85)]'
      : 'bg-court-warning shadow-[0_0_9px_rgba(255,213,31,0.7)]';

  return (
    <header className="sticky top-0 z-30 px-3 pt-3 sm:px-4 lg:px-3">
      <div className="tactical-panel mx-auto flex min-h-[5.5rem] w-full max-w-[96rem] items-stretch overflow-visible bg-court-panel/95 backdrop-blur-xl">
        <button
          type="button"
          onClick={onMenuToggle}
          className="m-3 inline-flex w-11 shrink-0 items-center justify-center rounded border border-court-line text-court-cyan transition hover:bg-court-cyan/10 lg:hidden"
          aria-label="Open navigation"
        >
          <Menu aria-hidden="true" className="h-5 w-5" />
        </button>

        <div className="flex min-w-0 flex-1 items-center px-3 sm:px-5 lg:w-[20rem] lg:flex-none lg:px-5">
          <img
            src={assetUrl('shuttlecock-mark')}
            alt=""
            className="mr-2 hidden h-[4.5rem] w-[4.5rem] shrink-0 object-contain sm:block"
          />
          <div className="min-w-0">
            <div className="truncate font-display text-lg font-bold italic leading-none tracking-tactical sm:text-2xl">
              <span className="text-white">COURT</span>{' '}
              <span className="neon-green-text">SNIPER</span>
            </div>
            <p className="mt-2 hidden truncate text-xs font-medium text-court-text/90 sm:block">
              Book the court. Exactly on time.
            </p>
          </div>
        </div>

        <div className="ml-auto hidden min-w-0 flex-1 items-stretch border-l border-court-line-soft/70 xl:flex">
          <StatusBlock label="System Time" dot={false}>
            <div>
              <div className="font-mono text-lg font-bold leading-none text-court-cyan xl:text-xl">
                {formattedTime}<span className="text-xs">.{milliseconds}</span>
              </div>
              <div className="mt-1.5 text-[0.65rem] font-medium text-court-muted">
                {formattedDate}
              </div>
            </div>
          </StatusBlock>

          <StatusBlock icon={ShieldCheck} label="Backend Status" dotClassName={connectionDot}>
            {connectionLabel}
          </StatusBlock>

          <StatusBlock
            icon={CalendarClock}
            label="Scheduler Status"
            dotClassName={schedulerDot}
          >
            {schedulerLabel}
          </StatusBlock>
        </div>

        <div className="ml-auto flex items-center border-l border-court-line-soft/70 px-3 md:ml-0">
          <button
            type="button"
            className="inline-flex h-11 w-11 items-center justify-center rounded border border-court-line text-court-text transition hover:border-court-cyan hover:bg-court-cyan/10 hover:text-court-cyan hover:shadow-cyan"
            aria-label="Open settings"
          >
            <Settings aria-hidden="true" className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}
