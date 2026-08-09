const toneClasses = {
  green: 'text-court-green drop-shadow-[0_0_8px_rgba(99,255,0,0.28)]',
  cyan: 'text-court-cyan drop-shadow-[0_0_8px_rgba(0,231,255,0.24)]',
  warning: 'text-court-warning drop-shadow-[0_0_8px_rgba(255,213,31,0.2)]',
  danger: 'text-court-danger drop-shadow-[0_0_8px_rgba(255,55,72,0.2)]',
};

export default function StatusCard({ icon: Icon, label, value, tone = 'green' }) {
  return (
    <div className="flex min-h-[6.3rem] min-w-0 items-center gap-3 rounded-md border border-court-line-soft/80 bg-court-inset/70 px-4 py-4 shadow-[inset_0_1px_rgba(0,231,255,0.025)]">
      <Icon aria-hidden="true" className="h-8 w-8 shrink-0 text-court-text/90" strokeWidth={1.45} />
      <div className="min-w-0">
        <p className="truncate text-[0.68rem] font-semibold text-court-text/85">{label}</p>
        <p className={`mt-2 truncate text-sm font-bold uppercase tracking-wide ${toneClasses[tone]}`}>
          {value}
        </p>
      </div>
    </div>
  );
}
