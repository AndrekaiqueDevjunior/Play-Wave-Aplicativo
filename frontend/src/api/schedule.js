/**
 * api/schedule.js
 * Endpoints FastAPI — módulo Agenda / Calendário
 *
 * CONTRATO FASTAPI:
 *
 * GET    /schedule                          (autenticado)
 *   query: start?, end?, skip?, limit?
 *   resp: Campaign[]  (campanhas com start_date ou end_date)
 *
 * GET    /schedule/upcoming                 (autenticado)
 *   query: days?  (padrão 7, máx 90)
 *   resp: Campaign[]
 *
 * GET    /schedule/active                   (autenticado)
 *   resp: Campaign[]  (campanhas com status "active" agora)
 */
import { apiFetch } from "./http";

/** Lista campanhas agendadas com filtro opcional de intervalo de datas */
export const listarAgenda = (params = {}) => {
  const qs = new URLSearchParams(
    Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    )
  ).toString();
  return apiFetch(`/schedule${qs ? `?${qs}` : ""}`);
};

/** Campanhas que iniciam nos próximos N dias */
export const listarProximas = (days = 7) =>
  apiFetch(`/schedule/upcoming?days=${days}`);

/** Campanhas ativas no momento */
export const listarAtivasAgora = () => apiFetch("/schedule/active");
