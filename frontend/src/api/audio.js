/**
 * api/audio.js
 * Endpoints FastAPI — módulo Rádio Indoor (Áudio)
 *
 * CONTRATO FASTAPI:
 *
 * GET    /audio/tracks                     (admin)
 *   query: tenant_id?, status?, category?
 *   resp: AudioTrack[]
 *
 * POST   /audio/tracks/upload              (admin, multipart)
 *   fields: file, name, category?, description?
 *   resp: AudioTrack
 *
 * PATCH  /audio/tracks/{id}               (admin)
 *   body: Partial<AudioTrack>
 *   resp: AudioTrack
 *
 * DELETE /audio/tracks/{id}              (admin)
 *   resp: 204
 *
 * GET    /audio/playlists                  (admin)
 *   query: tenant_id?, status?
 *   resp: AudioPlaylist[]
 *
 * GET    /audio/playlists/{id}             (admin)
 *   resp: AudioPlaylist
 *
 * POST   /audio/playlists                  (admin)
 *   body: AudioPlaylist (sem id)
 *   resp: AudioPlaylist
 *
 * PATCH  /audio/playlists/{id}            (admin)
 *   body: Partial<AudioPlaylist>
 *   resp: AudioPlaylist
 *
 * DELETE /audio/playlists/{id}           (admin)
 *   resp: 204
 *
 * GET    /audio/devices/{id}/playlist      (device, X-Device-Token)
 *   resp: { playlist_id, tracks: [{id, file_url, name, duration_seconds}], volume, loop, shuffle }
 */
import { apiFetch, apiUpload } from "./http";

// ── Faixas ─────────────────────────────────────────────────────────────────
export const listarFaixas = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/audio/tracks${qs ? `?${qs}` : ""}`);
};

export const uploadFaixa = async (file, metadata = {}) => {
  const form = new FormData();
  form.append("file", file);
  Object.entries(metadata).forEach(([k, v]) => {
    if (v !== undefined && v !== null) form.append(k, String(v));
  });

  return apiUpload("/audio/tracks/upload", form);
};

export const uploadMultipleFaixas = async (formData) => {
  return apiUpload("/audio/tracks/upload-multiple", formData);
};

export const atualizarFaixa = (id, payload) =>
  apiFetch(`/audio/tracks/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarFaixa = (id) =>
  apiFetch(`/audio/tracks/${id}`, { method: "DELETE" });

// ── Playlists ──────────────────────────────────────────────────────────────
export const listarPlaylistsAudio = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/audio/playlists${qs ? `?${qs}` : ""}`);
};

export const buscarPlaylistAudio = (id) => apiFetch(`/audio/playlists/${id}`);

export const criarPlaylistAudio = (payload) =>
  apiFetch("/audio/playlists", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarPlaylistAudio = (id, payload) =>
  apiFetch(`/audio/playlists/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarPlaylistAudio = (id) =>
  apiFetch(`/audio/playlists/${id}`, { method: "DELETE" });

// ── TV: Busca playlist de áudio ────────────────────────────────────────────
export const buscarPlaylistAudioDispositivo = (deviceId, token) =>
  apiFetch(`/audio/devices/${deviceId}/playlist`, { token });

// ── Pastas de áudio ────────────────────────────────────────────────────────
export const listarPastas = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/audio/folders${qs ? `?${qs}` : ""}`);
};

export const buscarPasta = (id) => apiFetch(`/audio/folders/${id}`);

export const criarPasta = (payload) =>
  apiFetch("/audio/folders", { method: "POST", body: JSON.stringify(payload) });

export const atualizarPasta = (id, payload) =>
  apiFetch(`/audio/folders/${id}`, { method: "PUT", body: JSON.stringify(payload) });

export const deletarPasta = (id) =>
  apiFetch(`/audio/folders/${id}`, { method: "DELETE" });

export const listarFaixasDaPasta = (folderId) =>
  apiFetch(`/audio/folders/${folderId}/tracks`);

export const adicionarFaixasNaPasta = (folderId, trackIds) =>
  apiFetch(`/audio/folders/${folderId}/tracks`, {
    method: "POST",
    body: JSON.stringify({ tracks: trackIds.map((id) => ({ track_id: id })) }),
  });

export const removerFaixaDaPasta = (folderId, itemId) =>
  apiFetch(`/audio/folders/${folderId}/tracks/${itemId}`, { method: "DELETE" });

// ── Folder schedules (agenda de pastas por playlist) ───────────────────────
export const listarFolderSchedules = (playlistId) =>
  apiFetch(`/audio/playlists/${playlistId}/folder-schedules`);

export const criarFolderSchedule = (playlistId, payload) =>
  apiFetch(`/audio/playlists/${playlistId}/folder-schedules`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarFolderSchedule = (playlistId, scheduleId, payload) =>
  apiFetch(`/audio/playlists/${playlistId}/folder-schedules/${scheduleId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarFolderSchedule = (playlistId, scheduleId) =>
  apiFetch(`/audio/playlists/${playlistId}/folder-schedules/${scheduleId}`, {
    method: "DELETE",
  });

// ── Spots ──────────────────────────────────────────────────────────────────
export const listarSpots = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/audio/spots${qs ? `?${qs}` : ""}`);
};

export const criarSpot = (payload) =>
  apiFetch("/audio/spots", { method: "POST", body: JSON.stringify(payload) });

export const atualizarSpot = (id, payload) =>
  apiFetch(`/audio/spots/${id}`, { method: "PUT", body: JSON.stringify(payload) });

export const deletarSpot = (id) =>
  apiFetch(`/audio/spots/${id}`, { method: "DELETE" });

// ── Spot schedules ─────────────────────────────────────────────────────────
export const listarSpotSchedules = (playlistId) =>
  apiFetch(`/audio/spots/playlists/${playlistId}/spot-schedules`);

export const criarSpotSchedule = (playlistId, payload) =>
  apiFetch(`/audio/spots/playlists/${playlistId}/spot-schedules`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarSpotSchedule = (playlistId, scheduleId, payload) =>
  apiFetch(`/audio/spots/playlists/${playlistId}/spot-schedules/${scheduleId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarSpotSchedule = (playlistId, scheduleId) =>
  apiFetch(`/audio/spots/playlists/${playlistId}/spot-schedules/${scheduleId}`, {
    method: "DELETE",
  });
