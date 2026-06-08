/**
 * Testes SPEC 007 Fase E — AudioManager (audioManager.js)
 *
 * Cobre: loadRadioPlaylist, playRadio, silence, playSpot, subscribe/unsubscribe.
 * Usa AudioManager diretamente (não o singleton) para isolamento entre testes.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { AudioManager, AUDIO_STATE, AUDIO_MODE } from "@/lib/audioManager";

// Stub _fadeIn/_fadeOut no prototype para que resolvam imediatamente.
// Isso evita a dependência de requestAnimationFrame e Date.now(),
// focando o teste no comportamento de estado/notificação.
// _fadeIn agora retorna { ok, reason? } (resultado do watchdog) — o stub
// replica o formato de sucesso para não quebrar os call-sites que checam result.ok.
AudioManager.prototype._fadeIn  = vi.fn().mockResolvedValue({ ok: true });
AudioManager.prototype._fadeOut = vi.fn().mockResolvedValue(undefined);

/**
 * Cria um mock de HTMLAudioElement mínimo.
 * Os event listeners são armazenados para disparar manualmente.
 */
function makeMockAudio() {
  const listeners = {};
  return {
    play: vi.fn().mockResolvedValue(undefined),
    pause: vi.fn(),
    load: vi.fn(),
    volume: 1,
    src: "",
    addEventListener: vi.fn((event, cb) => {
      if (!listeners[event]) listeners[event] = [];
      listeners[event].push(cb);
    }),
    _trigger(event) {
      (listeners[event] || []).forEach((cb) => cb());
    },
  };
}

// ── loadRadioPlaylist ─────────────────────────────────────────────────────────

describe("AudioManager — loadRadioPlaylist", () => {
  it("armazena faixas em queue.radio", () => {
    const am = new AudioManager();
    const tracks = [
      { file_url: "a.mp3", title: "A" },
      { file_url: "b.mp3", title: "B" },
    ];
    am.loadRadioPlaylist(tracks);
    expect(am.queue.radio).toEqual(tracks);
  });

  it("modo SHUFFLE embaralha (mesmo comprimento e mesmas faixas)", () => {
    const am = new AudioManager();
    const tracks = Array.from({ length: 10 }, (_, i) => ({
      file_url: `track${i}.mp3`,
      title: `Track ${i}`,
    }));
    am.loadRadioPlaylist([...tracks], AUDIO_MODE.SHUFFLE);
    expect(am.queue.radio).toHaveLength(tracks.length);
    // Todas as faixas originais devem estar presentes (conteúdo igual, ordem possivelmente diferente)
    const urls = am.queue.radio.map((t) => t.file_url).sort();
    const origUrls = tracks.map((t) => t.file_url).sort();
    expect(urls).toEqual(origUrls);
  });

  it("modo SEQUENTIAL não embaralha (faixas na mesma ordem)", () => {
    const am = new AudioManager();
    const tracks = [
      { file_url: "a.mp3" },
      { file_url: "b.mp3" },
      { file_url: "c.mp3" },
    ];
    am.loadRadioPlaylist([...tracks], AUDIO_MODE.SEQUENTIAL);
    expect(am.queue.radio.map((t) => t.file_url)).toEqual(["a.mp3", "b.mp3", "c.mp3"]);
  });
});

// ── playRadio ─────────────────────────────────────────────────────────────────

describe("AudioManager — playRadio", () => {
  it("playRadio() notifica currentTrack com a primeira faixa", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    am.initPlayers(radio, null, null);

    const tracks = [{ file_url: "track1.mp3", title: "Track 1" }];
    am.loadRadioPlaylist(tracks);

    const states = [];
    am.subscribe((s) => states.push(s));

    await am.playRadio();

    const lastState = states[states.length - 1];
    expect(lastState.currentTrack).toEqual(tracks[0]);
  });

  it("playRadio() define current = AUDIO_STATE.RADIO", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    am.initPlayers(radio, null, null);

    am.loadRadioPlaylist([{ file_url: "track1.mp3" }]);

    await am.playRadio();

    expect(am.state.current).toBe(AUDIO_STATE.RADIO);
  });

  it("playRadio() quando já em RADIO+isPlaying não reinicia (guard)", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    am.initPlayers(radio, null, null);

    am.loadRadioPlaylist([{ file_url: "track1.mp3" }]);

    await am.playRadio(); // primeira chamada
    const firstCallCount = radio.play.mock.calls.length;

    await am.playRadio(); // segunda chamada — deve ser ignorada

    // play não deve ter sido chamado novamente
    expect(radio.play.mock.calls.length).toBe(firstCallCount);
  });

  it("_onTrackEnded('radio') avança radioIndex e chama _playRadioByIndex", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    am.initPlayers(radio, null, null);

    const tracks = [
      { file_url: "t1.mp3" },
      { file_url: "t2.mp3" },
    ];
    am.loadRadioPlaylist(tracks);
    am.queue.radioIndex = 0;

    const spy = vi.spyOn(am, "_playRadioByIndex");
    am._onTrackEnded("radio");

    expect(am.queue.radioIndex).toBe(1);
    expect(spy).toHaveBeenCalledOnce();
  });

  it("_onTrackError('radio') chama nextTrack (não trava)", () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    am.initPlayers(radio, null, null);

    am.loadRadioPlaylist([{ file_url: "t1.mp3" }, { file_url: "t2.mp3" }]);

    const spy = vi.spyOn(am, "nextTrack");
    expect(() => am._onTrackError("radio")).not.toThrow();
    expect(spy).toHaveBeenCalledOnce();
  });
});

// ── silence ───────────────────────────────────────────────────────────────────

describe("AudioManager — silence", () => {
  it("silence() emite current = AUDIO_STATE.SILENT", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    am.initPlayers(null, null, null);

    const states = [];
    am.subscribe((s) => states.push(s));

    await am.silence();

    const last = states[states.length - 1];
    expect(last.current).toBe(AUDIO_STATE.SILENT);
  });

  it("silence() emite currentTrack: null", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    am.initPlayers(null, null, null);
    am.state.currentTrack = { file_url: "x.mp3" };

    const states = [];
    am.subscribe((s) => states.push(s));

    await am.silence();

    const last = states[states.length - 1];
    expect(last.currentTrack).toBeNull();
  });

  it("silence() emite isPlaying: false", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    am.initPlayers(null, null, null);
    am.state.isPlaying = true;

    const states = [];
    am.subscribe((s) => states.push(s));

    await am.silence();

    const last = states[states.length - 1];
    expect(last.isPlaying).toBe(false);
  });
});

// ── playSpot ──────────────────────────────────────────────────────────────────

describe("AudioManager — playSpot", () => {
  it("playSpot(url, 'interrupt') emite current = AUDIO_STATE.SPOT", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    const spot = makeMockAudio();
    am.initPlayers(radio, null, spot);

    // Simula estado anterior como RADIO
    am.state.current = AUDIO_STATE.RADIO;

    const states = [];
    am.subscribe((s) => states.push(s));

    await am.playSpot("jingle.mp3", "interrupt");

    const last = states[states.length - 1];
    expect(last.current).toBe(AUDIO_STATE.SPOT);
  });
});

// ── subscribe / unsubscribe ───────────────────────────────────────────────────

// ── playWithWatchdog (resiliência de áudio) ──────────────────────────────────
//
// Estes testes usam playWithWatchdog diretamente (não passa pelo stub global
// de _fadeIn) para validar o contrato do watchdog isoladamente: sucesso,
// rejeição, bloqueio de autoplay e timeout — incluindo marcação em quarentena.

describe("AudioManager — playWithWatchdog", () => {
  let logSpy;
  let warnSpy;

  beforeEach(() => {
    logSpy = vi.spyOn(console, "log").mockImplementation(() => {});
    warnSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  it("play() resolve => { ok: true } e loga PLAY_REQUEST/PLAY_SUCCESS", async () => {
    const am = new AudioManager();
    const el = makeMockAudio();
    el.play.mockResolvedValue(undefined);
    el.src = "https://cdn.example.com/track1.mp3";

    const result = await am.playWithWatchdog(el, { id: "track-1" }, { label: "radio" });

    expect(result).toEqual({ ok: true });
    const events = logSpy.mock.calls.map(([, entry]) => entry.event);
    expect(events).toContain("PLAY_REQUEST");
    expect(events).toContain("PLAY_SUCCESS");
    expect(am._isAudioMarkedFailed("track-1")).toBe(false);
  });

  it("play() rejeita (erro genérico) => { ok: false, reason: 'rejected' } e entra em quarentena", async () => {
    const am = new AudioManager();
    const el = makeMockAudio();
    const err = Object.assign(new Error("decode failed"), { name: "NotSupportedError" });
    el.play.mockRejectedValue(err);
    el.src = "https://cdn.example.com/broken.mp3";

    const result = await am.playWithWatchdog(el, { id: "track-broken" }, { label: "radio" });

    expect(result.ok).toBe(false);
    expect(result.reason).toBe("rejected");
    expect(am._isAudioMarkedFailed("track-broken")).toBe(true);

    const payload = warnSpy.mock.calls.find(([, entry]) => entry.event === "PLAY_REJECTED")?.[1];
    expect(payload).toMatchObject({
      audioId: "track-broken",
      url: "https://cdn.example.com/broken.mp3",
      reason: "NotSupportedError",
    });
    expect(payload).toHaveProperty("elapsedMs");
  });

  it("play() rejeita com NotAllowedError => autoplay_blocked, NÃO entra em quarentena", async () => {
    const am = new AudioManager();
    const el = makeMockAudio();
    const err = Object.assign(new Error("blocked"), { name: "NotAllowedError" });
    el.play.mockRejectedValue(err);

    const states = [];
    am.subscribe((s) => states.push(s));

    const result = await am.playWithWatchdog(el, { id: "spot-1" }, { label: "spot" });

    expect(result).toMatchObject({ ok: false, reason: "autoplay_blocked" });
    expect(am._isAudioMarkedFailed("spot-1")).toBe(false);
    expect(states[states.length - 1].autoplayBlocked).toBe(true);
  });

  it("play() nunca resolve nem rejeita => watchdog estoura após o timeout (PLAY_TIMEOUT) e quarentena", async () => {
    vi.useFakeTimers();
    try {
      const am = new AudioManager();
      const el = makeMockAudio();
      // Promise que nunca resolve nem rejeita — simula o cenário real do bug
      el.play.mockReturnValue(new Promise(() => {}));
      el.src = "https://cdn.example.com/stuck.mp3";

      const pending = am.playWithWatchdog(el, { id: "track-stuck" }, { label: "radio" });

      await vi.advanceTimersByTimeAsync(10_000);
      const result = await pending;

      expect(result).toEqual({ ok: false, reason: "timeout" });
      expect(am._isAudioMarkedFailed("track-stuck")).toBe(true);

      const payload = warnSpy.mock.calls.find(([, entry]) => entry.event === "PLAY_TIMEOUT")?.[1];
      expect(payload).toMatchObject({ audioId: "track-stuck", reason: "watchdog_timeout_exceeded" });
    } finally {
      vi.useRealTimers();
    }
  });
});

// ── Quarentena (failedAudioIds com TTL) ──────────────────────────────────────

describe("AudioManager — quarentena de áudio (TTL)", () => {
  it("_markAudioFailed + _isAudioMarkedFailed => true enquanto dentro do TTL", () => {
    const am = new AudioManager();
    am._markAudioFailed("x1");
    expect(am._isAudioMarkedFailed("x1")).toBe(true);
  });

  it("expira sozinho após o TTL (lazy expiry) e libera o áudio para nova tentativa", () => {
    vi.useFakeTimers();
    try {
      const am = new AudioManager();
      const now = Date.now();
      vi.setSystemTime(now);
      am._markAudioFailed("x2");
      expect(am._isAudioMarkedFailed("x2")).toBe(true);

      vi.setSystemTime(now + 5 * 60 * 1000 + 1);
      expect(am._isAudioMarkedFailed("x2")).toBe(false);
      // Lazy expiry remove a entrada do mapa
      expect(am.failedAudioIds.has("x2")).toBe(false);
    } finally {
      vi.useRealTimers();
    }
  });
});

// ── _handleRadioTrackFailure (skip automático + guarda contra loop infinito) ─

describe("AudioManager — _handleRadioTrackFailure", () => {
  beforeEach(() => {
    vi.spyOn(console, "log").mockImplementation(() => {});
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  it("marca falha, loga SKIP_FAILED_AUDIO e avança para a próxima faixa", () => {
    const am = new AudioManager({ fadeMs: 0 });
    am.initPlayers(makeMockAudio(), null, null);
    am.loadRadioPlaylist([{ id: "a", file_url: "a.mp3" }, { id: "b", file_url: "b.mp3" }]);

    const spy = vi.spyOn(am, "nextTrack").mockImplementation(() => {});
    am._handleRadioTrackFailure(am.queue.radio[0], "rejected");

    expect(am._isAudioMarkedFailed("a")).toBe(true);
    expect(spy).toHaveBeenCalledOnce();
  });

  it("nunca entra em loop infinito: ao esgotar a fila inteira, vai para SILENT (NO_VALID_AUDIO) e zera o streak", () => {
    const am = new AudioManager({ fadeMs: 0 });
    am.initPlayers(makeMockAudio(), null, null);
    const tracks = [
      { id: "a", file_url: "a.mp3" },
      { id: "b", file_url: "b.mp3" },
    ];
    am.loadRadioPlaylist(tracks);

    // Impede que nextTrack acione nova reprodução real (isolamento do teste)
    vi.spyOn(am, "_playRadioByIndex").mockResolvedValue(undefined);

    const states = [];
    am.subscribe((s) => states.push(s));

    am._handleRadioTrackFailure(tracks[0], "rejected");
    am._handleRadioTrackFailure(tracks[1], "rejected");

    const last = states[states.length - 1];
    expect(last.current).toBe(AUDIO_STATE.SILENT);
    expect(last.isPlaying).toBe(false);
    expect(am._radioSkipStreak).toBe(0);
  });
});

// ── playRadio — pula faixas em quarentena sem tentar tocá-las ────────────────

describe("AudioManager — playRadio respeita quarentena", () => {
  beforeEach(() => {
    vi.spyOn(console, "log").mockImplementation(() => {});
    vi.spyOn(console, "warn").mockImplementation(() => {});
  });

  it("não chama play() para uma faixa marcada como falha — pula direto para a próxima", async () => {
    const am = new AudioManager({ fadeMs: 0 });
    const radio = makeMockAudio();
    am.initPlayers(radio, null, null);
    am.loadRadioPlaylist([
      { id: "broken", file_url: "broken.mp3" },
      { id: "ok", file_url: "ok.mp3" },
    ]);
    am._markAudioFailed("broken");

    const skipSpy = vi.spyOn(am, "_handleRadioTrackFailure");
    await am.playRadio();

    expect(skipSpy).toHaveBeenCalledWith(
      am.queue.radio[0],
      "quarantine_ttl",
      { markFailed: false },
    );
    expect(radio.play).not.toHaveBeenCalled();
  });
});

describe("AudioManager — subscribe", () => {
  it("subscribe retorna função de unsubscribe", () => {
    const am = new AudioManager();
    const unsub = am.subscribe(() => {});
    expect(typeof unsub).toBe("function");
  });

  it("unsubscribe remove listener — listener não é mais chamado", () => {
    const am = new AudioManager();
    const listener = vi.fn();
    const unsub = am.subscribe(listener);

    // Notifica antes de remover — deve chamar
    am._notify({ test: 1 });
    expect(listener).toHaveBeenCalledOnce();

    // Remove e notifica novamente — não deve chamar
    unsub();
    am._notify({ test: 2 });
    expect(listener).toHaveBeenCalledOnce(); // ainda apenas 1
  });
});
