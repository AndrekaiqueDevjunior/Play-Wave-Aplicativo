/**
 * scheduler-fila.spec.ts — TESTE CENTRAL: arquitetura de Scheduler/Fila.
 *
 * Fonte de verdade server-side:
 *   - GET /api/v1/player/schedule  → fila resolvida (services/spot_resolver.py)
 *   - GET /devices/{id}/debug-spots → diagnóstico de elegibilidade
 *   - GET /devices/{id}            → schedule_version (versionamento)
 *   - SSE /devices/{id}/playlist/updates → push em tempo real
 *
 * Cada teste é POSITIVO e valida comportamento real no backend. Partes que são
 * exclusivamente do player client-side (ordem de reprodução, retomada após
 * spot, "sem reload") são validadas pelo que o backend ENTREGA + marcadas com
 * pointer para os testes unitários do player quando o runtime não é observável
 * por API.
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uploadAudioTracks, createPlaylist, createSpot } from "../helpers/factories.js";
import { collectSse } from "../helpers/sse.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api Scheduler / Fila — arquitetura central", () => {
  test.beforeEach(async ({ playerEnabled }) => {
    test.skip(!playerEnabled, "RUN_PLAYER_API=false — exige backend+DB+Redis no ar.");
  });

  test("fila inicial: device com playlist entrega payload coerente (playlist + spots)", async ({ api, tracker }) => {
    const tracks = await uploadAudioTracks(api, 3);
    const playlist = await createPlaylist(api, tracks.map((t) => t.id));
    const dev = await api.pairDevice({ name: uniqueName("fila-inicial") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const sched = await api.playerSchedule(dev.device_id, dev.device_token);

    expect(sched.device_id).toBe(dev.device_id);
    expect(sched.server_time, "payload deve trazer server_time").toBeTruthy();
    expect(sched).toHaveProperty("schedule_version");
    expect(sched.audio_playlist, "playlist ativa deve estar na fila").toBeTruthy();
    expect(sched.audio_playlist.id).toBe(playlist.id);
    expect(Array.isArray(sched.spot_schedules)).toBe(true);
  });

  test("spot entra na fila quando dentro da janela; NÃO entra fora da janela", async ({ api, tracker }) => {
    const [trackPlaylist] = await uploadAudioTracks(api, 1);
    const [trackSpot] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [trackPlaylist.id]);
    const spot = await createSpot(api, trackSpot.id);

    const dev = await api.pairDevice({ name: uniqueName("spot-janela") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    // (a) Janela que cobre agora → elegível.
    const inWindow = tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 300,
        start_time: "00:00",
        end_time: "23:59",
        is_active: true,
      })).id,
    );

    let sched = await api.playerSchedule(dev.device_id, dev.device_token);
    const ids = (sched.spot_schedules || []).map((s: any) => s.id);
    expect(ids, "spot dentro da janela deve estar na fila").toContain(inWindow);

    // (b) Schedule só de madrugada (02:00–03:00) — fora do horário atual de teste.
    //     (assumindo que a suíte não roda exatamente entre 02:00–03:00)
    const outWindow = tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 300,
        start_time: "02:00",
        end_time: "03:00",
        is_active: true,
      })).id,
    );
    sched = await api.playerSchedule(dev.device_id, dev.device_token);
    const eligibleNow = (sched.spot_schedules || []).map((s: any) => s.id);
    const hour = new Date().getHours();
    if (hour < 2 || hour >= 3) {
      expect(eligibleNow, "spot fora da janela NÃO deve estar elegível agora").not.toContain(outWindow);
    }
  });

  test("spot NÃO substitui a playlist: payload mantém playlist E spots juntos", async ({ api, tracker }) => {
    // Regressão do bug "spot substituindo playlist": a fila resolvida deve conter
    // a playlist ativa íntegra ao mesmo tempo que o spot agendado.
    const tracks = await uploadAudioTracks(api, 2);
    const [spotTrack] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, tracks.map((t) => t.id));
    const spot = await createSpot(api, spotTrack.id, { insertion_policy: "wait_silence" });

    const dev = await api.pairDevice({ name: uniqueName("spot-nao-substitui") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });
    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 120,
        is_active: true,
      })).id,
    );

    const sched = await api.playerSchedule(dev.device_id, dev.device_token);
    expect(sched.audio_playlist?.id, "playlist deve continuar presente").toBe(playlist.id);
    const tracksInQueue = sched.audio_playlist?.tracks || sched.audio_playlist?.items || [];
    expect(tracksInQueue.length, "playlist deve manter suas faixas").toBeGreaterThan(0);
    expect((sched.spot_schedules || []).length, "spot deve coexistir com a playlist").toBeGreaterThan(0);
  });

  test("modo sequencial vs aleatório: flag da playlist é refletida na fila", async ({ api, tracker }) => {
    const tracks = await uploadAudioTracks(api, 4);
    const seq = await createPlaylist(api, tracks.map((t) => t.id), { shuffle: false });
    const shuffle = await createPlaylist(api, tracks.map((t) => t.id), { shuffle: true });

    const devSeq = await api.pairDevice({ name: uniqueName("seq") });
    tracker.device(devSeq.device_id);
    await api.updateDevice(devSeq.device_id, { audio_playlist_id: seq.id });
    const schedSeq = await api.playerSchedule(devSeq.device_id, devSeq.device_token);
    expect(schedSeq.audio_playlist?.shuffle, "sequencial → shuffle=false").toBeFalsy();

    const devShuf = await api.pairDevice({ name: uniqueName("shuf") });
    tracker.device(devShuf.device_id);
    await api.updateDevice(devShuf.device_id, { audio_playlist_id: shuffle.id });
    const schedShuf = await api.playerSchedule(devShuf.device_id, devShuf.device_token);
    expect(schedShuf.audio_playlist?.shuffle, "aleatório → shuffle=true").toBeTruthy();
    // NOTA: a ordem aleatória em si é aplicada no player (client-side).
    // Ver frontend/src/__tests__/audio_manager.test.js para a randomização.
  });

  test("versionamento: criar schedule de spot DEVICE-scoped incrementa schedule_version", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await createSpot(api, st.id);

    const dev = await api.pairDevice({ name: uniqueName("versao") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const before = Number((await api.getDevice(dev.device_id)).schedule_version);

    // Schedule com escopo de DEVICE → _bump_versions incrementa device.schedule_version.
    tracker.spotSchedule(
      (await api.createSpotSchedule({
        spot_id: spot.id,
        device_id: dev.device_id,
        playlist_id: playlist.id,
        interval_seconds: 180,
        is_active: true,
      })).id,
    );

    const after = await api.waitForScheduleVersionAbove(dev.device_id, before);
    expect(Number(after.schedule_version)).toBeGreaterThan(before);
  });

  test("após mutação, /player/schedule reflete o novo estado (sem ficar com cache antigo)", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await createSpot(api, st.id);
    const dev = await api.pairDevice({ name: uniqueName("cache") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    const before = await api.playerSchedule(dev.device_id, dev.device_token);
    const countBefore = (before.spot_schedules || []).length;

    const created = tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 120,
        is_active: true,
      })).id,
    );

    const after = await api.waitForQueue(
      dev.device_id,
      dev.device_token,
      (s) => (s.spot_schedules || []).some((x: any) => x.id === created),
    );
    expect((after.spot_schedules || []).length).toBeGreaterThan(countBefore);
  });

  test("debug-spots explica a fila: elegibilidade e motivo por spot", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await createSpot(api, st.id);
    const dev = await api.pairDevice({ name: uniqueName("debug") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });
    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 120,
        is_active: true,
      })).id,
    );

    const debug = await api.debugSpots(dev.device_id);
    // Estrutura real (devices.py:debug_device_spots): lista de diagnósticos por spot.
    expect(debug).toBeTruthy();
    const diags = debug.spot_diagnostics || debug.diagnostics || debug.spots || [];
    // Mesmo que o nome do array varie, o debug deve referenciar o spot criado.
    const asText = JSON.stringify(debug);
    expect(asText).toContain(spot.id);
    expect(asText, "debug deve expor flag de elegibilidade").toMatch(/eligible/i);
  });

  test("@sse SSE entrega push após mutação de schedule (não há WebSocket no backend)", async ({ api, tracker }) => {
    const [t] = await uploadAudioTracks(api, 1);
    const [st] = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, [t.id]);
    const spot = await createSpot(api, st.id);
    const dev = await api.pairDevice({ name: uniqueName("sse") });
    tracker.device(dev.device_id);
    await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });

    // Coleta SSE em paralelo enquanto disparamos a mutação que invalida a playlist.
    const collector = collectSse(dev.device_id, dev.device_token, {
      collectMs: 8000,
      until: (e) => e.event === "playlist_invalidated",
    });
    // Pequeno atraso para o stream conectar antes de mutar.
    await new Promise((r) => setTimeout(r, 1000));
    tracker.spotSchedule(
      (await api.createSpotSchedule({
        spot_id: spot.id,
        device_id: dev.device_id,
        playlist_id: playlist.id,
        interval_seconds: 120,
        is_active: true,
      })).id,
    );

    const events = await collector;
    const got = events.map((e) => e.event);
    expect(
      got.includes("playlist_invalidated") || got.includes("snapshot"),
      `esperava evento SSE de invalidação; recebidos: ${got.join(",") || "(nenhum)"}`,
    ).toBeTruthy();
  });
});
