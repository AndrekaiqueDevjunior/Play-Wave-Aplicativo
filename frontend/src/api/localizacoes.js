/**
 * api/localizacoes.js
 * Endpoints FastAPI — módulo Localizações / Grupos
 *
 * CONTRATO FASTAPI:
 *
 * GET    /locations                        (admin)
 *   query: tenant_id?
 *   resp: Location[]
 *
 * GET    /locations/{id}                   (admin)
 *   resp: Location
 *
 * POST   /locations                        (admin)
 *   body: { name, description?, address? }
 *   resp: Location
 *
 * PATCH  /locations/{id}                   (admin)
 *   body: Partial<Location>
 *   resp: Location
 *
 * DELETE /locations/{id}                   (admin)
 *   resp: 204
 *
 * GET    /locations/{id}/devices           (admin)
 *   resp: Device[]
 */
import { apiFetch } from "./http";

export const listarLocalizacoes = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/locations${qs ? `?${qs}` : ""}`);
};

export const buscarLocalizacao = (id) => apiFetch(`/locations/${id}`);

export const criarLocalizacao = (payload) =>
  apiFetch("/locations", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarLocalizacao = (id, payload) =>
  apiFetch(`/locations/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarLocalizacao = (id) =>
  apiFetch(`/locations/${id}`, { method: "DELETE" });

export const listarDispositivosDaLocalizacao = (id) =>
  apiFetch(`/locations/${id}/devices`);
