// @ts-nocheck
/**
 * storage.js — Motor de armazenamento unificado.
 *
 * Camadas:
 *   1. localStorage  (sempre disponível — dados de pareamento e config)
 *   2. IndexedDB     (mídia em cache, playlists, logs)
 *
 * API pública simples: get / set / remove / clear
 * Funciona em: Web, Electron, Capacitor, Android WebView, SmartTV
 */

const DB_NAME  = "pw_player";
const DB_VERSION = 1;
const STORE_CACHE = "media_cache";
const STORE_STATE = "player_state";

let _db = null;

function openDB() {
  if (_db) return Promise.resolve(_db);
  return new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") return reject(new Error("no indexedDB"));
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains(STORE_CACHE)) {
        db.createObjectStore(STORE_CACHE, { keyPath: "key" });
      }
      if (!db.objectStoreNames.contains(STORE_STATE)) {
        db.createObjectStore(STORE_STATE, { keyPath: "key" });
      }
    };
    req.onsuccess  = (e) => { _db = e.target.result; resolve(_db); };
    req.onerror    = (e) => reject(e.target.error);
  });
}

function idbGet(store, key) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(store, "readonly");
        const req = tx.objectStore(store).get(key);
        req.onsuccess = () => resolve(req.result?.value ?? null);
        req.onerror   = () => reject(req.error);
      })
  );
}

function idbSet(store, key, value) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(store, "readwrite");
        tx.objectStore(store).put({ key, value, ts: Date.now() });
        tx.oncomplete = () => resolve();
        tx.onerror    = () => reject(tx.error);
      })
  );
}

function idbRemove(store, key) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(store, "readwrite");
        tx.objectStore(store).delete(key);
        tx.oncomplete = () => resolve();
        tx.onerror    = () => reject(tx.error);
      })
  );
}

function idbClear(store) {
  return openDB().then(
    (db) =>
      new Promise((resolve, reject) => {
        const tx = db.transaction(store, "readwrite");
        tx.objectStore(store).clear();
        tx.oncomplete = () => resolve();
        tx.onerror    = () => reject(tx.error);
      })
  );
}

// ── Pairing (sempre localStorage — rápido, crítico) ─────────────────────────
const LS_CODE  = "pw_player_code";
const LS_ID    = "pw_player_device_id";
const LS_TOKEN = "pw_player_device_token";
const LS_TOKEN_VERSION   = "pw_player_token_version";   // SPEC 004
const LS_PAIRING_VERSION = "pw_player_pairing_version"; // SPEC 004

function _parseInt(v) {
  if (v == null) return null;
  const n = parseInt(v, 10);
  return Number.isFinite(n) ? n : null;
}

export const PairingStorage = {
  load() {
    return {
      code:           localStorage.getItem(LS_CODE)  || null,
      id:             localStorage.getItem(LS_ID)    || null,
      token:          localStorage.getItem(LS_TOKEN) || null,
      tokenVersion:   _parseInt(localStorage.getItem(LS_TOKEN_VERSION)),
      pairingVersion: _parseInt(localStorage.getItem(LS_PAIRING_VERSION)),
    };
  },
  /**
   * Salva credenciais de pareamento.
   *
   * Aceita formato legado `save(code, id, token)` ou novo formato com versões:
   * `save({ code, id, token, tokenVersion, pairingVersion })`.
   */
  save(...args) {
    let payload;
    if (args.length === 1 && typeof args[0] === "object" && args[0] !== null) {
      payload = args[0];
    } else {
      const [code, id, token] = args;
      payload = { code, id, token };
    }
    if (payload.code  != null) localStorage.setItem(LS_CODE,  payload.code);
    if (payload.id    != null) localStorage.setItem(LS_ID,    payload.id);
    if (payload.token != null) localStorage.setItem(LS_TOKEN, payload.token);
    if (payload.tokenVersion != null) {
      localStorage.setItem(LS_TOKEN_VERSION, String(payload.tokenVersion));
    }
    if (payload.pairingVersion != null) {
      localStorage.setItem(LS_PAIRING_VERSION, String(payload.pairingVersion));
    }
  },
  /**
   * Setters individuais para conveniência (interceptor http etc).
   */
  setTokenVersion(v) {
    if (v == null) localStorage.removeItem(LS_TOKEN_VERSION);
    else           localStorage.setItem(LS_TOKEN_VERSION, String(v));
  },
  tokenVersion() {
    return _parseInt(localStorage.getItem(LS_TOKEN_VERSION));
  },
  pairingVersion() {
    return _parseInt(localStorage.getItem(LS_PAIRING_VERSION));
  },
  token() {
    return localStorage.getItem(LS_TOKEN);
  },
  deviceId() {
    return localStorage.getItem(LS_ID);
  },
  clear() {
    [LS_CODE, LS_ID, LS_TOKEN, LS_TOKEN_VERSION, LS_PAIRING_VERSION].forEach((k) =>
      localStorage.removeItem(k),
    );
  },
};

// ── Cache de playlist / campanha (IndexedDB) ─────────────────────────────────
export const PlaylistCache = {
  async get(deviceId) {
    try {
      return await idbGet(STORE_CACHE, `playlist_${deviceId}`);
    } catch {
      return null;
    }
  },
  async set(deviceId, data) {
    try {
      await idbSet(STORE_CACHE, `playlist_${deviceId}`, data);
    } catch {
      /* non-critical */
    }
  },
  async clear(deviceId) {
    try {
      if (deviceId) await idbRemove(STORE_CACHE, `playlist_${deviceId}`);
      else          await idbClear(STORE_CACHE);
    } catch { /* non-critical */ }
  },
};

// ── Estado do player (IndexedDB com fallback localStorage) ───────────────────
export const PlayerState = {
  async get(key) {
    try {
      return await idbGet(STORE_STATE, key);
    } catch {
      return localStorage.getItem(`pw_state_${key}`);
    }
  },
  async set(key, value) {
    try {
      await idbSet(STORE_STATE, key, value);
    } catch {
      try { localStorage.setItem(`pw_state_${key}`, value); } catch { /* full */ }
    }
  },
};
