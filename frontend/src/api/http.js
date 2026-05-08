/**
 * api/http.js
 * Cliente HTTP base para o backend FastAPI.
 *
 * Configure VITE_API_URL no .env:
 *   VITE_API_URL=http://localhost:8000
 *
 * O JWT de admin é injetado automaticamente a partir do storage.
 * O token de device pode ser passado via options.deviceToken.
 */

const BASE_URL = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

export const isApiConfigurada = () => !!BASE_URL;
export const getBaseUrl       = () => BASE_URL;

// Mesmas chaves usadas pelo AuthContext
const TOKEN_KEY = "pw_access_token";

function getStoredJwt() {
  return sessionStorage.getItem(TOKEN_KEY) ?? localStorage.getItem(TOKEN_KEY) ?? null;
}

/**
 * Realiza uma chamada ao backend FastAPI.
 *
 * options:
 *   deviceToken  — token do dispositivo (X-Device-Token)
 *   adminToken   — JWT explícito (sobrescreve o token armazenado)
 *   noAuth       — true para chamadas sem autenticação
 *   ...restante  — opções nativas de fetch (method, body, headers, etc.)
 */
export async function apiFetch(path, options = {}) {
  if (!BASE_URL) return null;

  // `token` é alias legado de `deviceToken` para retrocompatibilidade
  const { deviceToken, token: legacyToken, adminToken, noAuth, ...fetchOptions } = options;
  const deviceTok = deviceToken ?? legacyToken;

  const jwt = adminToken ?? (!noAuth ? getStoredJwt() : null);

  const headers = {
    "Content-Type": "application/json",
    ...(jwt       ? { Authorization: `Bearer ${jwt}` }  : {}),
    ...(deviceTok ? { "X-Device-Token": deviceTok }     : {}),
    ...fetchOptions.headers,
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...fetchOptions, headers });

  if (res.status === 401) {
    // Token expirado — limpa sessão e força relogin
    [localStorage, sessionStorage].forEach((s) => {
      s.removeItem(TOKEN_KEY);
      s.removeItem("pw_user");
    });
    window.location.href = "/login";
    return null;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body.detail || body.message || detail;
    } catch {
      detail = (await res.text()) || detail;
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;

  return res.json();
}

/** Verifica saúde do backend (sem auth) */
export const verificarSaude = () => apiFetch("/health", { noAuth: true });
