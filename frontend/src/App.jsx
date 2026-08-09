import AppShell from './components/AppShell';
import Dashboard from './sections/Dashboard';
import Configuration from './sections/Configuration';
import Session from './sections/Session';
import Scheduler from './sections/Scheduler';
import SystemStatus from './sections/SystemStatus';
import ExecutionConsole from './sections/ExecutionConsole';
import SecurityNotice from './components/SecurityNotice';

function App() {
  return (
    <AppShell>
      <section id="dashboard" className="scroll-mt-28">
        <Dashboard />
      </section>

      <section id="configuration" className="scroll-mt-28">
        <Configuration />
      </section>

      <section id="session" className="scroll-mt-28">
        <Session />
      </section>

      <section id="scheduler" className="scroll-mt-28">
        <Scheduler />
      </section>

      <section id="system-status" className="scroll-mt-28">
        <SystemStatus />
      </section>

      <section id="logs" className="scroll-mt-28">
        <ExecutionConsole />
      </section>

      <SecurityNotice />
    </AppShell>
  );
}

export default App;
