export default function SectionHeader({ icon: Icon, title }) {
  return (
    <div className="flex items-center gap-2.5 border-b border-court-line-soft/65 px-4 py-3 sm:px-5">
      <Icon aria-hidden="true" className="h-5 w-5 text-court-cyan" strokeWidth={1.7} />
      <h2 className="text-sm font-bold uppercase tracking-tactical text-court-cyan">
        {title}
      </h2>
    </div>
  );
}
