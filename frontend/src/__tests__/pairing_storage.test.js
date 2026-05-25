/**
 * Testes SPEC 004 — PairingStorage (storage.js)
 *
 * Cobre: save/load com token_version e pairing_version, clear, getters individuais.
 * Ambiente: jsdom (localStorage disponível via vitest + jsdom).
 */

import { describe, it, expect, beforeEach } from "vitest";
import { PairingStorage } from "../player-core/storage.js";

// Reset localStorage antes de cada teste
beforeEach(() => {
  localStorage.clear();
});

describe("PairingStorage — campos básicos (pré-SPEC 004)", () => {
  it("save() e load() preservam code, id, token", () => {
    PairingStorage.save({ code: "TV-ABCD", id: "dev-1", token: "tok-abc" });
    const loaded = PairingStorage.load();
    expect(loaded.code).toBe("TV-ABCD");
    expect(loaded.id).toBe("dev-1");
    expect(loaded.token).toBe("tok-abc");
  });

  it("load() retorna null para campos não definidos", () => {
    const loaded = PairingStorage.load();
    expect(loaded.code).toBeNull();
    expect(loaded.id).toBeNull();
    expect(loaded.token).toBeNull();
  });
});

describe("PairingStorage — SPEC 004: token_version e pairing_version", () => {
  it("save() persiste tokenVersion no localStorage", () => {
    PairingStorage.save({ code: "TV-X", id: "dev-1", token: "tok", tokenVersion: 3 });
    expect(localStorage.getItem("pw_player_token_version")).toBe("3");
  });

  it("save() persiste pairingVersion no localStorage", () => {
    PairingStorage.save({ pairingVersion: 2 });
    expect(localStorage.getItem("pw_player_pairing_version")).toBe("2");
  });

  it("load() retorna tokenVersion como número", () => {
    PairingStorage.save({ tokenVersion: 5 });
    const loaded = PairingStorage.load();
    expect(loaded.tokenVersion).toBe(5);
    expect(typeof loaded.tokenVersion).toBe("number");
  });

  it("load() retorna null para tokenVersion quando não salvo", () => {
    const loaded = PairingStorage.load();
    expect(loaded.tokenVersion).toBeNull();
  });

  it("tokenVersion() retorna o valor correto", () => {
    PairingStorage.save({ tokenVersion: 7 });
    expect(PairingStorage.tokenVersion()).toBe(7);
  });

  it("setTokenVersion() atualiza o valor", () => {
    PairingStorage.save({ tokenVersion: 1 });
    PairingStorage.setTokenVersion(4);
    expect(PairingStorage.tokenVersion()).toBe(4);
  });

  it("setTokenVersion(null) remove a chave", () => {
    PairingStorage.save({ tokenVersion: 3 });
    PairingStorage.setTokenVersion(null);
    expect(localStorage.getItem("pw_player_token_version")).toBeNull();
  });
});

describe("PairingStorage — SPEC 004: clear()", () => {
  it("clear() remove todas as chaves pw_player_*", () => {
    PairingStorage.save({
      code: "TV-X",
      id: "dev-1",
      token: "tok",
      tokenVersion: 3,
      pairingVersion: 2,
    });

    PairingStorage.clear();

    expect(localStorage.getItem("pw_player_code")).toBeNull();
    expect(localStorage.getItem("pw_player_device_id")).toBeNull();
    expect(localStorage.getItem("pw_player_device_token")).toBeNull();
    expect(localStorage.getItem("pw_player_token_version")).toBeNull();
    expect(localStorage.getItem("pw_player_pairing_version")).toBeNull();
  });

  it("clear() é idempotente — não lança erro se chamado múltiplas vezes", () => {
    expect(() => {
      PairingStorage.clear();
      PairingStorage.clear();
      PairingStorage.clear();
    }).not.toThrow();
  });

  it("load() retorna tudo nulo após clear()", () => {
    PairingStorage.save({ code: "TV-A", id: "dev-1", token: "tok", tokenVersion: 2 });
    PairingStorage.clear();
    const loaded = PairingStorage.load();
    expect(loaded.code).toBeNull();
    expect(loaded.tokenVersion).toBeNull();
  });
});

describe("PairingStorage — compatibilidade com formato legado save(code, id, token)", () => {
  it("save(obj) aceita formato novo de objeto", () => {
    PairingStorage.save({ code: "TV-ZZ", id: "dev-z", token: "tok-z" });
    expect(PairingStorage.load().code).toBe("TV-ZZ");
  });
});
