import { useEffect, useState } from 'react';
import {
  CalendarDays,
  LayoutGrid,
  Settings,
  TerminalSquare,
  UserRound,
  X,
} from 'lucide-react';
import { assetUrl } from '../assets';

const navigation = [
  { name: 'Dashboard', icon: LayoutGrid, href: '#dashboard', section: 'dashboard' },
  { name: 'Configuration', icon: Settings, href: '#configuration', section: 'configuration' },
  { name: 'Session', icon: UserRound, href: '#session', section: 'session' },
  { name: 'Scheduler', icon: CalendarDays, href: '#scheduler', section: 'scheduler' },
  { name: 'Logs', icon: TerminalSquare, href: '#logs', section: 'logs' },
  { name: 'Settings', icon: Settings, href: '#settings', section: 'settings' },
];

function useActiveSection() {
  const [activeSection, setActiveSection] = useState('dashboard');

  useEffect(() => {
    const sectionIds = navigation
      .map((item) => item.section)
      .filter((section) => document.getElementById(section));

    const updateActiveSection = () => {
      let current = sectionIds[0] ?? 'dashboard';
      let largestVisibleArea = 0;
      const headerOffset = 112;

      sectionIds.forEach((id) => {
        const element = document.getElementById(id);
        if (!element) return;

        const bounds = element.getBoundingClientRect();
        const visibleTop = Math.max(bounds.top, headerOffset);
        const visibleBottom = Math.min(bounds.bottom, window.innerHeight);
        const visibleArea = Math.max(0, visibleBottom - visibleTop);

        if (visibleArea > largestVisibleArea) {
          largestVisibleArea = visibleArea;
          current = id;
        }
      });

      setActiveSection(current);
    };

    updateActiveSection();
    window.addEventListener('scroll', updateActiveSection, { passive: true });
    window.addEventListener('resize', updateActiveSection);

    return () => {
      window.removeEventListener('scroll', updateActiveSection);
      window.removeEventListener('resize', updateActiveSection);
    };
  }, []);

  return [activeSection, setActiveSection];
}

export default function Sidebar({ isOpen, onClose }) {
  const [activeSection, setActiveSection] = useActiveSection();

  const handleNavigation = (section) => {
    setActiveSection(section);
    onClose();
  };

  return (
    <>
      <button
        type="button"
        aria-label="Close navigation overlay"
        onClick={onClose}
        className={`fixed inset-0 z-40 bg-court-void/80 backdrop-blur-sm transition-opacity lg:hidden ${
          isOpen ? 'pointer-events-auto opacity-100' : 'pointer-events-none opacity-0'
        }`}
      />

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[10rem] flex-col border-r border-court-line bg-court-panel/98 shadow-panel transition-transform duration-300 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
        aria-label="Primary navigation"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-2 top-2 inline-flex h-8 w-8 items-center justify-center rounded border border-court-line text-court-cyan lg:hidden"
          aria-label="Close navigation"
        >
          <X aria-hidden="true" className="h-4 w-4" />
        </button>

        <a
          href="#dashboard"
          onClick={onClose}
          className="flex h-[9.8rem] shrink-0 flex-col items-center justify-center border-b border-court-line-soft/80 px-3 text-center"
          aria-label="CourtSniper dashboard"
        >
          <span className="mb-1.5 block w-[6.6rem] overflow-hidden">
            <img
              src={assetUrl('shuttlecock-mark')}
              alt=""
              className="w-full"
            />
          </span>
          <span className="font-display text-[1.25rem] font-bold italic leading-[0.95] tracking-tactical text-white">
            COURT
          </span>
          <span className="neon-green-text mt-1 font-display text-[1.25rem] font-bold italic leading-[0.95] tracking-tactical">
            SNIPER
          </span>
        </a>

        <nav className="flex-1 py-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = activeSection === item.section;

            return (
              <a
                key={item.name}
                href={item.href}
                onClick={() => handleNavigation(item.section)}
                aria-current={isActive ? 'page' : undefined}
                className={`group relative flex h-[3.85rem] items-center gap-3.5 px-5 text-[0.86rem] font-semibold transition-colors ${
                  isActive
                    ? 'bg-court-green/[0.08] text-white'
                    : 'text-court-text/80 hover:bg-court-cyan/[0.05] hover:text-white'
                }`}
              >
                <span
                  className={`absolute inset-y-0 left-0 w-[3px] transition-all ${
                    isActive
                      ? 'bg-court-green shadow-[0_0_12px_rgba(99,255,0,0.9)]'
                      : 'bg-transparent group-hover:bg-court-cyan/50'
                  }`}
                />
                <Icon
                  aria-hidden="true"
                  className={`h-5 w-5 shrink-0 ${
                    isActive ? 'text-court-cyan' : 'text-court-text'
                  }`}
                  strokeWidth={1.7}
                />
                <span className="truncate">{item.name}</span>
              </a>
            );
          })}
        </nav>

        <div className="shrink-0 border-t border-court-line-soft/80 px-5 py-4">
          <div className="mb-2 flex items-center gap-2 text-[0.76rem] font-semibold text-court-text">
            <span className="status-dot h-2 w-2 animate-status-pulse" />
            <span>All systems go.</span>
          </div>
          <p className="text-[0.73rem] font-medium text-court-muted">Good luck! 🎯</p>
        </div>
      </aside>
    </>
  );
}
