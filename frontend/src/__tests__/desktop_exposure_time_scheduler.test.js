import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import {
  createDesktopExposureTimeScheduler,
  nextOccurrence,
  computeNext,
  EXPOSURE_STATE,
} from "../player-core/desktopExposureTimeScheduler.js";

// Quarta-feira, 2026-06-03 07:00:00 local (getDay() === 3)
const BASE = new Date(2026, 5, 3, 7, 0, 0, 0);

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(BASE);
  vi.clearAllMocks();
});

afterEach(() => {
  vi.runOnlyPendingTimers();
  vi.useRealTimers();
});

describe("nextOccurrence", () => {
  it("agenda para hoje quando o horário ainda não passou", () => {
    const at = nextOccurrence({ time: "08:00" }, BASE);
    expect(at.getDate()).toBe(3);
    expect(at.getHours()).toBe(8);
  });

  it("agenda para amanhã quando o horário já passou", () => {
    const at = nextOccurrence({ time: "06:00" }, BASE);
    expect(at.getDate()).toBe(4);
    expect(at.getHours()).toBe(6);
  });

  it("respeita weekdays (pula dias não permitidos)", () => {
    // Só segunda(1): de quarta 03/06, próxima segunda é 08/06.
    const at = nextOccurrence({ time: "08:00", weekdays: "1" }, BASE);
    expect(at.getDay()).toBe(1);
    expect(at.getDate()).toBe(8);
  });

  it("retorna null para horário inválido", () => {
    expect(nextOccurrence({ time: "99:99" }, BASE)).toBeNull();
    expect(nextOccurrence({ time: "abc" }, BASE)).toBeNull();
  });
});

describe("computeNext", () => {
  it("escolhe o menor próximo horário entre eventos ativos", () => {
    const events = [
      { id: "a", time: "14:00", duration_seconds: 10, enabled: true },
      { id: "b", time: "08:00", duration_seconds: 15, enabled: true },
      { id: "c", time: "10:00", duration_seconds: 30, enabled: true },
    ];
    const next = computeNext(events, BASE);
    expect(next.event.id).toBe("b");
    expect(next.at.getHours()).toBe(8);
  });

  it("ignora eventos desabilitados", () => {
    const events = [
      { id: "a", time: "08:00", duration_seconds: 10, enabled: false },
      { id: "b", time: "10:00", duration_seconds: 10, enabled: true },
    ];
    const next = computeNext(events, BASE);
    expect(next.event.id).toBe("b");
  });
});

describe("desktopExposureTimeScheduler — agendamento", () => {
  it("não agenda fora do Electron", () => {
    const executeShowDesktop = vi.fn();
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      isElectron: false,
    });
    s.schedule({
      events: [{ id: "a", time: "08:00", duration_seconds: 10, enabled: true }],
      phase: "playing",
    });
    expect(s.isScheduled()).toBe(false);
  });

  it("não agenda em fase waiting/loading", () => {
    const executeShowDesktop = vi.fn();
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      isElectron: true,
    });
    s.schedule({
      events: [{ id: "a", time: "08:00", duration_seconds: 10, enabled: true }],
      phase: "loading",
    });
    expect(s.isScheduled()).toBe(false);
  });

  it("dispara show_desktop no horário e volta para RUNNING", async () => {
    const executeShowDesktop = vi.fn().mockResolvedValue({ ok: true });
    const persist = vi.fn();
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      persist,
      isElectron: true,
    });

    s.schedule({
      events: [{ id: "a", time: "08:00", duration_seconds: 15, enabled: true }],
      phase: "playing",
    });
    expect(s.isScheduled()).toBe(true);
    expect(s.getState()).toBe(EXPOSURE_STATE.RUNNING);

    // Avança 1h (07:00 → 08:00) para disparar.
    await vi.advanceTimersByTimeAsync(60 * 60 * 1000);

    expect(executeShowDesktop).toHaveBeenCalledWith(15);
    expect(persist).toHaveBeenCalledWith(
      expect.objectContaining({ status: "running", durationSeconds: 15 }),
    );
    expect(s.getState()).toBe(EXPOSURE_STATE.WAITING_TIMER);

    // Avança a duração (15s) → restaura.
    await vi.advanceTimersByTimeAsync(15 * 1000);
    expect(persist).toHaveBeenLastCalledWith(null);
    expect(s.getState()).toBe(EXPOSURE_STATE.RUNNING);
    // Reagendou o próximo (amanhã).
    expect(s.isScheduled()).toBe(true);

    s.stop();
  });

  it("não dispara duas vezes se já estiver em exposição", async () => {
    const executeShowDesktop = vi.fn().mockResolvedValue({ ok: true });
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      isElectron: true,
    });

    // Dois eventos no mesmo minuto — o segundo não deve disparar durante o primeiro.
    s.schedule({
      events: [
        { id: "a", time: "08:00", duration_seconds: 30, enabled: true },
      ],
      phase: "playing",
    });
    await vi.advanceTimersByTimeAsync(60 * 60 * 1000); // 08:00
    expect(executeShowDesktop).toHaveBeenCalledTimes(1);
    expect(s.getState()).toBe(EXPOSURE_STATE.WAITING_TIMER);
    s.stop();
  });
});

describe("desktopExposureTimeScheduler — recover()", () => {
  it("limpa quando a ação pendente já expirou", async () => {
    const executeShowDesktop = vi.fn().mockResolvedValue({ ok: true });
    const persist = vi.fn();
    const pending = {
      status: "running",
      startedAt: new Date(BASE.getTime() - 60 * 1000).toISOString(), // 60s atrás
      durationSeconds: 30,
    };
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      persist,
      loadPending: () => pending,
      isElectron: true,
    });

    const recovered = await s.recover();
    expect(recovered).toBe(false);
    expect(executeShowDesktop).not.toHaveBeenCalled();
    expect(persist).toHaveBeenCalledWith(null);
  });

  it("retoma o tempo restante quando ainda não expirou", async () => {
    const executeShowDesktop = vi.fn().mockResolvedValue({ ok: true });
    const persist = vi.fn();
    const pending = {
      status: "running",
      startedAt: new Date(BASE.getTime() - 10 * 1000).toISOString(), // 10s atrás
      durationSeconds: 30,
    };
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      persist,
      loadPending: () => pending,
      isElectron: true,
    });

    const recovered = await s.recover();
    expect(recovered).toBe(true);
    // Restante ≈ 20s.
    expect(executeShowDesktop).toHaveBeenCalledWith(20);
    expect(s.getState()).toBe(EXPOSURE_STATE.WAITING_TIMER);

    await vi.advanceTimersByTimeAsync(20 * 1000);
    expect(persist).toHaveBeenLastCalledWith(null);
    expect(s.getState()).toBe(EXPOSURE_STATE.RUNNING);
    s.stop();
  });

  it("ignora quando não há ação pendente", async () => {
    const executeShowDesktop = vi.fn();
    const s = createDesktopExposureTimeScheduler({
      executeShowDesktop,
      loadPending: () => null,
      isElectron: true,
    });
    const recovered = await s.recover();
    expect(recovered).toBe(false);
    expect(executeShowDesktop).not.toHaveBeenCalled();
  });
});
