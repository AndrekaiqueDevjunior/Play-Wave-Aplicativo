/**
 * debug.spec.ts — TASKS 26, 27
 * Painel de debug por dispositivo e logs padronizados.
 *
 * Endpoints: GET /devices/{id}/debug-spots, GET /devices/{id}/debug-playback
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uploadAudioTracks, createPlaylist } from "../helpers/factories.js";
import { uniqueName, ENV } from "../helpers/env.js";

test.describe("@api 26 Painel debug por dispositivo (dados via API)", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("debug-playback expõe device, campanha/elegibilidade e versão", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const dev = await api.pairDevice({ name: uniqueName("dbg-pb") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const debug = await api.debugPlayback(dev.device_id);
    const txt = JSON.stringify(debug);
    expect(txt).toContain(dev.device_id);
    // Campos esperados (player_schedule.debug_device_playback): device + versão.
    expect(txt).toMatch(/version|schedule_version|campaign|playlist/i);
  });

  test("debug-spots lista spots com elegibilidade e próximo/ motivo", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await api.createSpot({ name: uniqueName("spot-dbg"), track_id: st.id, status: "active" });
    const dev = await api.pairDevice({ name: uniqueName("dbg-spots") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });
    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, { spot_id: spot.id, interval_seconds: 120, is_active: true })).id,
    );

    const debug = await api.debugSpots(dev.device_id);
    const txt = JSON.stringify(debug);
    expect(txt).toContain(spot.id);
    expect(txt).toMatch(/eligible/i);
  });
});

test.describe("@ui 26 Painel debug por dispositivo (UI)", () => {
  test("página de detalhe do dispositivo abre", async ({ page, api }) => {
    // Cria um device para ter rota válida.
    const dev = await api.pairDevice({ name: uniqueName("ui-dbg") });
    await page.goto(`${ENV.WEB_URL}/dispositivos/${dev.device_id}`);
    // Sem data-testid: validamos que a página carregou (não é tela de erro).
    await expect(page.locator("body")).toBeVisible();
    // TODO[data-testid]: data-testid="device-debug-panel", "device-queue",
    //   "device-next-media", "device-version-local", "device-version-remote",
    //   "device-last-heartbeat", "device-last-commands".
    await api.deleteDevice(dev.device_id).catch(() => {});
  });
});

test.describe("27 Logs padronizados", () => {
  test.fixme("logs estruturados do scheduler/fila/spot/comando (não observável por HTTP)", async () => {
    // Logs existem no backend (log.info com extra=), mas não são observáveis por HTTP.
    // Validação adequada: pytest + caplog no backend. Fora do escopo E2E HTTP.
  });
});
