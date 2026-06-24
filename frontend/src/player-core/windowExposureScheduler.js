import {
  INTERRUPTION_POLICY,
  normalizeInterruptionPolicy,
} from "./contentGuard.js";

/**
 * windowExposureScheduler — exposição de desktop por INTERVALO (SPEC 009/015).
 *
 * Fluxo correto da ação (SPEC-007 / pedido do cliente Windows):
 *
 *   [intervalo vence]
 *     → política de interrupção (never | after_current_item | immediate)
 *     → (after_current_item) aguarda o item atual terminar  ← não atravessa mídia
 *     → exibe o AVISO configurado (onWarning)               ← aviso aparece
 *     → aguarda warning_seconds_before                      ← tempo de leitura
 *     → minimiza (executeCommand show_desktop)
 *     → Electron restaura após duration_seconds
 *
 * Ponto-chave da correção: o aviso é disparado IMEDIATAMENTE ANTES de
 * minimizar (depois de respeitada a fronteira do item), com um atraso real
 * (warning_seconds_before) entre aviso e minimização. Antes, o aviso era
 * disparado no momento do intervalo e a minimização acontecia depois, sem
 * atraso — quando não havia mídia ativa, a janela minimizava no mesmo tick do
 * setState do aviso (antes do React pintar), e o aviso "não aparecia".
 */
export function createWindowExposureScheduler({
  executeCommand,
  isElectron = false,
  logger = console,
  // SPEC 015 — contentGuard é opcional (testes/instâncias antigas). Sem ele,
  // a ação executa imediatamente no intervalo (comportamento legado).
  contentGuard = null,
  onWarning = null, // ({ secondsBefore, text, mediaId }) => void
}) {
  let timerId = null;
  let warnTimerId = null;
  let cancelWaitForEnd = null;

  const clearWarnTimer = () => {
    if (warnTimerId) {
      clearTimeout(warnTimerId);
      warnTimerId = null;
    }
  };

  const stop = () => {
    if (timerId) {
      clearTimeout(timerId);
      timerId = null;
    }
    if (cancelWaitForEnd) {
      cancelWaitForEnd();
      cancelWaitForEnd = null;
    }
    clearWarnTimer();
  };

  const schedule = ({
    desktopExposureConfig,
    deviceId,
    deviceToken,
    phase,
    commandContext,
  }) => {
    stop();

    if (
      !deviceId ||
      !deviceToken ||
      !desktopExposureConfig?.enabled ||
      phase === "waiting" ||
      phase === "loading" ||
      !isElectron
    ) {
      return;
    }

    const interval = Number(desktopExposureConfig.interval_seconds || 0);
    const duration = Number(desktopExposureConfig.duration_seconds || 0);
    if (
      !Number.isFinite(interval) ||
      interval <= 0 ||
      !Number.isFinite(duration) ||
      duration <= 0
    ) {
      return;
    }

    const policy = normalizeInterruptionPolicy(
      desktopExposureConfig.interruption_policy,
    );

    logger.log(
      "[windowExposureScheduler] scheduling desktop exposure in",
      interval,
      "seconds (policy:",
      policy + ")",
      desktopExposureConfig,
    );

    const reschedule = () =>
      schedule({
        desktopExposureConfig,
        deviceId,
        deviceToken,
        phase,
        commandContext,
      });

    const runExposure = async () => {
      logger.log("[windowExposureScheduler] minimizando (show_desktop)", {
        duration_seconds: duration,
      });
      try {
        await executeCommand(
          {
            command_type: "show_desktop",
            payload: {
              duration_seconds: duration,
              restore_fullscreen: desktopExposureConfig.restore_fullscreen,
            },
          },
          commandContext,
        );
      } catch (err) {
        logger.warn(
          "[windowExposureScheduler] desktop exposure command failed:",
          err,
        );
      }
      reschedule();
    };

    // Exibe o aviso (se configurado) e só então minimiza, após o atraso de
    // leitura. Sem aviso, minimiza direto.
    const warnThenRun = () => {
      const wantWarning =
        Boolean(desktopExposureConfig.show_warning) &&
        typeof onWarning === "function";
      if (!wantWarning) {
        runExposure();
        return;
      }
      const secondsBefore = Number(
        desktopExposureConfig.warning_seconds_before || 0,
      );
      onWarning({
        secondsBefore,
        text: desktopExposureConfig.warning_text || null,
        mediaId: desktopExposureConfig.warning_media_id || null,
      });
      const delayMs = Math.max(secondsBefore, 1) * 1000;
      logger.log(
        "[windowExposureScheduler] aviso exibido — minimizando em",
        delayMs / 1000,
        "s",
      );
      clearWarnTimer();
      warnTimerId = setTimeout(() => {
        warnTimerId = null;
        runExposure();
      }, delayMs);
    };

    // Aplica a política de interrupção quando o intervalo vence.
    const proceed = () => {
      const busy = contentGuard ? contentGuard.isContentBusy() : false;

      if (!contentGuard || policy === INTERRUPTION_POLICY.IMMEDIATE || !busy) {
        warnThenRun();
        return;
      }

      if (policy === INTERRUPTION_POLICY.NEVER) {
        logger.log(
          "[windowExposureScheduler] conteúdo ativo + policy 'never' — exposição pulada neste ciclo",
        );
        reschedule();
        return;
      }

      // after_current_item (padrão): aguarda o item atual terminar.
      logger.log(
        "[windowExposureScheduler] conteúdo ativo — aguardando fim do item antes de avisar/minimizar",
      );
      cancelWaitForEnd = contentGuard.onceContentEnd(() => {
        cancelWaitForEnd = null;
        warnThenRun();
      });
    };

    timerId = setTimeout(() => {
      timerId = null;
      proceed();
    }, interval * 1000);
  };

  const isScheduled = () => timerId != null;

  return { schedule, stop, isScheduled };
}
