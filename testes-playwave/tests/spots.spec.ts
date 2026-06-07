/**
 * spots.spec.ts — TASKS 07, 08, 09
 * Spot a cada X min, "spot não toca" (cenário positivo) e "spot não substitui playlist".
 *
 * Endpoints: POST /audio/spots, POST /audio/spots/schedules,
 *            POST /audio/spots/playlists/{id}/spot-schedules,
 *            GET /api/v1/player/schedule, GET /devices/{id}/debug-spots
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uploadAudioTracks, createPlaylist, createSpot } from "../helpers/factories.js";
import { uniqueName } from "../helpers/env.js";

async function deviceWithPlaylist(api: any, tracker: any, label: string) {
  const tracks = await uploadAudioTracks(api, 2);
  const playlist = await createPlaylist(api, tracks.map((t: any) => t.id));
  const dev = await api.pairDevice({ name: uniqueName(label) });
  tracker.device(dev.device_id);
  await api.updateDevice(dev.device_id, { audio_playlist_id: playlist.id });
  return { dev, playlist };
}

test.describe("@api 07 Spot a cada X minutos", () => {
  test.beforeEach(async ({ playerEnabled }) => {
    test.skip(!playerEnabled, "RUN_PLAYER_API=false");
  });

  test("spot com interval_seconds entra na fila com o intervalo correto", async ({ api, tracker }) => {
    const { dev, playlist } = await deviceWithPlaylist(api, tracker, "spot-x-min");
    const [st] = await uploadAudioTracks(api, 1);
    const spot = await createSpot(api, st.id, { insertion_policy: "wait_silence" });

    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 600, // 10 min
        is_active: true,
      })).id,
    );

    const sched = await api.playerSchedule(dev.device_id, dev.device_token);
    const mine = (sched.spot_schedules || []).find((s: any) => s.spot_id === spot.id);
    expect(mine, "spot deve estar na fila resolvida").toBeTruthy();
    expect(mine.interval_seconds).toBe(600);
    expect(mine.insertion_policy, "policy resolvida deve vir no payload").toBeTruthy();
  });

  test("insertion_policy override (interrupt) é refletida na fila", async ({ api, tracker }) => {
    const { dev, playlist } = await deviceWithPlaylist(api, tracker, "spot-policy");
    const [st] = await uploadAudioTracks(api, 1);
    const spot = await createSpot(api, st.id, { insertion_policy: "wait_silence" });
    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 300,
        insertion_policy: "interrupt", // override no schedule
        is_active: true,
      })).id,
    );
    const sched = await api.playerSchedule(dev.device_id, dev.device_token);
    const mine = (sched.spot_schedules || []).find((s: any) => s.spot_id === spot.id);
    expect(mine.insertion_policy).toBe("interrupt");
  });
});

test.describe("@api 08 Spot não toca — cenário POSITIVO (deve tocar)", () => {
  test.beforeEach(async ({ playerEnabled }) => {
    test.skip(!playerEnabled, "RUN_PLAYER_API=false");
  });

  test("spot ativo, na janela e vinculado fica elegível e aparece no debug", async ({ api, tracker }) => {
    const { dev, playlist } = await deviceWithPlaylist(api, tracker, "spot-toca");
    const [st] = await uploadAudioTracks(api, 1);
    const spot = await createSpot(api, st.id, { status: "active" });
    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 120,
        start_time: "00:00",
        end_time: "23:59",
        is_active: true,
      })).id,
    );

    const sched = await api.playerSchedule(dev.device_id, dev.device_token);
    expect((sched.spot_schedules || []).some((s: any) => s.spot_id === spot.id)).toBe(true);

    const debug = await api.debugSpots(dev.device_id);
    const txt = JSON.stringify(debug);
    expect(txt).toContain(spot.id);
    expect(txt).toMatch(/eligible/i);
  });
});

test.describe("@api 09 Spot não substitui playlist (regressão)", () => {
  test.beforeEach(async ({ playerEnabled }) => {
    test.skip(!playerEnabled, "RUN_PLAYER_API=false");
  });

  test("playlist permanece íntegra ao lado do spot na fila", async ({ api, tracker }) => {
    const { dev, playlist } = await deviceWithPlaylist(api, tracker, "spot-coexiste");
    const [st] = await uploadAudioTracks(api, 1);
    const spot = await createSpot(api, st.id);
    tracker.spotSchedule(
      (await api.createSpotScheduleForPlaylist(playlist.id, {
        spot_id: spot.id,
        interval_seconds: 120,
        is_active: true,
      })).id,
    );
    const sched = await api.playerSchedule(dev.device_id, dev.device_token);
    expect(sched.audio_playlist?.id).toBe(playlist.id);
    const tracks = sched.audio_playlist?.tracks || sched.audio_playlist?.items || [];
    expect(tracks.length).toBeGreaterThan(0);
    expect((sched.spot_schedules || []).length).toBeGreaterThan(0);
  });
});
