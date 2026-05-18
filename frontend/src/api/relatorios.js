/**
 * api/relatorios.js
 * Endpoints FastAPI — módulo Relatórios / Analytics
 *
 * CONTRATO FASTAPI:
 *
 * GET    /reports/playback                 (admin)
 *   query: tenant_id?, device_id?, campaign_id?, date_from?, date_to?, limit?, skip?
 *   resp: PlaybackLog[]
 *
 * GET    /reports/summary                  (admin)
 *   query: tenant_id?, date_from?, date_to?
 *   resp: {
 *     total_views, total_devices, active_campaigns,
 *     top_campaign: {id, name, views},
 *     top_device:   {id, name, views},
 *     views_per_day: [{date, views}]
 *   }
 *
 * GET    /reports/device/{id}              (admin)
 *   query: date_from?, date_to?
 *   resp: { device_id, total_views, uptime_pct, campaigns: [{id, name, views}] }
 *
 * GET    /reports/campaign/{id}            (admin)
 *   query: date_from?, date_to?
 *   resp: { campaign_id, total_views, devices: [{id, name, views}], media: [{id, name, views}] }
 *
 * POST   /reports/playback                 (device, X-Device-Token)
 *   body: PlaybackLog (sem id)
 *   resp: 204
 *
 * GET    /reports/export/csv              (admin)
 *   query: mesmos filtros de /reports/playback
 *   resp: CSV file download
 *
 * GET    /events                           (admin)
 *   query: tenant_id?, device_id?, event_type?, severity?, limit?
 *   resp: DeviceEvent[]
 */
import { apiFetch, getBaseUrl } from "./http";

export const buscarLogPlayback = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/reports/playback${qs ? `?${qs}` : ""}`);
};

export const buscarResumoRelatorio = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/reports/summary${qs ? `?${qs}` : ""}`);
};

export const buscarRelatorioDevice = (deviceId, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/reports/device/${deviceId}${qs ? `?${qs}` : ""}`);
};

export const buscarRelatorioCampanha = (campanhaId, params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/reports/campaign/${campanhaId}${qs ? `?${qs}` : ""}`);
};

/** Device registra exibição de mídia */
export const registrarPlayback = (token, payload) =>
  apiFetch("/reports/playback", {
    method: "POST",
    token,
    body: JSON.stringify(payload),
  });

/** Download CSV de relatório (autenticado via JWT) */
export const exportarRelatorioCSV = async (params = {}) => {
  const BASE_URL = getBaseUrl();
  if (!BASE_URL) return null;

  const token =
    sessionStorage.getItem("pw_access_token") ??
    localStorage.getItem("pw_access_token");

  const qs = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""))
  ).toString();

  const res = await fetch(`${BASE_URL}/reports/export/csv${qs ? `?${qs}` : ""}`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });

  if (!res.ok) throw new Error(`Erro ao exportar CSV: HTTP ${res.status}`);

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `relatorio_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
};

export const buscarEventosDispositivo = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/monitoring/events${qs ? `?${qs}` : ""}`);
};
