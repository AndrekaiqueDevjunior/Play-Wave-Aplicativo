/**
 * api/http.js
 * Cliente HTTP base para o backend FastAPI.
 *
 * Configure VITE_API_URL no .env:
 *   VITE_API_URL=http://localhost:8000
 *
 * Quando VITE_API_URL não está definido, isApiConfigurada() retorna false
 * e todas as funções retornam null — o app faz fallback automático para Base44.
 */

const BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export const isApiConfigurada = () => !!BASE_URL;
export const getBaseUrl = () => BASE_URL;

/**
 * Realiza uma chamada autenticada ao backend FastAPI.
 * O token do device (device_token) pode ser passado via options.token.
 * O admin token (JWT) pode ser passado via options.adminToken.
 */
export async function apiFetch(path, options = {}) {
  if (!BASE_URL) return null;

  const { token, adminToken, ...fetchOptions } = options;

  const headers = {
    "Content-Type": "application/json",
    ...(token ? { "X-Device-Token": token } : {}),
    ...(adminToken ? { Authorization: `Bearer ${adminToken}` } : {}),
    ...fetchOptions.headers,
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    ...fetchOptions,
    headers,
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }

  // 204 No Content
  if (res.status === 204) return null;

  return res.json();
}

/** Verifica saúde do backend */
export const verificarSaude = () => apiFetch("/health");
