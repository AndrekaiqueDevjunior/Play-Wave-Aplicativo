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
 * PUT    /campaigns/{id}                   (admin)
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

// ── Itens relacionais da playlist visual ─────────────────────────────────
export const listarItensCampanha = (campaignId) =>
  apiFetch(`/campaigns/${campaignId}/items`);

export const adicionarItensCampanha = (campaignId, items) =>
  apiFetch(`/campaigns/${campaignId}/items`, {
    method: "POST",
    body: JSON.stringify({ items }),
  });

export const atualizarItemCampanha = (campaignId, itemId, payload) =>
  apiFetch(`/campaigns/${campaignId}/items/${itemId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const removerItemCampanha = (campaignId, itemId) =>
  apiFetch(`/campaigns/${campaignId}/items/${itemId}`, { method: "DELETE" });

export const reordenarItensCampanha = (campaignId, items) =>
  apiFetch(`/campaigns/${campaignId}/items/reorder`, {
    method: "PATCH",
    body: JSON.stringify({ items }),
  });

export async function sincronizarItensCampanha(campaignId, desiredItems = []) {
  const currentItems = await listarItensCampanha(campaignId);
  const currentById = new Map((currentItems || []).map((item) => [item.id, item]));
  const desiredExistingIds = new Set(
    desiredItems.map((item) => item.id).filter((id) => currentById.has(id)),
  );

  await Promise.all(
    (currentItems || [])
      .filter((item) => !desiredExistingIds.has(item.id))
      .map((item) => removerItemCampanha(campaignId, item.id)),
  );

  const toCreate = [];

  for (const [index, item] of desiredItems.entries()) {
    const payload = {
      media_id: item.media_id,
      order_index: index * 10,
      display_duration_seconds: item.display_duration_seconds || null,
      starts_at: item.starts_at || null,
      ends_at: item.ends_at || null,
      is_active: item.is_active !== false,
      repeat_count: item.repeat_count || 1,
    };

    if (item.id && currentById.has(item.id)) {
      await atualizarItemCampanha(campaignId, item.id, payload);
    } else {
      toCreate.push(payload);
    }
  }

  if (toCreate.length > 0) {
    await adicionarItensCampanha(campaignId, toCreate);
  }

  const synced = await listarItensCampanha(campaignId);
  const orderItems = (synced || []).map((item, index) => ({
    item_id: item.id,
    order_index: index * 10,
  }));
  if (orderItems.length > 0) {
    return reordenarItensCampanha(campaignId, orderItems);
  }
  return synced;
}
