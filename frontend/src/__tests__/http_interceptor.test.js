/**
 * Testes SPEC 004 — apiFetch interceptor (api/http.js)
 *
 * Cobre: tratamento de 401/403 com error_code de repair, sem deviceToken,
 * erro 500 genérico, e redirecionamento /login para chamadas admin.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock do módulo repair.js (importado dinamicamente por http.js)
vi.mock("@/player-core/repair.js", () => {
  class RepairTriggeredError extends Error {
    constructor(code) {
      super(code);
      this.name = "RepairTriggeredError";
      this.errorCode = code;
      this.isRepairTriggered = true;
    }
  }
  return {
    REPAIR_ERROR_CODES: new Set([
      "TOKEN_REVOKED",
      "TOKEN_VERSION_MISMATCH",
      "DEVICE_BLOCKED",
      "REQUIRES_REPAIRING",
      "PAIRING_CODE_EXPIRED",
      "TOKEN_VERSION_REQUIRED",
    ]),
    forceRepair: vi.fn().mockResolvedValue(undefined),
    RepairTriggeredError,
  };
});

// Helper para montar uma resposta fetch mockada
function makeFetchResponse({ status = 200, errorCode = null, ok = null } = {}) {
  const isOk = ok !== null ? ok : status >= 200 && status < 300;
  const body = errorCode
    ? { detail: { error_code: errorCode } }
    : status >= 400
    ? { detail: "Erro" }
    : {};
  return {
    status,
    ok: isOk,
    clone() {
      return this;
    },
    json: vi.fn().mockResolvedValue(body),
    text: vi.fn().mockResolvedValue(""),
  };
}

// Captura window.location.href via Object.defineProperty no jsdom
let locationHrefSpy;

beforeEach(() => {
  // jsdom não permite atribuir window.location diretamente; usa delete + Object.defineProperty
  delete window.location;
  window.location = { href: "" };
  vi.clearAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

describe("apiFetch interceptor SPEC 004", () => {
  it("401 com error_code TOKEN_REVOKED + deviceToken → forceRepair chamado + lança RepairTriggeredError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(makeFetchResponse({ status: 401, errorCode: "TOKEN_REVOKED" })),
    );

    const { apiFetch } = await import("@/api/http");
    const { forceRepair } = await import("@/player-core/repair.js");

    await expect(
      apiFetch("/test", { deviceToken: "device-tok-123" }),
    ).rejects.toMatchObject({ name: "RepairTriggeredError", errorCode: "TOKEN_REVOKED" });

    expect(forceRepair).toHaveBeenCalled();
  });

  it("401 com error_code TOKEN_VERSION_MISMATCH + deviceToken → forceRepair chamado", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        makeFetchResponse({ status: 401, errorCode: "TOKEN_VERSION_MISMATCH" }),
      ),
    );

    const { apiFetch } = await import("@/api/http");
    const { forceRepair } = await import("@/player-core/repair.js");

    await expect(
      apiFetch("/test", { deviceToken: "device-tok-123" }),
    ).rejects.toMatchObject({ name: "RepairTriggeredError" });

    expect(forceRepair).toHaveBeenCalled();
  });

  it("403 com error_code DEVICE_BLOCKED + deviceToken → forceRepair chamado", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        makeFetchResponse({ status: 403, errorCode: "DEVICE_BLOCKED" }),
      ),
    );

    const { apiFetch } = await import("@/api/http");
    const { forceRepair } = await import("@/player-core/repair.js");

    await expect(
      apiFetch("/test", { deviceToken: "device-tok-123" }),
    ).rejects.toMatchObject({ name: "RepairTriggeredError" });

    expect(forceRepair).toHaveBeenCalled();
  });

  it("401 sem error_code + deviceToken → NÃO chama forceRepair, redireciona /login", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        status: 401,
        ok: false,
        clone() { return this; },
        json: vi.fn().mockResolvedValue({ detail: "Não autorizado" }),
        text: vi.fn().mockResolvedValue(""),
      }),
    );

    const { apiFetch } = await import("@/api/http");
    const { forceRepair } = await import("@/player-core/repair.js");

    // Com deviceToken, mas redirectOnUnauthorized=true (padrão), após verificar
    // que não há errorCode, redireciona /login
    const result = await apiFetch("/test", {
      deviceToken: "device-tok-123",
      redirectOnUnauthorized: true,
    });

    expect(forceRepair).not.toHaveBeenCalled();
    expect(result).toBeNull();
    expect(window.location.href).toBe("/login");
  });

  it("500 com deviceToken → NÃO chama forceRepair, lança Error genérico", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(makeFetchResponse({ status: 500, ok: false })),
    );

    const { apiFetch } = await import("@/api/http");
    const { forceRepair } = await import("@/player-core/repair.js");

    await expect(
      apiFetch("/test", { deviceToken: "device-tok-123" }),
    ).rejects.toBeInstanceOf(Error);

    expect(forceRepair).not.toHaveBeenCalled();
  });

  it("401 com error_code TOKEN_REVOKED mas SEM deviceToken → NÃO chama forceRepair, redireciona /login", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        makeFetchResponse({ status: 401, errorCode: "TOKEN_REVOKED" }),
      ),
    );

    const { apiFetch } = await import("@/api/http");
    const { forceRepair } = await import("@/player-core/repair.js");

    // Chamada admin: sem deviceToken
    const result = await apiFetch("/test", { redirectOnUnauthorized: true });

    expect(forceRepair).not.toHaveBeenCalled();
    expect(result).toBeNull();
    expect(window.location.href).toBe("/login");
  });
});
