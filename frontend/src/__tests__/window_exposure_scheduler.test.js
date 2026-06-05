import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createWindowExposureScheduler } from "../player-core/windowExposureScheduler.js";

beforeEach(() => {
  vi.useFakeTimers();
  vi.clearAllMocks();
});

afterEach(() => {
  vi.runOnlyPendingTimers();
  vi.useRealTimers();
});

describe("window exposure scheduler", () => {
  it("does not schedule when desktop exposure is disabled", () => {
    const executeCommand = vi.fn();
    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
    });

    scheduler.schedule({
      desktopExposureConfig: {
        enabled: false,
        interval_seconds: 10,
        duration_seconds: 10,
        restore_fullscreen: true,
      },
      deviceId: "device-1",
      deviceToken: "token-1",
      phase: "playing",
      commandContext: {},
    });

    expect(executeCommand).not.toHaveBeenCalled();
    expect(scheduler.isScheduled()).toBe(false);
  });

  it("schedules and executes show_desktop when enabled on Electron", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
    });

    scheduler.schedule({
      desktopExposureConfig: {
        enabled: true,
        interval_seconds: 1,
        duration_seconds: 2,
        restore_fullscreen: false,
      },
      deviceId: "device-1",
      deviceToken: "token-1",
      phase: "playing",
      commandContext: {
        deviceId: "device-1",
        setPhase: vi.fn(),
        setPlaylist: vi.fn(),
        setCurrentIndex: vi.fn(),
        setProgress: vi.fn(),
      },
    });

    expect(scheduler.isScheduled()).toBe(true);
    await vi.advanceTimersByTimeAsync(1000);

    expect(executeCommand).toHaveBeenCalledTimes(1);
    expect(executeCommand).toHaveBeenCalledWith(
      {
        command_type: "show_desktop",
        payload: {
          duration_seconds: 2,
          restore_fullscreen: false,
        },
      },
      expect.any(Object),
    );
    expect(scheduler.isScheduled()).toBe(true);

    scheduler.stop();
    expect(scheduler.isScheduled()).toBe(false);
  });

  it("does not schedule outside Electron platform", () => {
    const executeCommand = vi.fn();
    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: false,
    });

    scheduler.schedule({
      desktopExposureConfig: {
        enabled: true,
        interval_seconds: 1,
        duration_seconds: 1,
        restore_fullscreen: true,
      },
      deviceId: "device-1",
      deviceToken: "token-1",
      phase: "playing",
      commandContext: {},
    });

    expect(executeCommand).not.toHaveBeenCalled();
    expect(scheduler.isScheduled()).toBe(false);
  });
});
