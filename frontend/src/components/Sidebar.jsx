import {
  LayoutDashboard,
  Settings,
  User,
  CalendarClock,
  Terminal,
  Target
} from 'lucide-react';

export default function Sidebar() {
  const navItems = [
    { name: 'Dashboard', icon: LayoutDashboard, href: '#dashboard', active: true },
    { name: 'Configuration', icon: Settings, href: '#configuration' },
    { name: 'Session', icon: User, href: '#session' },
    { name: 'Scheduler', icon: CalendarClock, href: '#scheduler' },
    { name: 'Logs', icon: Terminal, href: '#logs' },
    { name: 'Settings', icon: Settings, href: '#settings' },
  ];

  return (
    <aside className="w-64 h-screen bg-[#0a0f1c] border-r border-slate-800 flex flex-col justify-between hidden lg:flex sticky top-0 shrink-0">

      {/* 1. Logo Section */}
      <div className="p-8 border-b border-slate-800 flex items-center space-x-3">
        <Target className="text-[#00FF66] w-10 h-10 shrink-0" />
        <div className="flex flex-col">
          <span className="text-white font-black text-2xl italic tracking-widest leading-none">COURT</span>
          <span className="text-[#00FF66] font-black text-xl italic tracking-widest leading-none">SNIPER</span>
        </div>
      </div>

      {/* 2. Anchor Navigation Links */}
      <nav className="flex-1 p-4 space-y-2 overflow-y-auto mt-4">
        {navItems.map((item) => (
          <a
            key={item.name}
            href={item.href}
            className={`flex items-center space-x-3 px-4 py-3 rounded-md transition-all duration-200 group ${
              item.active 
                ? 'bg-slate-800/50 text-[#00FF66] border-l-2 border-[#00FF66]' 
                : 'text-slate-400 hover:bg-slate-800/30 hover:text-white border-l-2 border-transparent'
            }`}
          >
            <item.icon className={`w-5 h-5 ${item.active ? 'text-[#00FF66]' : 'text-slate-500 group-hover:text-cyan-400'}`} />
            <span className="font-semibold text-sm tracking-wide">{item.name}</span>
          </a>
        ))}
      </nav>

      {/* 3. Bottom Status Footer */}
      <div className="p-6 border-t border-slate-800">
        <div className="flex items-center space-x-2 mb-2">
          <div className="w-2.5 h-2.5 bg-[#00FF66] rounded-full animate-pulse shadow-[0_0_8px_#00FF66]"></div>
          <span className="text-slate-300 text-xs font-semibold">All systems go.</span>
        </div>
        <div className="text-slate-500 text-xs flex items-center space-x-2">
          <span>Good luck! 🎯</span>
        </div>
      </div>

    </aside>
  );
}