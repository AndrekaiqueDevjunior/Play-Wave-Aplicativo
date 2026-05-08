import { apiFetch } from "./http";

export const listarUsuarios = (params = {}) => {
  const qs = new URLSearchParams(params).toString();
  return apiFetch(`/users${qs ? `?${qs}` : ""}`);
};

export const buscarUsuario = (id) => apiFetch(`/users/${id}`);

export const criarUsuario = (payload) =>
  apiFetch("/users", { method: "POST", body: JSON.stringify(payload) });

export const atualizarUsuario = (id, payload) =>
  apiFetch(`/users/${id}`, { method: "PUT", body: JSON.stringify(payload) });

export const deletarUsuario = (id) =>
  apiFetch(`/users/${id}`, { method: "DELETE" });

export const alterarRoleUsuario = (id, role) =>
  apiFetch(`/users/${id}/role`, { method: "PATCH", body: JSON.stringify({ role }) });

export const alterarStatusUsuario = (id, is_active) =>
  apiFetch(`/users/${id}/status`, { method: "PATCH", body: JSON.stringify({ is_active }) });

export const buscarMe = () => apiFetch("/api/auth/me", { noAuth: false });
