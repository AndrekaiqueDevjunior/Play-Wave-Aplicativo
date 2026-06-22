export function createWindowExposureScheduler({
  executeCommand,
  isElectron = false,
  logger = console,
  // SPEC 015 — política WAIT_CONTENT_END: quando o horário do intervalo
  // chega, espera o conteúdo atual terminar (contentGuard.onceContentEnd)
  // antes de minimizar. contentGuard é opcional para não quebrar quem
  // instancia o scheduler sem essa dependência (ex.: testes antigos).
  contentGuard = null,
  onWarning = null, // ({ secondsBefore, text, mediaId }) => void
}) {
  let timerId = null;
  let cancelWaitForEnd = null;

  const stop = () => {
    if (timerId) {
      clearTimeout(timerId);
      timerId = null;
    }
    if (cancelWaitForEnd) {
      cancelWaitForEnd();
      cancelWaitForEnd = null;
    }
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

    logger.log(
      "[windowExposureScheduler] scheduling desktop exposure in",
      interval,
      "seconds",
      desktopExposureConfig,
    );

    const runExposure = async () => {
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
      schedule({
        desktopExposureConfig,
        deviceId,
        deviceToken,
        phase,
        commandContext,
      });
    };

    timerId = setTimeout(() => {
      timerId = null;

      if (!contentGuard) {
        runExposure();
        return;
      }

      if (desktopExposureConfig.show_warning && onWarning) {
        onWarning({
          secondsBefore: Number(desktopExposureConfig.warning_seconds_before || 0),
          text: desktopExposureConfig.warning_text || null,
          mediaId: desktopExposureConfig.warning_media_id || null,
        });
      }

      if (contentGuard.isContentBusy()) {
        logger.log(
          "[windowExposureScheduler] conteúdo ativo — aguardando fim antes de minimizar",
        );
      }
      cancelWaitForEnd = contentGuard.onceContentEnd(() => {
        cancelWaitForEnd = null;
        runExposure();
      });
    }, interval * 1000);
  };

  const isScheduled = () => timerId != null;

  return { schedule, stop, isScheduled };
}
