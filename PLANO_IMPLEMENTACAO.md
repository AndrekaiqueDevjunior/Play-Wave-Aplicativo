# AGENTES.md — Plano de Implementação Play Wave

> Documento de referência para agentes de implementação.
> Cada seção descreve **o que fazer**, **onde mexer**, **o que NÃO quebrar**.
> Status: [ ] pendente | [x] concluído | [~] parcial

---

## CONTEXTO DO PROJETO

- **Backend**: FastAPI + SQLAlchemy + PostgreSQL + Redis, rodando em `playwave-backend` (Docker)
  - Código em `/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/backend/`
  - Dentro do container: `/app/`
  - Rodar testes: `docker exec playwave-backend python -m pytest tests/<arquivo> -v`
- **Frontend**: React + Vite + TailwindCSS + shadcn/ui
  - Código em `/home/andre-kaique/projetos/play_wave_aplicativo/Play-Wave-Aplicativo/frontend/src/`
  - Componentes UI já existentes em `components/ui/` (button, dialog, input, select, table, etc.)
  - API calls em `src/api/` — padrão: `apiClient.js` com axios
- **Player**: `frontend/src/pages/Player.jsx` — app de exibição nas TVs
  - AudioManager: `frontend/src/lib/audioManager.js`
  - Comandos remotos: `frontend/src/player-core/commands.js`
- **Testes existentes**: `backend/tests/` — padrão unittest + TestClient + MagicMock (sem DB real)

---

## GRUPO A — RÁDIO INDOOR

### A1 — Upload múltiplo de músicas (do PC ao sistema de uma vez)

**Problema**: O upload de faixas de áudio aceita apenas um arquivo por vez.

**Backend** — `backend/api/v1/audio/tracks.py`
- O endpoint `POST /audio/tracks/upload` já existe mas processa um arquivo por vez
- Criar novo endpoint `POST /audio/tracks/upload-batch` que aceita `List[UploadFile]`
- Retorna lista de tracks criadas com status individual (sucesso/falha por arquivo)
- Validar: mime_type de áudio (mp3, mpeg, ogg, wav, flac, aac), tamanho máximo por arquivo

**Frontend** — `frontend/src/components/audio/MultiAudioUploadDialog.jsx` (já existe! verificar se funcional)
- Se não funcional: adicionar `multiple` no `<input type="file">` e enviar em paralelo ou batch
- Mostrar progresso individual por arquivo
- Usar `src/api/audio.js` — adicionar função `uploadAudioTracks(files[])` que faz loop ou batch POST
- Página de uso: `frontend/src/pages/FaixasAudio.jsx`

**Não quebrar**: endpoint individual de upload existente

---

### A2 — Agendamento de Spot com intervalo de tempo (tocar a cada X minutos)

**Status parcial**: Backend tem `AudioSpotSchedule.interval_seconds` e `start_time/end_time`.
**Problema**: A UI não expõe o campo `interval_seconds` de forma amigável.

**Frontend** — `frontend/src/components/audio/AudioSpotScheduleManager.jsx`
- Adicionar campo "Intervalo" com seletor amigável: "A cada 15 min", "A cada 30 min", "A cada 1h", "Personalizado (X min)"
- Exibir a janela de horário (start_time / end_time) de forma clara
- Bug confirmado: revisar se `interval_seconds` está sendo enviado no payload do PUT/POST

**Player** — `frontend/src/pages/Player.jsx` linhas ~884-925
- Bug: `setInterval` de spot não retorna ao rádio após o spot terminar (ver AGENTES_BUGS.md)
- Fix necessário: após `mgr.playSpot()` resolver, garantir `mgr.playRadio()` é chamado
- Fix: verificar janela de horário a cada tick do interval, não só na montagem

---

### A3 — Seleção múltipla de áudios para playlist de rádio/ponto

**Problema**: Ao adicionar faixas a uma playlist, só é possível adicionar uma por vez.

**Frontend** — `frontend/src/components/audio/AudioTrackSelector.jsx`
- Adicionar modo multi-seleção: checkboxes em cada faixa
- Botão "Adicionar selecionadas (N)" no rodapé
- Ao confirmar, chamar `POST /audio/playlists/{id}/items` em batch ou loop sequencial

**Backend** — `backend/api/v1/audio/playlists.py`
- Verificar se existe endpoint batch para adicionar itens
- Se não: criar `POST /audio/playlists/{id}/items/batch` que aceita `{ track_ids: [uuid] }`

**Página de uso**: `frontend/src/pages/PlaylistDetalhe.jsx` e `PlaylistsSonoras.jsx`

---

### A4 — Pastas de músicas com agendamento por horário (dia/tarde/noite) e período de data

**Status parcial**: Modelo `AudioFolder` + `AudioPlaylistFolderSchedule` existem no backend.
**Problema**: UI não tem interface completa para criar/gerenciar pastas e seus agendamentos.

**Frontend** — `frontend/src/components/audio/AudioFolderManager.jsx` (já existe — verificar se funcional)
- Criar/editar pasta: nome + descrição
- Adicionar faixas à pasta (seleção múltipla)
- Agendar pasta na playlist: início HH:MM, fim HH:MM, dias da semana, data início, data fim
- Listar pastas com seus horários ativos

**Backend** — `backend/api/v1/audio/folders.py`
- Verificar endpoints: GET/POST/PUT/DELETE de pastas e seus agendamentos
- `AudioPlaylistFolderSchedule`: campos `start_time`, `end_time`, `days_of_week`, `start_date`, `end_date`, `priority`

**Página de uso**: `frontend/src/pages/FaixasAudio.jsx` e `PlaylistDetalhe.jsx`

---

### A5 — Reprodução sequencial ou embaralhada na playlist

**Status parcial**: Backend tem `shuffle_enabled` na `AudioPlaylist`. Player lê `audioPlaylist.shuffle`.
**Problema**: UI não expõe esse toggle de forma clara.

**Frontend** — `frontend/src/pages/PlaylistDetalhe.jsx` ou `PlaylistsSonoras.jsx`
- Adicionar toggle "Reprodução: Sequencial / Embaralhar" no formulário/edição da playlist
- Enviar `shuffle_enabled: true/false` no PUT da playlist

**Sem mudanças no backend necessárias** (campo já existe).

---

## GRUPO B — CAMPANHA / PLAYLIST

### B1 — Upload de mídias separado do tick na campanha

**Problema**: O `CampaignFormModal` adiciona mídias via checkbox/tick em lista existente.
Não há como subir um arquivo novo diretamente dentro do fluxo de criação/edição de campanha.

**Frontend** — `frontend/src/components/campaigns/CampaignPlaylistBuilder.jsx`
- Adicionar botão "Subir nova mídia" dentro do builder que abre `MidiaUpload` em modal
- Após upload concluído, a nova mídia já aparece na lista de disponíveis e pode ser adicionada
- Separar visualmente: "Mídias disponíveis" (biblioteca) vs "Mídias na campanha" (playlist atual)

**Frontend** — `frontend/src/components/media/MediaFormModal.jsx`
- Verificar se pode ser usado como modal embutido dentro do CampaignPlaylistBuilder

---

### B2 — Reordenar mídias na campanha/playlist com drag-and-drop

**Status parcial**: Backend tem `PATCH /campaigns/{id}/items/reorder` e `order_index`.
**Problema**: UI não tem drag-and-drop implementado.

**Frontend** — `frontend/src/components/campaigns/CampaignPlaylistBuilder.jsx`
- Adicionar drag-and-drop na lista de mídias da campanha
- Biblioteca sugerida: `@dnd-kit/core` + `@dnd-kit/sortable` (checar se já instalada no package.json)
- Ao soltar item, chamar `PATCH /campaigns/{id}/items/reorder` com nova ordem
- Ou alternativamente: botões ↑ ↓ por item (mais simples, sem lib extra)

**API** — `frontend/src/api/campanhas.js`
- Adicionar função `reordenarItensCampanha(campaignId, items[{item_id, order_index}])`

---

## GRUPO C — MÍDIA

### C1 — Duração automática de vídeo (sem digitar o tempo)

**Status parcial**: Backend tem `ffprobe_service.py` e campo `duration_seconds`.
**Problema**: O frontend não usa a duração detectada automaticamente no upload.

**Backend** — `backend/api/v1/media.py`
- Verificar endpoint de upload: após salvar arquivo, deve chamar `ffprobe_service` para extrair duração
- Se já chama: verificar se o resultado é gravado em `display_duration_seconds` ou `duration_seconds`
- O campo `display_duration_seconds` é o que o player usa via `_media_playback_duration()`

**Frontend** — `frontend/src/pages/MidiaUpload.jsx`
- Após upload bem-sucedido, exibir a duração detectada automaticamente (campo somente leitura)
- Se duração = null: mostrar aviso "Duração não detectada — informe manualmente"
- No formulário de edição: campo de duração pré-preenchido com o valor detectado

---

### C2 — Período de exibição na própria mídia (starts_at / ends_at)

**Status parcial**: Modelo `Media` tem `starts_at` e `ends_at`. Backend filtra por eles.
**Problema**: UI não expõe esses campos no formulário de upload/edição.

**Frontend** — `frontend/src/components/media/MediaFormModal.jsx`
- Adicionar seção "Período de exibição" com DatePicker para início e fim
- Campos opcionais — se vazios, mídia é exibida sempre
- Exibir badge "Agendada para X" na lista `BibliotecaMidias.jsx`

**Frontend** — `frontend/src/pages/BibliotecaMidias.jsx`
- Mostrar indicador visual de mídias com agendamento ativo / expirado / futuro

---

### C3 — Substituir mídia sem sair do agendamento

**Problema**: Para trocar um vídeo exibido, o usuário precisa remover a mídia da campanha, subir a nova, e re-adicionar. O agendamento se perde.

**Solução**: Atualizar o arquivo de uma mídia existente sem mudar o `id`.

**Backend** — `backend/api/v1/media.py`
- Criar endpoint `PUT /media/{id}/replace-file` que:
  1. Recebe novo arquivo `UploadFile`
  2. Salva em novo path (com novo hash/versão)
  3. Atualiza `file_url`, `file_version`, `file_hash`, `duration_seconds` na mesma linha
  4. Incrementa `file_version` para invalidar cache do player
  5. NÃO muda o `id` — a mídia permanece nas campanhas onde está

**Frontend** — `frontend/src/components/media/MediaFormModal.jsx` e `BibliotecaMidias.jsx`
- Botão "Substituir arquivo" na mídia existente → abre file picker → faz PUT replace-file
- Exibir badge "v2", "v3" na miniatura indicando versão atual

---

## GRUPO D — PLAYER (BUGS CRÍTICOS)

### D1 — Player não desliga/reinicia pelo gerenciador

**Causa**: `restart_device` e `shutdown_device` requerem bridge nativa (`window.PlayWaveNative`) que não existe no web browser.

**Solução A (web)** — `frontend/src/player-core/commands.js`
- Para `restart_app`: o fallback `window.location.reload()` já existe e FUNCIONA
- Para `shutdown_device` no web: não é possível — mostrar mensagem clara: "Comando não suportado no player web. Use o APK Android ou Electron."

**Solução B (Android/APK)** — `backend/compatibilidade_SO/apk/`
- Implementar `window.AndroidPlayer.restartDevice()` e `window.AndroidPlayer.shutdownDevice()` na bridge Java/Kotlin
- Documentar no `README.md` do APK

**Frontend gerenciador** — `frontend/src/pages/DispositivoDetalhe.jsx`
- Ao enviar comando, mostrar resultado do ACK com mensagem clara:
  - `BROWSER_ENVIRONMENT` → "Player web não suporta este comando. Instale o APK."
  - `success: true` → "Comando executado com sucesso"
  - `success: false` → mensagem do erro

---

### D2 — Player continua funcionando após alterar código de pareamento

**Causa**: Ao mudar o `pairing_code` via PUT do device, o backend revoga o token e publica SSE `pairing:revoked`. O player deve escutar e voltar para tela de pareamento. O bug é que o player pode não estar reconectando o SSE após um reload.

**Verificar** — `frontend/src/pages/Player.jsx` linhas ~699-787
- O handler `onPairingRevoked` chama `forceRepair()` que limpa storage e vai para fase "waiting"
- Verificar se o SSE (`abrirStreamPlaylistUpdates`) reconecta após o player voltar para fase "waiting"
- Bug potencial: o `useEffect` do SSE depende de `[deviceId, deviceToken]` — se ambos são zerados em `onForceRepair`, o SSE é fechado (correto), mas o novo pareamento precisa reabri-lo

**Fix**: Após voltar para "waiting", o player gera novo código e mostra tela de pareamento — isso é correto. O problema pode ser que o dispositivo antigo ainda tem token válido no backend. Verificar se `_publish_pairing_revoked` é chamado no `update_device` quando `pairing_code` muda.

**Backend** — `backend/api/v1/devices.py` função `update_device` linhas ~1069-1098
- `pairing_code_changed` já revoga token e seta `requires_repairing = True` ✓
- Verificar se `_publish_pairing_revoked` É CHAMADO nesse bloco — se não estiver, adicionar

---

### D3 — Mídia misturando áudio com a rádio

**Causa confirmada**: `audioManager.playSpot()` não retorna ao rádio após spot terminar (ver test_radio_indoor_bugs.py).

**Fix** — `frontend/src/lib/audioManager.js`
- Em `playSpot()`: após `spot.play()`, adicionar listener `spot.addEventListener('ended', () => this._resumeAfterSpot('spot'), { once: true })`
- Garantir que `_resumeAfterSpot` é chamado mesmo se o spot terminar naturalmente
- Adicionar cleanup: se `playSpot` é chamado novamente antes do anterior terminar, cancelar o anterior

**Fix** — `frontend/src/pages/Player.jsx` bloco `useAudioConflictResolver`
- A política `audio_policy_effective` por mídia controla se o áudio da mídia toca junto com a rádio
- Verificar se `has_audio: true` + `audio_policy_effective: "muted_video_with_radio"` está sendo respeitado

---

### D4 — Mostrar nome da música no canto da tela do player/TV (OSD)

**Status parcial**: `PlayerOSD.jsx` existe e recebe `currentAudioTrack` e `osdConfig`.
**Problema**: Verificar se está sendo exibido e se a posição/estilo está correta.

**Frontend** — `frontend/src/components/player/PlayerOSD.jsx`
- Garantir que `currentAudioTrack.name` é exibido quando `osdConfig.show_current_audio = true`
- Posição configurável via `osdConfig.position`: top_right, top_left, bottom_right, bottom_left
- Exibir por `osdConfig.duration_seconds` segundos ao mudar de faixa (fade out automático)
- Estilo sugerido: fundo semitransparente, ícone de nota musical + nome da faixa

**Frontend** — `frontend/src/pages/Player.jsx`
- Verificar se `currentAudioTrack` está sendo passado corretamente para `PlayerOSD`
- `currentAudioTrack` vem do `audioManagerRef` via callback de subscription

---

## GRUPO E — PLAYER: REINÍCIO INDEVIDO (BUG CRÍTICO)

### E1 — Player reinicia ao qualquer mudança no gerenciador

**Causa confirmada** (test_player_campaign_bugs.py):
- `onPlaylistInvalidated` em Player.jsx linha ~722 não verifica `config_version`
- `_broadcast_playlist_invalidated` é chamado para TODA mudança de campanha

**Fix — Frontend** — `frontend/src/pages/Player.jsx`
```javascript
// ANTES (bugado):
const onPlaylistInvalidated = () => triggerReload("playlist_invalidated");

// DEPOIS (correto):
const onPlaylistInvalidated = (evt) => {
  try {
    const data = JSON.parse(evt.data);
    if (data.config_version && data.config_version === campaignConfigVersion) return;
  } catch {}
  triggerReload("playlist_invalidated");
};
```

**Fix — Backend** (opcional, melhoria): `backend/api/v1/campaigns.py`
- Em `update_campaign`: só incrementar `config_version` e broadcast se campos que afetam o player foram alterados
- Campos que afetam player: `media_ids`, `media_order`, `device_ids`, `status`, `audio_playlist_id`, `schedule_*`, `start_date`, `end_date`, `loop_count`, `video_muted`
- Campos que NÃO afetam: `name`, `description`, `priority`, `tags`

---

## ORDEM DE IMPLEMENTAÇÃO SUGERIDA

### Sprint 1 — Bugs críticos (sem novos recursos)
1. **E1** — Fix reinício indevido do player (1 linha no frontend)
2. **D2** — Fix player continua após mudar código de pareamento (verificar backend)
3. **D3** — Fix áudio misturado: retorno ao rádio após spot (audioManager.js)
4. **D4** — Verificar/ativar OSD de nome da música

### Sprint 2 — Mídias
5. **C1** — Duração automática de vídeo
6. **C2** — Período de exibição na mídia (starts_at/ends_at na UI)
7. **C3** — Substituir arquivo de mídia (novo endpoint backend + UI)

### Sprint 3 — Campanha
8. **B2** — Reordenar mídias (drag-and-drop ou botões ↑↓)
9. **B1** — Upload de mídia dentro do fluxo de campanha

### Sprint 4 — Rádio
10. **A5** — Toggle sequencial/embaralhar (simples, campo já existe)
11. **A2** — Fix spot schedule (intervalo na UI + fix retorno ao rádio)
12. **A3** — Seleção múltipla de áudios na playlist
13. **A4** — UI de pastas com agendamento horário
14. **A1** — Upload múltiplo de áudios

### Sprint 5 — Comandos de dispositivo
15. **D1** — Melhorar feedback de comandos não suportados no web player

---

## INSTRUÇÕES PARA AGENTES

### Ao implementar qualquer item:

1. **Leia o arquivo antes de editar** — use a tool Read
2. **Teste no container**: `docker exec playwave-backend python -m pytest tests/<arquivo> -v`
3. **Não quebre APIs existentes** — adicione endpoints novos, não modifique os existentes sem necessidade
4. **Padrão de imports frontend**: `import { Button } from "@/components/ui/button"` etc.
5. **API calls frontend**: criar função em `src/api/audio.js` ou `src/api/midias.js`, chamar do componente via `useQuery`/`useMutation` do React Query (`src/lib/query-client.js`)
6. **Invalidar cache após mutations**: usar `queryClient.invalidateQueries(["chave"])`
7. **Toasts de feedback**: usar `import { toast } from "sonner"` (já instalado)

### Padrão de teste backend:
```python
import unittest
from unittest.mock import MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace
import uuid

# Montar mini-app com override de dependências
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = lambda: MagicMock()
app.dependency_overrides[get_current_user] = lambda: user_mock
client = TestClient(app)
```

### Arquivos-chave por área:

| Área | Backend | Frontend |
|------|---------|----------|
| Rádio/Áudio | `api/v1/audio/` | `pages/FaixasAudio.jsx`, `pages/PlaylistDetalhe.jsx`, `components/audio/` |
| Campanha | `api/v1/campaigns.py` | `pages/Campanhas.jsx`, `components/campaigns/` |
| Mídia | `api/v1/media.py` | `pages/BibliotecaMidias.jsx`, `pages/MidiaUpload.jsx`, `components/media/` |
| Player | *(sem backend novo)* | `pages/Player.jsx`, `lib/audioManager.js`, `player-core/commands.js` |
| Dispositivos | `api/v1/devices.py` | `pages/Dispositivos.jsx`, `pages/DispositivoDetalhe.jsx` |

---

## STATUS ATUAL DOS BUGS (confirmados por testes)

| Bug | Arquivo | Linha | Teste que confirma |
|-----|---------|-------|--------------------|
| Player reinicia a qualquer mudança | Player.jsx | ~722 | test_player_campaign_bugs.py |
| Spot bloqueia rádio permanentemente | audioManager.js | ~187 | test_radio_indoor_bugs.py |
| Pasta de música vazia se faixas não-ACTIVE | devices.py | 534 | test_radio_indoor_bugs.py |
| restart_device falha no web | commands.js | ~47 | test_device_commands_bugs.py |
| Campanha draft/paused não aparece no player | crud_campaign.py | — | test_player_campaign_bugs.py |
| Agenda duplicada (redundante com campanha) | agenda.jsx | — | test_campaign_schedule_bugs.py |
