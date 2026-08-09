import { Terminal, Target, CheckCircle2 } from 'lucide-react';

export default function ExecutionConsole() {
  // Simulating the exact log output from your design
  const logs = [
    { time: '08:57:40.123', msg: 'CourtSniper initialized successfully.', type: 'info' },
    { time: '08:57:40.456', msg: 'Configuration loaded.', type: 'info' },
    { time: '08:57:40.789', msg: 'Session loaded and authenticated.', type: 'info' },
    { time: '08:57:41.012', msg: 'Browser ready. Navigated to target chat.', type: 'info' },
    { time: '08:57:41.789', msg: 'Synchronizing with target time...', type: 'info' },
    { time: '08:57:42.123', msg: 'Countdown started. Target: 09:00:00.000', type: 'info' },
    { time: '08:59:58.250', msg: 'T - 00:01.750', type: 'info' },
    { time: '08:59:59.500', msg: 'T - 00:00.500', type: 'info' },
    { time: '08:59:59.900', msg: 'Final sync...', type: 'success' },
    { time: '09:00:00.000', msg: '>>> BOOKING MESSAGE DISPATCHED <<<', type: 'success', bold: true },
    { time: '09:00:00.230', msg: 'Message sent successfully!', type: 'success' },
  ];

  return (
    <div className="bg-[#0a0f1c] border border-slate-800 rounded-xl p-6 lg:p-8 shadow-lg relative overflow-hidden mb-12">

      {/* Section Header */}
      <div className="flex items-center space-x-3 mb-8">
        <Terminal className="w-5 h-5 text-[#00E5FF]" />
        <h2 className="text-[#00E5FF] text-sm font-bold tracking-widest uppercase">Execution Console</h2>
      </div>

      <div className="flex flex-col xl:flex-row gap-6">

        {/* Left: Terminal Window */}
        <div className="flex-1 bg-black border border-slate-800 rounded-lg p-5 font-mono text-[10px] sm:text-xs overflow-y-auto h-72 shadow-inner">
          <div className="space-y-2">
            {logs.map((log, index) => (
              <div key={index} className="flex space-x-3">
                <span className="text-[#00E5FF]/70 shrink-0">[{log.time}]</span>
                <span className={`${
                  log.type === 'success' ? 'text-[#00FF66]' : 'text-slate-300'
                } ${log.bold ? 'font-bold tracking-wider' : ''}`}>
                  {log.msg}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Target Hit Graphic */}
        <div className="xl:w-1/3 bg-[#050a14] border border-[#00FF66]/30 rounded-lg p-6 flex flex-col items-center justify-center relative overflow-hidden shadow-[0_0_20px_rgba(0,255,102,0.1)] h-72 xl:h-auto">

          {/* Decorative Radar Background */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_20%,_#00FF66_150%)] opacity-10"></div>

          <div className="relative z-10 flex flex-col items-center">

            {/* Animated Crosshair */}
            <div className="relative mb-6">
              <Target className="w-20 h-20 text-[#00FF66] animate-pulse" />
              {/* Ping effect behind the crosshair */}
              <div className="absolute inset-0 border-2 border-[#00FF66] rounded-full animate-ping opacity-20"></div>
            </div>

            <h3 className="text-[#00FF66] text-2xl lg:text-3xl font-black tracking-widest uppercase mb-2 drop-shadow-[0_0_10px_rgba(0,255,102,0.5)]">
              TARGET HIT!
            </h3>

            <div className="flex items-center space-x-2 text-slate-300 text-sm font-medium">
              <span>Booking request sent.</span>
              <CheckCircle2 className="w-4 h-4 text-[#00FF66]" />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}