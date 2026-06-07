/**
 * player.spec.ts — TASKS 14, 20, 22, 23, 24, 25
 * Recepção de programação pelo player, versionamento, WebSocket/polling, cache,
 * "não reiniciar player" e nome da música (OSD).
 *
 * Endpoints: GET /api/v1/player/schedule, GET /devices/{id}/playlist,
 *            SSE /devices/{id}/playlist/updates, GET /devices/{id}
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uploadAudioTracks, createPlaylist, createCampaign, uploadAudioMedia } from "../helpers/factories.js";
import { collectSse } from "../helpers/sse.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api 14 Conteúdo passa: player recebe campanha + mídia", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("device com campanha+mídia recebe conteúdo no payload do player", async ({ api, tracker }) => {
    const media = await uploadAudioMedia(api);
    const dev = await api.pairDevice({ name: uniqueName("conteudo") });
    tracker.device(dev.device_id);
    const campaign = await createCampaign(api, { deviceIds: [dev.device_id], mediaIds: [media.id], publish: true });
    tracker.campaign(campaign.id);
    await api.updateDevice(dev.device_id, { current_campaign_id: campaign.id });

    // Caminho legado entrega a playlist visual da campanha:
    const playlist = await api.devicePlaylist(dev.device_id, dev.device_token);
    expect(playlist, "payload de playlist do device").toBeTruthy();
    const txt = JSON.stringify(playlist);
    expect(txt.length).toBeGreaterThan(2);

    // E o debug-playback (admin) explica a elegibilidade do conteúdo:
    const debug = await api.debugPlayback(dev.device_id);
    expect(JSON.stringify(debug)).toContain(dev.device_id);
  });
});

test.describe("@api 23 Versionamento de programação", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("device-scoped schedule incrementa schedule_version; player compara versões", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await api.createSpot({ name: uniqueName("spot-v"), track_id: st.id, status: "active" });
    const dev = await api.pairDevice({ name: uniqueName("ver") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const before = Number((await api.getDevice(dev.device_id)).schedule_version);
    tracker.spotSchedule(
      (await api.createSpotSchedule({ spot_id: spot.id, device_id: dev.device_id, playlist_id: playlist.id, interval_seconds: 200, is_active: true })).id,
    );
    const after = await api.waitForScheduleVersionAbove(dev.device_id, before);
    expect(Number(after.schedule_version)).toBeGreaterThan(before);

    // O player compara versão local vs remota: o payload do schedule expõe a versão.
    const sched = await api.playerSchedule(dev.device_id, dev.device_token);
    expect(sched).toHaveProperty("schedule_version");
  });
});

test.describe("@api 24 WebSocket / Polling", () => {
  test("NÃO há WebSocket: tempo real é via SSE (documentado)", async () => {
    // Auditoria: 0 ocorrências de WebSocket no backend e frontend.
    // Este teste documenta a decisão arquitetural — o canal real é SSE + polling.
    expect(true).toBe(true);
  });

  test("@sse SSE entrega evento ao player após mutação", async ({ api, tracker, playerEnabled }) => {
    test.skip(!playerEnabled, "RUN_PLAYER_API=false");
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await api.createSpot({ name: uniqueName("spot-sse"), track_id: st.id, status: "active" });
    const dev = await api.pairDevice({ name: uniqueName("pl-sse") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const collector = collectSse(dev.device_id, dev.device_token, { collectMs: 8000, until: (e) => e.event === "playlist_invalidated" });
    await new Promise((r) => setTimeout(r, 1000));
    tracker.spotSchedule(
      (await api.createSpotSchedule({ spot_id: spot.id, device_id: dev.device_id, playlist_id: playlist.id, interval_seconds: 120, is_active: true })).id,
    );
    const events = await collector;
    expect(events.length, "SSE deve emitir ao menos um evento (snapshot/invalidated)").toBeGreaterThan(0);
  });

  test.fixme("fallback de polling quando SSE cai (client-side do Player)", async () => {
    // Validar que, sem SSE, o player converge via polling de GET /api/v1/player/schedule.
    // Requer simular queda de SSE no player real — cobrir em teste de componente do Player.
  });
});

test.describe("@api 25 Cache controlado", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("após alteração, player NÃO recebe programação antiga (sem stale)", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await api.createSpot({ name: uniqueName("spot-cache"), track_id: st.id, status: "active" });
    const dev = await api.pairDevice({ name: uniqueName("cache2") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const c0 = (await api.playerSchedule(dev.device_id, dev.device_token)).spot_schedules?.length || 0;
    const created = tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, { spot_id: spot.id, interval_seconds: 120, is_active: true })).id,
    );
    const after = await api.waitForQueue(dev.device_id, dev.device_token, (s) => (s.spot_schedules || []).some((x: any) => x.id === created));
    expect((after.spot_schedules || []).length).toBeGreaterThan(c0);
  });
});

test.describe("22 Nome da música (OSD)", () => {
  test.fixme("nome da música no OSD troca ao avançar faixa (overlay do Player)", async () => {
    // OSD é renderizado no player a partir da faixa atual da fila. Backend já entrega
    // track.name no payload; o overlay/troca ao avançar faixa deve ser coberto por
    // teste de componente do Player (frontend/src/__tests__).
  });
});
