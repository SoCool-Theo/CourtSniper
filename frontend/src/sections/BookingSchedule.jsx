import { CalendarDays, ExternalLink } from 'lucide-react';

const scheduleUrl = 'https://docs.google.com/spreadsheets/d/1G8k_wcWEt75Udp_ueUd42EGNAyFaq2gy/htmlview#gid=1516199695';

export default function BookingSchedule() {
  return (
    <section
      aria-labelledby="booking-schedule-title"
      className="tactical-panel flex flex-wrap items-center gap-4 p-5 sm:p-6 md:flex-nowrap"
    >
      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border border-court-line bg-court-cyan/5 text-court-cyan">
        <CalendarDays aria-hidden="true" className="h-6 w-6" />
      </div>

      <div className="min-w-0 flex-1 basis-[calc(100%-4rem)] md:basis-auto">
        <h2 id="booking-schedule-title" className="text-lg font-bold text-court-text">
          Court Booking Schedule
        </h2>
        <p className="mt-1 text-sm font-medium text-court-text/70">
          Check the schedule before setting up your booking.
        </p>
      </div>

      <div className="w-full shrink-0 text-center md:w-auto">
        <a
          href={scheduleUrl}
          target="_blank"
          rel="noopener noreferrer"
          aria-label="View booking schedule, opens in a new tab"
          className="tactical-button min-h-11 w-full px-4 md:w-auto"
        >
          View Schedule
          <ExternalLink aria-hidden="true" className="h-4 w-4" />
        </a>
        <p className="mt-2 text-xs font-medium text-court-muted">Opens in a new tab</p>
      </div>
    </section>
  );
}
