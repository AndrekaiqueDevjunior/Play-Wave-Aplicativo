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
import { apiFetch, getBaseUrl } from "./http";

export const listarMidias = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/media${qs ? `?${qs}` : ""}`);
};

export const buscarMidia = (id) => apiFetch(`/media/${id}`);

/** Upload de arquivo binário (multipart) */
export const uploadMidia = async (file, metadata = {}) => {
  const BASE_URL = getBaseUrl();
  if (!BASE_URL) return null;

  const form = new FormData();
  form.append("file", file);
  Object.entries(metadata).forEach(([k, v]) => {
    if (v !== undefined && v !== null) form.append(k, String(v));
  });

  const res = await fetch(`${BASE_URL}/media/upload`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) throw new Error(`Upload error ${res.status}`);
  return res.json();
};

export const criarMidiaExterna = (payload) =>
  apiFetch("/media", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarMidia = (id, payload) =>
  apiFetch(`/media/${id}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const deletarMidia = (id) =>
  apiFetch(`/media/${id}`, { method: "DELETE" });
