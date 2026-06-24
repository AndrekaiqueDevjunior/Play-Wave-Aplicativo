import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { createWindowExposureScheduler } from "../player-core/windowExposureScheduler.js";
import { createContentGuard } from "../player-core/contentGuard.js";

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

describe("window exposure scheduler — WAIT_CONTENT_END (SPEC 015)", () => {
  it("com contentGuard e conteúdo ativo, espera o fim antes de executar show_desktop", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });

    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
      contentGuard: guard,
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
      commandContext: {},
    });

    await vi.advanceTimersByTimeAsync(1000);
    expect(executeCommand).not.toHaveBeenCalled();

    guard.notifyContentEnded();
    await vi.advanceTimersByTimeAsync(0);
    expect(executeCommand).toHaveBeenCalledTimes(1);

    scheduler.stop();
  });

  it("com contentGuard e sem conteúdo ativo, executa imediatamente no intervalo", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const guard = createContentGuard();
    guard.update({ phase: "no_campaign", hasPlaylist: false });

    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
      contentGuard: guard,
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
      commandContext: {},
    });

    await vi.advanceTimersByTimeAsync(1000);
    expect(executeCommand).toHaveBeenCalledTimes(1);

    scheduler.stop();
  });

  it("exibe o aviso só após a fronteira do item e minimiza depois de warning_seconds_before", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    const onWarning = vi.fn();

    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
      contentGuard: guard,
      onWarning,
    });

    scheduler.schedule({
      desktopExposureConfig: {
        enabled: true,
        interval_seconds: 1,
        duration_seconds: 2,
        restore_fullscreen: false,
        show_warning: true,
        warning_seconds_before: 10,
        warning_text: "Aviso",
        warning_media_id: "media-1",
      },
      deviceId: "device-1",
      deviceToken: "token-1",
      phase: "playing",
      commandContext: {},
    });

    // Intervalo vence com conteúdo ativo: NÃO avisa nem minimiza ainda —
    // primeiro respeita o item atual (não atravessa a mídia).
    await vi.advanceTimersByTimeAsync(1000);
    expect(onWarning).not.toHaveBeenCalled();
    expect(executeCommand).not.toHaveBeenCalled();

    // Item terminou → aviso aparece imediatamente antes da minimização.
    guard.notifyContentEnded();
    await vi.advanceTimersByTimeAsync(0);
    expect(onWarning).toHaveBeenCalledWith({
      secondsBefore: 10,
      text: "Aviso",
      mediaId: "media-1",
    });
    // Ainda dentro da janela do aviso: não minimizou.
    expect(executeCommand).not.toHaveBeenCalled();

    // Após warning_seconds_before → minimiza.
    await vi.advanceTimersByTimeAsync(10_000);
    expect(executeCommand).toHaveBeenCalledTimes(1);

    scheduler.stop();
  });

  it("policy 'never' pula a exposição enquanto há mídia tocando", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });

    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
      contentGuard: guard,
    });

    scheduler.schedule({
      desktopExposureConfig: {
        enabled: true,
        interval_seconds: 1,
        duration_seconds: 2,
        restore_fullscreen: false,
        interruption_policy: "never",
      },
      deviceId: "device-1",
      deviceToken: "token-1",
      phase: "playing",
      commandContext: {},
    });

    await vi.advanceTimersByTimeAsync(1000);
    // Conteúdo ativo + never → pulou; terminar o item NÃO deve minimizar.
    guard.notifyContentEnded();
    await vi.advanceTimersByTimeAsync(0);
    expect(executeCommand).not.toHaveBeenCalled();

    scheduler.stop();
  });

  it("policy 'immediate' minimiza mesmo com mídia tocando", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });

    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
      contentGuard: guard,
    });

    scheduler.schedule({
      desktopExposureConfig: {
        enabled: true,
        interval_seconds: 1,
        duration_seconds: 2,
        restore_fullscreen: false,
        interruption_policy: "immediate",
      },
      deviceId: "device-1",
      deviceToken: "token-1",
      phase: "playing",
      commandContext: {},
    });

    await vi.advanceTimersByTimeAsync(1000);
    expect(executeCommand).toHaveBeenCalledTimes(1);

    scheduler.stop();
  });

  it("stop() cancela a espera por fim de conteúdo pendente", async () => {
    const executeCommand = vi.fn().mockResolvedValue({ success: true });
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });

    const scheduler = createWindowExposureScheduler({
      executeCommand,
      isElectron: true,
      contentGuard: guard,
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
      commandContext: {},
    });

    await vi.advanceTimersByTimeAsync(1000);
    scheduler.stop();
    guard.notifyContentEnded();
    await vi.advanceTimersByTimeAsync(0);

    expect(executeCommand).not.toHaveBeenCalled();
  });
});
