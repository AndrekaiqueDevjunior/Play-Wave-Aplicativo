/**
 * Testes SPEC 015 — contentGuard (política WAIT_CONTENT_END).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { createContentGuard } from "@/player-core/contentGuard";

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-06-18T10:00:00.000Z"));
});

afterEach(() => {
  vi.useRealTimers();
});

describe("contentGuard — isContentBusy", () => {
  it("não está ocupado por padrão (estado inicial)", () => {
    const guard = createContentGuard();
    expect(guard.isContentBusy()).toBe(false);
  });

  it("fica ocupado quando phase=playing e há playlist", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    expect(guard.isContentBusy()).toBe(true);
  });

  it("não fica ocupado em outras fases mesmo com playlist", () => {
    const guard = createContentGuard();
    guard.update({ phase: "loading", hasPlaylist: true });
    expect(guard.isContentBusy()).toBe(false);
  });

  it("não fica ocupado quando playing mas sem playlist (só rádio)", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: false });
    expect(guard.isContentBusy()).toBe(false);
  });
});

describe("contentGuard — onceContentEnd", () => {
  it("chama o callback imediatamente quando não há conteúdo ativo", () => {
    const guard = createContentGuard();
    const cb = vi.fn();
    guard.onceContentEnd(cb);
    expect(cb).toHaveBeenCalledOnce();
  });

  it("represa o callback até notifyContentEnded quando há conteúdo ativo", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    const cb = vi.fn();
    guard.onceContentEnd(cb);
    expect(cb).not.toHaveBeenCalled();

    guard.notifyContentEnded();
    expect(cb).toHaveBeenCalledOnce();
  });

  it("dispara apenas uma vez mesmo que notifyContentEnded seja chamado de novo", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    const cb = vi.fn();
    guard.onceContentEnd(cb);

    guard.notifyContentEnded();
    guard.notifyContentEnded();

    expect(cb).toHaveBeenCalledOnce();
  });

  it("dispara múltiplos callbacks registrados na mesma janela", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    const cb1 = vi.fn();
    const cb2 = vi.fn();
    guard.onceContentEnd(cb1);
    guard.onceContentEnd(cb2);

    guard.notifyContentEnded();

    expect(cb1).toHaveBeenCalledOnce();
    expect(cb2).toHaveBeenCalledOnce();
  });

  it("a função de cancelamento remove o callback antes do disparo", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    const cb = vi.fn();
    const cancel = guard.onceContentEnd(cb);
    cancel();

    guard.notifyContentEnded();
    expect(cb).not.toHaveBeenCalled();
  });

  it("um erro em um callback não impede os demais de disparar", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true });
    const throwing = vi.fn(() => {
      throw new Error("boom");
    });
    const cb2 = vi.fn();
    guard.onceContentEnd(throwing);
    guard.onceContentEnd(cb2);

    expect(() => guard.notifyContentEnded()).not.toThrow();
    expect(cb2).toHaveBeenCalledOnce();
  });
});

describe("contentGuard — getRemainingMs", () => {
  it("retorna null quando não há conteúdo ativo", () => {
    const guard = createContentGuard();
    expect(guard.getRemainingMs()).toBeNull();
  });

  it("retorna null quando endsAt é desconhecido (duração natural)", () => {
    const guard = createContentGuard();
    guard.update({ phase: "playing", hasPlaylist: true, endsAt: null });
    expect(guard.getRemainingMs()).toBeNull();
  });

  it("calcula o tempo restante em ms quando endsAt é conhecido", () => {
    const guard = createContentGuard();
    const endsAt = Date.now() + 15_000;
    guard.update({ phase: "playing", hasPlaylist: true, endsAt });
    expect(guard.getRemainingMs()).toBe(15_000);
  });

  it("nunca retorna negativo quando endsAt já passou", () => {
    const guard = createContentGuard();
    const endsAt = Date.now() - 5_000;
    guard.update({ phase: "playing", hasPlaylist: true, endsAt });
    expect(guard.getRemainingMs()).toBe(0);
  });
});
