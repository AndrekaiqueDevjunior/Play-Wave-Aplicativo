// @ts-nocheck
/**
 * spotScheduleResolver — resolve QUAIS spots devem tocar AGORA, considerando
 * janela horária, período de datas, dias da semana e prioridade.
 *
 * Mesma convenção de dias do radioScheduleResolver:
 * Backend usa Python weekday() (segunda=0 … domingo=6).
 */

function nowHHMM(date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes(),
  ).padStart(2, "0")}`;
}

function pythonWeekday(date) {
  return (date.getDay() + 6) % 7;
}

function inDayOfWeek(daysOfWeek, date) {
  if (!Array.isArray(daysOfWeek) || daysOfWeek.length === 0) return true;
  const dow = pythonWeekday(date);
  return daysOfWeek.some((d) => Number(d) === dow);
}

function inTimeWindow(schedule, date) {
  if (!schedule.start_time && !schedule.end_time) return true;

  const hhmm = nowHHMM(date);
  const start = schedule.start_time;
  const end = schedule.end_time;

  if (start && !end) return hhmm >= start;
  if (!start && end) return hhmm <= end;
  if (start <= end) return hhmm >= start && hhmm <= end;

  return hhmm >= start || hhmm <= end;
}

/**
 * Converte string de data/hora do backend (naive, fuso Brasília) para Date local.
 * O backend grava starts_at/ends_at como datetime naive em UTC (sem sufixo Z).
 * new Date("2026-06-07 13:00:00") é ambíguo: Chrome trata como local, Node como UTC.
 * Normalizamos substituindo espaço por T e garantindo sufixo Z para UTC → depois
 * comparamos com now em UTC também para consistência.
 */
function parseBackendDate(str) {
  if (!str) return null;
  // "2026-06-07T13:00:00" ou "2026-06-07 13:00:00" → força UTC com Z
  return new Date(str.replace(" ", "T").replace(/Z?$/, "Z"));
}

function spotScheduleActive(schedule, now = new Date()) {
  // Validar período de datas (starts_at/ends_at do backend estão em UTC)
  if (schedule.starts_at) {
    const start = parseBackendDate(schedule.starts_at);
    if (start && now < start) return false;
  }
  if (schedule.ends_at) {
    const end = parseBackendDate(schedule.ends_at);
    if (end && now > end) return false;
  }

  // Validar janela de hora do dia (start_time/end_time são HH:MM locais)
  if (!inTimeWindow(schedule, now)) return false;

  // Validar dia da semana
  if (!inDayOfWeek(schedule.days_of_week, now)) return false;

  return true;
}

export const spotScheduleResolver = {
  /**
   * Retorna spots elegíveis para tocar agora, ordenados por prioridade.
   * @param {Array} schedules spot_schedules do backend
   * @param {Date} now
   * @returns {Array}
   */
  getEligibleSpots(schedules, now = new Date()) {
    if (!Array.isArray(schedules)) return [];
    return schedules
      .filter((s) => s?.file_url && s?.interval_seconds && spotScheduleActive(s, now))
      .sort((a, b) => (b.priority || 0) - (a.priority || 0));
  },

  /**
   * Verifica se um spot específico está ativo agora.
   * @param {object} schedule
   * @param {Date} now
   * @returns {boolean}
   */
  isActive(schedule, now = new Date()) {
    return spotScheduleActive(schedule, now);
  },
};
