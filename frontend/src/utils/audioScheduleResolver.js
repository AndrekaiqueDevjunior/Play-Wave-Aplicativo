/**
 * audioScheduleResolver.js — Resolvedor de agendamentos de áudio
 *
 * Funções para determinar:
 * - Qual pasta de áudio deve tocar no horário atual
 * - Quais spots devem ser executados
 * - Resolução de conflitos por prioridade
 */

/**
 * Verifica se um horário está dentro de um intervalo
 * @param {string} time - Horário atual "HH:MM"
 * @param {string} startTime - Horário início "HH:MM"
 * @param {string} endTime - Horário fim "HH:MM"
 * @returns {boolean}
 */
function isTimeInRange(time, startTime, endTime) {
  if (!startTime || !endTime) return true;

  const [h, m] = time.split(":").map(Number);
  const [sh, sm] = startTime.split(":").map(Number);
  const [eh, em] = endTime.split(":").map(Number);

  const current = h * 60 + m;
  const start = sh * 60 + sm;
  const end = eh * 60 + em;

  // Caso normal: start < end (ex: 08:00 - 18:00)
  if (start < end) {
    return current >= start && current < end;
  }

  // Caso overnight: start > end (ex: 22:00 - 06:00)
  return current >= start || current < end;
}

/**
 * Verifica se uma data está dentro de um intervalo
 * @param {Date} now - Data atual
 * @param {string|null} startsAt - Data início (ISO string)
 * @param {string|null} endsAt - Data fim (ISO string)
 * @returns {boolean}
 */
function isDateInRange(now, startsAt, endsAt) {
  const nowMs = now.getTime();

  if (startsAt) {
    const startMs = Date.parse(startsAt);
    if (Number.isFinite(startMs) && nowMs < startMs) return false;
  }

  if (endsAt) {
    const endMs = Date.parse(endsAt);
    if (Number.isFinite(endMs) && nowMs > endMs) return false;
  }

  return true;
}

/**
 * Verifica se um dia da semana está ativo
 * @param {Date} now - Data atual
 * @param {Array<number>|null} daysOfWeek - Array de dias (0=domingo, 6=sábado)
 * @returns {boolean}
 */
function isDayActive(now, daysOfWeek) {
  if (!daysOfWeek || !Array.isArray(daysOfWeek) || daysOfWeek.length === 0) {
    return true;
  }

  const currentDay = now.getDay(); // 0 = domingo, 6 = sábado
  return daysOfWeek.includes(currentDay);
}

/**
 * Resolve qual pasta de áudio deve tocar no momento atual
 *
 * @param {Array} folderSchedules - Array de AudioPlaylistFolderSchedule
 * @param {Date} now - Data/hora atual (opcional, default = agora)
 * @returns {Object|null} - Pasta ativa ou null
 */
export function resolveActiveFolderForNow(folderSchedules, now = new Date()) {
  if (!folderSchedules || folderSchedules.length === 0) return null;

  const currentTime = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;

  // Filtrar pastas ativas
  const activeFolders = folderSchedules.filter((schedule) => {
    // Verificar se está ativa
    if (schedule.is_active === false) return false;

    // Verificar data
    if (!isDateInRange(now, schedule.starts_at, schedule.ends_at)) return false;

    // Verificar dia da semana
    if (!isDayActive(now, schedule.days_of_week)) return false;

    // Verificar horário
    if (!isTimeInRange(currentTime, schedule.start_time, schedule.end_time)) {
      return false;
    }

    return true;
  });

  if (activeFolders.length === 0) return null;

  // Se houver múltiplas pastas ativas, usar prioridade
  if (activeFolders.length > 1) {
    activeFolders.sort((a, b) => (b.priority || 0) - (a.priority || 0));
  }

  return activeFolders[0];
}

/**
 * Resolve quais spots devem ser executados no momento atual
 *
 * @param {Array} spotSchedules - Array de AudioSpotSchedule
 * @param {Date} now - Data/hora atual (opcional, default = agora)
 * @returns {Array} - Array de spots ativos ordenados por prioridade
 */
export function resolveActiveSpotsForNow(spotSchedules, now = new Date()) {
  if (!spotSchedules || spotSchedules.length === 0) return [];

  const currentTime = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}`;

  // Filtrar spots ativos
  const activeSpots = spotSchedules.filter((schedule) => {
    // Verificar se está ativo
    if (schedule.is_active === false) return false;

    // Verificar data
    if (!isDateInRange(now, schedule.starts_at, schedule.ends_at)) return false;

    // Verificar horário
    if (!isTimeInRange(currentTime, schedule.start_time, schedule.end_time)) {
      return false;
    }

    return true;
  });

  // Ordenar por prioridade (maior primeiro)
  activeSpots.sort((a, b) => (b.priority || 0) - (a.priority || 0));

  return activeSpots;
}

/**
 * Calcula quando o próximo spot deve tocar
 *
 * @param {Object} spotSchedule - AudioSpotSchedule
 * @param {Date} lastPlayedAt - Última vez que o spot tocou
 * @param {Date} now - Data/hora atual (opcional, default = agora)
 * @returns {Date|null} - Próximo horário de execução ou null
 */
export function calculateNextSpotTime(spotSchedule, lastPlayedAt, now = new Date()) {
  if (!spotSchedule || !spotSchedule.interval_seconds) return null;

  const intervalMs = spotSchedule.interval_seconds * 1000;

  if (!lastPlayedAt) {
    // Primeira execução: tocar agora
    return now;
  }

  const nextTime = new Date(lastPlayedAt.getTime() + intervalMs);

  // Se o próximo horário já passou, calcular o próximo válido
  if (nextTime < now) {
    const elapsed = now.getTime() - lastPlayedAt.getTime();
    const intervals = Math.ceil(elapsed / intervalMs);
    return new Date(lastPlayedAt.getTime() + intervals * intervalMs);
  }

  return nextTime;
}

/**
 * Verifica se é hora de tocar um spot
 *
 * @param {Object} spotSchedule - AudioSpotSchedule
 * @param {Date} lastPlayedAt - Última vez que o spot tocou
 * @param {Date} now - Data/hora atual (opcional, default = agora)
 * @param {number} toleranceMs - Tolerância em ms (default: 5000 = 5s)
 * @returns {boolean}
 */
export function shouldPlaySpotNow(
  spotSchedule,
  lastPlayedAt,
  now = new Date(),
  toleranceMs = 5000
) {
  const nextTime = calculateNextSpotTime(spotSchedule, lastPlayedAt, now);
  if (!nextTime) return false;

  const diff = now.getTime() - nextTime.getTime();

  // Tocar se estamos dentro da tolerância (antes ou depois)
  return Math.abs(diff) <= toleranceMs;
}

/**
 * Embaralha array usando algoritmo Fisher-Yates
 *
 * @param {Array} array - Array para embaralhar
 * @returns {Array} - Novo array embaralhado
 */
export function shuffleArray(array) {
  const shuffled = [...array];

  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }

  return shuffled;
}

/**
 * Cria fila de reprodução baseada no modo
 *
 * @param {Array} tracks - Array de faixas
 * @param {string} mode - Modo de reprodução: "sequential", "shuffle", "loop"
 * @returns {Array} - Fila de reprodução
 */
export function createPlaybackQueue(tracks, mode = "sequential") {
  if (!tracks || tracks.length === 0) return [];

  switch (mode) {
    case "shuffle":
      return shuffleArray(tracks);

    case "loop":
    case "sequential":
    default:
      return [...tracks];
  }
}

/**
 * Detecta mudança de pasta ativa
 *
 * @param {Object} currentFolder - Pasta atual
 * @param {Object} newFolder - Nova pasta
 * @returns {boolean} - True se mudou
 */
export function hasFolderChanged(currentFolder, newFolder) {
  if (!currentFolder && !newFolder) return false;
  if (!currentFolder && newFolder) return true;
  if (currentFolder && !newFolder) return true;

  return currentFolder.id !== newFolder.id;
}

/**
 * Formata tempo para exibição
 *
 * @param {number} seconds - Segundos
 * @returns {string} - Formato "MM:SS"
 */
export function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return "00:00";

  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);

  return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
}

/**
 * Calcula tempo total de uma playlist
 *
 * @param {Array} tracks - Array de faixas
 * @returns {number} - Tempo total em segundos
 */
export function calculateTotalDuration(tracks) {
  if (!tracks || tracks.length === 0) return 0;

  return tracks.reduce((total, track) => {
    return total + (track.duration_seconds || 0);
  }, 0);
}
