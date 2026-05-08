import { apiFetch } from "./http";

export const listarPlanos = () => apiFetch("/plans");

export const buscarPlano = (id) => apiFetch(`/plans/${id}`);

export const criarPlano = (payload) =>
  apiFetch("/plans", { method: "POST", body: JSON.stringify(payload) });

export const atualizarPlano = (id, payload) =>
  apiFetch(`/plans/${id}`, { method: "PUT", body: JSON.stringify(payload) });

export const deletarPlano = (id) =>
  apiFetch(`/plans/${id}`, { method: "DELETE" });
