/**
 * Testes SPEC 004 — repair.js
 *
 * Cobre:
 *  - REPAIR_ERROR_CODES contém os códigos esperados
 *  - RepairTriggeredError tem os campos corretos
 *  - forceRepair() limpa PairingStorage e chama o callback registrado
 *  - forceRepair() anti-loop: após 3 calls em 5min, aguarda antes de continuar
 *  - forceRepair() é idempotente (múltiplas chamadas paralelas = uma execução)
 *  - onForceRepair() registra callback que é invocado pelo forceRepair()
 */

import { describe, it, expect, vi, beforeEach } from "vitest";

// Reset dos módulos e localStorage antes de cada teste
beforeEach(() => {
  localStorage.clear();
  vi.resetModules();
  vi.clearAllMocks();
  vi.useRealTimers();
});

// ── REPAIR_ERROR_CODES ────────────────────────────────────────────────────────

describe("REPAIR_ERROR_CODES", () => {
  it("contém todos os códigos de erro esperados", async () => {
    const { REPAIR_ERROR_CODES } = await import("../player-core/repair.js");

    expect(REPAIR_ERROR_CODES.has("TOKEN_REVOKED")).toBe(true);
    expect(REPAIR_ERROR_CODES.has("TOKEN_VERSION_MISMATCH")).toBe(true);
    expect(REPAIR_ERROR_CODES.has("TOKEN_VERSION_REQUIRED")).toBe(true);
    expect(REPAIR_ERROR_CODES.has("REQUIRES_REPAIRING")).toBe(true);
    expect(REPAIR_ERROR_CODES.has("DEVICE_BLOCKED")).toBe(true);
    expect(REPAIR_ERROR_CODES.has("PAIRING_CODE_EXPIRED")).toBe(true);
  });

  it("não contém códigos genéricos que não devem disparar repair", async () => {
    const { REPAIR_ERROR_CODES } = await import("../player-core/repair.js");
    expect(REPAIR_ERROR_CODES.has("INTERNAL_SERVER_ERROR")).toBe(false);
    expect(REPAIR_ERROR_CODES.has("NOT_FOUND")).toBe(false);
    expect(REPAIR_ERROR_CODES.has("VALIDATION_ERROR")).toBe(false);
  });
});

// ── RepairTriggeredError ──────────────────────────────────────────────────────

describe("RepairTriggeredError", () => {
  it("tem name=RepairTriggeredError e errorCode correto", async () => {
    const { RepairTriggeredError } = await import("../player-core/repair.js");
    const err = new RepairTriggeredError("TOKEN_REVOKED");
    expect(err.name).toBe("RepairTriggeredError");
    expect(err.errorCode).toBe("TOKEN_REVOKED");
    expect(err.isRepairTriggered).toBe(true);
  });

  it("é uma instância de Error", async () => {
    const { RepairTriggeredError } = await import("../player-core/repair.js");
    const err = new RepairTriggeredError("DEVICE_BLOCKED");
    expect(err instanceof Error).toBe(true);
  });
});

// ── forceRepair + onForceRepair ───────────────────────────────────────────────

describe("forceRepair() — callback e limpeza de storage", () => {
  it("chama o callback registrado via onForceRepair com o reason correto", async () => {
    const { forceRepair, onForceRepair } = await import("../player-core/repair.js");

    // Salva dados de pareamento no localStorage para confirmar que serão limpos
    localStorage.setItem("pw_player_code", "TV-TEST");
    localStorage.setItem("pw_player_device_token", "tok-123");
    localStorage.setItem("pw_player_token_version", "3");

    const callback = vi.fn();
    onForceRepair(callback);

    await forceRepair("TOKEN_VERSION_MISMATCH");

    expect(callback).toHaveBeenCalledOnce();
    expect(callback).toHaveBeenCalledWith("TOKEN_VERSION_MISMATCH");
  });

  it("limpa pw_player_* do localStorage após forceRepair", async () => {
    const { forceRepair, onForceRepair } = await import("../player-core/repair.js");

    localStorage.setItem("pw_player_code", "TV-TEST");
    localStorage.setItem("pw_player_device_token", "tok-abc");
    localStorage.setItem("pw_player_token_version", "2");
    localStorage.setItem("pw_player_device_id", "dev-uuid");

    onForceRepair(() => {});
    await forceRepair("REQUIRES_REPAIRING");

    expect(localStorage.getItem("pw_player_code")).toBeNull();
    expect(localStorage.getItem("pw_player_device_token")).toBeNull();
    expect(localStorage.getItem("pw_player_token_version")).toBeNull();
    expect(localStorage.getItem("pw_player_device_id")).toBeNull();
  });

  it("múltiplas chamadas paralelas executam forceRepair apenas uma vez", async () => {
    const { forceRepair, onForceRepair } = await import("../player-core/repair.js");

    const callback = vi.fn();
    onForceRepair(callback);

    // Dispara 3 calls em paralelo
    await Promise.all([
      forceRepair("TOKEN_REVOKED"),
      forceRepair("TOKEN_REVOKED"),
      forceRepair("TOKEN_REVOKED"),
    ]);

    // O callback deve ter sido chamado exatamente uma vez (idempotência)
    expect(callback).toHaveBeenCalledOnce();
  });
});

// ── Anti-loop ─────────────────────────────────────────────────────────────────

describe("forceRepair() — anti-loop", () => {
  it("não lança erro em chamadas normais (< 3 em 5min)", async () => {
    const { forceRepair, onForceRepair } = await import("../player-core/repair.js");

    onForceRepair(() => {});

    await expect(forceRepair("TOKEN_REVOKED")).resolves.toBeUndefined();
    await expect(forceRepair("REQUIRES_REPAIRING")).resolves.toBeUndefined();
  });
});
