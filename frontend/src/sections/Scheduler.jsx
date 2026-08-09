import { CalendarClock, CheckSquare, ExternalLink, Calendar } from 'lucide-react';

export default function Scheduler() {
  return (
    <div className="bg-[#0a0f1c] border border-slate-800 rounded-xl p-6 lg:p-8 shadow-lg relative overflow-hidden">

      {/* Section Header */}
      <div className="flex items-center space-x-3 mb-8">
        <CalendarClock className="w-5 h-5 text-[#00E5FF]" />
        <h2 className="text-[#00E5FF] text-sm font-bold tracking-widest uppercase">Scheduler</h2>
      </div>

      <div className="flex flex-col lg:flex-row gap-8">

        {/* Left: Execution Details */}
        <div className="grid grid-cols-2 gap-y-6 gap-x-8 lg:w-1/3 w-full">
          <div className="flex flex-col space-y-2">
            <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase">Status</span>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-[#00FF66] rounded-full shadow-[0_0_8px_#00FF66]"></div>
              <span className="text-[#00FF66] text-xs font-bold tracking-wider">ENABLED</span>
            </div>
          </div>

          <div className="flex flex-col space-y-2">
            <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase">Trigger</span>
            <span className="text-slate-200 text-sm">Daily</span>
          </div>

          <div className="flex flex-col space-y-2 col-span-2">
            <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase">Next Execution</span>
            <span className="text-slate-200 text-sm">Tomorrow 07:55 AM</span>
          </div>
        </div>

        {/* Middle: Checklist */}
        <div className="flex flex-col space-y-4 lg:w-1/3 w-full lg:border-l lg:border-slate-800 lg:pl-8">
          <div className="flex items-center space-x-3">
            <CheckSquare className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-slate-300 text-xs">Wake the computer to run this task</span>
          </div>
          <div className="flex items-center space-x-3">
            <CheckSquare className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-slate-300 text-xs">Run only when user is logged on</span>
          </div>
          <div className="flex items-center space-x-3">
            <CheckSquare className="w-4 h-4 text-[#00E5FF]" />
            <span className="text-slate-300 text-xs">Run with highest privileges</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex flex-col justify-center lg:w-1/3 w-full">
           <button className="flex items-center justify-center space-x-2 px-6 py-3 bg-[#0f172a] border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white rounded-md transition-all font-bold tracking-wider text-xs shadow-md group">
             <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-white transition-colors" />
             <span>OPEN TASK SCHEDULER</span>
           </button>
        </div>

      </div>

      {/* Bottom Banner */}
      <div className="mt-8 bg-[#0f172a] border border-slate-800 rounded-md p-4 flex items-start sm:items-center space-x-3">
        <Calendar className="w-4 h-4 text-slate-400 mt-0.5 sm:mt-0 shrink-0" />
        <p className="text-slate-400 text-xs leading-relaxed">
          Scheduled daily at 07:55 AM. Script self-checks <strong className="text-[#00FF66]">STATUS</strong> in .env; executes only when <strong className="text-[#00FF66]">STATUS = ARMED</strong>.
        </p>
      </div>

    </div>
  );
}