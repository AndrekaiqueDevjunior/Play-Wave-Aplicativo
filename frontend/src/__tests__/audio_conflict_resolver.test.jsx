import React from "react";
import { createRoot } from "react-dom/client";
import { act } from "react-dom/test-utils";
import { afterEach, describe, expect, it } from "vitest";

import { useAudioConflictResolver } from "../hooks/useAudioConflictResolver";
import { AUDIO_POLICY } from "../utils/audioPolicy";

let root;
let container;
let latestResult;

function HookProbe(props) {
  latestResult = useAudioConflictResolver(props);
  return null;
}

function renderHookProps(props) {
  if (!container) {
    container = document.createElement("div");
    document.body.appendChild(container);
    root = createRoot(container);
  }
  act(() => {
    root.render(<HookProbe {...props} />);
  });
  return latestResult;
}

afterEach(() => {
  if (root) {
    act(() => root.unmount());
  }
  root = null;
  container?.remove();
  container = null;
  latestResult = undefined;
});

describe("useAudioConflictResolver", () => {
  const radio = { tracks: [{ id: "track-1" }] };

  it("mantém rádio ligada quando não há mídia visual atual", () => {
    expect(renderHookProps({ currentMedia: null, audioPlaylist: radio })).toEqual({
      videoMuted: true,
      audioEnabled: true,
      audioDucked: false,
    });
  });

  it("AUTO pausa rádio quando mídia tem áudio", () => {
    expect(
      renderHookProps({
        currentMedia: { id: "m1", has_audio: true, audio_policy_effective: AUDIO_POLICY.AUTO },
        audioPlaylist: radio,
      }),
    ).toEqual({ videoMuted: false, audioEnabled: false, audioDucked: false });
  });

  it("AUTO mantém rádio quando mídia não tem áudio", () => {
    expect(
      renderHookProps({
        currentMedia: { id: "m1", has_audio: false, audio_policy_effective: AUDIO_POLICY.AUTO },
        audioPlaylist: radio,
      }),
    ).toEqual({ videoMuted: true, audioEnabled: true, audioDucked: false });
  });

  it("RADIO_ONLY sempre muta vídeo e só liga áudio se houver playlist", () => {
    expect(
      renderHookProps({
        currentMedia: {
          id: "m1",
          has_audio: true,
          audio_policy_effective: AUDIO_POLICY.RADIO_ONLY,
        },
        audioPlaylist: null,
      }),
    ).toEqual({ videoMuted: true, audioEnabled: false, audioDucked: false });
  });

  it("MEDIA_AUDIO_ONLY desliga rádio e deixa vídeo com som quando mídia tem áudio", () => {
    expect(
      renderHookProps({
        currentMedia: {
          id: "m1",
          has_audio: true,
          audio_policy_effective: AUDIO_POLICY.MEDIA_AUDIO_ONLY,
        },
        audioPlaylist: radio,
      }),
    ).toEqual({ videoMuted: false, audioEnabled: false, audioDucked: false });
  });

  it("MIX permite mídia com som e rádio ao mesmo tempo", () => {
    expect(
      renderHookProps({
        currentMedia: { id: "m1", has_audio: true, audio_policy_effective: AUDIO_POLICY.MIX },
        audioPlaylist: radio,
      }),
    ).toEqual({ videoMuted: false, audioEnabled: true, audioDucked: false });
  });

  it("usa fallbackPolicy quando a mídia não traz política efetiva", () => {
    expect(
      renderHookProps({
        currentMedia: { id: "m1", has_audio: true },
        audioPlaylist: radio,
        fallbackPolicy: AUDIO_POLICY.MUTED_VIDEO_WITH_RADIO,
      }),
    ).toEqual({ videoMuted: true, audioEnabled: true, audioDucked: false });
  });

  it("spot atual tem prioridade sobre a mídia", () => {
    expect(
      renderHookProps({
        currentMedia: { id: "m1", has_audio: true, audio_policy_effective: AUDIO_POLICY.AUTO },
        audioPlaylist: radio,
        currentSpot: { id: "spot-1" },
      }),
    ).toEqual({ videoMuted: true, audioEnabled: true, audioDucked: false });
  });
});
