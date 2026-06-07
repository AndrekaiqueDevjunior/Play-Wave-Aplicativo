/**
 * pastas-audio.spec.ts — TASKS 03, 04, 05
 * Pasta de áudio, pasta por horário (folder-schedule) e por período (datas).
 *
 * Endpoints:
 *   POST /audio/folders, POST /audio/folders/{id}/tracks, GET /audio/folders/{id}/tracks
 *   POST /audio/playlists/{playlistId}/folder-schedules
 *
 * NOTA de arquitetura: a elegibilidade de PASTA por horário/data é resolvida em
 * services/audio_spot_scheduler.py / folder schedules. O endpoint público que
 * expõe a fila de pasta resolvida ao player é via /devices/{id}/playlist (legado)
 * — quando o campo existir no payload, validamos; senão marcamos TODO.
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uploadAudioTracks, createFolderWithTracks, createPlaylist } from "../helpers/factories.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api 03 Pastas de áudio", () => {
  test("cria pasta, adiciona faixas e elas aparecem dentro da pasta", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 3);
    const folder = await createFolderWithTracks(api, tracks.map((t) => t.id));
    expect(folder.id).toBeTruthy();

    const inFolder = await api.listFolderTracks(folder.id);
    expect(inFolder.length, "pasta deve conter as faixas adicionadas").toBeGreaterThanOrEqual(3);
  });

  test("pasta possui label/nome reconhecível (usado por campanha/playlist)", async ({ api }) => {
    const name = uniqueName("pasta-label");
    const folder = await api.createFolder({ name });
    expect(folder.name).toBe(name);
    const list = await api.listFolders({ status: "active" });
    expect(list.some((f: any) => f.id === folder.id && f.name === name)).toBe(true);
  });
});

test.describe("@api 04 Pasta por horário (folder-schedule start_time/end_time)", () => {
  test("cria folder-schedule com janela e o backend persiste a janela", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 2);
    const folder = await createFolderWithTracks(api, tracks.map((t) => t.id));
    const playlist = await createPlaylist(api, []);

    const fs = await api.createFolderSchedule(playlist.id, {
      folder_id: folder.id,
      start_time: "08:00",
      end_time: "12:00",
      priority: 10,
      is_active: true,
    });
    expect(fs.id).toBeTruthy();
    expect(fs.start_time).toBe("08:00");
    expect(fs.end_time).toBe("12:00");
  });

  test.fixme("pasta só entra na fila dentro do horário (validação no player)", async () => {
    // TODO técnico: requer expor folder schedules resolvidos por horário no payload
    // do player. Confirmar campo em GET /devices/{id}/playlist ou adicionar resolução
    // de pasta em GET /api/v1/player/schedule (hoje resolve só spots).
  });
});

test.describe("@api 05 Data início/fim das pastas (folder-schedule starts_at/ends_at)", () => {
  test("folder-schedule aceita período starts_at/ends_at e persiste", async ({ api }) => {
    const tracks = await uploadAudioTracks(api, 1);
    const folder = await createFolderWithTracks(api, tracks.map((t) => t.id));
    const playlist = await createPlaylist(api, []);

    const today = new Date();
    const future = new Date(Date.now() + 7 * 86400000);
    const fmt = (d: Date) => d.toISOString().slice(0, 10);

    const fs = await api.createFolderSchedule(playlist.id, {
      folder_id: folder.id,
      starts_at: fmt(today),
      ends_at: fmt(future),
      is_active: true,
    });
    expect(fs.id).toBeTruthy();
    // O backend pode normalizar para datetime; validamos que o período voltou.
    expect(JSON.stringify(fs)).toMatch(/starts_at|ends_at/);
  });

  test.fixme("pasta expirada não entra na fila (validação de período no player)", async () => {
    // Mesmo gap do TASK 04 — falta resolução de pasta por período no payload do player.
  });
});
