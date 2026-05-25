/**
 * Testes SPEC 001 — isMediaCurrentlyPlayable (mediaSchedule.js)
 *
 * Cobre verificação de período de vigência de mídia: status, is_active,
 * starts_at, ends_at, valores inválidos e combinações.
 */

import { describe, it, expect } from "vitest";
import { isMediaCurrentlyPlayable } from "@/utils/mediaSchedule";

const NOW = 1_700_000_000_000; // timestamp fixo para testes determinísticos

describe("isMediaCurrentlyPlayable — SPEC 001", () => {
  it("retorna false para null", () => {
    expect(isMediaCurrentlyPlayable(null, NOW)).toBe(false);
  });

  it("retorna false para undefined", () => {
    expect(isMediaCurrentlyPlayable(undefined, NOW)).toBe(false);
  });

  it("retorna false se status === 'pending'", () => {
    expect(isMediaCurrentlyPlayable({ status: "pending" }, NOW)).toBe(false);
  });

  it("retorna false se status === 'archived'", () => {
    expect(isMediaCurrentlyPlayable({ status: "archived" }, NOW)).toBe(false);
  });

  it("retorna true se status === 'available'", () => {
    expect(isMediaCurrentlyPlayable({ status: "available" }, NOW)).toBe(true);
  });

  it("retorna false se is_active === false", () => {
    expect(isMediaCurrentlyPlayable({ is_active: false }, NOW)).toBe(false);
  });

  it("retorna true se is_active não presente (undefined)", () => {
    expect(isMediaCurrentlyPlayable({}, NOW)).toBe(true);
  });

  it("retorna false se starts_at está no futuro", () => {
    const media = { starts_at: new Date(NOW + 1000).toISOString() };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(false);
  });

  it("retorna true se starts_at está no passado", () => {
    const media = { starts_at: new Date(NOW - 1000).toISOString() };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(true);
  });

  it("retorna false se ends_at está no passado", () => {
    const media = { ends_at: new Date(NOW - 1000).toISOString() };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(false);
  });

  it("retorna true se ends_at está no futuro", () => {
    const media = { ends_at: new Date(NOW + 1000).toISOString() };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(true);
  });

  it("retorna true se starts_at no passado E ends_at no futuro", () => {
    const media = {
      starts_at: new Date(NOW - 1000).toISOString(),
      ends_at: new Date(NOW + 1000).toISOString(),
    };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(true);
  });

  it("retorna false se starts_at está no futuro (período invertido/starts > ends)", () => {
    // starts_at no futuro — mesmo que ends_at também esteja no futuro
    const media = {
      starts_at: new Date(NOW + 2000).toISOString(),
      ends_at: new Date(NOW + 5000).toISOString(),
    };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(false);
  });

  it("ignora starts_at inválido ('invalid') — comportamento: NaN não é Finite, portanto ignora", () => {
    // Date.parse("invalid") === NaN → Number.isFinite(NaN) === false → ignora
    const media = { starts_at: "invalid" };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(true);
  });

  it("media com todos os campos válidos retorna true", () => {
    const media = {
      status: "available",
      is_active: true,
      starts_at: new Date(NOW - 5000).toISOString(),
      ends_at: new Date(NOW + 5000).toISOString(),
    };
    expect(isMediaCurrentlyPlayable(media, NOW)).toBe(true);
  });
});
