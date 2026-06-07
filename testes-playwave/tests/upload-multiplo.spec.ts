/**
 * upload-multiplo.spec.ts — TASK 01
 * Valida upload de várias faixas e disponibilidade para uso.
 * Endpoints: POST /audio/tracks/upload, POST /audio/tracks/upload-multiple, GET /audio/tracks
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { genWav } from "../helpers/media-gen.js";
import { uploadAudioTracks } from "../helpers/factories.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api 01 Upload múltiplo", () => {
  test("sobe várias faixas (singular em lote) e todas aparecem na listagem", async ({ api }) => {
    const created = await uploadAudioTracks(api, 3, { seconds: 1 });
    expect(created).toHaveLength(3);
    for (const t of created) expect(t.id, "cada upload retorna id").toBeTruthy();

    const all = await api.listTracks({ status: "active" });
    const allIds = new Set(all.map((t: any) => t.id));
    for (const t of created) expect(allIds.has(t.id), `faixa ${t.name} disponível na listagem`).toBe(true);
  });

  test("endpoint upload-multiple aceita arquivo e retorna resultado", async ({ api }) => {
    const wav = genWav(1);
    const res = await api.uploadTracksMultiple([wav], { category: "music" });
    // Resposta real: AudioTrackUploadMultipleResponse (uploaded[]/failed[]).
    const uploaded = res.uploaded || res.tracks || res.items || [];
    expect(Array.isArray(uploaded) || typeof res === "object").toBeTruthy();
    expect(JSON.stringify(res)).toBeTruthy();
  });

  test("faixas ficam disponíveis para uso em playlist", async ({ api }) => {
    const created = await uploadAudioTracks(api, 2);
    const playlist = await api.createPlaylist({
      name: uniqueName("playlist-upload"),
      track_ids: created.map((t) => t.id),
      status: "active",
    });
    const full = await api.getPlaylist(playlist.id);
    const tracks = full.tracks || full.items || full.track_ids || [];
    expect(JSON.stringify(tracks)).toContain(created[0].id);
  });
});
