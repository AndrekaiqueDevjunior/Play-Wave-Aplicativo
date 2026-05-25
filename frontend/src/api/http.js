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

export const isApiConfigurada = () => true; // sempre true: BASE_URL vazio = URL relativa
export const getBaseUrl       = () => BASE_URL;

// SPEC 004 — chave do localStorage onde o player guarda token_version.
// Inline aqui para evitar dependência circular com player-core/storage.js.
const LS_TOKEN_VERSION = "pw_player_token_version";

function getDeviceTokenVersion() {
  try {
    const v = localStorage.getItem(LS_TOKEN_VERSION);
    if (v == null) return null;
    const n = parseInt(v, 10);
    return Number.isFinite(n) ? n : null;
  } catch {
    return null;
  }
}

// Mesmas chaves usadas pelo AuthContext
const TOKEN_KEY = "pw_access_token";

function getStoredJwt() {
  return sessionStorage.getItem(TOKEN_KEY) ?? localStorage.getItem(TOKEN_KEY) ?? null;
}

function clearStoredSession() {
  [localStorage, sessionStorage].forEach((s) => {
    s.removeItem(TOKEN_KEY);
    s.removeItem("pw_user");
  });
}

function parseErrorDetail(raw) {
  if (!raw) return null;
  if (Array.isArray(raw)) {
    // Pydantic v2 validation errors: [{loc, msg, type}, ...]
    return raw
      .map((e) => {
        const loc = Array.isArray(e.loc)
          ? e.loc.filter((l) => l !== "body").join(" → ")
          : "";
        return loc ? `${loc}: ${e.msg}` : e.msg || JSON.stringify(e);
      })
      .join(" | ");
  }
  return String(raw);
}

/**
 * Realiza uma chamada ao backend FastAPI.
 *
 * options:
 *   deviceToken  — token do dispositivo (X-Device-Token)
 *   adminToken   — JWT explícito (sobrescreve o token armazenado)
 *   noAuth       — true para chamadas sem autenticação
 *   redirectOnUnauthorized — false para chamadas do player/device
 *   ...restante  — opções nativas de fetch (method, body, headers, etc.)
 */
export async function apiFetch(path, options = {}) {
  // BASE_URL vazio = URL relativa (mesma origem do Nginx)

  // `token` é alias legado de `deviceToken` para retrocompatibilidade
  const {
    deviceToken,
    token: legacyToken,
    adminToken,
    noAuth,
    redirectOnUnauthorized = true,
    ...fetchOptions
  } = options;
  const deviceTok = deviceToken ?? legacyToken;

  const jwt = adminToken ?? (!noAuth ? getStoredJwt() : null);

  // SPEC 004 — quando a chamada é do player (deviceTok presente), envia
  // também a versão atual do token. Backend valida via get_device_by_token.
  // Permite override via fetchOptions.headers.
  const deviceTokenVersion =
    deviceTok ? getDeviceTokenVersion() : null;

  const headers = {
    "Content-Type": "application/json",
    ...(jwt       ? { Authorization: `Bearer ${jwt}` }  : {}),
    ...(deviceTok ? { "X-Device-Token": deviceTok }     : {}),
    ...(deviceTokenVersion != null
      ? { "X-Device-Token-Version": String(deviceTokenVersion) }
      : {}),
    ...fetchOptions.headers,
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...fetchOptions, headers });

  // SPEC 004 — 401/403 com error_code conhecido → forceRepair() automático
  // para chamadas do player. Importa lazy para evitar ciclo de imports.
  if ((res.status === 401 || res.status === 403) && deviceTok) {
    const cloned = res.clone();
    let errorCode = null;
    try {
      const body = await cloned.json();
      // FastAPI HTTPException com dict no detail vira { detail: {error_code, ...} };
      // se já vem flat, lê direto.
      const inner = body?.detail && typeof body.detail === "object" ? body.detail : body;
      errorCode = inner?.error_code ?? body?.error_code ?? null;
    } catch {
      /* body não-JSON, ignora */
    }

    if (errorCode) {
      try {
        const { REPAIR_ERROR_CODES, forceRepair, RepairTriggeredError } =
          await import("../player-core/repair.js");
        if (REPAIR_ERROR_CODES.has(errorCode)) {
          // Fire-and-forget: forceRepair limpa storage e dispara callback do Player.
          forceRepair(errorCode).catch(() => {});
          throw new RepairTriggeredError(errorCode);
        }
      } catch (err) {
        if (err && err.isRepairTriggered) throw err;
        // Falha ao importar repair.js (ex: SSR) — segue fluxo normal.
      }
    }
  }

  if (res.status === 401 && redirectOnUnauthorized) {
    clearStoredSession();
    window.location.href = "/login";
    return null;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      // Body pode ser { detail: "..." } ou { detail: { error_code, detail, ...} }.
      const rawDetail =
        body.detail && typeof body.detail === "object"
          ? body.detail.detail || body.detail.error_code || body.detail
          : body.detail || body.message;
      detail = parseErrorDetail(rawDetail) || detail;
    } catch {
      try { detail = (await res.text()) || detail; } catch { /* ignore */ }
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;

  return res.json();
}

/** Verifica saúde do backend (sem auth) */
export const verificarSaude = () => apiFetch("/health", { noAuth: true });

export async function apiUpload(path, formData, options = {}) {
  // BASE_URL vazio = URL relativa

  const { adminToken, noAuth, headers: customHeaders, ...fetchOptions } = options;
  const jwt = adminToken ?? (!noAuth ? getStoredJwt() : null);
  const headers = {
    ...(jwt ? { Authorization: `Bearer ${jwt}` } : {}),
    ...customHeaders,
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    ...fetchOptions,
    body: formData,
    headers,
  });

  if (res.status === 401) {
    clearStoredSession();
    window.location.href = "/login";
    return null;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = parseErrorDetail(body.detail || body.message) || detail;
    } catch {
      try { detail = (await res.text()) || detail; } catch { /* ignore */ }
    }
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}
