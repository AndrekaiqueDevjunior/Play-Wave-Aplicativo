# SPEC 005 — Design Tecnico

## Resumo

A spec introduz hierarquia de politica de audio com 4 niveis (midia > campanha > device > tenant) + enum `AudioPolicy` com 5 valores. Backend calcula politica efetiva e envia ao player; player aplica a decisao via hook `useAudioConflictResolver` a cada troca de midia. Fade in/out de 200ms suaviza transicoes.

Compatibilidade: `campaign.video_muted` continua sendo enviado e respeitado por players antigos. Quando `audio_policy_effective` esta presente, ele tem prioridade.

## Arquitetura atual relacionada

### Backend

- `backend/core/models.py`:
  - `Media` linhas ~250-300 (criar `has_audio`, `audio_policy`).
  - `Campaign` linha 189-212 (criar `audio_policy`).
  - `Device` linhas 109-165 (criar `audio_policy_default`).
  - `Tenant` (criar `audio_policy_default`, `audio_fade_ms`).
- `backend/api/v1/devices.py`: builder do payload do player.
- `backend/services/media_processing.py` ou similar: detecao de `has_audio` via ffprobe.

### Frontend / Player

- `frontend/src/pages/Player.jsx`: integra hook `useAudioConflictResolver`.
- `frontend/src/hooks/useAudioConflictResolver.js` (novo).
- `frontend/src/components/audio/AudioPlayer.jsx`: adicionar `pauseWithFade`, `resumeWithFade`.
- `frontend/src/components/player/MediaRenderer.jsx`: aceita prop `muted` (ja aceita).

### Frontend Admin

- `frontend/src/components/campaigns/CampaignFormModal.jsx`.
- `frontend/src/components/media/MediaFormModal.jsx`.
- `frontend/src/pages/DispositivoDetalhe.jsx`.
- `frontend/src/pages/ConfigEmpresa.jsx`.
- `frontend/src/components/shared/AudioPolicySelector.jsx` (novo, reusavel).

## Enum `AudioPolicy`

Backend (`backend/core/models.py`):

```python
class AudioPolicy(str, Enum):
    AUTO = "auto"
    RADIO_ONLY = "radio_only"
    MEDIA_AUDIO_ONLY = "media_audio_only"
    MIX = "mix"
    MUTED_VIDEO_WITH_RADIO = "muted_video_with_radio"
```

Frontend (`frontend/src/utils/audioPolicy.js`):

```javascript
export const AUDIO_POLICY = {
  AUTO: "auto",
  RADIO_ONLY: "radio_only",
  MEDIA_AUDIO_ONLY: "media_audio_only",
  MIX: "mix",
  MUTED_VIDEO_WITH_RADIO: "muted_video_with_radio",
};

export const AUDIO_POLICY_LABELS = {
  auto: { label: "Automatico (recomendado)", description: "Se a midia tem audio, pausa a radio. Se nao tem, mantem a radio." },
  radio_only: { label: "Apenas radio", description: "Video sempre mudo. Radio sempre ativa." },
  media_audio_only: { label: "Apenas audio da midia", description: "Radio pausa enquanto video com audio toca." },
  mix: { label: "Misturar ambos", description: "Audio da midia + radio simultaneamente. Pode soar confuso." },
  muted_video_with_radio: { label: "Video mudo com radio ambiente", description: "Video sempre mudo. Radio ativa quando configurada." },
};
```

## Resolver Backend

Arquivo novo: `backend/services/audio_policy_resolver.py`:

```python
def resolve_effective_audio_policy(media, campaign, device, tenant) -> str:
    """
    Hierarquia: media > campaign > device > tenant > "auto".
    """
    if media and media.audio_policy:
        return media.audio_policy
    if campaign and campaign.audio_policy:
        return campaign.audio_policy
    if device and device.audio_policy_default:
        return device.audio_policy_default
    if tenant and tenant.audio_policy_default:
        return tenant.audio_policy_default
    return "auto"


def resolve_media_payload(media, campaign, device, tenant):
    """
    Constroi dict de midia para o payload do player incluindo audio_policy_effective.
    """
    base = media_to_dict(media)
    base["audio_policy_effective"] = resolve_effective_audio_policy(media, campaign, device, tenant)
    base["has_audio"] = media.has_audio if media.has_audio is not None else _infer_has_audio(media)
    return base


def _infer_has_audio(media):
    """Fallback quando has_audio nao foi detectado: video=True, resto=False."""
    return media.type == "video"
```

Backward-compat no builder de playlist:

```python
def build_player_playlist(device, db):
    # ... existing code ...
    campaign = device.current_campaign
    tenant = device.tenant
    items = []
    for media_id in campaign.media_order or campaign.media_ids:
        m = get_media(db, media_id)
        item = resolve_media_payload(m, campaign, device, tenant)
        items.append(item)

    return {
        "device_name": device.name,
        "campaign": {
            "id": str(campaign.id),
            "name": campaign.name,
            "config_version": str(campaign.config_version),
            "video_muted": campaign.video_muted,  # LEGADO
            "audio_policy_default": resolve_effective_audio_policy(None, campaign, device, tenant),
            "audio_fade_ms": tenant.audio_fade_ms or 200,
            # ...
        },
        "media": items,
        "audio_playlist": ...,
    }
```

## Resolver Player

Hook novo `frontend/src/hooks/useAudioConflictResolver.js`:

```javascript
import { useMemo } from "react";

const POLICY = {
  AUTO: "auto",
  RADIO_ONLY: "radio_only",
  MEDIA_AUDIO_ONLY: "media_audio_only",
  MIX: "mix",
  MUTED_VIDEO_WITH_RADIO: "muted_video_with_radio",
};

/**
 * Decide videoMuted, audioEnabled (radio) baseado em politica efetiva.
 * @param {Object} currentMedia - { audio_policy_effective, has_audio, type }
 * @param {Object} audioPlaylist - { tracks: [...] } ou null
 * @param {Object} currentSpot - { audio_id } ou null (preparado para SPEC futura)
 * @param {string} fallbackPolicy - politica default da campanha (auto se ausente)
 * @returns {Object} { videoMuted, audioEnabled, audioDucked }
 */
export function useAudioConflictResolver({
  currentMedia,
  audioPlaylist,
  currentSpot = null,
  fallbackPolicy = "auto",
}) {
  return useMemo(() => {
    // Spot tem prioridade absoluta.
    if (currentSpot) {
      return { videoMuted: true, audioEnabled: true, audioDucked: false };
    }

    if (!currentMedia) {
      return { videoMuted: true, audioEnabled: !!audioPlaylist?.tracks?.length, audioDucked: false };
    }

    const policy = currentMedia.audio_policy_effective || fallbackPolicy || "auto";
    const hasMediaAudio = currentMedia.has_audio === true;
    const hasRadio = !!audioPlaylist?.tracks?.length;

    switch (policy) {
      case POLICY.RADIO_ONLY:
        return { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };
      case POLICY.MEDIA_AUDIO_ONLY:
        return { videoMuted: !hasMediaAudio, audioEnabled: false, audioDucked: false };
      case POLICY.MIX:
        return { videoMuted: !hasMediaAudio, audioEnabled: hasRadio, audioDucked: false };
      case POLICY.MUTED_VIDEO_WITH_RADIO:
        return { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };
      case POLICY.AUTO:
      default:
        return hasMediaAudio
          ? { videoMuted: false, audioEnabled: false, audioDucked: false }
          : { videoMuted: true, audioEnabled: hasRadio, audioDucked: false };
    }
  }, [currentMedia?.id, currentMedia?.audio_policy_effective, currentMedia?.has_audio, audioPlaylist?.tracks?.length, currentSpot, fallbackPolicy]);
}
```

## Integracao em `Player.jsx`

```javascript
import { useAudioConflictResolver } from "../hooks/useAudioConflictResolver";

function PlayerComponent() {
  // ... state existente
  const currentMedia = playlist?.[currentIndex];
  const fallbackPolicy = campaign?.audio_policy_default;
  const audioFadeMs = campaign?.audio_fade_ms || 200;

  const { videoMuted, audioEnabled } = useAudioConflictResolver({
    currentMedia,
    audioPlaylist,
    currentSpot: null,  // preparado para SPEC futura
    fallbackPolicy,
  });

  // Remover usos diretos de `videoMuted` baseado em `campaign.video_muted`.
  // Passar `videoMuted` e `audioEnabled` para os componentes.

  return (
    <>
      <MediaRenderer media={currentMedia} muted={videoMuted} ... />
      <AudioPlayer
        playlist={audioPlaylist}
        enabled={audioEnabled}
        fadeMs={audioFadeMs}
        ...
      />
    </>
  );
}
```

## Mudanca em `AudioPlayer.jsx`

Adicionar fade in/out controlado por `fadeMs` prop:

```javascript
const FADE_INTERVAL_MS = 25;

useEffect(() => {
  if (!audioRef.current) return;
  const audio = audioRef.current;

  if (enabled) {
    audio.volume = 0;
    audio.play().catch(() => {});
    fadeIn(audio, targetVolume, fadeMs);
  } else {
    fadeOut(audio, fadeMs).then(() => audio.pause());
  }
}, [enabled, fadeMs, targetVolume]);

function fadeIn(audio, target, durationMs) {
  const steps = durationMs / FADE_INTERVAL_MS;
  const delta = target / steps;
  const interval = setInterval(() => {
    audio.volume = Math.min(target, audio.volume + delta);
    if (audio.volume >= target) clearInterval(interval);
  }, FADE_INTERVAL_MS);
}

function fadeOut(audio, durationMs) {
  return new Promise((resolve) => {
    const start = audio.volume;
    const steps = durationMs / FADE_INTERVAL_MS;
    const delta = start / steps;
    const interval = setInterval(() => {
      audio.volume = Math.max(0, audio.volume - delta);
      if (audio.volume <= 0.001) {
        clearInterval(interval);
        resolve();
      }
    }, FADE_INTERVAL_MS);
  });
}
```

## Componente `AudioPolicySelector.jsx`

Reusavel em 4 telas (Campaign, Media, Device, Tenant). Props:

```javascript
<AudioPolicySelector
  value={value}            // string ou null
  onChange={onChange}
  allowNull={true}         // true: oferece "Usar default do nivel superior"
  level="campaign"         // "campaign" | "media" | "device" | "tenant"
/>
```

Render:

```
+--------------------------------------------------+
| Politica de audio                                |
| ( ) Usar default da empresa (Automatico)         |
| ( ) Automatico (recomendado)                     |
| ( ) Apenas radio                                 |
| ( ) Apenas audio da midia                        |
| ( ) Misturar ambos                               |
| ( ) Video mudo com radio                         |
|                                                  |
| [tooltip detalhado por opcao selecionada]        |
+--------------------------------------------------+
```

## Deteccao de `has_audio`

Ao upload de video em `backend/api/v1/media.py` (ou onde quer que esteja a pipeline de upload):

```python
def detect_audio_streams(file_path: str) -> bool:
    """Usa ffprobe para detectar se ha streams de audio."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a",
        "-show_entries", "stream=codec_type",
        "-of", "json",
        file_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        data = json.loads(result.stdout)
        return len(data.get("streams", [])) > 0
    except Exception as e:
        logger.warning(f"ffprobe falhou para {file_path}: {e}")
        return True  # fallback: assume tem audio
```

Apos upload, setar `media.has_audio = detect_audio_streams(path)` para videos. Para imagens/URLs, sempre `false`.

Endpoint admin para forcar recalculo: `POST /media/{id}/recompute-audio-detection`.

## SSE — atualizacao em tempo real

Quando admin muda `audio_policy` em Campaign ou Media, backend deve:

1. Invalidar cache Redis de devices afetados.
2. Publicar SSE `playlist_invalidated` (ja existe).
3. Player recarrega playlist → recebe novo `audio_policy_effective`.
4. Resolver no player re-executa na proxima troca de midia.

Nao force troca no meio de uma midia tocando — espera proxima.

## Decisoes tecnicas

- Resolver no backend retorna politica efetiva, nao decisao final.
- Decisao final (`videoMuted`, `audioEnabled`) eh do player — permite logica futura (spots, ducking) sem mudar API.
- Fade de 200ms eh imperceptivel; ajustavel via tenant.
- `has_audio` nullable: NULL = nao detectado, infer no resolver.
- `audio_policy` em todos os niveis: NULL = herda do superior.
- Resolver eh `useMemo` para evitar recalculo desnecessario.
- Cache busting da playlist usa `config_version` da campanha — incrementado ao mudar `audio_policy`.

## Pontos parcialmente existentes

- `campaign.video_muted` ja existe → migrado para `audio_policy`.
- `AudioPlayer` ja aceita `enabled` boolean → ganha `fadeMs`.
- `MediaRenderer` ja aceita `muted` boolean → sem mudanca.
- SSE de playlist ja existe → reaproveitado.

## Lacunas de design

- Ducking automatico (abaixar volume da radio durante voz no video) requer analise de stream — fora desta SPEC.
- Crossfade entre faixas da radio — fora desta SPEC.
- Politica por horario — fora desta SPEC, parte de scheduling.

## Riscos e mitigacoes

### Risco: fade in/out causa pop sonoro em audio HTML5

Mitigacao:

- Garantir `audio.volume = 0` ANTES do play.
- Testar em Chrome, Firefox, Safari, Capacitor Android.

### Risco: deteccao de `has_audio` falha em videos antigos

Mitigacao:

- Backfill nao-bloqueante: campo `has_audio = NULL` significa "nao detectado".
- Resolver assume video → `has_audio=true` como fallback.
- Botao "Recalcular" no painel.

### Risco: cliente escolhe `mix` e reclama do som confuso

Mitigacao:

- UI tem tooltip explicito avisando.
- Default eh `auto`, nao `mix`.
- Doc mostra cenarios recomendados.

### Risco: SSE chega no meio da midia e troca abrupta

Mitigacao:

- Resolver aplica decisao apenas na proxima troca de midia (`useMemo` reage a `currentMedia.id`).
- Mudanca de `audioEnabled` durante a mesma midia tem fade de 200ms.

### Risco: compat com player legado quebra

Mitigacao:

- Backend continua enviando `campaign.video_muted` por 2 releases.
- Player legado usa `video_muted` ignorando `audio_policy_effective`.
- Migration backfilla `audio_policy` baseado em `video_muted`.

## Criterio de pronto tecnico

- Migrations aplicadas em `media`, `campaigns`, `devices`, `tenants`.
- Backend resolver puro, com testes unitarios.
- Backend pipeline ffprobe detectando `has_audio` em uploads novos.
- Backfill de `has_audio` em videos existentes (script ou Celery task).
- Backfill de `audio_policy` baseado em `video_muted` legado.
- Player aplica resolver via hook em `Player.jsx`.
- AudioPlayer faz fade in/out de 200ms.
- UI selector reusavel em 4 lugares.
- Documentacao operacional publicada.
- Cliente confirma: video com audio + radio se comporta corretamente conforme politica.
