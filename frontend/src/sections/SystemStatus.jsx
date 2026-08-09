import {
  Globe2,
  HardDrive,
  PlugZap,
  ShieldCheck,
  Wifi,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';
import StatusCard from '../components/StatusCard';

const systemStatuses = [
  { icon: Wifi, label: 'Internet Connection', value: 'Online' },
  { icon: PlugZap, label: 'System Power', value: 'AC Power' },
  { icon: Globe2, label: 'Browser Status', value: 'Ready' },
  { icon: ShieldCheck, label: 'Session Status', value: 'Valid' },
  { icon: HardDrive, label: 'Disk Space', value: '128 GB Free' },
];

export default function SystemStatus() {
  return (
    <div className="tactical-panel">
      <SectionHeader icon={PlugZap} title="System Status" />

      <div className="grid gap-3 p-4 sm:grid-cols-2 lg:grid-cols-5">
        {systemStatuses.map((status) => (
          <StatusCard key={status.label} {...status} />
        ))}
      </div>
    </div>
  );
}
