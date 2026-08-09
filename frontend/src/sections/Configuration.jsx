import { useState } from 'react';
import { Save, ExternalLink, CalendarDays, Settings2 } from 'lucide-react';

export default function Configuration() {
  // Local state to hold the form values before saving to the backend
  const [url, setUrl] = useState('https://www.messenger.com/t/1234567890123456');
  const [message, setMessage] = useState('Hi, I would like to book badminton court\nat 4 - 5pm. Thank you!');
  const [date, setDate] = useState('2025-05-23');
  const [hour, setHour] = useState('09');
  const [minute, setMinute] = useState('00');
  const [second, setSecond] = useState('00');

  return (
    <div className="bg-[#0a0f1c] border border-slate-800 rounded-xl p-6 lg:p-8 shadow-lg relative overflow-hidden">

      {/* Section Header */}
      <div className="flex items-center space-x-3 mb-8">
        <Settings2 className="w-5 h-5 text-[#00E5FF]" />
        <h2 className="text-[#00E5FF] text-sm font-bold tracking-widest uppercase">Booking Configuration</h2>
      </div>

      {/* Form Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

        {/* Left Column */}
        <div className="space-y-6">
          {/* Target URL */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold tracking-wide mb-2">Target URL</label>
            <div className="relative">
              <input
                type="text"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full bg-[#0f172a] border border-slate-700 text-slate-200 text-sm rounded-md px-4 py-2.5 focus:outline-none focus:border-[#00E5FF] focus:ring-1 focus:ring-[#00E5FF]/50 transition-colors"
              />
              <ExternalLink className="absolute right-3 top-2.5 w-4 h-4 text-slate-500 hover:text-slate-300 cursor-pointer" />
            </div>
          </div>

          {/* Booking Message */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold tracking-wide mb-2">Booking Message</label>
            <div className="relative">
              <textarea
                rows="4"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                className="w-full bg-[#0f172a] border border-slate-700 text-slate-200 text-sm rounded-md px-4 py-3 focus:outline-none focus:border-[#00E5FF] focus:ring-1 focus:ring-[#00E5FF]/50 transition-colors resize-none font-mono"
              ></textarea>
              <span className="absolute bottom-3 right-3 text-[10px] text-slate-500 font-mono">{message.length} / 1000</span>
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">
          {/* Target Date */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold tracking-wide mb-2">Target Date</label>
            <div className="relative">
              <CalendarDays className="absolute left-3 top-2.5 w-4 h-4 text-slate-500" />
              <input
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
                className="w-full bg-[#0f172a] border border-slate-700 text-slate-200 text-sm rounded-md pl-10 pr-4 py-2.5 focus:outline-none focus:border-[#00E5FF] focus:ring-1 focus:ring-[#00E5FF]/50 transition-colors [color-scheme:dark]"
              />
            </div>
          </div>

          {/* Target Time (24H) */}
          <div>
            <label className="block text-slate-400 text-xs font-semibold tracking-wide mb-2">Target Time (24H)</label>
            <div className="flex space-x-4">

              {/* Hours */}
              <div className="flex-1">
                <select
                  value={hour}
                  onChange={(e) => setHour(e.target.value)}
                  className="w-full bg-[#0f172a] border border-slate-700 text-slate-200 text-sm rounded-md px-3 py-2.5 focus:outline-none focus:border-[#00E5FF] cursor-pointer"
                >
                  {[...Array(24)].map((_, i) => {
                    const val = i.toString().padStart(2, '0');
                    return <option key={val} value={val}>{val}</option>
                  })}
                </select>
                <div className="text-center mt-1.5"><span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">HH</span></div>
              </div>

              {/* Minutes */}
              <div className="flex-1">
                <select
                  value={minute}
                  onChange={(e) => setMinute(e.target.value)}
                  className="w-full bg-[#0f172a] border border-slate-700 text-slate-200 text-sm rounded-md px-3 py-2.5 focus:outline-none focus:border-[#00E5FF] cursor-pointer"
                >
                  {[...Array(60)].map((_, i) => {
                    const val = i.toString().padStart(2, '0');
                    return <option key={val} value={val}>{val}</option>
                  })}
                </select>
                <div className="text-center mt-1.5"><span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">MM</span></div>
              </div>

              {/* Seconds */}
              <div className="flex-1">
                <select
                  value={second}
                  onChange={(e) => setSecond(e.target.value)}
                  className="w-full bg-[#0f172a] border border-slate-700 text-slate-200 text-sm rounded-md px-3 py-2.5 focus:outline-none focus:border-[#00E5FF] cursor-pointer"
                >
                  {[...Array(60)].map((_, i) => {
                    const val = i.toString().padStart(2, '0');
                    return <option key={val} value={val}>{val}</option>
                  })}
                </select>
                <div className="text-center mt-1.5"><span className="text-[10px] text-slate-500 uppercase font-bold tracking-widest">SS</span></div>
              </div>

            </div>
          </div>
        </div>

      </div>

      {/* Save Button */}
      <div className="mt-8 pt-6 border-t border-slate-800 flex justify-center">
        <button className="flex items-center space-x-2 px-8 py-2.5 bg-[#0f172a] border border-[#00E5FF]/40 text-[#00E5FF] hover:bg-[#00E5FF]/10 hover:border-[#00E5FF] rounded-md transition-all font-bold tracking-wider text-xs shadow-[0_0_10px_rgba(0,229,255,0.05)] hover:shadow-[0_0_15px_rgba(0,229,255,0.15)]">
          <Save className="w-4 h-4" />
          <span>SAVE CONFIGURATION</span>
        </button>
      </div>

    </div>
  );
}