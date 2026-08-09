import {
  AppWindow,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';

const sessionDetails = [
  { label: 'Last Refresh', value: 'May 22, 2025 10:15 PM' },
  { label: 'User Data', value: 'user_data/ (Local)', mono: true },
  { label: 'Browser', value: 'Chromium (Persistent)' },
];

export default function Session() {
  return (
    <div className="tactical-panel">
      <SectionHeader icon={UserRound} title="Session" />

      <div className="grid gap-5 p-4 lg:grid-cols-[1.05fr_1.2fr_1.05fr] lg:items-center lg:gap-0 lg:p-5">
        <div className="lg:pr-6">
          <div className="flex min-h-24 items-center gap-4 rounded-md border border-court-green/25 bg-court-inset/70 p-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-md bg-court-green/10 text-court-green shadow-green">
              <ShieldCheck aria-hidden="true" className="h-9 w-9 fill-court-green/15" />
            </div>
            <div>
              <div className="text-xs font-bold uppercase tracking-tactical text-court-green">Session Valid</div>
              <p className="mt-1.5 text-[0.68rem] font-medium text-court-text/75">Authenticated and ready to go.</p>
            </div>
          </div>
        </div>

        <dl className="grid gap-x-5 gap-y-4 border-court-line-soft/70 lg:grid-cols-2 lg:border-x lg:px-6">
          {sessionDetails.map((detail) => (
            <div key={detail.label} className={detail.label === 'Browser' ? 'lg:col-span-2' : ''}>
              <dt className="text-[0.62rem] font-bold uppercase tracking-label text-court-muted">{detail.label}</dt>
              <dd className={`mt-1 text-xs font-medium text-court-text ${detail.mono ? 'font-mono' : ''}`}>
                {detail.value}
              </dd>
            </div>
          ))}
        </dl>

        <div className="grid gap-3 lg:pl-6">
          <button type="button" className="tactical-button min-h-10 px-4">
            <RefreshCw aria-hidden="true" className="h-4 w-4" />
            Refresh Session
          </button>
          <button type="button" className="tactical-button min-h-10 px-4">
            <AppWindow aria-hidden="true" className="h-4 w-4" />
            Open Login Browser
          </button>
        </div>
      </div>
    </div>
  );
}
