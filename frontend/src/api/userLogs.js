import { apiFetch } from "./http";

export const listarLogs = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/user-logs${qs ? `?${qs}` : ""}`);
};

export const listarLogsPorUsuario = (userId) =>
  apiFetch(`/user-logs/by-user/${userId}`);

export const listarLogsRecentes = () => apiFetch("/user-logs/recent");

export const criarLog = (payload) =>
  apiFetch("/user-logs", { method: "POST", body: JSON.stringify(payload) });
