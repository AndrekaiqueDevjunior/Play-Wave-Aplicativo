# SPEC 005 — Player

## Arquivos afetados

- `frontend/src/hooks/useAudioConflictResolver.js` (novo).
- `frontend/src/utils/audioPolicy.js` (compartilhado com admin — criado em frontend.md).
- `frontend/src/pages/Player.jsx` — integra hook.
- `frontend/src/components/audio/AudioPlayer.jsx` — fade in/out.
- `frontend/src/components/player/MediaRenderer.jsx` — recebe prop `muted` calculada.

## Hook `useAudioConflictResolver.js`

```javascript
import { useMemo } from "react";
import { AUDIO_POLICY } from "../utils/audioPolicy";

/**
 * Decide videoMuted, audioEnabled, audioDucked para a midia atual.
 *
 * @param {Object} params
 * @param {Object} params.currentMedia - midia atual { id, audio_policy_effective, has_audio, type }
 * @param {Object} params.audioPlaylist - { tracks: [...] } ou null
 * @param {Object} params.currentSpot - reservado para SPEC futura de spots
 * @param {string} params.fallbackPolicy - politica default da campanha
 * @returns {{videoMuted: boolean, audioEnabled: boolean, audioDucked: boolean}}
 */
export function useAudioConflictResolver({
  currentMedia,
  audioPlaylist,
  currentSpot = null,
  fallbackPolicy = "auto",
}) {
  return useMemo(() => {
    // Spot futuro tem prioridade absoluta.
    if (currentSpot) {
      return { videoMuted: true, audioEnabled: true, audioDucked: false };
    }

    if (!currentMedia) {
      return {
        videoMuted: true,
        audioEnabled: !!audioPlaylist?.tracks?.length,
        audioDucked: false,
      };
    }

    const policy = currentMedia.audio_policy_effective || fallbackPolicy || AUDIO_POLICY.AUTO;
    const hasMediaAudio = currentMedia.has_audio === true;
    const hasRadio = !!audioPlaylist?.tracks?.length;

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
    currentSpot,
    fallbackPolicy,
  ]);
}
```

## `Player.jsx` — integracao

Remover usos diretos de `videoMuted = campaign.video_muted`. Substituir por:

```javascript
import { useAudioConflictResolver } from "../hooks/useAudioConflictResolver";

function PlayerComponent() {
  // ... state existente ...

  const currentMedia = playlist?.[currentIndex];
  const audioFadeMs = campaign?.audio_fade_ms || 200;
  const fallbackPolicy = campaign?.audio_policy_default || "auto";

  const { videoMuted, audioEnabled } = useAudioConflictResolver({
    currentMedia,
    audioPlaylist,
    currentSpot: null,
    fallbackPolicy,
  });

  // Fallback compat: player legado sem audio_policy_effective usa video_muted.
  const finalVideoMuted = currentMedia?.audio_policy_effective
    ? videoMuted
    : campaign?.video_muted !== false;

  return (
    <>
      <MediaRenderer
        media={currentMedia}
        muted={finalVideoMuted}
        onEnded={advanceMedia}
        // ...
      />
      <AudioPlayer
        playlist={audioPlaylist}
        enabled={audioEnabled && phase === "playing"}
        fadeMs={audioFadeMs}
        volume={audioPlaylist?.volume || 0.7}
        // ...
      />
    </>
  );
}
```

A linha `enabled={audioEnabled && phase === "playing"}` garante que audio pausa quando player nao esta tocando (fase loading/error/pairing).

## SSE — atualizar campos em tempo real

O handler de SSE `playlist_invalidated` ja recarrega a playlist. Apos recarregar:

- `campaign.audio_policy_default` atualiza.
- Cada `media.audio_policy_effective` atualiza.
- `useAudioConflictResolver` re-executa na proxima troca de midia.

Nao force interrupcao da midia atual — espera proxima. Comportamento esperado: politica nova vale a partir da proxima troca.

## `AudioPlayer.jsx` — fade in/out

Adicionar prop `fadeMs` (default 200) e implementar fade quando `enabled` muda.

```javascript
const FADE_INTERVAL_MS = 25;

export function AudioPlayer({ playlist, enabled, volume, fadeMs = 200 }) {
  const audioRef = useRef(null);
  const fadeIntervalRef = useRef(null);
  const targetVolumeRef = useRef(volume);

  useEffect(() => {
    targetVolumeRef.current = volume;
  }, [volume]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio || !playlist?.tracks?.length) return;

    // Cancela fade anterior se houver.
    if (fadeIntervalRef.current) {
      clearInterval(fadeIntervalRef.current);
      fadeIntervalRef.current = null;
    }

    if (enabled) {
      if (audio.paused) {
        audio.volume = 0;
        audio.play().catch((e) => console.warn("[AudioPlayer] play failed:", e));
      }
      fadeIntervalRef.current = doFade(audio, targetVolumeRef.current, fadeMs, () => {
        fadeIntervalRef.current = null;
      });
    } else {
      fadeIntervalRef.current = doFade(audio, 0, fadeMs, () => {
        audio.pause();
        fadeIntervalRef.current = null;
      });
    }

    return () => {
      if (fadeIntervalRef.current) {
        clearInterval(fadeIntervalRef.current);
        fadeIntervalRef.current = null;
      }
    };
  }, [enabled, fadeMs, playlist]);

  // ... resto existente: navigation entre tracks, onEnded, etc.
}

function doFade(audio, targetVolume, durationMs, onComplete) {
  if (durationMs <= 0) {
    audio.volume = targetVolume;
    onComplete?.();
    return null;
  }
  const steps = Math.max(1, Math.floor(durationMs / FADE_INTERVAL_MS));
  const delta = (targetVolume - audio.volume) / steps;
  let currentStep = 0;

  const id = setInterval(() => {
    currentStep++;
    audio.volume = Math.max(0, Math.min(1, audio.volume + delta));
    if (currentStep >= steps) {
      audio.volume = targetVolume;
      clearInterval(id);
      onComplete?.();
    }
  }, FADE_INTERVAL_MS);

  return id;
}
```

## `MediaRenderer.jsx` — sem mudanca

`MediaRenderer` ja aceita prop `muted`. Player passa `finalVideoMuted` calculado. Sem mudanca aqui.

## Comportamento esperado por cenario

| Cenario | currentMedia.has_audio | policy | videoMuted | audioEnabled |
|---|---|---|---|---|
| Video instrumental + radio Manha | true | auto | **false** | **false** |
| Banner imagem + radio Manha | false | auto | true | true |
| Video promo com voz + radio | true | media_audio_only | false | false |
| Video promo + radio (manter mix) | true | mix | false | true |
| Tela de pause sem audio | false | radio_only | true | true |
| Video tutorial com voz | true | radio_only | **true** | true |
| Video silencioso (drone shot) | false | media_audio_only | **true** | false |

Nota: "video silencioso sem audio + media_audio_only" resulta em silencio total. Isso eh esperado — operador escolheu nao tocar radio durante essa midia, e ela nao tem audio.

## Watchdog de mudanca de midia

Para evitar flapping (politica mudando varias vezes para mesma midia), o `useMemo` do hook depende de `currentMedia.id`. Mudancas internas no objeto (ex: SSE atualiza campo) so re-disparam se o id muda OU se uma das deps explicitas muda.

## Verificacoes pre-deploy

- Em dev, ativar campanha com:
  - 1 video com audio + radio + policy=auto → na troca para esse video, radio para com fade e video toca com som.
  - 1 imagem + radio + policy=auto → ao trocar para imagem, radio retoma com fade e video desliga.
- Mudar policy via gerenciador → SSE invalida → proxima troca de midia reflete.
- Console do player: log claro `[player] audio decision: { videoMuted, audioEnabled, reason: policy }`.
- Inspecionar `audio.volume` durante transicao: deve descer/subir progressivamente em 200ms.

## Logging para debug

Adicionar log no Player.jsx ao mudar de midia:

```javascript
useEffect(() => {
  if (!currentMedia) return;
  console.log("[player] audio resolver:", {
    media: currentMedia.name,
    policy: currentMedia.audio_policy_effective,
    has_audio: currentMedia.has_audio,
    decision: { videoMuted, audioEnabled },
  });
}, [currentMedia?.id, videoMuted, audioEnabled]);
```

Ajuda suporte a diagnosticar comportamento inesperado.
