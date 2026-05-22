/**
 * api/dispositivos.js
 * Endpoints FastAPI — módulo Dispositivos / Pairing / Heartbeat
 *
 * CONTRATO FASTAPI:
 *
 * POST   /devices/pair-request
 *   body: { code, player_version?, os?, screen_resolution? }
 *   resp: { id, code, expires_at, status }
 *
 * GET    /devices/by-code/{code}/status
 *   resp: { status: "waiting"|"paired"|"expired", device_token?, device_id? }
 *
 * POST   /devices/{id}/pair-confirm         (admin)
 *   body: { name, device_type, location?, group?, os? }
 *   resp: Device
 *
 * GET    /devices                           (admin)
 *   query: tenant_id?, status?, search?
 *   resp: Device[]
 *
 * GET    /devices/{id}                      (admin)
 *   resp: Device
 *
 * PATCH  /devices/{id}                      (admin)
 *   body: Partial<Device>
 *   resp: Device
 *
 * DELETE /devices/{id}                      (admin)
 *   resp: 204
 *
 * GET    /devices/{id}/playlist             (device, X-Device-Token)
 *   resp: { campaign_id, campaign_name, media: [{id,name,file_url,type,duration}] }
 *
 * POST   /devices/{id}/heartbeat            (device, X-Device-Token)
 *   body: { timestamp, status?, ip_address?, player_version?, storage_used? }
 *   resp: { ok, is_blocked, config_version, has_update }
 *
 * GET    /devices/{id}/metrics              (admin)
 *   resp: { last_seen_at, status, storage_used, player_version, ip_address }
 *
 * POST   /devices/{id}/command              (admin)
 *   body: { command: "restart"|"sync"|"clear_cache"|"screenshot" }
 *   resp: { queued: true }
 *
 * POST   /devices/{id}/block               (admin)
 *   resp: Device
 *
 * POST   /devices/{id}/unblock             (admin)
 *   resp: Device
 *
 * POST   /devices/{id}/revoke-token        (admin)
 *   resp: { new_token }
 */
import { apiFetch, getBaseUrl } from "./http";

// ── TV: Pareamento ─────────────────────────────────────────────────────────
export const solicitarPareamento = (payload) =>
  apiFetch("/devices/pair-request", {
    method: "POST",
    noAuth: true,
    redirectOnUnauthorized: false,
    body: JSON.stringify(payload),
  });

export const verificarStatusPareamento = (codigo) =>
  apiFetch(`/devices/by-code/${codigo}/status`, {
    noAuth: true,
    redirectOnUnauthorized: false,
  });

// ── Admin: Pareamento ──────────────────────────────────────────────────────
export const confirmarPareamento = (deviceId, payload) =>
  apiFetch(`/devices/${deviceId}/pair-confirm`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

// ── Admin: CRUD ────────────────────────────────────────────────────────────
export const criarDispositivo = (payload) =>
  apiFetch("/devices", { method: "POST", body: JSON.stringify(payload) });

export const listarDispositivos = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/devices${qs ? `?${qs}` : ""}`);
};

export const buscarDispositivo = (id) => apiFetch(`/devices/${id}`);

export const atualizarDispositivo = (id, payload) =>
  apiFetch(`/devices/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });

export const deletarDispositivo = (id) =>
  apiFetch(`/devices/${id}`, { method: "DELETE" });

// ── TV: Playlist & Heartbeat ───────────────────────────────────────────────
export const buscarPlaylistDispositivo = (deviceId, token) =>
  apiFetch(`/devices/${deviceId}/playlist`, {
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
  });

export const enviarHeartbeat = (deviceId, token, payload = {}) =>
  apiFetch(`/devices/${deviceId}/heartbeat`, {
    method: "POST",
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
    body: JSON.stringify({ timestamp: new Date().toISOString(), ...payload }),
  });

// ── Admin: Monitoramento ───────────────────────────────────────────────────
export const buscarMetricasDispositivo = (deviceId) =>
  apiFetch(`/devices/${deviceId}/metrics`);

/**
 * Envia comando ao dispositivo.
 * SPEC 003 — aceita `expires_in_seconds` opcional (60-3600) e `payload`.
 */
export const enviarComando = (deviceId, comando, opts = {}) => {
  const body = { command_type: comando };
  if (opts.payload) body.payload = opts.payload;
  if (opts.expiresInSeconds != null) body.expires_in_seconds = opts.expiresInSeconds;
  return apiFetch(`/devices/${deviceId}/command`, {
    method: "POST",
    body: JSON.stringify(body),
  });
};

/**
 * Cancela comando ainda em PENDING ou SENT.
 * SPEC 003 — endpoint POST /devices/{id}/commands/{cmd}/cancel.
 */
export const cancelarComando = (deviceId, commandId) =>
  apiFetch(`/devices/${deviceId}/commands/${commandId}/cancel`, {
    method: "POST",
  });

export const listarComandosDispositivo = (deviceId, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/devices/${deviceId}/commands${qs ? `?${qs}` : ""}`);
};

export const bloquearDispositivo = (deviceId) =>
  apiFetch(`/devices/${deviceId}/block`, { method: "POST" });

export const desbloquearDispositivo = (deviceId) =>
  apiFetch(`/devices/${deviceId}/unblock`, { method: "POST" });

export const revogarTokenDispositivo = (deviceId) =>
  apiFetch(`/devices/${deviceId}/revoke-token`, { method: "POST" });

export const regenerarCodigoPareamento = (deviceId) =>
  apiFetch(`/devices/${deviceId}/pairing-code/regenerate`, { method: "POST" });

// ── TV: Command queue (player) ───────────────────────────────────────────
export const buscarComandosPendentes = (deviceId, token) =>
  apiFetch(`/devices/${deviceId}/commands/pending`, {
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
  });

export const marcarComandoRecebido = (deviceId, commandId, token) =>
  apiFetch(`/devices/${deviceId}/commands/${commandId}/received`, {
    method: "POST",
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
  });

export const marcarComandoIniciado = (deviceId, commandId, token) =>
  apiFetch(`/devices/${deviceId}/commands/${commandId}/started`, {
    method: "POST",
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
  });

export const ackComando = (deviceId, commandId, token, success = true, errorMessage = null, result = null) =>
  apiFetch(`/devices/${deviceId}/commands/${commandId}/ack`, {
    method: "POST",
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
    body: JSON.stringify({ success, error_message: errorMessage, result }),
  });

// ── TV: SSE — playlist/config updates em tempo real ──────────────────
/**
 * Abre stream Server-Sent Events para receber eventos do device
 * (playlist_invalidated, snapshot, command). Retorna o EventSource —
 * o caller deve chamar `.close()` no cleanup.
 *
 * Auth via query string (EventSource não suporta headers customizados).
 */
export const abrirStreamPlaylistUpdates = (deviceId, deviceToken) => {
  const base = getBaseUrl();
  if (!deviceId || !deviceToken) return null;
  const url = `${base}/devices/${deviceId}/playlist/updates?token=${encodeURIComponent(deviceToken)}`;
  return new EventSource(url);
};

// ── TV: Playback log ─────────────────────────────────────────
export const registrarPlayback = (deviceId, token, payload) =>
  apiFetch(`/devices/${deviceId}/playback-log`, {
    method: "POST",
    token,
    noAuth: true,
    redirectOnUnauthorized: false,
    body: JSON.stringify(payload),
  });
