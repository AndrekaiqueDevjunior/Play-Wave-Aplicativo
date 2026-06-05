import { describe, it, expect, beforeEach, vi } from "vitest";
import { createWindowExposureScheduler } from "@/player-core/windowExposureScheduler";

/**
 * Teste de regressão: scheduler não executa sem campanha
 *
 * Bug: O scheduler deve detectar quando player está em phase="loading"
 * e NÃO agendar a execução de show_desktop.
 *
 * Contexto: Quando não há campanha ativa, player fica em "loading".
 * Se a config de desktop exposure estiver ativa, scheduler não deve
 * executar comandos automaticamente.
 */

describe("Window Exposure Scheduler with no campaign", () => {
  let scheduler;
  let mockExecuteCommand;
  let commandLog;

  beforeEach(() => {
    vi.useFakeTimers();
    commandLog = [];

    mockExecuteCommand = vi.fn(async (cmd, ctx) => {
      commandLog.push({
        type: cmd.command_type,
        payload: cmd.payload,
        time: Date.now(),
      });
      return { ok: true };
    });

    scheduler = createWindowExposureScheduler({
      executeCommand: mockExecuteCommand,
      isElectron: true,
      logger: { log: vi.fn(), warn: vi.fn() },
    });
  });

  const mockDeviceId = "device-123";
  const mockDeviceToken = "token-xyz";
  const mockContext = {};

  it("should not schedule when phase is 'loading'", () => {
    const config = {
      enabled: true,
      interval_seconds: 30,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "loading", // No campaign
      commandContext: mockContext,
    });

    // Should not be scheduled
    expect(scheduler.isScheduled()).toBe(false);

    // Advance time beyond interval
    vi.advanceTimersByTime(30000);

    // No command should execute
    expect(mockExecuteCommand).not.toHaveBeenCalled();
    expect(commandLog).toHaveLength(0);

    console.log(
      "[test] PASS: Scheduler blocked when phase=loading (no campaign)",
    );
  });

  it("should not schedule when phase is 'waiting' (pairing)", () => {
    const config = {
      enabled: true,
      interval_seconds: 30,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "waiting", // Pairing
      commandContext: mockContext,
    });

    expect(scheduler.isScheduled()).toBe(false);
    vi.advanceTimersByTime(30000);
    expect(mockExecuteCommand).not.toHaveBeenCalled();
  });

  it("should schedule when phase is 'playing'", () => {
    const config = {
      enabled: true,
      interval_seconds: 10,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "playing", // Campaign active
      commandContext: mockContext,
    });

    expect(scheduler.isScheduled()).toBe(true);

    vi.advanceTimersByTime(10000);

    // Command should execute once
    expect(mockExecuteCommand).toHaveBeenCalledOnce();
    expect(commandLog[0]).toMatchObject({
      type: "show_desktop",
      payload: { duration_seconds: 5, restore_fullscreen: true },
    });
  });

  it("should reschedule when phase changes from loading to playing", () => {
    const config = {
      enabled: true,
      interval_seconds: 30,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    // Start in loading phase (no schedule)
    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "loading",
      commandContext: mockContext,
    });

    expect(scheduler.isScheduled()).toBe(false);

    vi.advanceTimersByTime(15000);
    expect(mockExecuteCommand).not.toHaveBeenCalled();

    // Change to playing phase
    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "playing",
      commandContext: mockContext,
    });

    // Now should be scheduled (waiting for next 30s)
    expect(scheduler.isScheduled()).toBe(true);

    vi.advanceTimersByTime(30000);

    // Command executes after 30s from playing start
    expect(mockExecuteCommand).toHaveBeenCalledOnce();

    console.log("[test] PASS: Scheduler enabled when campaign starts");
  });

  it("should stop scheduling when phase changes back to loading", () => {
    const config = {
      enabled: true,
      interval_seconds: 10,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    // Start playing
    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "playing",
      commandContext: mockContext,
    });

    vi.advanceTimersByTime(10000);

    // First command executes
    expect(mockExecuteCommand).toHaveBeenCalledTimes(1);

    // Campaign ends (back to loading)
    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "loading",
      commandContext: mockContext,
    });

    // Should not be scheduled anymore
    expect(scheduler.isScheduled()).toBe(false);

    vi.advanceTimersByTime(20000);

    // No additional commands
    expect(mockExecuteCommand).toHaveBeenCalledTimes(1);

    console.log("[test] PASS: Scheduler disabled when campaign ends");
  });

  it("should not schedule if config disabled", () => {
    const config = {
      enabled: false, // Disabled
      interval_seconds: 30,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    scheduler.schedule({
      desktopExposureConfig: config,
      deviceId: mockDeviceId,
      deviceToken: mockDeviceToken,
      phase: "playing",
      commandContext: mockContext,
    });

    expect(scheduler.isScheduled()).toBe(false);
  });

  it("should require valid intervals and durations", () => {
    const testCases = [
      { interval_seconds: 0, duration_seconds: 5 }, // Invalid interval
      { interval_seconds: 30, duration_seconds: 0 }, // Invalid duration
      { interval_seconds: -10, duration_seconds: 5 }, // Negative
      { interval_seconds: "invalid", duration_seconds: 5 }, // Non-numeric
    ];

    testCases.forEach((config) => {
      commandLog = [];
      mockExecuteCommand.mockClear();

      scheduler.schedule({
        desktopExposureConfig: {
          enabled: true,
          ...config,
          restore_fullscreen: true,
        },
        deviceId: mockDeviceId,
        deviceToken: mockDeviceToken,
        phase: "playing",
        commandContext: mockContext,
      });

      expect(scheduler.isScheduled()).toBe(false);
      expect(mockExecuteCommand).not.toHaveBeenCalled();
    });

    console.log("[test] PASS: Invalid intervals/durations blocked");
  });
});
