import { useState } from 'react';
import { Crosshair, Calendar, Clock, FlaskConical, Info } from 'lucide-react';

export default function Dashboard() {
  // This state controls the glowing toggle switch
  const [isArmed, setIsArmed] = useState(true);

  return (
    <div className="space-y-6">

      {/* 1. Main Dashboard Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

        {/* Left Column: Countdown & Status */}
        <div className="lg:col-span-7 bg-[#0a0f1c] border border-slate-800 rounded-xl p-6 lg:p-8 flex flex-col justify-between relative overflow-hidden shadow-lg">
          {/* Subtle Top Glow */}
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-[#00FF66] to-transparent opacity-30"></div>

          <div>
            <h2 className="text-[#00E5FF] text-xs font-bold tracking-widest uppercase mb-4">Next Booking</h2>
            <div className="flex items-baseline space-x-2 lg:space-x-4 mb-2">
              <span className="text-[#00FF66] font-mono text-6xl lg:text-7xl font-bold tracking-tight">00:02</span>
              <span className="text-[#00FF66] font-mono text-4xl lg:text-5xl font-bold tracking-tight">:157</span>
            </div>
            <div className="flex space-x-10 lg:space-x-12 text-slate-500 text-[10px] font-bold tracking-widest uppercase ml-1">
              <span>Hours</span>
              <span>Minutes</span>
              <span>Milliseconds</span>
            </div>
          </div>

          <div className="mt-10 lg:mt-12">
            <div className="flex items-center space-x-2 mb-4">
              <h3 className="text-[#00E5FF] text-xs font-bold tracking-widest uppercase">Execution Status</h3>
              <Info className="w-4 h-4 text-slate-500 cursor-pointer hover:text-slate-300 transition-colors" />
            </div>

            {/* The ARMED / DISARMED Toggle */}
            <div className="flex bg-[#0f172a] p-1.5 rounded-lg border border-slate-800 max-w-sm shadow-inner">
              <button
                onClick={() => setIsArmed(true)}
                className={`flex-1 py-3 text-sm font-bold tracking-wider rounded-md transition-all duration-300 ${
                  isArmed
                    ? 'bg-[#00FF66]/10 text-[#00FF66] border border-[#00FF66]/30 shadow-[0_0_15px_rgba(0,255,102,0.15)]'
                    : 'text-slate-500 hover:text-slate-300 border border-transparent'
                }`}
              >
                <Crosshair className="w-4 h-4 inline-block mr-2 mb-0.5" />
                ARMED
              </button>
              <button
                onClick={() => setIsArmed(false)}
                className={`flex-1 py-3 text-sm font-bold tracking-wider rounded-md transition-all duration-300 ${
                  !isArmed
                    ? 'bg-red-500/10 text-red-500 border border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)]'
                    : 'text-slate-500 hover:text-slate-300 border border-transparent'
                }`}
              >
                DISARMED
              </button>
            </div>

            <p className="text-slate-400 text-xs mt-4 border border-slate-800 bg-[#0f172a]/80 p-3 rounded-md max-w-sm leading-relaxed">
              Task runs daily; booking executes only when <strong className="text-[#00FF66]">STATUS = ARMED</strong> (from .env).
            </p>
          </div>
        </div>

        {/* Right Column: Target Info */}
        <div className="lg:col-span-5 bg-[#0a0f1c] border border-slate-800 rounded-xl p-6 lg:p-8 flex flex-col justify-center relative overflow-hidden shadow-lg">
           {/* Decorative Radar Background */}
           <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-[#00E5FF] via-[#0a0f1c] to-[#0a0f1c]"></div>

          <h2 className="text-[#00E5FF] text-xs font-bold tracking-widest uppercase mb-8 relative z-10">Target Booking</h2>

          <div className="space-y-6 relative z-10">
            <div className="flex items-center space-x-4">
              <Crosshair className="w-5 h-5 text-[#00E5FF]" />
              <span className="text-slate-200 font-semibold tracking-wide">Court Booking</span>
            </div>
            <div className="flex items-center space-x-4">
              <Calendar className="w-5 h-5 text-slate-500" />
              <span className="text-slate-200 font-semibold tracking-wide">May 23, 2025</span>
            </div>
            <div className="flex items-center space-x-4">
              <Clock className="w-5 h-5 text-slate-500" />
              <span className="text-slate-200 font-mono tracking-wider">09:00:00.000 AM</span>
            </div>
          </div>
        </div>

      </div>

      {/* 2. Action Bar */}
      <div className="bg-[#0a0f1c] border border-slate-800 rounded-xl p-5 flex flex-col sm:flex-row items-center justify-between space-y-4 sm:space-y-0 shadow-lg">

        {/* Left Status Text */}
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 bg-[#0f172a] px-3 py-1.5 rounded-md border ${isArmed ? 'border-[#00FF66]/20' : 'border-red-500/20'}`}>
             <div className={`w-2 h-2 rounded-full ${isArmed ? 'bg-[#00FF66] shadow-[0_0_8px_#00FF66]' : 'bg-red-500 shadow-[0_0_8px_#ef4444]'}`}></div>
             <span className={`text-[10px] font-bold tracking-widest ${isArmed ? 'text-[#00FF66]' : 'text-red-500'}`}>
                {isArmed ? 'ARMED & READY' : 'DISARMED'}
             </span>
          </div>
          <span className="text-slate-500 text-xs font-medium hidden sm:block">Target time: 09:00:00.000 AM</span>
        </div>

        {/* Right Action Buttons */}
        <div className="flex space-x-4 w-full sm:w-auto">
           <button className="flex-1 sm:flex-none group relative bg-[#0f172a] border border-[#00FF66]/50 hover:border-[#00FF66] text-[#00FF66] px-8 py-3 rounded-md transition-all overflow-hidden flex items-center justify-center space-x-3 shadow-[0_0_15px_rgba(0,255,102,0.1)] hover:shadow-[0_0_25px_rgba(0,255,102,0.2)]">
              <div className="absolute inset-0 bg-[#00FF66]/10 group-hover:bg-[#00FF66]/20 transition-all"></div>
              <Crosshair className="w-5 h-5 relative z-10" />
              <div className="flex flex-col items-start text-left relative z-10">
                <span className="font-bold tracking-widest leading-none text-sm mb-1">START SNIPER</span>
                <span className="text-[8px] opacity-80 tracking-widest leading-none uppercase">Send Booking Message</span>
              </div>
           </button>

           <button className="px-6 py-3 bg-[#0f172a] border border-slate-700 hover:border-slate-500 text-slate-300 hover:text-white rounded-md transition-all flex items-center justify-center space-x-2 text-sm font-bold tracking-wider">
              <FlaskConical className="w-4 h-4 text-[#00E5FF]" />
              <span>TEST RUN</span>
           </button>
        </div>

      </div>

    </div>
  );
}