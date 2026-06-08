// @ts-nocheck
/**
 * spotScheduleResolver — resolve QUAIS spots devem tocar AGORA, considerando
 * janela horária, período de datas, dias da semana e prioridade.
 *
 * Mesma convenção de dias do radioScheduleResolver:
 * Backend usa Python weekday() (segunda=0 … domingo=6).
 */

import {
  isDateTimeInRange,
  isDayAllowed,
  isTimeInWindow,
  nowHHMM,
} from "./scheduleTime.js";

function spotScheduleActive(schedule, now = new Date()) {
  if (!isDateTimeInRange(now, schedule.starts_at, schedule.ends_at)) return false;

  // Validar janela de hora do dia (start_time/end_time são HH:MM locais)
  if (!isTimeInWindow(nowHHMM(now), schedule.start_time, schedule.end_time)) return false;

  // Validar dia da semana
  if (!isDayAllowed(schedule.days_of_week, now)) return false;

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
