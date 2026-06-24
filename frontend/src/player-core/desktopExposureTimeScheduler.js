// @ts-nocheck
/**
 * desktopExposureTimeScheduler.js — SPEC 010
 *
 * Agenda exposições de desktop por HORÁRIO do dia (ex.: 08:00, 14:00), com
 * suporte a múltiplos eventos nomeados e dias da semana, reaproveitando a
 * primitiva `show_desktop` do Electron (SPEC 009) para minimizar/restaurar.
 *
 * Diferente de `windowExposureScheduler.js` (que dispara por INTERVALO), este
 * dispara em horários fixos e sobrevive a reinício do Player (recover()).
 *
 * Máquina de estados:
 *   RUNNING → MINIMIZING → MINIMIZED → WAITING_TIMER → RESTORING → RUNNING
 *
 * Convenção de weekdays: 0=Domingo .. 6=Sábado (Date.getDay()).
 * `weekdays` nulo/vazio = todos os dias.
 */

import {
  INTERRUPTION_POLICY,
  normalizeInterruptionPolicy,
} from "./contentGuard.js";

export const EXPOSURE_STATE = {
  RUNNING: "RUNNING",
  MINIMIZING: "MINIMIZING",
  MINIMIZED: "MINIMIZED",
  WAITING_TIMER: "WAITING_TIMER",
  RESTORING: "RESTORING",
};

const SCHEDULABLE_PHASES = new Set(["playing", "no_campaign"]);

function parseHHMM(time) {
  if (typeof time !== "string") return null;
  const m = /^([01]\d|2[0-3]):([0-5]\d)$/.exec(time.trim());
  if (!m) return null;
  return { h: Number(m[1]), m: Number(m[2]) };
}

/** Normaliza weekdays (CSV "1,2,3" ou array) → Set de inteiros 0..6, ou null. */
function parseWeekdays(weekdays) {
  if (weekdays == null || weekdays === "") return null;
  const arr = Array.isArray(weekdays)
    ? weekdays
    : String(weekdays).split(",");
  const set = new Set(
    arr
      .map((d) => Number(String(d).trim()))
      .filter((n) => Number.isInteger(n) && n >= 0 && n <= 6),
  );
  return set.size > 0 ? set : null;
}

/**
 * Próxima ocorrência (Date) de um evento, estritamente após `from`.
 * Respeita weekdays. Retorna null se o evento for inválido.
 */
export function nextOccurrence(event, from) {
  const hhmm = parseHHMM(event?.time);
  if (!hhmm) return null;
  const allowed = parseWeekdays(event?.weekdays);

  for (let offset = 0; offset <= 7; offset++) {
    const candidate = new Date(
      from.getFullYear(),
      from.getMonth(),
      from.getDate() + offset,
      hhmm.h,
      hhmm.m,
      0,
      0,
    );
    if (candidate.getTime() <= from.getTime()) continue;
    if (allowed && !allowed.has(candidate.getDay())) continue;
    return candidate;
  }
  return null;
}

/** Entre os eventos habilitados, o de menor próxima ocorrência. */
export function computeNext(events, from) {
  let best = null;
  for (const event of events || []) {
    if (!event?.enabled) continue;
    const at = nextOccurrence(event, from);
    if (!at) continue;
    if (!best || at.getTime() < best.at.getTime()) {
      best = { event, at };
    }
  }
  return best;
}

function clampDuration(value) {
  return Math.max(1, Math.min(300, Math.round(Number(value) || 1)));
}

export function createDesktopExposureTimeScheduler({
  executeShowDesktop, // (durationSeconds) => Promise
  persist = () => {}, // (action|null) => void | Promise
  loadPending = () => null, // () => action|null  (sync ou Promise)
  isElectron = false,
  now = () => new Date(),
  logger = console,
  // SPEC 015 — política WAIT_CONTENT_END: ao chegar o horário do evento,
  // espera o conteúdo atual terminar antes de minimizar. Opcional para não
  // quebrar instâncias existentes/testes que não passam essa dependência —
  // nesse caso o comportamento é o mesmo de antes (minimiza no horário exato).
  contentGuard = null,
  onWarning = null, // ({ secondsBefore, text, mediaId }) => void
}) {
  let nextTimerId = null;
  let restoreTimerId = null;
  let warnTimerId = null;
  let state = EXPOSURE_STATE.RUNNING;
  let lastEvents = [];
  let lastPhase = null;
  let cancelWaitForEnd = null;

  const clearNextTimer = () => {
    if (nextTimerId) {
      clearTimeout(nextTimerId);
      nextTimerId = null;
    }
  };
  const clearRestoreTimer = () => {
    if (restoreTimerId) {
      clearTimeout(restoreTimerId);
      restoreTimerId = null;
    }
  };
  const clearWarnTimer = () => {
    if (warnTimerId) {
      clearTimeout(warnTimerId);
      warnTimerId = null;
    }
  };

  const stop = () => {
    clearNextTimer();
    clearRestoreTimer();
    clearWarnTimer();
    if (cancelWaitForEnd) {
      cancelWaitForEnd();
      cancelWaitForEnd = null;
    }
  };

  const beginRestoreCountdown = (durationSeconds) => {
    state = EXPOSURE_STATE.WAITING_TIMER;
    clearRestoreTimer();
    restoreTimerId = setTimeout(() => {
      restoreTimerId = null;
      state = EXPOSURE_STATE.RESTORING;
      Promise.resolve(persist(null)).catch(() => {});
      logger.log("[desktopExposureTime] restored, back to RUNNING");
      state = EXPOSURE_STATE.RUNNING;
      // Reagenda o próximo evento.
      schedule({ events: lastEvents, phase: lastPhase });
    }, durationSeconds * 1000);
  };

  const runMinimize = async (event) => {
    const duration = clampDuration(event.duration_seconds);
    state = EXPOSURE_STATE.MINIMIZING;

    const action = {
      actionId: `${event.id ?? "evt"}-${now().getTime()}`,
      eventId: event.id ?? null,
      startedAt: now().toISOString(),
      durationSeconds: duration,
      status: "running",
    };

    logger.log("[desktopExposureTime] firing", event.name, action);

    try {
      await Promise.resolve(persist(action));
      state = EXPOSURE_STATE.MINIMIZED;
      await executeShowDesktop(duration);
      beginRestoreCountdown(duration);
    } catch (err) {
      logger.warn("[desktopExposureTime] fire failed:", err);
      Promise.resolve(persist(null)).catch(() => {});
      state = EXPOSURE_STATE.RUNNING;
      schedule({ events: lastEvents, phase: lastPhase });
    }
  };

  // Exibe o aviso configurado (se houver) e só então minimiza, após o atraso
  // de leitura (warning_seconds_before). Sem aviso, minimiza direto. O aviso é
  // disparado imediatamente ANTES da minimização (já respeitada a fronteira do
  // item), garantindo que apareça na tela antes da janela sumir.
  const warnThenMinimize = (event) => {
    if (event.show_warning && onWarning) {
      const secondsBefore = Number(event.warning_seconds_before || 0);
      onWarning({
        secondsBefore,
        text: event.warning_text || null,
        mediaId: event.warning_media_id || null,
      });
      const delayMs = Math.max(secondsBefore, 1) * 1000;
      logger.log(
        "[desktopExposureTime] aviso exibido — minimizando em",
        delayMs / 1000,
        "s",
        event.name,
      );
      clearWarnTimer();
      warnTimerId = setTimeout(() => {
        warnTimerId = null;
        runMinimize(event);
      }, delayMs);
      return;
    }
    runMinimize(event);
  };

  const fire = (event) => {
    // Só dispara em RUNNING — evita conflito com SPEC 009 e sobreposição.
    if (state !== EXPOSURE_STATE.RUNNING) {
      logger.log(
        "[desktopExposureTime] skip fire — state is",
        state,
        "not RUNNING",
      );
      schedule({ events: lastEvents, phase: lastPhase });
      return;
    }

    const policy = normalizeInterruptionPolicy(event.interruption_policy);
    const busy = contentGuard ? contentGuard.isContentBusy() : false;

    if (!contentGuard || policy === INTERRUPTION_POLICY.IMMEDIATE || !busy) {
      warnThenMinimize(event);
      return;
    }

    if (policy === INTERRUPTION_POLICY.NEVER) {
      logger.log(
        "[desktopExposureTime] conteúdo ativo + policy 'never' — evento pulado",
        event.name,
      );
      schedule({ events: lastEvents, phase: lastPhase });
      return;
    }

    // after_current_item (padrão): aguarda o item atual terminar.
    logger.log(
      "[desktopExposureTime] conteúdo ativo — aguardando fim do item antes de avisar/minimizar",
      event.name,
    );
    cancelWaitForEnd = contentGuard.onceContentEnd(() => {
      cancelWaitForEnd = null;
      warnThenMinimize(event);
    });
  };

  const schedule = ({ events, phase }) => {
    lastEvents = events || [];
    lastPhase = phase;
    clearNextTimer();

    if (!isElectron || !SCHEDULABLE_PHASES.has(phase)) return;

    const next = computeNext(lastEvents, now());
    if (!next) return;

    const delay = Math.max(0, next.at.getTime() - now().getTime());
    logger.log(
      "[desktopExposureTime] scheduling",
      next.event.name,
      "at",
      next.at.toISOString(),
      `(in ${Math.round(delay / 1000)}s)`,
    );
    nextTimerId = setTimeout(() => {
      nextTimerId = null;
      fire(next.event);
    }, delay);
  };

  /**
   * No boot do Player: retoma uma exposição que estava em andamento quando o
   * app foi reiniciado (CA-009).
   */
  const recover = async () => {
    let pending = null;
    try {
      pending = await Promise.resolve(loadPending());
    } catch {
      pending = null;
    }
    if (!pending || pending.status !== "running") return false;

    const elapsed =
      (now().getTime() - new Date(pending.startedAt).getTime()) / 1000;

    if (!Number.isFinite(elapsed) || elapsed >= pending.durationSeconds) {
      await Promise.resolve(persist(null)).catch(() => {});
      logger.log("[desktopExposureTime] recover: expired, cleared");
      return false;
    }

    const remaining = Math.max(1, Math.ceil(pending.durationSeconds - elapsed));
    logger.log("[desktopExposureTime] recover: resuming", remaining, "s");

    if (isElectron) {
      state = EXPOSURE_STATE.MINIMIZED;
      try {
        await executeShowDesktop(remaining);
        beginRestoreCountdown(remaining);
      } catch (err) {
        logger.warn("[desktopExposureTime] recover failed:", err);
        await Promise.resolve(persist(null)).catch(() => {});
        state = EXPOSURE_STATE.RUNNING;
      }
    }
    return true;
  };

  const getState = () => state;
  const isScheduled = () => nextTimerId != null;

  return { schedule, stop, recover, getState, isScheduled };
}
