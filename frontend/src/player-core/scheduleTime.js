// Helpers compartilhados para regras de agenda no player.
// Convencao do backend: weekday Python (segunda=0 ... domingo=6) e datetimes
// sem timezone representam o horario operacional/local, nao UTC.

export function pythonWeekday(date) {
  return (date.getDay() + 6) % 7;
}

export function parseBackendDateTime(value) {
  if (!value) return null;
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value;

  const raw = String(value).trim();
  if (!raw) return null;

  const normalized = raw.includes(" ") ? raw.replace(" ", "T") : raw;
  const parsed = new Date(normalized);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function nowHHMM(date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes(),
  ).padStart(2, "0")}`;
}

function hhmmToMinutes(value) {
  if (!value) return null;
  const [h, m] = String(value).split(":").map(Number);
  if (!Number.isFinite(h) || !Number.isFinite(m)) return null;
  return h * 60 + m;
}

export function isTimeInWindow(hhmm, startTime, endTime) {
  const current = hhmmToMinutes(hhmm);
  if (current == null) return false;

  const start = hhmmToMinutes(startTime);
  const end = hhmmToMinutes(endTime);

  if (start != null && end != null) {
    if (start <= end) return current >= start && current < end;
    return current >= start || current < end;
  }
  if (start != null) return current >= start;
  if (end != null) return current < end;
  return true;
}

export function isDateTimeInRange(now, startsAt, endsAt) {
  const start = parseBackendDateTime(startsAt);
  if (start && now < start) return false;

  const end = parseBackendDateTime(endsAt);
  if (end && now > end) return false;

  return true;
}

export function isDayAllowed(daysOfWeek, date) {
  if (!Array.isArray(daysOfWeek) || daysOfWeek.length === 0) return true;
  const dow = pythonWeekday(date);
  return daysOfWeek.some((d) => Number(d) === dow);
}
