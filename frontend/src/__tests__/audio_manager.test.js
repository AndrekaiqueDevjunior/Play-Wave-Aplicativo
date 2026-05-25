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
AudioManager.prototype._fadeIn  = vi.fn().mockResolvedValue(undefined);
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
