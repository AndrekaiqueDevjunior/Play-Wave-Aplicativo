/**
 * radio-playlists.spec.ts — TASKS 06, 10, 11, 21(backend)
 * Playlist sonora: modo sequencial/aleatório, reconhecer pasta, seleção múltipla
 * e política de mistura de áudio (audio_policy na campanha — backend).
 *
 * Endpoints: POST/GET /audio/playlists, POST /audio/playlists/{id}/folder-schedules,
 *            POST /campaigns (audio_policy)
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uploadAudioTracks, createFolderWithTracks, createPlaylist, createCampaign } from "../helpers/factories.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api 06 Sequencial / Aleatório (flags da playlist)", () => {
  test("playlist sequencial persiste shuffle_enabled=false", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 3);
    const pl = await createPlaylist(api, tracks.map((t) => t.id), { shuffle: false });
    const full = await api.getPlaylist(pl.id);
    expect(full.shuffle_enabled ?? full.shuffle).toBeFalsy();
  });

  test("playlist aleatória persiste shuffle_enabled=true", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 3);
    const pl = await createPlaylist(api, tracks.map((t) => t.id), { shuffle: true });
    const full = await api.getPlaylist(pl.id);
    expect(full.shuffle_enabled ?? full.shuffle).toBeTruthy();
  });
});

test.describe("@api 10 /radio/playlists reconhece pasta", () => {
  test("playlist recebe folder-schedule (vínculo com pasta) e persiste o folder_id", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 2);
    const folder = await createFolderWithTracks(api, tracks.map((t) => t.id));
    const playlist = await createPlaylist(api, []);

    const fs = await api.createFolderSchedule(playlist.id, {
      folder_id: folder.id,
      start_time: "00:00",
      end_time: "23:59",
      is_active: true,
    });
    expect(fs.id).toBeTruthy();
    expect(fs.folder_id).toBe(folder.id);
    // Confirma o schema da resposta (design diferente não pode quebrar o vínculo).
    expect(JSON.stringify(fs)).toContain(folder.id);
  });
});

test.describe("@api 11 Seleção múltipla de áudios", () => {
  test("associação em massa de faixas via track_ids persiste na playlist", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 5);
    const ids = tracks.map((t) => t.id);
    const pl = await api.createPlaylist({ name: uniqueName("massa"), track_ids: ids, status: "active" });

    const full = await api.getPlaylist(pl.id);
    const persisted = JSON.stringify(full.tracks || full.items || full.track_ids || full);
    for (const id of ids) expect(persisted, `faixa ${id} associada`).toContain(id);
  });
});

test.describe("@api 21 Mistura áudio/rádio — política (backend)", () => {
  test("campanha aceita audio_policy e persiste a política escolhida", async ({ api, tracker }) => {
    // AudioPolicyEnum: auto | radio_only | media_audio_only | mix | muted_video_with_radio
    const tracks = await uploadAudioTracks(api, 1);
    const playlist = await createPlaylist(api, tracks.map((t) => t.id));
    const campaign = await createCampaign(api, { audioPlaylistId: playlist.id, extra: { audio_policy: "mix" } });
    tracker.campaign(campaign.id);

    const full = await api.getCampaign(campaign.id);
    expect(full.audio_policy).toBe("mix");
    // NOTA: a mixagem real (1 canal ativo, prioridade) ocorre no player —
    // ver frontend/src/hooks/useAudioConflictResolver.js e audioManager.js.
  });
});
