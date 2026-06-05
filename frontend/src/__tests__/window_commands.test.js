import { beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => {
  vi.resetModules();
  vi.clearAllMocks();
  delete window.__ELECTRON__;
});

function context() {
  return {
    deviceId: "device-1",
    phase: "playing",
    setPhase: vi.fn(),
    setProgress: vi.fn(),
  };
}

describe("window commands", () => {
  it("returns platform_unsupported without Electron bridge", async () => {
    const { executeCommand } = await import("../player-core/commands.js");

    const result = await executeCommand(
      { command_type: "show_desktop", payload: { duration_seconds: 5 } },
      context(),
    );

    expect(result.success).toBe(false);
    expect(result.result.platform_unsupported).toBe(true);
    expect(result.result.error_code).toBe("BROWSER_ENVIRONMENT");
    expect(result.result.reason).toBe("window_control_requires_electron");
  });

  it("calls Electron bridge for show_desktop", async () => {
    const showDesktop = vi.fn().mockResolvedValue({ ok: true });
    window.__ELECTRON__ = { player: { showDesktop } };
    const { executeCommand } = await import("../player-core/commands.js");

    const result = await executeCommand(
      { command_type: "show_desktop", payload: { duration_seconds: 7 } },
      context(),
    );

    expect(result.success).toBe(true);
    expect(showDesktop).toHaveBeenCalledWith(7, true);
    expect(result.result.handler).toEqual({ ok: true });
  });

  it("passes restore_fullscreen false to show_desktop", async () => {
    const showDesktop = vi.fn().mockResolvedValue({ ok: true });
    window.__ELECTRON__ = { player: { showDesktop } };
    const { executeCommand } = await import("../player-core/commands.js");

    const result = await executeCommand(
      {
        command_type: "show_desktop",
        payload: { duration_seconds: 5, restore_fullscreen: false },
      },
      context(),
    );

    expect(result.success).toBe(true);
    expect(showDesktop).toHaveBeenCalledWith(5, false);
    expect(result.result.handler).toEqual({ ok: true });
  });

  it("defaults restore_fullscreen to true when omitted", async () => {
    const showDesktop = vi.fn().mockResolvedValue({ ok: true });
    window.__ELECTRON__ = { player: { showDesktop } };
    const { executeCommand } = await import("../player-core/commands.js");

    const result = await executeCommand(
      { command_type: "show_desktop", payload: { duration_seconds: 5 } },
      context(),
    );

    expect(result.success).toBe(true);
    expect(showDesktop).toHaveBeenCalledWith(5, true);
    expect(result.result.handler).toEqual({ ok: true });
  });
});
