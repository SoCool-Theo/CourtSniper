import { User, ShieldCheck, RefreshCw, AppWindow } from 'lucide-react';

export default function Session() {
  return (
    <div className="bg-[#0a0f1c] border border-slate-800 rounded-xl p-6 lg:p-8 shadow-lg relative overflow-hidden">

      {/* Section Header */}
      <div className="flex items-center space-x-3 mb-8">
        <User className="w-5 h-5 text-[#00E5FF]" />
        <h2 className="text-[#00E5FF] text-sm font-bold tracking-widest uppercase">Session</h2>
      </div>

      {/* Content Wrapper */}
      <div className="flex flex-col lg:flex-row gap-8 items-start lg:items-center justify-between">

        {/* Left: Status Badge */}
        <div className="flex items-center space-x-4 bg-[#0f172a] border border-[#00FF66]/20 p-5 rounded-lg lg:w-1/3 w-full">
          <div className="bg-[#00FF66]/10 p-3 rounded-full border border-[#00FF66]/20 shadow-[0_0_15px_rgba(0,255,102,0.15)]">
            <ShieldCheck className="w-8 h-8 text-[#00FF66]" />
          </div>
          <div className="flex flex-col">
            <span className="text-[#00FF66] font-bold tracking-widest text-sm mb-1">SESSION VALID</span>
            <span className="text-slate-400 text-xs">Authenticated and ready to go.</span>
          </div>
        </div>

        {/* Middle: Details */}
        <div className="grid grid-cols-2 gap-x-8 gap-y-4 lg:w-1/3 w-full text-sm">
          <div className="flex flex-col space-y-1">
            <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase">Last Refresh</span>
            <span className="text-slate-200">May 22, 2025 10:15 PM</span>
          </div>
          <div className="flex flex-col space-y-1">
            <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase">User Data</span>
            <span className="text-slate-200 font-mono">user_data/ (Local)</span>
          </div>
          <div className="flex flex-col space-y-1">
            <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase">Browser</span>
            <span className="text-slate-200">Chromium (Persistent)</span>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex flex-col space-y-3 lg:w-1/3 w-full">
          <button className="flex items-center justify-center space-x-2 px-6 py-2.5 bg-[#0f172a] border border-[#00E5FF]/40 text-[#00E5FF] hover:bg-[#00E5FF]/10 hover:border-[#00E5FF] rounded-md transition-all font-bold tracking-wider text-xs shadow-[0_0_10px_rgba(0,229,255,0.05)] hover:shadow-[0_0_15px_rgba(0,229,255,0.15)]">
            <RefreshCw className="w-4 h-4" />
            <span>REFRESH SESSION</span>
          </button>
          <button className="flex items-center justify-center space-x-2 px-6 py-2.5 bg-[#0f172a] border border-[#00E5FF]/40 text-[#00E5FF] hover:bg-[#00E5FF]/10 hover:border-[#00E5FF] rounded-md transition-all font-bold tracking-wider text-xs shadow-[0_0_10px_rgba(0,229,255,0.05)] hover:shadow-[0_0_15px_rgba(0,229,255,0.15)]">
            <AppWindow className="w-4 h-4" />
            <span>OPEN LOGIN BROWSER</span>
          </button>
        </div>
      </div>
    </div>
  );
}