/**
 * api/campanhas.js
 * Endpoints FastAPI — módulo Campanhas
 *
 * CONTRATO FASTAPI:
 *
 * GET    /campaigns                        (admin)
 *   query: tenant_id?, status?, search?
 *   resp: Campaign[]
 *
 * GET    /campaigns/{id}                   (admin)
 *   resp: Campaign
 *
 * POST   /campaigns                        (admin)
 *   body: Campaign (sem id)
 *   resp: Campaign
 *
 * PATCH  /campaigns/{id}                   (admin)
 *   body: Partial<Campaign>
 *   resp: Campaign
 *
 * DELETE /campaigns/{id}                   (admin)
 *   resp: 204
 *
 * POST   /campaigns/{id}/publish           (admin)
 *   body: { device_ids?: string[] }
 *   resp: { published_to: number, config_version: string }
 *
 * POST   /campaigns/{id}/pause            (admin)
 *   resp: Campaign
 *
 * POST   /campaigns/{id}/resume           (admin)
 *   resp: Campaign
 *
 * GET    /campaigns/{id}/stats            (admin)
 *   resp: { total_views, devices_active, media_breakdown: [{media_id, views}] }
 */
import { apiFetch } from "./http";

export const listarCampanhas = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/campaigns${qs ? `?${qs}` : ""}`);
};

export const buscarCampanha = (id) => apiFetch(`/campaigns/${id}`);

export const criarCampanha = (payload) =>
  apiFetch("/campaigns", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarCampanha = (id, payload) =>
  apiFetch(`/campaigns/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarCampanha = (id) =>
  apiFetch(`/campaigns/${id}`, { method: "DELETE" });

export const publicarCampanha = (id, payload = {}) =>
  apiFetch(`/campaigns/${id}/publish`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const pausarCampanha = (id) =>
  apiFetch(`/campaigns/${id}/pause`, { method: "POST" });

export const retormarCampanha = (id) =>
  apiFetch(`/campaigns/${id}/resume`, { method: "POST" });

export const buscarEstatisticasCampanha = (id) =>
  apiFetch(`/campaigns/${id}/stats`);
