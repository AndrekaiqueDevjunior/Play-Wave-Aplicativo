/**
 * electron-windows.spec.ts — TASK 28
 * Windows/Electron: sintonia com painel, minimizar/maximizar por timer event.
 *
 * Estado real auditado:
 *   - Comandos de exposição de desktop existem: command_type "show_desktop"
 *     (POST /devices/{id}/command) + config em PATCH /devices/{id}/desktop-exposure-config.
 *   - A AÇÃO de minimizar/maximizar a janela é do processo Electron (preload
 *     window.__ELECTRON__) — não há browser Chromium do Playwright controlando
 *     o app Electron nesta suíte (exigiria _electron.launch apontando ao build).
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api 28 Windows/Electron — comando de exposição de desktop (backend)", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("desktop-exposure-config persiste e comando show_desktop é aceito", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("electron") });
    tracker.device(dev.device_id);

    // Configura exposição de desktop (intervalo/duração/restore_fullscreen).
    const cfgRes = await api.raw("patch", `/devices/${dev.device_id}/desktop-exposure-config`, {
      data: { enabled: true, interval_seconds: 10, duration_seconds: 10, restore_fullscreen: true },
    });
    expect([200], "config de exposição aceita").toContain(cfgRes.status());

    // Dispara o comando de mostrar desktop (minimizar) com payload de duração.
    const cmdRes = await api.raw("post", `/devices/${dev.device_id}/command`, {
      data: { command_type: "show_desktop", payload: { duration_seconds: 10 } },
    });
    expect([200, 201], "comando show_desktop aceito").toContain(cmdRes.status());

    // Player consome via pending (sintonia com painel).
    const pending = await api.pendingCommands(dev.device_id, dev.device_token);
    expect(Array.isArray(pending)).toBe(true);
  });
});

test.describe("28 Electron — minimizar/maximizar real da janela", () => {
  test.fixme("janela Electron minimiza e re-maximiza após timer event", async () => {
    // Exige Playwright-Electron (_electron.launch) apontando ao build do app desktop.
    // A lógica de timer já tem teste de unidade em frontend/src/__tests__/
    // (window_exposure_scheduler.test.js, window_commands.test.js).
  });
});
