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

function spotScheduleActive(schedule, now = new Date()) {
  // Validar período de datas
  if (schedule.starts_at && now < new Date(schedule.starts_at)) return false;
  if (schedule.ends_at && now > new Date(schedule.ends_at)) return false;

  // Validar janela de hora do dia
  const hhmm = nowHHMM(now);
  if (schedule.start_time && hhmm < schedule.start_time) return false;
  if (schedule.end_time && hhmm > schedule.end_time) return false;

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
