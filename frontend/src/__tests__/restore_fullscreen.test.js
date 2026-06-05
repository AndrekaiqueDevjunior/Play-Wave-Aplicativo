import { describe, it, expect, beforeEach, vi } from "vitest";

/**
 * Teste de regressão: restore após sair de fullscreen
 *
 * Bug: Quando show_desktop é chamado com restore_fullscreen=true,
 * se a janela sair de fullscreen durante o tempo de exposição,
 * o restore deveria:
 * 1. Restaurar a janela de minimize
 * 2. Restaurar o estado de fullscreen que foi capturado
 */

describe("Window Restore after fullscreen change", () => {
  // Simula o comportamento de main.js (electron)
  let windowState = {
    fullscreen: true,
    kiosk: true,
    alwaysOnTop: false,
  };

  let lastSnapshot = null;
  let desktopExposureTimer = null;

  function snapshotWindowState() {
    return { ...windowState };
  }

  function prepareWindowForDesktopExposure() {
    lastSnapshot = snapshotWindowState();
    if (windowState.kiosk) windowState.kiosk = false;
    if (windowState.fullscreen) windowState.fullscreen = false;
    if (windowState.alwaysOnTop) windowState.alwaysOnTop = false;
  }

  function restoreWindowState(state = lastSnapshot) {
    // Simula mainWindow.restore(), show(), focus()
    if (state?.alwaysOnTop) windowState.alwaysOnTop = true;
    if (state?.fullscreen) windowState.fullscreen = true;
    if (state?.kiosk) windowState.kiosk = true;
  }

  function simulateShowDesktop(durationSeconds, restoreFullscreen) {
    if (desktopExposureTimer) clearTimeout(desktopExposureTimer);

    const restoreState = snapshotWindowState();
    console.log("[test] show_desktop snapshot:", restoreState);

    prepareWindowForDesktopExposure();
    console.log("[test] after prepare:", windowState);

    if (restoreFullscreen) {
      desktopExposureTimer = setTimeout(() => {
        desktopExposureTimer = null;
        try {
          restoreWindowState(restoreState);
          console.log("[test] restored to:", windowState);
        } catch (e) {
          console.error("[test] restore failed:", e);
        }
      }, durationSeconds * 1000);
    }
  }

  beforeEach(() => {
    vi.useFakeTimers();
    windowState = { fullscreen: true, kiosk: true, alwaysOnTop: false };
    lastSnapshot = null;
    desktopExposureTimer = null;
  });

  it("should snapshot fullscreen state before desktop exposure", () => {
    prepareWindowForDesktopExposure();

    expect(lastSnapshot).toEqual({
      fullscreen: true,
      kiosk: true,
      alwaysOnTop: false,
    });
    expect(windowState).toEqual({
      fullscreen: false,
      kiosk: false,
      alwaysOnTop: false,
    });
  });

  it("should restore fullscreen state after desktop exposure", () => {
    simulateShowDesktop(5, true);

    // Window is now minimized (simulated by desktop exposed state)
    expect(windowState.fullscreen).toBe(false);
    expect(windowState.kiosk).toBe(false);

    // Advance time by 5 seconds
    vi.advanceTimersByTime(5000);

    // Window should be restored to original state
    expect(windowState.fullscreen).toBe(true);
    expect(windowState.kiosk).toBe(true);
  });

  it("should restore fullscreen even if user exited fullscreen during exposure", () => {
    simulateShowDesktop(5, true);

    // User manually exits fullscreen while window is minimized (during exposure)
    // Simulating external change: setTimeout(() => { windowState.fullscreen = false }, 2000)
    setTimeout(() => {
      windowState.fullscreen = false; // User or OS changed this
    }, 2000);

    vi.advanceTimersByTime(2000);
    expect(windowState.fullscreen).toBe(false); // User exited fullscreen

    // Now advance to completion of desktop exposure (5s total)
    vi.advanceTimersByTime(3000);

    // Bug check: Should still restore fullscreen from snapshot
    // NOT from current windowState.fullscreen
    expect(windowState.fullscreen).toBe(true);
    expect(lastSnapshot.fullscreen).toBe(true);
    console.log("[test] PASS: Fullscreen restored from snapshot despite user exit");
  });

  it("should not restore if restore_fullscreen=false", () => {
    simulateShowDesktop(5, false);

    vi.advanceTimersByTime(5000);

    // Timer should not fire, window state unchanged from prepare
    expect(desktopExposureTimer).toBeNull();
    expect(windowState.fullscreen).toBe(false);
  });

  it("should handle multiple show_desktop calls (cancel previous restore)", () => {
    // First exposure
    simulateShowDesktop(5, true);
    const firstSnapshot = { ...lastSnapshot };

    vi.advanceTimersByTime(2000);

    // Second exposure (cancels previous timer)
    // At this point, window is already in exposed state (fullscreen=false)
    simulateShowDesktop(10, true);
    const secondSnapshot = { ...lastSnapshot };

    // Second snapshot should be from current (already exposed) state
    expect(secondSnapshot.fullscreen).toBe(false);
    expect(firstSnapshot.fullscreen).toBe(true);

    // Advance to original 5s (first timer should have been cancelled)
    vi.advanceTimersByTime(3000); // 5s total from start

    // Window should still be in exposed state (first timer was cancelled)
    expect(windowState.fullscreen).toBe(false);

    // Advance to 10s from second call start (total 12s)
    vi.advanceTimersByTime(8000); // 10s from second call

    // Now should restore (to the exposed state captured by second snapshot)
    expect(windowState.fullscreen).toBe(false);
  });
});
