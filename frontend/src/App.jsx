import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Dashboard from './sections/Dashboard';
import Configuration from './sections/Configuration';
import Session from './sections/Session';
import Scheduler from './sections/Scheduler';
import ExecutionConsole from './sections/ExecutionConsole';

function App() {
  return (
    <div className="flex h-screen bg-[#0f172a] text-slate-300 font-sans overflow-hidden">

      {/* 1. Left Sidebar (Fixed) */}
      <Sidebar />

      {/* 2. Main Scrollable Container */}
      <div className="flex-1 flex flex-col h-full overflow-y-auto scroll-smooth">

        {/* Top Status Header */}
        <Header />

        {/* 3. The Anchor-Nav Sections */}
        <main className="flex-1 p-6 lg:p-10 space-y-12 max-w-7xl mx-auto w-full">
          <section id="dashboard" className="scroll-mt-24">
            <Dashboard />
          </section>

          <section id="configuration" className="scroll-mt-24">
            <Configuration />
          </section>

          <section id="session" className="scroll-mt-24">
            <Session />
          </section>

          <section id="scheduler" className="scroll-mt-24">
            <Scheduler />
          </section>

          <section id="logs" className="scroll-mt-24">
            <ExecutionConsole />
          </section>
        </main>

      </div>
    </div>
  );
}

export default App;