import React from "react";
import { act } from "react-dom/test-utils";
import { createRoot } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

const pollCommands = vi.fn();
const fakeEventSource = {
  readyState: 0,
  listeners: {},
  addEventListener(type, callback) {
    this.listeners[type] = callback;
  },
  removeEventListener(type, callback) {
    if (this.listeners[type] === callback) {
      delete this.listeners[type];
    }
  },
  close: vi.fn(() => {
    this.readyState = 2;
  }),
  dispatch(type, event = { data: "{}" }) {
    const callback = this.listeners[type];
    if (typeof callback === "function") {
      callback(event);
    }
  },
};

vi.mock("@/lib/api", () => ({
  isApiConfigured: vi.fn(() => true),
  pairRequest: vi.fn(),
  getPairStatus: vi.fn(),
  getDevicePlaylist: vi.fn(async () => ({
    device_name: "Test device",
    media: [{ id: "m1", file_url: "/m1.mp4", type: "video", duration: 1 }],
    campaign: { id: "camp1", config_version: "v1" },
    audio_playlist: null,
    osd_config: null,
    desktop_exposure_config: null,
  })),
  sendHeartbeat: vi.fn().mockResolvedValue({}),
}));

vi.mock("@/api/http", () => ({
  getBaseUrl: vi.fn(() => "http://localhost"),
}));

vi.mock("@/api/dispositivos", () => ({
  abrirStreamPlaylistUpdates: vi.fn(() => fakeEventSource),
  marcarComandoRecebido: vi.fn(),
  marcarComandoIniciado: vi.fn(),
  ackComando: vi.fn(),
  registrarPlayback: vi.fn(),
}));

vi.mock("@/player-core/commandPoller", () => ({
  createCommandPoller: vi.fn(() => ({ pollCommands })),
}));

vi.mock("@/player-core/repair", () => ({
  onForceRepair: vi.fn(() => () => {}),
}));

vi.mock("@/player-core/platform", () => ({
  default: { name: "test", isElectron: true, isCapacitor: false },
  acquireWakeLock: vi.fn(),
  releaseWakeLock: vi.fn(),
}));

vi.mock("@/player-core/network", () => ({
  startWatchdog: vi.fn(),
  stopWatchdog: vi.fn(),
  notifyHeartbeatOk: vi.fn(),
  useOnlineStatus: vi.fn(() => true),
}));

vi.mock("@/hooks/useAudioConflictResolver", () => ({
  useAudioConflictResolver: vi.fn(() => ({
    videoMuted: false,
    audioEnabled: false,
  })),
}));

vi.mock("@/lib/audioManager", () => ({
  createAudioManager: vi.fn(() => ({
    initPlayers: vi.fn(),
    subscribe: vi.fn((cb) => {
      return () => {};
    }),
    destroy: vi.fn(),
    state: { fadeMs: 200 },
    playRadio: vi.fn().mockResolvedValue(null),
    silence: vi.fn().mockResolvedValue(null),
    playSpot: vi.fn().mockResolvedValue(null),
  })),
  AUDIO_STATE: { SILENT: "silent", SPOT: "spot", RADIO: "radio" },
  AUDIO_MODE: { SEQUENTIAL: "sequential", SHUFFLE: "shuffle" },
}));

vi.mock("@/lib/playbackEventLogger", () => ({
  logTrackStarted: vi.fn(),
  logTrackEnded: vi.fn(),
}));

vi.mock("@/player-core/storage", () => ({
  PairingStorage: {
    load: vi.fn(() => ({ id: "device-1", token: "token-1", code: "TV-ABC1" })),
    save: vi.fn(),
    clear: vi.fn(),
  },
  PlaylistCache: {
    get: vi.fn(async () => null),
    set: vi.fn().mockResolvedValue(null),
  },
}));

vi.mock("@/utils/mediaUtils", () => ({
  assetUrl: (url) => url,
}));

vi.mock("@/utils/mediaSchedule", () => ({
  isMediaCurrentlyPlayable: vi.fn(() => true),
}));

vi.mock("@/player-core/windowExposureScheduler", () => ({
  createWindowExposureScheduler: vi.fn(() => ({
    schedule: vi.fn(),
    stop: vi.fn(),
  })),
}));

vi.mock("@/components/player/PairingScreen", () => ({
  default: () => <div data-testid="pairing-screen" />,
}));
vi.mock("@/components/player/LoadingScreen", () => ({
  default: () => <div data-testid="loading-screen" />,
}));
vi.mock("@/components/player/ErrorScreen", () => ({
  default: ({ onRetry }) => (
    <button data-testid="error-screen" onClick={onRetry} />
  ),
}));
vi.mock("@/components/player/MediaRenderer", () => ({
  default: () => <div data-testid="media-renderer" />,
}));
vi.mock("@/components/player/PlayerOSD", () => ({
  default: () => <div data-testid="player-osd" />,
}));

const Player = (await import("../pages/Player.jsx")).default;

let container;
let root;

beforeEach(() => {
  vi.clearAllMocks();
  pollCommands.mockClear();
  fakeEventSource.close.mockClear();
  fakeEventSource.listeners = {};
  fakeEventSource.readyState = 0;
  container = document.createElement("div");
  document.body.appendChild(container);
  root = createRoot(container);
});

afterEach(() => {
  act(() => root.unmount());
  container.remove();
});

describe("Player SSE integration", () => {
  it("opens SSE and triggers polling on command:new and reconnect", async () => {
    await act(async () => {
      root.render(<Player />);
    });

    expect(fakeEventSource.addEventListener).toBeDefined();
    expect(fakeEventSource.listeners["command:new"]).toBeTypeOf("function");
    expect(fakeEventSource.listeners.open).toBeTypeOf("function");
    expect(pollCommands).toHaveBeenCalled();

    act(() => {
      fakeEventSource.dispatch("command:new");
    });

    expect(pollCommands).toHaveBeenCalledTimes(2);

    act(() => {
      fakeEventSource.dispatch("open");
    });

    expect(pollCommands).toHaveBeenCalledTimes(3);
  });
});
