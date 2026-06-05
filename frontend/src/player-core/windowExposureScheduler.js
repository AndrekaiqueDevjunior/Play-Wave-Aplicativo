export function createWindowExposureScheduler({
  executeCommand,
  isElectron = false,
  logger = console,
}) {
  let timerId = null;

  const stop = () => {
    if (timerId) {
      clearTimeout(timerId);
      timerId = null;
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

    timerId = setTimeout(async () => {
      timerId = null;
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
    }, interval * 1000);
  };

  const isScheduled = () => timerId != null;

  return { schedule, stop, isScheduled };
}
