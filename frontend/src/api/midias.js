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

export const deletarMidia = (id) =>
  apiFetch(`/media/${id}`, { method: "DELETE" });
