import { useState, useEffect } from 'react';
import { Settings } from 'lucide-react';

export default function Header() {
  const [time, setTime] = useState(new Date());

  // This hook creates a highly responsive interval to update the clock every 10 milliseconds
  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 10);
    return () => clearInterval(timer);
  }, []);

  // Format helpers for our tactical digital clock
  const formatTime = (date) => {
    return date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatMs = (date) => {
    return date.getMilliseconds().toString().padStart(3, '0');
  };

  const formatDate = (date) => {
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  };

  return (
    <header className="bg-[#0a0f1c] border-b border-slate-800 p-4 lg:px-8 flex flex-col lg:flex-row justify-between items-center shrink-0">

      {/* 1. Left Tagline */}
      <div className="hidden lg:block text-slate-400 text-sm font-medium tracking-wide">
        Book the court. <span className="text-[#00FF66]">Exactly on time.</span>
      </div>

      {/* 2. Right Status & Clock Container */}
      <div className="flex items-center space-x-6 lg:space-x-8 w-full lg:w-auto justify-between lg:justify-end">

        {/* System Time */}
        <div className="flex flex-col items-start lg:items-end min-w-[140px]">
          <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase mb-1">System Time</span>
          <div className="flex items-baseline space-x-1">
            <span className="text-[#00E5FF] font-mono text-xl lg:text-2xl font-bold tracking-wider">{formatTime(time)}</span>
            <span className="text-[#00E5FF]/70 font-mono text-xs lg:text-sm">.{formatMs(time)}</span>
          </div>
          <span className="text-slate-400 text-[10px] lg:text-xs mt-0.5">{formatDate(time)}</span>
        </div>

        {/* Vertical Divider */}
        <div className="hidden sm:block h-10 w-px bg-slate-800"></div>

        {/* Session Status */}
        <div className="flex flex-col">
          <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase mb-1">Session Status</span>
          <div className="flex items-center space-x-2 mt-1">
            <div className="w-2 h-2 bg-[#00FF66] rounded-full shadow-[0_0_8px_#00FF66]"></div>
            <span className="text-slate-200 text-xs font-bold tracking-wider">AUTHENTICATED</span>
          </div>
        </div>

        {/* Vertical Divider */}
        <div className="hidden sm:block h-10 w-px bg-slate-800"></div>

        {/* Scheduler Status */}
        <div className="hidden sm:flex flex-col">
          <span className="text-slate-500 text-[10px] font-bold tracking-widest uppercase mb-1">Scheduler Status</span>
          <div className="flex items-center space-x-2 mt-1">
            <div className="w-2 h-2 bg-[#00FF66] rounded-full shadow-[0_0_8px_#00FF66]"></div>
            <span className="text-slate-200 text-xs font-bold tracking-wider">READY</span>
          </div>
        </div>

        {/* Settings Button */}
        <button className="p-2.5 border border-slate-700 rounded-md text-slate-400 hover:text-white hover:bg-slate-800 hover:border-slate-500 transition-all ml-2">
          <Settings className="w-4 h-4 lg:w-5 lg:h-5" />
        </button>

      </div>
    </header>
  );
}