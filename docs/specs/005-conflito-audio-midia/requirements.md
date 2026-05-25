# SPEC 005 — Conflito de Audio entre Midia Visual e Radio

Status: especificacao inicial
Data: 2026-05-22
Projeto: PlayWave

## Objetivo

Tornar explicita e configuravel a regra de coexistencia entre o audio da midia visual (video, sobretudo) e o audio da radio ambiente. Hoje, quando uma campanha tem video com audio e tambem playlist de audio vinculada, o player toca os dois ao mesmo tempo gerando experiencia ruim. A unica controle existente eh `campaign.video_muted` (boolean global) que apenas silencia o video, sem decidir o destino da radio.

## Contexto

O cliente reclamou: "midia esta misturando audio com a radio". Auditoria em 2026-05-22 confirmou:

- `AudioPlayer` (`frontend/src/components/audio/AudioPlayer.jsx`) permanece sempre montado durante a fase `playing` da campanha. Ele toca a playlist de audio recebida no payload da campanha.
- `MediaRenderer` (`frontend/src/components/player/MediaRenderer.jsx`) toca video/imagem/url. Video respeita `muted` baseado em `campaign.video_muted`.
- Quando `campaign.video_muted = false` E `campaign.audio_playlist_id != null`, **ambos tocam ao mesmo tempo**.
- Nao existe nocao de "spot tem prioridade sobre musica ambiente".
- Nao existe controle por midia individual (apenas global por campanha).
- Nao existe override por device ou grupo.

A consequencia operacional: video com audio + radio = mistura caotica. Cliente desativa um dos dois manualmente (geralmente video sem audio), perdendo recurso.

## Escopo

Esta SPEC cobre:

- enum `audio_policy` com 5 valores: `radio_only`, `media_audio_only`, `mix`, `auto`, `muted_video_with_radio`;
- aplicacao da `audio_policy` em 4 niveis hierarquicos: midia individual > campanha > device > tenant;
- resolver no backend que calcula a politica efetiva e envia ao player;
- hook React `useAudioConflictResolver` no player que decide a cada troca de midia: mutar video, pausar radio, ou ambos;
- prioridade de spots (quando SPEC de spots for implementada, esta SPEC garante o slot de prioridade);
- transicoes suaves de audio (fade in/out) para evitar cortes bruscos;
- Compatibilidade com `campaign.video_muted` legado.

Esta SPEC nao cobre:

- spots recorrentes em si (escopo de SPEC futura).
- crossfade entre faixas da playlist de audio (nice-to-have, fora de escopo P0).
- ducking automatico (abaixar volume da radio quando voz no video) — escopo de SPEC futura.
- multi-canal/multi-zone (split-screen) — escopo de outra SPEC.

## Arquivos analisados

### Backend

- `backend/core/models.py`: `Media`, `Campaign`, `Device`.
- `backend/api/v1/devices.py`: builder de playlist do player (linhas que montam payload).
- `backend/core/schemas_completos.py`: `MediaResponse`, `CampaignResponse`.
- `backend/crud/entidades/crud_device.py`: `get_device_playlist`.

### Frontend / Player

- `frontend/src/pages/Player.jsx`: principalmente linhas 600-606 (AudioPlayer montado), 258 (uso de `video_muted`), 536-538 (SSE atualiza video_muted).
- `frontend/src/components/audio/AudioPlayer.jsx`: motor persistente.
- `frontend/src/components/player/MediaRenderer.jsx`: renderer da midia visual.
- `frontend/src/components/campaigns/CampaignFormModal.jsx`: edicao de campanha (sera estendida).
- `frontend/src/components/media/MediaFormModal.jsx`: edicao de midia individual (sera estendida).

## Estado atual encontrado

### Ja existe

- Campo `Campaign.video_muted` (boolean).
- `AudioPlayer` persistente que aceita prop `enabled`.
- `MediaRenderer` que aceita prop `muted` em video.
- Payload do player ja inclui `campaign.video_muted` e `campaign.audio_playlist`.
- SSE atualiza `video_muted` em tempo real.

### Existe parcialmente

- Controle binario (muted on/off) sem nocao de quem cede a vez.
- Sem campo de politica em `Media`.
- Sem campo de politica em `Device` (default por dispositivo).
- Sem campo de politica em `Tenant` (default global).

### Falta ou precisa consolidar

- Enum `AudioPolicyEnum` com 5 valores.
- Migrations adicionando coluna `audio_policy` em 4 tabelas.
- Backend resolver `effective_audio_policy(media, campaign, device, tenant)`.
- Player resolver que aplica decisao a cada troca de midia.
- UI de selecao em Campanha + Midia + Device + Tenant.
- Migracao dos dados existentes (`video_muted=true` mapeia para `muted_video_with_radio` quando ha radio, senao `radio_only`; `video_muted=false` sem radio = `media_audio_only`; com radio = `mix`).

## Requisitos funcionais

### RF005-01 — Enum `audio_policy`

O sistema deve suportar os seguintes valores de politica:

| Valor | Comportamento |
|---|---|
| `radio_only` | Radio toca, midia visual sempre muda. |
| `media_audio_only` | Audio da midia toca, radio pausa enquanto a midia visual estiver com audio nativo. |
| `mix` | Ambos tocam simultaneamente (comportamento legado para `video_muted=false`). |
| `auto` | Se a midia tem audio nativo → comporta como `media_audio_only`. Se nao tem → comporta como `radio_only`. **Padrao recomendado.** |
| `muted_video_with_radio` | Video sempre mudo, radio ativa. (Equivale a `video_muted=true` + radio ligada.) |

### RF005-02 — Hierarquia de aplicacao

A politica efetiva eh calculada nesta ordem (primeiro nao-nulo vence):

1. `media.audio_policy` (override por midia individual).
2. `campaign.audio_policy` (politica da campanha).
3. `device.audio_policy_default` (politica padrao do dispositivo).
4. `tenant.audio_policy_default` (politica global do tenant).
5. Hardcoded: `auto`.

### RF005-03 — Campo `media.has_audio`

Para `audio_policy = auto` funcionar, o sistema precisa saber se cada midia tem audio nativo.

Critérios:

- Coluna `media.has_audio` (boolean, nullable).
- Para video: detectar automaticamente via `ffprobe` ao upload (procura streams de audio).
- Para imagem/url/html: `has_audio = false` por padrao.
- Para midia legada sem deteccao: assumir `has_audio = true` para video, `false` para imagem.
- Recalcular ao substituir arquivo.

### RF005-04 — Backend resolver

O endpoint `GET /devices/{id}/playlist` deve incluir, para cada midia da playlist:

```json
{
  "id": "...",
  "audio_policy_effective": "media_audio_only",
  "has_audio": true,
  ...
}
```

A campanha tambem inclui no payload o `audio_policy_default` resolvido.

Critérios:

- Backend calcula `effective_audio_policy` por midia.
- Backend NAO faz a decisao final de pausa/mute — apenas envia a politica para o player decidir.
- Compatibilidade: se `campaign.video_muted` esta setado mas `audio_policy` nao, mapear para a politica equivalente.

### RF005-05 — Player resolver

O player deve aplicar a politica a cada troca de midia atual.

Hook `useAudioConflictResolver`:

Input:

- `currentMedia` (com `audio_policy_effective`, `has_audio`).
- `audioPlaylist` (presente ou nao).
- `currentSpot` (presente ou nao, alta prioridade).

Output:

- `videoMuted: bool` — passado para `MediaRenderer`.
- `audioEnabled: bool` — passado para `AudioPlayer`.
- `audioDucked: bool` — futuro, para ducking suave; por enquanto sempre false.

Regras:

```
if (currentSpot) {
  // Spot tem prioridade absoluta.
  return { videoMuted: true, audioEnabled: true };
}

const policy = currentMedia.audio_policy_effective || "auto";
const hasMediaAudio = currentMedia.has_audio === true;
const hasRadio = !!audioPlaylist?.tracks?.length;

switch (policy) {
  case "radio_only":
    return { videoMuted: true, audioEnabled: hasRadio };
  case "media_audio_only":
    return { videoMuted: !hasMediaAudio, audioEnabled: false };
  case "mix":
    return { videoMuted: !hasMediaAudio, audioEnabled: hasRadio };
  case "muted_video_with_radio":
    return { videoMuted: true, audioEnabled: hasRadio };
  case "auto":
  default:
    if (hasMediaAudio) {
      return { videoMuted: false, audioEnabled: false };
    } else {
      return { videoMuted: true, audioEnabled: hasRadio };
    }
}
```

### RF005-06 — Transicoes suaves

Mudanca de `audioEnabled` deve ter fade-out de 200ms antes de pausar, fade-in de 200ms ao retomar.

Critérios:

- `AudioPlayer` expoe metodos internos `pauseWithFade(ms)` e `resumeWithFade(ms)`.
- Hook resolver chama esses metodos em vez de set direto.
- Configuravel via `tenant.audio_fade_ms` (default 200).

### RF005-07 — UI: editor de campanha

`CampaignFormModal.jsx` deve mostrar:

- Campo "Politica de audio" com 5 opcoes (label amigavel + tooltip explicativo).
- Campo `video_muted` legado fica oculto/deprecated — explicitar que esta sendo substituido.
- Preview textual: "Quando uma midia desta campanha for um video com audio, a radio sera [pausada/mutada/mixada]."

Labels amigaveis:

- `auto` → "Automatico (recomendado)"
- `radio_only` → "Apenas radio (video sempre mudo)"
- `media_audio_only` → "Apenas audio da midia (radio pausa)"
- `mix` → "Misturar ambos"
- `muted_video_with_radio` → "Video mudo com radio ambiente"

### RF005-08 — UI: editor de midia

`MediaFormModal.jsx` deve mostrar:

- Campo "Politica de audio (override)" — opcoes + "Usar politica da campanha" (deixa nulo).
- Indicador "Esta midia [tem/nao tem] audio nativo (detectado automaticamente)."
- Botao "Recalcular" para forcar nova deteccao.

### RF005-09 — UI: device default

`DispositivoDetalhe.jsx` na secao de configuracao deve permitir definir politica padrao por dispositivo.

### RF005-10 — UI: tenant default

`ConfigEmpresa.jsx` (configuracoes da empresa/tenant) deve permitir definir politica padrao global do tenant.

### RF005-11 — Migracao dos dados existentes

A migration deve popular `audio_policy` baseado em `video_muted` legado:

| `video_muted` (legado) | `audio_playlist_id` | `audio_policy` migrado |
|---|---|---|
| `true` | nao-null | `muted_video_with_radio` |
| `true` | null | `muted_video_with_radio` (sem radio = video continua mudo) |
| `false` | nao-null | `mix` (preserva comportamento atual) |
| `false` | null | `auto` |
| `null` | qualquer | `auto` |

`campaign.video_muted` permanece como coluna legada por 2 releases, depois remove.

### RF005-12 — Documentacao operacional

Criar `docs/AUDIO_POLITICA.md` explicando para o cliente final:

- O que cada politica significa.
- Quando usar cada uma.
- Hierarquia de override.
- Como diagnosticar comportamento inesperado.

## Requisitos nao funcionais

- Resolver no player nao deve causar mais de 1 mudanca de audio por troca de midia (sem flapping).
- Fade in/out de 200ms eh imperceptivel mas suficiente para evitar pop sonoro.
- Mudanca de politica via SSE deve refletir na proxima troca de midia, nao interromper a atual.
- Backend resolver deve ser puro (sem side effects) para facilitar testing.
- Nao quebrar campanhas existentes (compatibilidade via migracao automatica).

## Decisoes de compatibilidade

- `campaign.video_muted` mantido como coluna legada por 2 releases.
- Player legado sem suporte a `audio_policy_effective`: continua usando `video_muted` (backend envia ambos os campos).
- Quando `audio_policy` esta setado, ele vence sobre `video_muted` no resolver do player.
- `tenant.audio_policy_default` default `auto`.

## Riscos

- Detecao automatica de `has_audio` em videos antigos pode falhar (sem `ffprobe` na pipeline). Mitigacao: backfill manual + assumir `true` para video.
- Politica `mix` pode soar mal mesmo com fade — clientes que escolherem mix ficam donos do problema.
- Spots futuros vao precisar reaproveitar este resolver — design ja prepara via `currentSpot` parameter.
- Mudanca via SSE pode confundir player se chegar no meio da troca — adicionar debounce 100ms.
- Audio HTML5 em alguns navegadores precisa de gesto do usuario para iniciar — ja resolvido por preload muted no projeto.

## Fora de escopo imediato

- Ducking automatico (abaixar volume da radio durante voz no video).
- Crossfade entre faixas da playlist de audio.
- Configuracao de fade duration por nivel (apenas global por tenant nesta SPEC).
- Multi-canal audio (Dolby/surround).
- Politica diferente por dia da semana / horario (parte de SPEC de scheduling).
- Spots recorrentes (SPEC propria).
