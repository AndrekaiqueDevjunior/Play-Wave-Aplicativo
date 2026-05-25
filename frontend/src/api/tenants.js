/**
 * api/tenants.js
 * Endpoints FastAPI — módulo Tenants (multi-tenancy)
 *
 * CONTRATO FASTAPI:
 *
 * GET    /tenants                          (superadmin)
 *   resp: Tenant[]
 *
 * GET    /tenants/{id}                     (admin)
 *   resp: Tenant
 *
 * POST   /tenants                          (superadmin)
 *   body: { name, plan, contact_email, max_devices? }
 *   resp: Tenant
 *
 * PATCH  /tenants/{id}                     (superadmin)
 *   body: Partial<Tenant>
 *   resp: Tenant
 *
 * DELETE /tenants/{id}                     (superadmin)
 *   resp: 204
 *
 * GET    /tenants/{id}/stats               (admin)
 *   resp: { devices_total, devices_online, campaigns_active, storage_used_mb }
 */
import { apiFetch } from "./http";

export const listarTenants = () => apiFetch("/tenants");

export const buscarMinhaEmpresa = () => apiFetch("/tenants/me");

export const atualizarMinhaEmpresa = (payload) =>
  apiFetch("/tenants/me", {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const buscarTenant = (id) => apiFetch(`/tenants/${id}`);

export const criarTenant = (payload) =>
  apiFetch("/tenants", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const atualizarTenant = (id, payload) =>
  apiFetch(`/tenants/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarTenant = (id) =>
  apiFetch(`/tenants/${id}`, { method: "DELETE" });

export const buscarEstatisticasTenant = (id) =>
  apiFetch(`/tenants/${id}/stats`);

// SPEC 005 — configuração de áudio do tenant
export const atualizarConfigAudioEmpresa = (payload) =>
  apiFetch("/tenants/me/audio-config", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });

export const atualizarOSDConfigEmpresa = (tenantId, payload) =>
  apiFetch(`/tenants/${tenantId}/osd-config`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
