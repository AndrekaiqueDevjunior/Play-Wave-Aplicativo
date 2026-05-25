import React from "react";
import { createRoot } from "react-dom/client";
import { act } from "react-dom/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AudioPlayer from "../components/audio/AudioPlayer";
import PlayerOSD from "../components/player/PlayerOSD";

let root;
let container;

function render(element) {
  if (!container) {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  }
  act(() => {
    root.render(element);
  });
}

beforeEach(() => {
  vi.useFakeTimers();
  HTMLMediaElement.prototype.play = vi.fn().mockResolvedValue(undefined);
  HTMLMediaElement.prototype.pause = vi.fn();
});

afterEach(() => {
  if (root) {
    act(() => root.unmount());
  }
  root = null;
  container?.remove();
  container = null;
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("AudioPlayer — SPEC 006", () => {
  const playlist = {
    id: "playlist-1",
    loop: false,
    volume: 0.7,
    tracks: [{ id: "track-1", name: "Faixa atual", file_url: "/audio.mp3" }],
  };

  it("chama onTrackChange após debounce de 500ms", () => {
    const onTrackChange = vi.fn();

    render(<AudioPlayer audioPlaylist={playlist} enabled onTrackChange={onTrackChange} />);

    expect(onTrackChange).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(499));
    expect(onTrackChange).not.toHaveBeenCalled();
    act(() => vi.advanceTimersByTime(1));

    expect(onTrackChange).toHaveBeenCalledWith(playlist.tracks[0]);
  });

  it("não re-chama onTrackChange para a mesma faixa", () => {
    const onTrackChange = vi.fn();

    render(<AudioPlayer audioPlaylist={playlist} enabled onTrackChange={onTrackChange} />);
    act(() => vi.advanceTimersByTime(500));
    render(<AudioPlayer audioPlaylist={playlist} enabled onTrackChange={onTrackChange} />);
    act(() => vi.advanceTimersByTime(500));

    expect(onTrackChange).toHaveBeenCalledTimes(1);
  });

  it("chama onTrackChange com null quando enabled vira false", () => {
    const onTrackChange = vi.fn();

    render(<AudioPlayer audioPlaylist={playlist} enabled onTrackChange={onTrackChange} />);
    act(() => vi.advanceTimersByTime(500));
    render(<AudioPlayer audioPlaylist={playlist} enabled={false} onTrackChange={onTrackChange} />);

    expect(onTrackChange).toHaveBeenLastCalledWith(null);
  });
});

describe("PlayerOSD — SPEC 006", () => {
  const track = { id: "track-1", name: "Nome de música muito longo para truncar no overlay" };

  it("renderiza overlay com posição, fonte, opacidade e truncamento configurados", () => {
    render(
      <PlayerOSD
        currentAudioTrack={track}
        audioEnabled
        media={{ name: "Midia", type: "video", file_url: "/video.mp4" }}
        currentIndex={0}
        totalItems={1}
        osdConfig={{
          show_current_audio: true,
          position: "bottom_left",
          duration_seconds: 8,
          opacity: 0.4,
          font_size: "large",
        }}
      />,
    );

    const text = document.body.querySelector("span.truncate");
    const overlay = text.closest(".absolute");
    const bubble = text.parentElement;

    expect(text.textContent).toBe(track.name);
    expect(text.className).toContain("max-w-[30vw]");
    expect(overlay.className).toContain("bottom-20");
    expect(overlay.className).toContain("left-5");
    expect(bubble.className).toContain("text-base");
    expect(bubble.style.backgroundColor).toBe("rgba(0, 0, 0, 0.4)");
  });

  it("oculta overlay após duration_seconds", () => {
    render(
      <PlayerOSD
        currentAudioTrack={track}
        audioEnabled
        media={{ name: "Midia", type: "video", file_url: "/video.mp4" }}
        currentIndex={0}
        totalItems={1}
        osdConfig={{
          show_current_audio: true,
          position: "top_right",
          duration_seconds: 2,
          opacity: 0.6,
          font_size: "medium",
        }}
      />,
    );

    const overlay = document.body.querySelector("span.truncate").closest(".absolute");
    expect(overlay.className).toContain("opacity-100");

    act(() => vi.advanceTimersByTime(2000));

    expect(overlay.className).toContain("opacity-0");
    expect(overlay.className).toContain("pointer-events-none");
  });

  it("mantém overlay visível quando duration_seconds é zero", () => {
    render(
      <PlayerOSD
        currentAudioTrack={track}
        audioEnabled
        media={{ name: "Midia", type: "video", file_url: "/video.mp4" }}
        currentIndex={0}
        totalItems={1}
        osdConfig={{
          show_current_audio: true,
          position: "top_right",
          duration_seconds: 0,
          opacity: 0.6,
          font_size: "medium",
        }}
      />,
    );

    const overlay = document.body.querySelector("span.truncate").closest(".absolute");
    act(() => vi.advanceTimersByTime(60_000));

    expect(overlay.className).toContain("opacity-100");
  });
});
