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
