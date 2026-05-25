// @ts-nocheck
/**
 * repair.js — Força reparamento do player (SPEC 004).
 *
 * Disparado quando:
 *  - backend retorna 401/403 com error_code em REPAIR_ERROR_CODES;
 *  - SSE `pairing:revoked` chega no canal do device;
 *  - código de pareamento expirou.
 *
 * Limpa PairingStorage + PlaylistCache, desativa watchdog e força o
 * Player.jsx a voltar para a fase `pairing` via callback registrado.
 */

import { PairingStorage, PlaylistCache } from "./storage.js";

/** Códigos de erro do backend que disparam reparamento automático. */
export const REPAIR_ERROR_CODES = new Set([
  "TOKEN_REVOKED",
  "TOKEN_VERSION_MISMATCH",
  "TOKEN_VERSION_REQUIRED",
  "REQUIRES_REPAIRING",
  "DEVICE_BLOCKED",
  "PAIRING_CODE_EXPIRED",
]);

/** Erro lançado pelo interceptor http quando dispara `forceRepair`. */
export class RepairTriggeredError extends Error {
  constructor(errorCode) {
    super(`forceRepair triggered: ${errorCode}`);
    this.name = "RepairTriggeredError";
    this.errorCode = errorCode;
    this.isRepairTriggered = true;
  }
}

let _onForceRepair = null;
let _lastRepairAt = 0;
let _repairCount = 0;
let _inFlight = null;
const REPAIR_LIMIT_MS = 5 * 60 * 1000;
const REPAIR_MAX_COUNT = 3;
const REPAIR_BACKOFF_MS = 30 * 1000;

/**
 * Registra callback do Player.jsx que reseta para fase `pairing`.
 * Deve ser chamado uma vez no mount do Player.
 */
export function onForceRepair(callback) {
  _onForceRepair = callback;
}

/**
 * Força o pareamento novo: limpa storages, desativa watchdog, dispara callback.
 *
 * É idempotente — múltiplas chamadas em paralelo retornam a mesma Promise.
 * Implementa anti-loop: após 3 disparos em 5 min, aguarda 30s antes do próximo.
 */
export async function forceRepair(reason = "unknown") {
  // Anti-reentrância: se já está em curso, devolve a mesma Promise.
  if (_inFlight) return _inFlight;

  _inFlight = (async () => {
    console.warn("[repair] forceRepair triggered:", reason);

    // Anti-loop: max 3 repairs em 5 min, depois 30s de backoff.
    const now = Date.now();
    if (now - _lastRepairAt < REPAIR_LIMIT_MS) {
      _repairCount += 1;
      if (_repairCount > REPAIR_MAX_COUNT) {
        console.error(
          "[repair] too many repairs in 5min — backing off " + REPAIR_BACKOFF_MS + "ms",
        );
        await new Promise((r) => setTimeout(r, REPAIR_BACKOFF_MS));
        _repairCount = 0;
      }
    } else {
      _repairCount = 1;
    }
    _lastRepairAt = Date.now();

    // 1) Pega deviceId antes de limpar.
    const deviceId = PairingStorage.deviceId();

    // 2) Desativa watchdog se houver.
    if (typeof window !== "undefined" && window.__pwWatchdog) {
      try { clearTimeout(window.__pwWatchdog); } catch {}
      window.__pwWatchdog = null;
    }

    // 3) Limpa storages (best-effort, ignora erros).
    try { PairingStorage.clear(); } catch (e) { console.warn("[repair] clear pairing:", e); }
    if (deviceId) {
      try { await PlaylistCache.clear(deviceId); } catch (e) { console.warn("[repair] clear cache:", e); }
    }

    // 4) Notifica React. Se não houver callback registrado, faz reload da página.
    if (_onForceRepair) {
      try {
        _onForceRepair(reason);
      } catch (e) {
        console.warn("[repair] callback failed:", e);
      }
    } else if (typeof window !== "undefined") {
      setTimeout(() => window.location.reload(), 200);
    }
  })();

  try {
    await _inFlight;
  } finally {
    _inFlight = null;
  }
}
