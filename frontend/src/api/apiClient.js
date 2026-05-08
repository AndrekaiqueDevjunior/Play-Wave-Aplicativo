/**
 * api/base44Client.js → Renomeado internamente para apiClient.
 *
 * Fornece um objeto `base44` compatível com os imports legados, mas
 * implementado 100% sobre a API própria do Play Wave.
 *
 * Migre os imports para os módulos específicos (dispositivos.js,
 * campanhas.js, etc.) e este arquivo poderá ser removido.
 */
import { apiFetch, getBaseUrl } from "./http";

// ── Helpers genéricos ─────────────────────────────────────────────────────

const qs = (params = {}) => {
  const s = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== ""))
  ).toString();
  return s ? `?${s}` : "";
};

const buildEntity = (endpoint) => ({
  list: (orderBy, limit) => {
    const params = {};
    if (limit) params.limit = limit;
    return apiFetch(`${endpoint}${qs(params)}`);
  },
  filter: (filtros = {}) => apiFetch(`${endpoint}${qs(filtros)}`),
  get: (id) => apiFetch(`${endpoint}/${id}`),
  create: (payload) =>
    apiFetch(endpoint, { method: "POST", body: JSON.stringify(payload) }),
  update: (id, payload) =>
    apiFetch(`${endpoint}/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  delete: (id) => apiFetch(`${endpoint}/${id}`, { method: "DELETE" }),
});

// ── Upload genérico ───────────────────────────────────────────────────────

const uploadFile = async ({ file, endpoint = "/media/upload" } = {}) => {
  const BASE_URL = getBaseUrl();
  if (!BASE_URL || !file) return { file_url: "" };
  const form = new FormData();
  form.append("file", file);
  const token =
    sessionStorage.getItem("pw_access_token") ??
    localStorage.getItem("pw_access_token");
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) throw new Error(`Upload error ${res.status}`);
  return res.json();
};

// ── Entidades mapeadas ────────────────────────────────────────────────────

export const base44 = {
  entities: {
    Device:        buildEntity("/devices"),
    Campaign:      buildEntity("/campaigns"),
    Media:         buildEntity("/media"),
    Location:      buildEntity("/locations"),
    AudioTrack:    buildEntity("/audio/tracks"),
    AudioPlaylist: buildEntity("/audio/playlists"),
    User:          buildEntity("/users"),
    UserLog:       buildEntity("/user-logs"),
  },
  auth: {
    me: () => apiFetch("/api/auth/me"),
  },
  users: {
    inviteUser: (email, role) =>
      apiFetch("/users", {
        method: "POST",
        body: JSON.stringify({ email, role, password: crypto.randomUUID() }),
      }),
  },
  integrations: {
    Core: {
      UploadFile: ({ file } = {}) => uploadFile({ file }),
    },
  },
};
