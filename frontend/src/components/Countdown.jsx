import { useEffect, useState } from 'react';

function getRemainingTime(targetDate) {
  const difference = Math.max(0, targetDate.getTime() - Date.now());

  return {
    hours: Math.floor(difference / 3_600_000),
    minutes: Math.floor((difference % 3_600_000) / 60_000),
    seconds: Math.floor((difference % 60_000) / 1_000),
    milliseconds: difference % 1_000,
    complete: difference === 0,
  };
}

function TimeUnit({ value, label, shortLabel, digits = 2 }) {
  return (
    <div className="min-w-0 text-center">
      <div className="font-mono font-bold leading-none tracking-[-0.08em] text-court-green drop-shadow-[0_0_16px_rgba(99,255,0,0.22)]">
        {value.toString().padStart(digits, '0')}
      </div>
      <div className="mt-2 whitespace-nowrap text-[0.5rem] font-bold uppercase tracking-[0.06em] text-court-cyan sm:mt-3 sm:text-[0.68rem] sm:tracking-label">
        <span className="sm:hidden">{shortLabel}</span>
        <span className="hidden sm:inline">{label}</span>
      </div>
    </div>
  );
}

export default function Countdown({ targetDate }) {
  const [remaining, setRemaining] = useState(() => getRemainingTime(targetDate));

  useEffect(() => {
    const timer = window.setInterval(() => {
      const nextRemaining = getRemainingTime(targetDate);
      setRemaining(nextRemaining);

      if (nextRemaining.complete) window.clearInterval(timer);
    }, 31);

    return () => window.clearInterval(timer);
  }, [targetDate]);

  return (
    <div
      className="mt-5 flex w-full items-start justify-center gap-0 text-[clamp(1.7rem,8vw,2.35rem)] sm:justify-start sm:gap-2 sm:text-[clamp(2.35rem,5.2vw,5rem)]"
      role="timer"
      aria-label={`${remaining.hours} hours, ${remaining.minutes} minutes, ${remaining.seconds} seconds, and ${remaining.milliseconds} milliseconds remaining`}
    >
      <TimeUnit value={remaining.hours} label="Hours" shortLabel="HRS" />
      <span className="font-mono font-bold leading-none text-court-green">:</span>
      <TimeUnit value={remaining.minutes} label="Minutes" shortLabel="MIN" />
      <span className="font-mono font-bold leading-none text-court-green">:</span>
      <TimeUnit value={remaining.seconds} label="Seconds" shortLabel="SEC" />
      <span className="font-mono font-bold leading-none text-court-green">.</span>
      <TimeUnit value={remaining.milliseconds} label="Milliseconds" shortLabel="MS" digits={3} />
    </div>
  );
}
