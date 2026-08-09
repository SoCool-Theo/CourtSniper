import {
  Globe2,
  HardDrive,
  PlugZap,
  ShieldCheck,
  Wifi,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import StatusCard from '../components/StatusCard';
import useCourtSniper from '../context/useCourtSniper';

export default function SystemStatus() {
  const { connectionStatus } = useCourtSniper();
  const apiStatus = connectionStatus === 'online'
    ? { value: 'Online', tone: 'green' }
    : connectionStatus === 'offline'
      ? { value: 'Offline', tone: 'danger' }
      : { value: 'Checking', tone: 'warning' };
  const systemStatuses = [
    { icon: Wifi, label: 'Backend Connection', ...apiStatus },
    { icon: PlugZap, label: 'System Power', value: 'Not Reported', tone: 'cyan' },
    { icon: Globe2, label: 'Browser Status', value: 'Not Reported', tone: 'cyan' },
    { icon: ShieldCheck, label: 'Session Status', value: 'Not Reported', tone: 'cyan' },
    { icon: HardDrive, label: 'Disk Space', value: 'Not Reported', tone: 'cyan' },
  ];

  return (
    <div className="tactical-panel">
      <SectionHeader icon={PlugZap} title="System Status" />

      <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {systemStatuses.map((status) => (
          <StatusCard key={status.label} {...status} />
        ))}
      </div>
    </div>
  );
}
