import { useState } from 'react';
import {
  CalendarDays,
  ExternalLink,
  Save,
  SlidersHorizontal,
} from 'lucide-react';
import SectionHeader from '../components/SectionHeader';

const hours = Array.from({ length: 24 }, (_, index) => index.toString().padStart(2, '0'));
const minutesAndSeconds = Array.from({ length: 60 }, (_, index) => index.toString().padStart(2, '0'));

function getDefaultDate() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  const year = date.getFullYear();
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const day = date.getDate().toString().padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function TimeSelect({ label, value, options, onChange }) {
  return (
    <div className="min-w-0 flex-1">
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="tactical-input h-10 cursor-pointer px-3 font-mono text-sm [color-scheme:dark]"
        aria-label={label}
      >
        {options.map((option) => (
          <option key={option} value={option}>{option}</option>
        ))}
      </select>
      <div className="mt-1.5 text-center text-[0.58rem] font-bold uppercase tracking-label text-court-muted">
        {label}
      </div>
    </div>
  );
}

export default function Configuration() {
  const [url, setUrl] = useState('https://www.messenger.com/t/1234567890123456');
  const [message, setMessage] = useState('Hi, I would like to book badminton court\nat 4 - 5pm. Thank you!');
  const [date, setDate] = useState(getDefaultDate);
  const [hour, setHour] = useState('09');
  const [minute, setMinute] = useState('00');
  const [second, setSecond] = useState('00');

  return (
    <div className="tactical-panel">
      <SectionHeader icon={SlidersHorizontal} title="Booking Configuration" />

      <div className="p-3 sm:p-4">
        <div className="grid gap-6 rounded-md border border-court-line-soft/75 bg-court-inset/40 p-4 lg:grid-cols-2 lg:p-5">
          <div className="space-y-4">
            <div>
              <label htmlFor="target-url" className="tactical-label mb-2 block">Target URL</label>
              <div className="relative">
                <input
                  id="target-url"
                  type="url"
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  className="tactical-input h-10 px-3 pr-10 text-sm"
                  spellCheck="false"
                />
                <ExternalLink aria-hidden="true" className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-court-text/70" />
              </div>
            </div>

            <div>
              <label htmlFor="booking-message" className="tactical-label mb-2 block">Booking Message</label>
              <div className="relative">
                <textarea
                  id="booking-message"
                  value={message}
                  onChange={(event) => setMessage(event.target.value)}
                  maxLength={1000}
                  rows={4}
                  className="tactical-input min-h-28 resize-none px-3 py-3 pb-7 font-mono text-xs leading-relaxed"
                />
                <span className="pointer-events-none absolute bottom-2.5 right-3 font-mono text-[0.6rem] text-court-muted">
                  {message.length} / 1000
                </span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <label htmlFor="target-date" className="tactical-label mb-2 block">Target Date</label>
              <div className="relative">
                <CalendarDays aria-hidden="true" className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-court-text/80" />
                <input
                  id="target-date"
                  type="date"
                  value={date}
                  onChange={(event) => setDate(event.target.value)}
                  className="tactical-input h-10 px-10 text-sm [color-scheme:dark]"
                />
              </div>
            </div>

            <div>
              <span className="tactical-label mb-2 block">Target Time (24H)</span>
              <div className="flex gap-3">
                <TimeSelect label="HH" value={hour} options={hours} onChange={setHour} />
                <TimeSelect label="MM" value={minute} options={minutesAndSeconds} onChange={setMinute} />
                <TimeSelect label="SS" value={second} options={minutesAndSeconds} onChange={setSecond} />
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-center pt-3">
          <button type="button" className="tactical-button min-h-10 w-full max-w-[24rem] px-6">
            <Save aria-hidden="true" className="h-4 w-4" />
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
