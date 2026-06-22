/**
 * api/midias.js
 * Endpoints FastAPI — módulo Mídias
 *
 * CONTRATO FASTAPI:
 *
 * GET    /media                            (admin)
 *   query: tenant_id?, type?, search?, tags?
 *   resp: Media[]
 *
 * GET    /media/{id}                       (admin)
 *   resp: Media
 *
 * POST   /media/upload                     (admin, multipart/form-data)
 *   fields: file (binary), name, type, description?, tags?, category?
 *   resp: Media
 *
 * POST   /media                            (admin, external_url)
 *   body: { name, type: "external_url", file_url, description? }
 *   resp: Media
 *
 * PATCH  /media/{id}                       (admin)
 *   body: Partial<Media>
 *   resp: Media
 *
 * DELETE /media/{id}                       (admin)
 *   resp: 204
 *
 * POST   /media/{id}/replace-file          (admin, multipart/form-data)
 * GET    /media/{id}/usage                 (admin)
 * GET    /media/{id}/versions              (admin)
 *
 * GET    /media/{id}/thumbnail             (admin)
 *   resp: { thumbnail_url }
 */
import { apiFetch, apiUpload } from "./http";

export const listarMidias = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/media${qs ? `?${qs}` : ""}`);
};

export const buscarMidia = (id) => apiFetch(`/media/${id}`);

/** Upload de arquivo binário (multipart) */
export const uploadMidia = async (file, metadata = {}) => {
  const form = new FormData();
  form.append("file", file);
  Object.entries(metadata).forEach(([key, value]) => {
    if (value === undefined || value === null) return;
    form.append(key === "type" ? "media_type" : key, String(value));
  });

  return apiUpload("/media/upload", form);
};

export const criarMidiaExterna = (payload) =>
  apiFetch("/media", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarMidia = (id, payload) =>
  apiFetch(`/media/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const substituirArquivoMidia = async (id, file) => {
  const form = new FormData();
  form.append("file", file);
  return apiUpload(`/media/${id}/replace-file`, form);
};

export const buscarUsoMidia = (id) => apiFetch(`/media/${id}/usage`);

export const listarVersoesMidia = (id) => apiFetch(`/media/${id}/versions`);

export const deletarMidia = (id, { force = false } = {}) =>
  apiFetch(`/media/${id}${force ? "?force=true" : ""}`, { method: "DELETE" });

// SPEC 005 — re-detecta has_audio via ffprobe
export const recomputarDeteccaoAudio = (id) =>
  apiFetch(`/media/${id}/recompute-audio-detection`, { method: "POST" });

// SPEC 018 — ações em massa: cada item é processado independentemente no
// backend, então a resposta sempre tem { requested, succeeded, failed,
// results: [{ media_id, success, reason? }] }, mesmo quando alguns itens
// falham (em uso, sem permissão, não encontrado).
export const arquivarMidiasEmMassa = (mediaIds) =>
  apiFetch("/media/bulk-archive", {
    method: "POST",
    body: JSON.stringify({ media_ids: mediaIds }),
  });

export const excluirMidiasEmMassa = (mediaIds) =>
  apiFetch("/media/bulk-delete", {
    method: "POST",
    body: JSON.stringify({ media_ids: mediaIds }),
  });
