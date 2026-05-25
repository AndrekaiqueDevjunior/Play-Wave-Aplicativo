# SPEC 006 — Player

## Arquivos afetados

- `frontend/src/components/audio/AudioPlayer.jsx` — adicionar prop `onTrackChange`.
- `frontend/src/components/player/PlayerOSD.jsx` — slot novo + leitura de `osdConfig`.
- `frontend/src/pages/Player.jsx` — wire-up de track state + osdConfig + heartbeat estendido.
- `frontend/src/api/dispositivos.js` — heartbeat aceita novos campos.

## `AudioPlayer.jsx` — callback de mudanca de faixa

```javascript
export function AudioPlayer({
  playlist,
  enabled,
  volume,
  fadeMs = 200,
  onTrackChange,          // NOVO
}) {
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const debounceRef = useRef(null);
  const lastReportedRef = useRef(null);

  // existing logic ...

  // NEW: report track change with debounce
  useEffect(() => {
    const track = playlist?.tracks?.[currentTrackIndex] || null;
    const trackId = track?.id || null;

    // Evita re-report da mesma faixa
    if (lastReportedRef.current === trackId) return;

    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    debounceRef.current = setTimeout(() => {
      lastReportedRef.current = trackId;
      if (onTrackChange) onTrackChange(track);
    }, 500);

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
    };
  }, [playlist?.tracks, currentTrackIndex, onTrackChange]);

  // NEW: report null when disabled
  useEffect(() => {
    if (!enabled && lastReportedRef.current !== null) {
      lastReportedRef.current = null;
      if (onTrackChange) onTrackChange(null);
    }
  }, [enabled, onTrackChange]);

  // ... rest ...
}
```

Garantias:

- Debounce 500ms previne report em skip rapido.
- Nao re-reporta se faixa eh a mesma.
- Reporta null quando `enabled=false`.

## `PlayerOSD.jsx` — slot novo

Codigo completo (substitui o existente, mantem features atuais):

```javascript
import { useState, useEffect } from "react";
import { Radio, Music } from "lucide-react";

const DEFAULT_OSD_CONFIG = {
  show_current_audio: true,
  position: "top_right",
  duration_seconds: 8,
  opacity: 0.6,
  font_size: "medium",
};

const POSITION_CLASSES = {
  top_left: "top-16 left-5",
  top_right: "top-16 right-5",
  bottom_left: "bottom-20 left-5",
  bottom_right: "bottom-20 right-5",
};

const FONT_SIZE_CLASSES = {
  small: "text-xs",
  medium: "text-sm",
  large: "text-base",
};

export default function PlayerOSD({
  media,
  totalItems,
  currentIndex,
  deviceName,
  currentAudioTrack,
  audioEnabled = true,
  osdConfig = DEFAULT_OSD_CONFIG,
}) {
  const [showMediaInfo, setShowMediaInfo] = useState(true);
  const [showAudioOverlay, setShowAudioOverlay] = useState(false);
  const [time, setTime] = useState(new Date());

  // Existing: media info appears 4s on change
  useEffect(() => {
    setShowMediaInfo(true);
    const t = setTimeout(() => setShowMediaInfo(false), 4000);
    return () => clearTimeout(t);
  }, [media?.file_url]);

  // Clock
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 30_000);
    return () => clearInterval(t);
  }, []);

  // NEW: audio overlay visibility
  useEffect(() => {
    if (!audioEnabled || !currentAudioTrack || !osdConfig.show_current_audio) {
      setShowAudioOverlay(false);
      return;
    }
    setShowAudioOverlay(true);
    if (osdConfig.duration_seconds > 0) {
      const t = setTimeout(() => setShowAudioOverlay(false), osdConfig.duration_seconds * 1000);
      return () => clearTimeout(t);
    }
  }, [currentAudioTrack?.id, audioEnabled, osdConfig.show_current_audio, osdConfig.duration_seconds]);

  const posClass = POSITION_CLASSES[osdConfig.position] || POSITION_CLASSES.top_right;
  const fontClass = FONT_SIZE_CLASSES[osdConfig.font_size] || FONT_SIZE_CLASSES.medium;
  const opacity = Math.max(0, Math.min(1, osdConfig.opacity ?? 0.6));

  return (
    <>
      {/* Top-left: logo + device name (existing) */}
      <div className="absolute top-4 left-5 flex items-center gap-2 opacity-40 hover:opacity-80 transition-opacity z-10">
        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center">
          <Radio className="w-3.5 h-3.5 text-white" />
        </div>
        {deviceName && (
          <span className="text-white text-xs font-medium tracking-wide">
            {deviceName}
          </span>
        )}
      </div>

      {/* Top-right: clock (existing) */}
      <div className="absolute top-4 right-5 opacity-40 hover:opacity-80 transition-opacity z-10">
        <span className="text-white text-sm font-mono tabular-nums">
          {time.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>

      {/* NEW: audio overlay (visivel apenas se audio rolando) */}
      {currentAudioTrack && (
        <div
          className={`absolute ${posClass} z-20 transition-opacity duration-300 ${showAudioOverlay ? "opacity-100" : "opacity-0 pointer-events-none"}`}
        >
          <div
            className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 backdrop-blur-sm ${fontClass}`}
            style={{ backgroundColor: `rgba(0, 0, 0, ${opacity})` }}
          >
            <Music className="w-3.5 h-3.5 text-white flex-shrink-0" />
            <span className="text-white font-medium truncate" style={{ maxWidth: "30vw" }}>
              {currentAudioTrack.name}
            </span>
          </div>
        </div>
      )}

      {/* Bottom: media info — appears briefly on media change (existing) */}
      <div
        className={`absolute bottom-4 left-5 right-5 transition-all duration-500 z-10 ${showMediaInfo ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}
      >
        <div className="inline-flex items-center gap-3 bg-black/50 backdrop-blur-sm rounded-xl px-4 py-2.5">
          <div>
            <p className="text-white text-sm font-medium leading-tight">
              {media?.name}
            </p>
            <p className="text-white/50 text-xs mt-0.5">
              {currentIndex + 1} / {totalItems} ·{" "}
              {media?.type === "video" ? "Vídeo" : "Imagem"}
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
```

Detalhes:

- Z-index hierarquia: existing (10), audio overlay (20).
- Audio overlay nao bloqueia clicks quando fade-out (`pointer-events-none`).
- `truncate` + `maxWidth: 30vw` previne quebra.
- `backdrop-blur-sm` melhora legibilidade sobre fundos claros.
- Posicao `top_*` ajusta para `top-16` (abaixo do logo/relogio).

## `Player.jsx` — wire-up

```javascript
function PlayerComponent() {
  const [currentAudioTrack, setCurrentAudioTrack] = useState(null);
  const lastHeartbeatTrackRef = useRef(null);

  // ... existing state ...

  const osdConfig = playlist?.osd_config || {
    show_current_audio: true,
    position: "top_right",
    duration_seconds: 8,
    opacity: 0.6,
    font_size: "medium",
  };

  // Report track in next heartbeat
  useEffect(() => {
    const trackId = currentAudioTrack?.id || null;
    if (lastHeartbeatTrackRef.current === trackId) return;
    lastHeartbeatTrackRef.current = trackId;
    // Heartbeat ja eh chamado periodicamente em useEffect existente.
    // Ele lera currentAudioTrack via closure ou via ref.
  }, [currentAudioTrack?.id]);

  return (
    <>
      <MediaRenderer
        media={currentMedia}
        muted={finalVideoMuted}
        onEnded={advanceMedia}
      />
      <AudioPlayer
        playlist={audioPlaylist}
        enabled={audioEnabled && phase === "playing"}
        volume={audioVolume}
        fadeMs={audioFadeMs}
        onTrackChange={setCurrentAudioTrack}
      />
      <PlayerOSD
        media={currentMedia}
        totalItems={playlist?.length || 0}
        currentIndex={currentIndex}
        deviceName={device?.name}
        currentAudioTrack={currentAudioTrack}
        audioEnabled={audioEnabled && phase === "playing"}
        osdConfig={osdConfig}
      />
    </>
  );
}
```

### Heartbeat estendido

Localizar funcao que envia heartbeat (provavelmente em useEffect intervalo 30s) e incluir track info:

```javascript
useEffect(() => {
  const heartbeatInterval = setInterval(() => {
    enviarHeartbeat(deviceId, token, {
      config_version: campaignConfigVersion,
      current_campaign_id: campaign?.id,
      current_media_id: currentMedia?.id,
      current_audio_track_id: currentAudioTrack?.id || null,
      current_audio_track_name: currentAudioTrack?.name || null,
      current_audio_track_started_at: currentAudioTrack ? trackStartedAtRef.current : null,
      playback_status: phase,
    }).catch(() => {});
  }, 30_000);

  return () => clearInterval(heartbeatInterval);
}, [deviceId, token, campaign?.id, currentMedia?.id, currentAudioTrack?.id, phase]);

// Track quando faixa comecou para reportar elapsed
const trackStartedAtRef = useRef(null);
useEffect(() => {
  trackStartedAtRef.current = currentAudioTrack ? new Date().toISOString() : null;
}, [currentAudioTrack?.id]);
```

## `dispositivos.js` — sem mudanca estrutural

`enviarHeartbeat(deviceId, token, payload)` ja aceita payload arbitrario. Apenas garantir que body envia novos campos quando presentes.

## Verificacoes pre-deploy

- Sem audio playlist no campaign: overlay nao aparece (componente nao renderiza, `currentAudioTrack=null`).
- Com audio playlist: ao trocar faixa, overlay aparece por N segundos depois fade out.
- Trocar `osd_config.duration_seconds = 0`: overlay fica visivel enquanto faixa toca.
- Mudar `position` via admin: re-render no proximo refetch da playlist (SSE invalida).
- Aumentar `opacity` a 1.0: fundo solido preto.
- Diminuir `opacity` a 0.2: fundo quase transparente.
- Trocar `font_size` para `large`: texto cresce.
- Nome muito longo (>50 chars): trunca com ellipsis sem quebrar layout.
- Player Linux/APK/Web: comportamento identico.

## Logging para debug

```javascript
useEffect(() => {
  if (currentAudioTrack) {
    console.log("[OSD] now playing:", currentAudioTrack.name);
  } else {
    console.log("[OSD] audio paused or empty");
  }
}, [currentAudioTrack?.id]);
```

Util para suporte rastrear porque overlay nao aparece (audio enabled? track presente? config show=true?).
