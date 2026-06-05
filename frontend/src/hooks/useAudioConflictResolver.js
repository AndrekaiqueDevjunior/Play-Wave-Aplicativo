// @ts-nocheck
/**
 * useAudioConflictResolver — SPEC 005: resolve política de áudio por mídia.
 *
 * Decide videoMuted e audioEnabled a cada troca de mídia, baseado na
 * audio_policy_effective da mídia atual e na presença de playlist de rádio.
 *
 * Input:
 *   currentMedia    — { id, audio_policy_effective, has_audio, type }
 *   audioPlaylist   — { tracks: [...] } | null
 *   currentSpot     — reservado para SPEC futura de spots (null por ora)
 *   fallbackPolicy  — política default da campanha (string | undefined)
 *
 * Output:
 *   { videoMuted: boolean, audioEnabled: boolean, audioDucked: boolean }
 */

import { useMemo } from "react";
import { AUDIO_POLICY } from "../utils/audioPolicy";
import { hasAnyRadioContent } from "../player-core/radioScheduleResolver";

export function useAudioConflictResolver({
  currentMedia,
  audioPlaylist,
  currentSpot = null,
  fallbackPolicy = AUDIO_POLICY.AUTO,
}) {
  return useMemo(() => {
    // Spots (SPEC futura) têm prioridade absoluta.
    if (currentSpot) {
      return { videoMuted: true, audioEnabled: true, audioDucked: false };
    }

    // hasRadio considera faixas base E pastas agendadas com faixas.
    const hasRadio = hasAnyRadioContent(audioPlaylist);

    if (!currentMedia) {
      return { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };
    }

    const policy =
      currentMedia.audio_policy_effective || fallbackPolicy || AUDIO_POLICY.AUTO;
    const hasMediaAudio = currentMedia.has_audio === true;

    switch (policy) {
      case AUDIO_POLICY.RADIO_ONLY:
        return { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };

      case AUDIO_POLICY.MEDIA_AUDIO_ONLY:
        return { videoMuted: !hasMediaAudio, audioEnabled: false, audioDucked: false };

      case AUDIO_POLICY.MIX:
        return { videoMuted: !hasMediaAudio, audioEnabled: hasRadio, audioDucked: false };

      case AUDIO_POLICY.MUTED_VIDEO_WITH_RADIO:
        return { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };

      case AUDIO_POLICY.AUTO:
      default:
        return hasMediaAudio
          ? { videoMuted: false, audioEnabled: false, audioDucked: false }
          : { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };
    }
  }, [
    currentMedia?.id,
    currentMedia?.audio_policy_effective,
    currentMedia?.has_audio,
    audioPlaylist?.tracks?.length,
    audioPlaylist?.folder_schedules?.length,
    currentSpot,
    fallbackPolicy,
  ]);
}
