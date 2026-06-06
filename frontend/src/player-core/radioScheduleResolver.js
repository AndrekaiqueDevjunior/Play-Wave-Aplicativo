// @ts-nocheck
/**
 * radioScheduleResolver — resolve QUAL conjunto de faixas o rádio indoor deve
 * tocar AGORA, considerando as pastas agendadas (folder_schedules) com janela
 * horária, dias da semana e prioridade.
 *
 * Hierarquia:
 *   1. folder_schedule ativo de MAIOR prioridade que tenha faixas → toca a pasta
 *   2. fallback → tracks base da playlist sonora
 *
 * Convenção de dias: backend usa Python weekday() (segunda=0 … domingo=6).
 * JS Date.getDay() usa domingo=0 … sábado=6, então convertemos.
 */

import { AUDIO_MODE } from "../lib/audioManager.js";

function nowHHMM(date) {
  return `${String(date.getHours()).padStart(2, "0")}:${String(
    date.getMinutes(),
  ).padStart(2, "0")}`;
}

/** Converte JS getDay() (dom=0) para weekday() Python (seg=0). */
function pythonWeekday(date) {
  return (date.getDay() + 6) % 7;
}

function inDayOfWeek(daysOfWeek, date) {
  if (!Array.isArray(daysOfWeek) || daysOfWeek.length === 0) return true;
  const dow = pythonWeekday(date);
  // Aceita tanto número (0-6) quanto string numérica.
  return daysOfWeek.some((d) => Number(d) === dow);
}

function scheduleActive(sched, date) {
  // Validar período de datas (starts_at / ends_at)
  if (sched.starts_at && date < new Date(sched.starts_at)) return false;
  if (sched.ends_at && date > new Date(sched.ends_at)) return false;

  // Validar janela de hora do dia
  const hhmm = nowHHMM(date);
  if (sched.start_time && hhmm < sched.start_time) return false;
  if (sched.end_time && hhmm > sched.end_time) return false;

  // Validar dia da semana
  if (!inDayOfWeek(sched.days_of_week, date)) return false;
  return true;
}

/**
 * Resolve o conjunto de faixas ativo do rádio indoor neste instante.
 *
 * @param {object|null} audioPlaylist payload do backend (audio_playlist)
 * @param {Date} now
 * @returns {{ source: "folder"|"playlist"|"empty", folderName: string|null,
 *             tracks: Array, mode: string, scheduleId: string|null }}
 */
export function resolveActiveRadio(audioPlaylist, now = new Date()) {
  const baseTracks = audioPlaylist?.tracks || [];
  const folderScheds = audioPlaylist?.folder_schedules || [];

  // Pasta agendada ativa de maior prioridade COM faixas.
  const activeFolder = folderScheds
    .filter((s) => s?.tracks?.length && scheduleActive(s, now))
    .sort((a, b) => (b.priority || 0) - (a.priority || 0))[0];

  if (activeFolder) {
    return {
      source: "folder",
      folderName: activeFolder.folder_name || null,
      tracks: activeFolder.tracks,
      mode:
        activeFolder.play_mode === "shuffle"
          ? AUDIO_MODE.SHUFFLE
          : AUDIO_MODE.SEQUENTIAL,
      scheduleId: activeFolder.id,
    };
  }

  if (baseTracks.length) {
    return {
      source: "playlist",
      folderName: null,
      tracks: baseTracks,
      mode: audioPlaylist?.shuffle
        ? AUDIO_MODE.SHUFFLE
        : AUDIO_MODE.SEQUENTIAL,
      scheduleId: null,
    };
  }

  return {
    source: "empty",
    folderName: null,
    tracks: [],
    mode: AUDIO_MODE.SEQUENTIAL,
    scheduleId: null,
  };
}

/**
 * Indica se a playlist tem QUALQUER fonte de áudio reproduzível agora ou no
 * futuro (faixas base ou pastas com faixas). Usado para decidir se o player
 * entra em "playing" mesmo sem mídia visual.
 */
export function hasAnyRadioContent(audioPlaylist) {
  if (audioPlaylist?.tracks?.length) return true;
  return (audioPlaylist?.folder_schedules || []).some(
    (s) => s?.tracks?.length,
  );
}
