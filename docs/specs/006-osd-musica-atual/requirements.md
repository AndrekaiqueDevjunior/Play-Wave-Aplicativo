# SPEC 006 — OSD com Musica Atual (Configuravel)

Status: especificacao inicial
Data: 2026-05-22
Projeto: PlayWave

## Objetivo

Permitir que o player exiba na tela um overlay discreto com o nome da musica atualmente tocando na radio, e dar ao operador controle sobre se/onde/como esse overlay aparece (posicao, duracao, tamanho da fonte, opacidade do fundo). Hoje o `PlayerOSD` ja existe mas mostra apenas o nome da midia visual (video/imagem) — nao expoe a faixa de audio em execucao.

## Contexto

O cliente reclamou: "queria mostrar o nome da musica no canto da tela do player/TV". Auditoria em 2026-05-22 confirmou:

- `PlayerOSD.jsx` em `frontend/src/components/player/` ja existe e exibe:
  - Logo + nome do device (top-left).
  - Relogio (top-right).
  - Nome da midia visual (bottom, 4s ao trocar).
- O componente recebe prop `media` mas NAO recebe `currentTrack` do AudioPlayer.
- `AudioPlayer.jsx` toca a playlist de audio mas nao emite callback `onTrackChange`.
- Nao existe configuracao por device/tenant para posicao/duracao/etc. do overlay.

O recurso atende a um caso de uso real: cliente final (visitantes em uma loja, sala de espera de academia, etc.) quer saber qual eh a musica tocando. Tambem ajuda na operacao: tecnico do PlayWave consegue confirmar visualmente que a faixa correta esta tocando.

## Escopo

Esta SPEC cobre:

- Callback `onTrackChange(track)` no `AudioPlayer`.
- Slot novo no `PlayerOSD` para mostrar musica atual ("Tocando agora: Nome da Musica").
- Configuracao por device (e por tenant como default):
  - `osd_show_current_audio` (bool, default true).
  - `osd_position` enum: top-left, top-right, bottom-left, bottom-right (default top-right).
  - `osd_duration_seconds` int (0 = sempre visivel, > 0 = aparece N segundos ao trocar; default 8).
  - `osd_opacity` float 0-1 (default 0.6).
  - `osd_font_size` enum: small, medium, large (default medium).
- Reportar no heartbeat o nome da musica atual (para painel admin mostrar tambem).
- Animacao de fade in/out no overlay.
- Compatibilidade: device sem configuracao usa default do tenant; tenant sem config usa hardcoded.

Esta SPEC nao cobre:

- Exibicao de artista/album/capa (apenas nome da faixa por enquanto).
- OSD para spots (sera SPEC futura quando spots forem implementados).
- Animacoes customizadas alem de fade.
- Tema/cor customizada do overlay (apenas opacidade).
- Tickers de texto livre (overlay de mensagens promocionais).
- Sincronizacao precisa com letras (lyrics).

## Arquivos analisados

### Frontend / Player

- `frontend/src/components/player/PlayerOSD.jsx` (atual: 70 linhas).
- `frontend/src/components/audio/AudioPlayer.jsx`.
- `frontend/src/pages/Player.jsx`.

### Backend

- `backend/core/models.py`: `Device`, `Tenant`.
- `backend/api/v1/devices.py`: builder do payload + heartbeat handler.
- `backend/core/schemas_completos.py`.

### Frontend admin

- `frontend/src/pages/DispositivoDetalhe.jsx`.
- `frontend/src/pages/ConfigEmpresa.jsx`.
- `frontend/src/components/devices/DeviceEditDrawer.jsx`.

## Estado atual encontrado

### Ja existe

- `PlayerOSD.jsx` com slot inferior mostrando nome da midia visual.
- `AudioPlayer.jsx` que mantem state da faixa atual (`currentTrackIndex`).
- `Player.jsx` que monta ambos os componentes lado a lado.
- Heartbeat ja envia metadados do device.

### Existe parcialmente

- `PlayerOSD` recebe `media` (midia visual) — pode ser estendido para receber `currentAudioTrack`.
- `AudioPlayer` tem state interno mas nao expoe callback.

### Falta ou precisa consolidar

- Callback `onTrackChange` no AudioPlayer.
- Slot dedicado no PlayerOSD para musica atual.
- Configuracao OSD persistida em device/tenant.
- Heartbeat enviar `current_audio_track_name`.
- UI admin para configurar.

## Requisitos funcionais

### RF006-01 — Callback `onTrackChange` no AudioPlayer

`AudioPlayer.jsx` deve aceitar prop `onTrackChange` invocada toda vez que a faixa atual muda.

Critérios:

- Prop: `onTrackChange?: (track: AudioTrack | null) => void`.
- Invoca com objeto `{ id, name, duration_seconds, file_url }` ao iniciar nova faixa.
- Invoca com `null` quando playlist termina ou eh removida.
- NAO invoca quando `enabled=false` (pausado pela politica de audio).
- Debounce: se faixa mudar rapido (skip), so reporta a estabilizacao apos 500ms.

### RF006-02 — Slot "Tocando agora" no PlayerOSD

`PlayerOSD.jsx` deve receber prop `currentAudioTrack` e exibir overlay configuravel.

Critérios:

- Layout: card pequeno com icone de musica + texto "Nome da Musica".
- Posicao configuravel: top-left, top-right, bottom-left, bottom-right.
- Fade in/out de 300ms ao entrar/sair.
- Comportamento de visibilidade depende de `osd_duration_seconds`:
  - 0 = sempre visivel enquanto musica tocando.
  - > 0 = aparece por N segundos ao trocar de faixa, depois fade out.
- Tamanho/opacidade configuravel.
- Z-index acima da midia visual mas abaixo de overlay de erro.
- Truncate de nome longo com ellipsis (max 50 chars visiveis).

### RF006-03 — Configuracao em Device

Adicionar colunas em `devices`:

- `osd_show_current_audio` boolean (default null = herda do tenant).
- `osd_position` enum (`top_left`, `top_right`, `bottom_left`, `bottom_right`, default null).
- `osd_duration_seconds` int (0-3600, default null).
- `osd_opacity` float (0.0-1.0, default null).
- `osd_font_size` enum (`small`, `medium`, `large`, default null).

Endpoint admin para atualizar: `PATCH /devices/{id}/osd-config`.

### RF006-04 — Configuracao em Tenant (default global)

Adicionar colunas em `tenants`:

- `osd_show_current_audio` boolean (default true).
- `osd_position` enum (default `top_right`).
- `osd_duration_seconds` int (default 8).
- `osd_opacity` float (default 0.6).
- `osd_font_size` enum (default `medium`).

Endpoint admin: `PATCH /tenants/{id}/osd-config`.

### RF006-05 — Resolucao hierarquica

Player recebe configuracao efetiva (device override tenant). Backend resolve antes de enviar.

Hierarquia:

1. `device.osd_*` se nao-null.
2. `tenant.osd_*` se nao-null.
3. Hardcoded default.

Resolucao acontece no backend e vai no payload da playlist (campo `osd_config`).

### RF006-06 — Payload do player

`GET /devices/{id}/playlist` retorna:

```json
{
  "device_name": "...",
  "osd_config": {
    "show_current_audio": true,
    "position": "top_right",
    "duration_seconds": 8,
    "opacity": 0.6,
    "font_size": "medium"
  },
  "campaign": {...},
  "media": [...],
  "audio_playlist": {...}
}
```

### RF006-07 — Heartbeat reporta musica atual

`POST /devices/{id}/heartbeat` ganha campos opcionais:

- `current_audio_track_id` (uuid).
- `current_audio_track_name` (string).
- `current_audio_track_started_at` (datetime).

Backend persiste em colunas:

- `devices.current_audio_track_id` (uuid nullable).
- `devices.current_audio_track_name` (varchar nullable).
- `devices.current_audio_track_started_at` (timestamp nullable).

### RF006-08 — Painel admin mostra musica atual

Em `DispositivoDetalhe.jsx`, card "Estado atual" inclui:

- "Tocando agora: <nome da musica>"
- "Inicio: ha N segundos"

Update via React Query refetch a cada 10s.

### RF006-09 — UI configuracao por device

`DispositivoDetalhe.jsx` ou `DeviceEditDrawer.jsx` ganha secao "Overlay OSD":

```
+-----------------------------------------------+
| Overlay com nome da musica                    |
|-----------------------------------------------|
| ( ) Usar configuracao da empresa              |
| ( ) Personalizar para este dispositivo:       |
|     [x] Mostrar nome da musica                |
|     Posicao: [Top right v]                    |
|     Duracao: [8] segundos (0 = sempre)        |
|     Opacidade: [====O======] 60%              |
|     Fonte:   [Medium v]                       |
|     Preview:                                  |
|     +-----------------------------------+     |
|     |                            [.] Tocando: |     |
|     |                            Nome da Musica |   |
|     +-----------------------------------+     |
+-----------------------------------------------+
```

### RF006-10 — UI configuracao por tenant

`ConfigEmpresa.jsx` ganha secao similar mas sempre habilitada (sem opcao "Usar default" porque eh o topo da hierarquia).

### RF006-11 — Preview ao vivo na configuracao

Ambos os formularios mostram preview em mini-viewport (tela falsa 16:9) com overlay sample renderizado.

### RF006-12 — Configuracoes aplicam em < 30s

Mudanca de OSD config em device ou tenant deve refletir no player em < 30s sem requerer reinicio.

Critérios:

- Backend invalida cache do device afetado.
- SSE `playlist_invalidated` ou novo `osd_config_changed`.
- Player recarrega playlist → recebe novo `osd_config` → PlayerOSD re-renderiza.

### RF006-13 — Ocultar quando audio nao toca

Quando `audioEnabled = false` (por politica), overlay nao aparece mesmo que tenha musica "cued".

Critérios:

- PlayerOSD recebe `audioEnabled` prop.
- Renderiza overlay so se `audioEnabled && currentAudioTrack && config.show_current_audio`.

## Requisitos nao funcionais

- Overlay deve ser leve (CSS-only, sem JS heavy).
- Render deve ser GPU-accelerated (transform/opacity) para evitar repaint.
- Texto deve ser legivel em 1080p (font-size minimo 14px medium).
- Truncate respeita largura disponivel (max 30% da tela).
- Sem dependencia de biblioteca de animacao adicional (CSS transitions).
- Backwards-compat: payload sem `osd_config` → player usa defaults hardcoded.

## Decisoes de compatibilidade

- Device sem colunas `osd_*` (legado) recebe null → herda do tenant.
- Tenant sem colunas `osd_*` (legado) recebe defaults via migration.
- Player legado sem suporte a `osd_config` continua mostrando apenas nome da midia visual (comportamento atual).

## Riscos

- Texto comprido (musica clássica com nome longo) — truncate previne quebra de layout.
- Caracteres especiais/emoji em nome de musica — testar Unicode.
- Performance: overlay re-renderizando a cada frame pode causar drop. Usar memo + animacao CSS-only.
- Multilinha indesejada se nome quebra — usar `white-space: nowrap`.
- Em telas verticais (totem), `top-right` pode ficar perto da camera/sensor — operador escolhe alternativa.

## Fora de escopo imediato

- Artista, album, capa.
- Tema/cor custom.
- Tickers de texto livre.
- Lyrics sincronizadas.
- OSD para spots (futuro).
- Animacoes alem de fade.
- OSD em zonas multi-tela.
