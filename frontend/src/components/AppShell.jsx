import { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';

export default function AppShell({ children }) {
  const [isNavigationOpen, setIsNavigationOpen] = useState(false);

  return (
    <div className="min-h-screen bg-court-page text-court-text lg:pl-[7.5rem]">
      <Sidebar
        isOpen={isNavigationOpen}
        onClose={() => setIsNavigationOpen(false)}
      />

      <div className="min-h-screen min-w-0">
        <Header onMenuToggle={() => setIsNavigationOpen((open) => !open)} />

        <main className="mx-auto w-full max-w-[96rem] space-y-3 px-3 pb-6 pt-3 sm:px-4 lg:px-3">
          {children}
        </main>
      </div>
    </div>
  );
}
