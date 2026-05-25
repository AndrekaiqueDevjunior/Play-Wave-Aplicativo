/**
 * network.js — Motor de rede com retry, reconexão e detecção online/offline.
 *
 * Expõe:
 *   fetchWithRetry(url, options, retries, delay)
 *   useOnlineStatus()          React hook
 *   onOnline(cb) / onOffline(cb)
 */

const DEFAULT_RETRIES = 3;
const DEFAULT_DELAY_MS = 2000;

/**
 * Fetch com retry exponencial.
 * Funciona em qualquer WebView — não depende de Service Worker.
 */
export async function fetchWithRetry(url, options = {}, retries = DEFAULT_RETRIES, delay = DEFAULT_DELAY_MS) {
  let lastErr;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, options);
      if (!res.ok) {
        const body = await res.text().catch(() => "");
        throw new Error(`HTTP ${res.status}: ${body.slice(0, 100)}`);
      }
      return res;
    } catch (err) {
      lastErr = err;
      if (attempt < retries) {
        const wait = delay * Math.pow(2, attempt);
        console.warn(`[network] retry ${attempt + 1}/${retries} in ${wait}ms — ${err.message}`);
        await sleep(wait);
      }
    }
  }
  throw lastErr;
}

function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

// ── Online/Offline detection ─────────────────────────────────────────────────
const onlineListeners  = new Set();
const offlineListeners = new Set();

if (typeof window !== "undefined") {
  window.addEventListener("online",  () => onlineListeners.forEach((cb)  => cb()));
  window.addEventListener("offline", () => offlineListeners.forEach((cb) => cb()));
}

export function onOnline(cb)  { onlineListeners.add(cb);  return () => onlineListeners.delete(cb); }
export function onOffline(cb) { offlineListeners.add(cb); return () => offlineListeners.delete(cb); }
export function isOnline()    { return typeof navigator !== "undefined" ? navigator.onLine : true; }

// ── React hook ───────────────────────────────────────────────────────────────
import { useState, useEffect } from "react";

export function useOnlineStatus() {
  const [online, setOnline] = useState(() => isOnline());
  useEffect(() => {
    const unsub1 = onOnline(()  => { setOnline(true);  console.log("[network] online");  });
    const unsub2 = onOffline(() => { setOnline(false); console.log("[network] offline"); });
    return () => { unsub1(); unsub2(); };
  }, []);
  return online;
}

// ── Watchdog — detecta falta de heartbeat e tenta reconectar ────────────────
let _watchdogTimer = null;
let _lastHeartbeat = Date.now();

export function notifyHeartbeatOk() {
  _lastHeartbeat = Date.now();
}

/**
 * startWatchdog(thresholdMs, onRecovery)
 * Se nenhum heartbeat for registrado em thresholdMs ms, chama onRecovery().
 */
export function startWatchdog(thresholdMs = 120_000, onRecovery) {
  stopWatchdog();
  _watchdogTimer = setInterval(() => {
    const age = Date.now() - _lastHeartbeat;
    if (age > thresholdMs) {
      console.warn(`[network] watchdog triggered — no heartbeat for ${Math.round(age / 1000)}s`);
      _lastHeartbeat = Date.now();
      onRecovery?.();
    }
  }, 30_000);
}

export function stopWatchdog() {
  if (_watchdogTimer) {
    clearInterval(_watchdogTimer);
    _watchdogTimer = null;
  }
}
