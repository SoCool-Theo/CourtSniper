import { ChevronRight, LockKeyhole } from 'lucide-react';

export default function SecurityNotice() {
  return (
    <aside className="flex flex-col gap-3 rounded-md border border-court-warning/55 bg-[linear-gradient(90deg,rgba(39,31,2,0.42),rgba(3,16,29,0.96))] px-4 py-3 shadow-[0_0_16px_rgba(255,213,31,0.04)] sm:flex-row sm:items-center">
      <LockKeyhole aria-hidden="true" className="h-5 w-5 shrink-0 text-court-warning" />

      <div className="min-w-0 flex-1">
        <h2 className="text-[0.68rem] font-bold uppercase tracking-tactical text-court-warning">Security Notice</h2>
        <p className="mt-1 text-[0.66rem] font-medium leading-relaxed text-court-text/75">
          Your session data is stored locally in the <span className="font-mono">user_data/</span> folder and must never be shared or uploaded.
        </p>
      </div>

      <button type="button" className="inline-flex min-h-9 w-full shrink-0 items-center justify-center gap-5 rounded border border-court-warning/60 px-5 text-[0.65rem] font-bold uppercase tracking-wide text-court-text transition hover:bg-court-warning/10 hover:text-court-warning sm:w-auto">
        Learn More
        <ChevronRight aria-hidden="true" className="h-4 w-4" />
      </button>
    </aside>
  );
}
