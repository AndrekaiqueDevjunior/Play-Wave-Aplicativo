# SPEC 006 — Design Tecnico

## Resumo

SPEC pequena, mais focada em UX/visual que em arquitetura. Quatro mudancas:

1. `AudioPlayer` expoe callback `onTrackChange(track)`.
2. `PlayerOSD` ganha slot dedicado para musica atual + lê config visual via props.
3. Backend persiste config OSD em `tenants` e `devices` (hierarquia simples) e envia config resolvida no payload.
4. Heartbeat reporta musica atual; painel admin exibe.

Sem nova entidade, sem nova tabela — apenas colunas adicionais.

## Arquitetura atual relacionada

### Player

- `frontend/src/pages/Player.jsx` — monta `MediaRenderer`, `AudioPlayer`, `PlayerOSD`.
- `frontend/src/components/audio/AudioPlayer.jsx` — controla `<audio>`, mantem `currentTrackIndex`.
- `frontend/src/components/player/PlayerOSD.jsx` — overlay top-left (logo), top-right (relogio), bottom (nome da midia).
- `frontend/src/api/dispositivos.js` — `enviarHeartbeat` (sera estendido).

### Backend

- `backend/api/v1/devices.py` — `heartbeat` endpoint (linhas ~XYZ — encontrar) + builder de playlist.
- `backend/core/models.py` — `Device`, `Tenant`.

### Admin

- `frontend/src/pages/DispositivoDetalhe.jsx` — card de estado atual.
- `frontend/src/pages/ConfigEmpresa.jsx` — config global do tenant.

## Estrutura `osd_config` no payload

```typescript
type OSDConfig = {
  show_current_audio: boolean;
  position: "top_left" | "top_right" | "bottom_left" | "bottom_right";
  duration_seconds: number; // 0 = always visible, > 0 = N seconds on track change
  opacity: number;          // 0.0-1.0
  font_size: "small" | "medium" | "large";
};
```

## Fluxo: musica troca → overlay aparece

1. `AudioPlayer` avança para proxima faixa internamente.
2. `AudioPlayer` chama `onTrackChange(track)`.
3. `Player.jsx` armazena `currentAudioTrack` em state.
4. `PlayerOSD` recebe novo `currentAudioTrack`.
5. PlayerOSD aciona useEffect com `setShowAudio(true)`.
6. Apos `osd_config.duration_seconds`, setTimeout faz `setShowAudio(false)` (se duration > 0).
7. CSS transition de 300ms faz fade out.

Tambem: heartbeat seguinte envia `current_audio_track_*` para backend.

## Fluxo: admin muda config

1. Admin abre DispositivoDetalhe.
2. Edita config OSD do device.
3. Frontend chama `PATCH /devices/{id}/osd-config`.
4. Backend persiste, invalida cache.
5. SSE `playlist_invalidated` para o device.
6. Player recarrega playlist → recebe novo `osd_config` resolvido.
7. PlayerOSD re-renderiza com nova config.

## Resolver de config

Helper `backend/services/osd_config_resolver.py`:

```python
DEFAULT_OSD_CONFIG = {
    "show_current_audio": True,
    "position": "top_right",
    "duration_seconds": 8,
    "opacity": 0.6,
    "font_size": "medium",
}

def resolve_osd_config(device, tenant) -> dict:
    result = {**DEFAULT_OSD_CONFIG}
    for key in DEFAULT_OSD_CONFIG.keys():
        tenant_val = getattr(tenant, f"osd_{key}", None) if tenant else None
        if tenant_val is not None:
            result[key] = tenant_val
        device_val = getattr(device, f"osd_{key}", None) if device else None
        if device_val is not None:
            result[key] = device_val
    return result
```

Chamado no builder de `GET /devices/{id}/playlist` para popular `osd_config`.

## PlayerOSD redesenhado

Estrutura visual:

```
+------------------------------------------------+
| [logo] DeviceName               12:34          |
|                                                |
|        [conteudo da midia visual]              |
|                                                |
|                                                |
|                          +-------------------+ |
|                          | ♫ Tocando: Track  | |  ← slot novo
|                          +-------------------+ |
|                                                |
| Nome da Midia Visual · 1/5 · Video             |  ← slot existente (4s ao trocar)
+------------------------------------------------+
```

(Posicao do slot novo depende de `osd_config.position`.)

Codigo:

```javascript
import { Music } from "lucide-react";

export default function PlayerOSD({
  media,
  totalItems,
  currentIndex,
  deviceName,
  currentAudioTrack,       // NOVO
  audioEnabled,            // NOVO
  osdConfig = DEFAULT_OSD_CONFIG, // NOVO
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

  const positionClass = POSITION_CLASSES[osdConfig.position] || POSITION_CLASSES.top_right;
  const fontSizeClass = FONT_SIZE_CLASSES[osdConfig.font_size] || FONT_SIZE_CLASSES.medium;

  return (
    <>
      {/* Existing: logo, clock, media info bottom */}
      <div className="absolute top-4 left-5 flex items-center gap-2 opacity-40 hover:opacity-80 transition-opacity">
        {/* ... logo + deviceName ... */}
      </div>

      <div className="absolute top-4 right-5 opacity-40 hover:opacity-80 transition-opacity">
        {/* ... clock ... */}
      </div>

      <div className={`absolute bottom-4 left-5 right-5 transition-all duration-500 ${showMediaInfo ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}>
        {/* ... media info ... */}
      </div>

      {/* NEW: audio overlay */}
      {currentAudioTrack && (
        <div
          className={`absolute ${positionClass} transition-opacity duration-300 ${showAudioOverlay ? "opacity-100" : "opacity-0 pointer-events-none"}`}
        >
          <div
            className={`inline-flex items-center gap-2 rounded-lg px-3 py-2 ${fontSizeClass}`}
            style={{ backgroundColor: `rgba(0, 0, 0, ${osdConfig.opacity})` }}
          >
            <Music className="w-3.5 h-3.5 text-white flex-shrink-0" />
            <span className="text-white font-medium truncate max-w-[30vw]">
              {currentAudioTrack.name}
            </span>
          </div>
        </div>
      )}
    </>
  );
}

const POSITION_CLASSES = {
  top_left: "top-16 left-5",        // abaixo do logo
  top_right: "top-16 right-5",      // abaixo do relogio
  bottom_left: "bottom-20 left-5",  // acima do media info
  bottom_right: "bottom-20 right-5",
};

const FONT_SIZE_CLASSES = {
  small:  "text-xs",
  medium: "text-sm",
  large:  "text-base",
};

const DEFAULT_OSD_CONFIG = {
  show_current_audio: true,
  position: "top_right",
  duration_seconds: 8,
  opacity: 0.6,
  font_size: "medium",
};
```

Importante:

- `position`s evitam colisao com logo (`top_16` em vez de `top_4`).
- Overlay tem `pointer-events-none` quando fade out — nao bloqueia clicks futuros.
- `max-w-[30vw]` + `truncate` previne quebra de layout.
- `transition-opacity 300ms` para fade.

## AudioPlayer — callback

```javascript
export function AudioPlayer({
  playlist,
  enabled,
  volume,
  fadeMs = 200,
  onTrackChange,   // NOVO
}) {
  const [currentTrackIndex, setCurrentTrackIndex] = useState(0);
  const trackChangeTimeoutRef = useRef(null);

  useEffect(() => {
    const track = playlist?.tracks?.[currentTrackIndex] || null;

    // Debounce 500ms para evitar spam em skip rapido.
    if (trackChangeTimeoutRef.current) {
      clearTimeout(trackChangeTimeoutRef.current);
    }
    trackChangeTimeoutRef.current = setTimeout(() => {
      onTrackChange?.(track);
    }, 500);

    return () => {
      if (trackChangeTimeoutRef.current) {
        clearTimeout(trackChangeTimeoutRef.current);
      }
    };
  }, [playlist?.tracks, currentTrackIndex, onTrackChange]);

  // Quando enabled=false, reportar null
  useEffect(() => {
    if (!enabled) {
      onTrackChange?.(null);
    }
  }, [enabled, onTrackChange]);

  // ... rest of audio control ...
}
```

## Player.jsx — integracao

```javascript
function PlayerComponent() {
  const [currentAudioTrack, setCurrentAudioTrack] = useState(null);

  // existing state...
  const osdConfig = playlist?.osd_config || DEFAULT_OSD_CONFIG;

  // Reportar musica atual no heartbeat
  useEffect(() => {
    if (!currentAudioTrack) return;
    sendHeartbeatTrackInfo(deviceId, token, {
      current_audio_track_id: currentAudioTrack.id,
      current_audio_track_name: currentAudioTrack.name,
      current_audio_track_started_at: new Date().toISOString(),
    });
  }, [currentAudioTrack?.id]);

  return (
    <>
      <MediaRenderer media={currentMedia} muted={videoMuted} />
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
        audioEnabled={audioEnabled}
        osdConfig={osdConfig}
      />
    </>
  );
}
```

## Heartbeat estendido

Frontend:

```javascript
export async function enviarHeartbeat(deviceId, token, payload) {
  // payload now includes current_audio_track_*
  await http.post(`/devices/${deviceId}/heartbeat`, payload, {
    headers: { "X-Device-Token": token }
  });
}
```

Player chama com `current_audio_track_id`, `current_audio_track_name`, `current_audio_track_started_at`.

Backend:

- `Device.current_audio_track_id`, `Device.current_audio_track_name`, `Device.current_audio_track_started_at` populated em cada heartbeat.

## Decisoes tecnicas

- Animacao via CSS transitions (sem dep nova).
- Configuracao hierarquica simples: device override tenant override hardcoded.
- Debounce 500ms no `onTrackChange` previne spam em skip.
- Overlay com `max-width 30vw` previne quebra.
- Heartbeat ja eh feito a cada 30s; piggyback do track info sem aumentar carga.
- `osd_config` no payload da playlist (nao endpoint separado) para reduzir round-trips.

## Pontos parcialmente existentes

- `PlayerOSD` ja tem estrutura — apenas adiciona slot novo.
- `AudioPlayer` ja mantem `currentTrackIndex` — apenas adiciona callback.
- Heartbeat ja existe — apenas adiciona campos.

## Lacunas de design

- Sem artista/album no payload da playlist (`audio_tracks` nao tem essas colunas hoje). Adicionar no futuro.
- Sem capa de album.
- Sem cor customizada (so opacidade do fundo preto).

## Riscos e mitigacoes

### Risco: nome longo quebra layout

Mitigacao:

- `max-w-[30vw]` + `truncate`.
- `white-space: nowrap`.

### Risco: overlay sobrepoe area importante do video

Mitigacao:

- 4 posicoes configuraveis.
- Operador escolhe baseado em conteudo.

### Risco: heartbeat sobrecarrega DB

Mitigacao:

- Heartbeat ja eh 30s.
- Update de 3 colunas adicionais eh trivial.

### Risco: payload OSD para player legado

Mitigacao:

- Player legado ignora `osd_config` (sem suporte).
- Comportamento atual preservado (so nome da midia visual).

## Criterio de pronto tecnico

- Migration aplicada em `tenants` e `devices`.
- Resolver retorna config efetiva.
- Payload da playlist inclui `osd_config`.
- AudioPlayer chama `onTrackChange` com debounce.
- PlayerOSD renderiza overlay novo conforme config.
- Heartbeat reporta musica atual.
- UI admin permite configurar em device e tenant.
- Preview ao vivo funciona.
- Cliente confirma: nome da musica aparece no canto da TV conforme configurado.
