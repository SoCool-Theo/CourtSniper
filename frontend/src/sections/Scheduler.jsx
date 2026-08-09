import {
  CalendarCheck,
  CalendarDays,
  CheckSquare2,
  ExternalLink,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';

const requirements = [
  'Wake the computer to run this task',
  'Run only when user is logged on',
  'Run with highest privileges',
];

export default function Scheduler() {
  return (
    <div className="tactical-panel">
      <SectionHeader icon={CalendarDays} title="Scheduler" />

      <div className="p-4 sm:p-5">
        <div className="grid gap-6 lg:grid-cols-[0.9fr_1.2fr_0.85fr] lg:items-center lg:gap-0">
          <dl className="grid grid-cols-[auto_1fr] gap-x-8 gap-y-3 lg:pr-7">
            <dt className="text-[0.65rem] font-bold text-court-text/75">Status</dt>
            <dd className="flex items-center gap-2 text-[0.68rem] font-bold uppercase tracking-wide text-court-green">
              <span className="status-dot" /> Enabled
            </dd>
            <dt className="text-[0.65rem] font-bold text-court-text/75">Next Execution</dt>
            <dd className="text-xs font-medium leading-snug text-court-text">
              Tomorrow 08:57 AM
              <span className="block text-[0.65rem] text-court-muted">(in approximately 24 hours)</span>
            </dd>
            <dt className="text-[0.65rem] font-bold text-court-text/75">Trigger</dt>
            <dd className="text-xs font-medium text-court-text">One time</dd>
          </dl>

          <div className="space-y-3 border-court-line-soft/70 lg:border-x lg:px-7">
            {requirements.map((requirement) => (
              <div key={requirement} className="flex items-center gap-3 text-xs font-medium text-court-text/90">
                <CheckSquare2 aria-hidden="true" className="h-4 w-4 shrink-0 text-court-cyan" />
                <span>{requirement}</span>
              </div>
            ))}
          </div>

          <div className="lg:pl-7">
            <button type="button" className="tactical-button min-h-11 w-full px-4">
              <ExternalLink aria-hidden="true" className="h-4 w-4" />
              Open Task Scheduler
            </button>
          </div>
        </div>

        <div className="mt-5 flex items-start gap-3 rounded-md border border-court-green/45 bg-court-inset/75 px-4 py-3">
          <CalendarCheck aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-court-cyan" />
          <p className="text-[0.7rem] font-medium leading-relaxed text-court-text/80">
            Scheduled daily at 08:57 AM. Script self-checks{' '}
            <strong className="font-mono text-court-green">STATUS</strong> in{' '}
            <span className="font-mono text-court-text">.env</span>; executes only when{' '}
            <strong className="font-mono text-court-green">STATUS = ARMED</strong>.
          </p>
        </div>
      </div>
    </div>
  );
}
