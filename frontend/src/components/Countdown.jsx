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

function TimeUnit({ value, label, digits = 2 }) {
  return (
    <div className="min-w-0 text-center">
      <div className="font-mono font-bold leading-none tracking-[-0.08em] text-court-green drop-shadow-[0_0_16px_rgba(99,255,0,0.22)]">
        {value.toString().padStart(digits, '0')}
      </div>
      <div className="mt-3 text-[0.62rem] font-bold uppercase tracking-label text-court-cyan sm:text-[0.68rem]">
        {label}
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
      className="mt-5 flex items-start gap-1 text-[clamp(2.35rem,5.2vw,5rem)] sm:gap-2"
      role="timer"
      aria-label={`${remaining.hours} hours, ${remaining.minutes} minutes, ${remaining.seconds} seconds, and ${remaining.milliseconds} milliseconds remaining`}
    >
      <TimeUnit value={remaining.hours} label="Hours" />
      <span className="font-mono font-bold leading-none text-court-green">:</span>
      <TimeUnit value={remaining.minutes} label="Minutes" />
      <span className="font-mono font-bold leading-none text-court-green">:</span>
      <TimeUnit value={remaining.seconds} label="Seconds" />
      <span className="font-mono font-bold leading-none text-court-green">.</span>
      <TimeUnit value={remaining.milliseconds} label="Milliseconds" digits={3} />
    </div>
  );
}
