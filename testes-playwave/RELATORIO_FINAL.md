# 📊 Relatório Final — Suíte E2E PlayWave (Scheduler/Fila)

**Data:** 2026-06-07 · **Branch:** `fix/dev-env` · **Autor:** QA/Fullstack

---

## 1. Auditoria do sistema (o que é REAL)

| Tema | Realidade encontrada | Fonte |
|------|----------------------|-------|
| **Auth** | `POST /api/auth/login {email,password}` → `{access_token, user}`; `GET /api/auth/me` | `backend/api/v1/auth.py` |
| **Base da API** | `VITE_API_URL`. Rotas na raiz (`/devices`, `/campaigns`, `/audio/*`), auth em `/api/auth`, player em `/api/v1/...` | `backend/main.py`, `frontend/src/api/http.js` |
| **Recepção de programação** | **Novo:** `GET /api/v1/player/schedule?device_id=&device_token=` (resolve spots+playlist+versão). **Legado:** `GET /devices/{id}/playlist` | `backend/api/v1/player_schedule.py`, `devices.py` |
| **Scheduler/Fila** | Resolução server-side em `services/spot_resolver.py` (`resolve_for_device`) e `services/audio_spot_scheduler.py` (`get_eligible_spots`). Fila de reprodução montada **client-side** no player | `backend/services/*`, `frontend/src/lib/audioManager.js`, `player-core/` |
| **Tempo real** | **SSE** `GET /devices/{id}/playlist/updates?token=` (eventos: `snapshot`, `playlist_invalidated`, `command:new`, `pairing:revoked`). **WebSocket NÃO existe** | `backend/api/v1/devices.py:2174`, `frontend/src/pages/Player.jsx` |
| **Polling** | Player faz poll de `/player/schedule` e `/commands/pending` | `Player.jsx` |
| **Versionamento** | `Device.schedule_version` (int), `Campaign.campaign_version` (int), `AudioPlaylist.version` (int), `Device.config_version` (str). Bump em `crud_audio_spot_schedule._bump_versions` por escopo | `backend/core/models.py`, `crud/entidades/crud_audio_spot_schedule.py` |
| **Cache** | Redis `device_playlist:{id}` invalidado em mutações; populado por Celery task. ⚠️ `/player/schedule` **não lê** esse cache (recomputa) | `backend/tasks/__init__.py`, `api/v1/*` |
| **Debug** | `GET /devices/{id}/debug-spots` e `GET /devices/{id}/debug-playback` (admin) | `devices.py`, `player_schedule.py` |
| **data-testid** | **0 ocorrências** no frontend inteiro | `grep` em `frontend/src` |

---

## 2. Arquivos criados (22)

**Infra:** `package.json`, `tsconfig.json`, `playwright.config.ts`, `.env.example`, `.gitignore`
**Helpers:** `helpers/{env,api,auth,media-gen,factories,sse,cleanup}.ts`
**Fixtures:** `fixtures/test-fixtures.ts`, `fixtures/media/` (drop `sample.mp4`)
**Tests (12):** `auth.setup.ts`, `scheduler-fila.spec.ts` (CORE), `upload-multiplo`, `categorias`, `pastas-audio`, `spots`, `radio-playlists`, `campanhas`, `player`, `dispositivos-comandos`, `debug`, `electron-windows`
**Docs:** `README.md`, `CHECKLIST_TESTES.md`, `RELATORIO_FINAL.md`

## 3. Comandos

```bash
cd testes-playwave
cp .env.example .env && $EDITOR .env
npm install
npx playwright install
npx playwright test            # ou: npm run test:fila
npx playwright show-report reports/html
```

---

## 4. `data-testid` faltantes (criar no frontend)

O painel não tem nenhum. Prioridade para tornar os `@ui` robustos:

### Login (`frontend/src/pages/Login.jsx`)
- `data-testid="login-email"`, `login-password`, `login-submit`

### Faixas de áudio (`frontend/src/pages/FaixasAudio.jsx`)
- `btn-nova-categoria`, `drawer-categoria`, `input-categoria-nome`, `btn-salvar-categoria`
- `btn-upload-faixas`, `input-upload-multiplo`, `lista-faixas`, `faixa-item`

### Spots (`frontend/src/pages/Spots.jsx`, `components/audio/SpotSchedulePanel.jsx`)
- `select-playlist-spot`, `btn-agendar-spot`, `spot-schedule-row`, `input-interval-value`,
  `select-interval-unit`, `input-spot-start-time`, `input-spot-end-time`, `select-insertion-policy`,
  `input-play-duration`, `btn-salvar-schedule`

### Dispositivo / Debug (`frontend/src/pages/DispositivoDetalhe.jsx`)
- `device-debug-panel`, `device-queue`, `device-next-media`, `device-version-local`,
  `device-version-remote`, `device-last-heartbeat`, `device-last-commands`, `btn-comando-{sync,restart,clear_cache}`

### Campanhas (`frontend/src/components/campaigns/CampaignFormModal.jsx`)
- `campaign-name`, `campaign-media-list`, `media-item`, `btn-reordenar`, `btn-substituir-midia`,
  `select-audio-policy`, `btn-publicar-campanha`

### Playlists (`frontend/src/pages/PlaylistDetalhe`/`radio/playlists`)
- `playlist-tracks`, `btn-add-folder`, `folder-schedule-row`, `toggle-shuffle`

---

## 5. Endpoints — existentes vs faltantes para testar a FILA

### ✅ Existem e foram usados
`/api/auth/login`, `/api/auth/me`, `/devices` (CRUD), `/devices/pair-request`,
`/devices/by-code/{code}/status`, `/devices/{id}/pair-confirm`, `/devices/{id}/command`,
`/devices/{id}/commands(+/pending)`, `/devices/{id}/revoke-token`, `/devices/{id}/playlist`,
`/devices/{id}/playlist/updates` (SSE), `/devices/{id}/debug-spots`, `/devices/{id}/debug-playback`,
`/api/v1/player/schedule`, `/audio/tracks(+/upload,/upload-multiple)`, `/audio/categories`,
`/audio/folders(+/{id}/tracks,/tracks/reorder)`, `/audio/playlists(+/{id}/folder-schedules)`,
`/audio/spots(+/schedules,/playlists/{id}/spot-schedules)`, `/media(+/upload,/{id}/replace-file,/{id}/usage)`,
`/campaigns(+/publish,/items,/items/reorder)`.

### ❌ Faltam para fechar a observabilidade da fila (TODO técnico)
1. **Fila de PASTA resolvida no payload do player.** `/api/v1/player/schedule` resolve **apenas spots**.
   Pasta por horário/data (TASKS 04/05) não aparece na fila resolvida → impossível validar elegibilidade
   de pasta por API. **Sugestão:** estender `resolve_for_device` para incluir `folder_schedules` elegíveis,
   ou criar `GET /api/v1/player/queue` unificada (playlist + pasta + spot + campanha) já ordenada.
2. **Snapshot de "fila ordenada" único.** Hoje o cliente monta a ordem. Para testar ordem/prioridade
   de forma determinística, expor a **fila final ordenada** server-side (mesma que o player tocaria).
3. **Endpoint de duração/processamento de mídia.** Confirmar se `duration_seconds` é síncrono no upload
   ou assíncrono (Celery). Se assíncrono, expor status de processamento para o teste aguardar.
4. **Próximo item / "next" explícito** no debug (campo `next_media` / `next_spot_at`) para TASK 26.

---

## 6. Gaps encontrados na arquitetura da FILA

| Gap | Severidade | Detalhe |
|-----|-----------|---------|
| **Fila não unificada** | 🔴 Alta | Spots resolvem no servidor (`spot_resolver`), mas playlist/pasta/ordem montam no cliente. Não há um "estado de fila" único e observável. Dificulta testar ordem/prioridade ponta a ponta. |
| **Dois caminhos de playlist divergentes** | 🔴 Alta | `/devices/{id}/playlist` (legado, com cache Redis) vs `/api/v1/player/schedule` (novo, sem cache). Risco de divergência de conteúdo entre os dois. |
| **Cache invalidado mas não consumido** | 🟡 Média | Mutações invalidam `device_playlist:{id}`, mas `/player/schedule` não lê esse cache — invalidação não acelera o caminho que serve spots (ver `ANALISE_PERFORMANCE_SPOTS.md`). |
| **N+1 no resolver** | 🟡 Média | `resolve_for_device` faz `1+2N` queries (spot+track por schedule), sem dedup. Escala mal por device/poll. |
| **Pasta sem resolução no player** | 🟡 Média | Folder-schedule persiste janela/período, mas não há resolução elegível por horário/data no payload do player. |
| **Versão por escopo divergente** | 🟢 Baixa | Schedule playlist-scoped bumpa `playlist.version`, não `device.schedule_version`. O player compara `schedule_version` do device — mudanças só-de-playlist podem não refletir na versão que o device observa. Verificar reconciliação. |
| **Ordem/anti-repetição do shuffle** | 🟢 Baixa | Aleatório é client-side; sem semente observável → difícil testar "sem repetição indevida" de forma determinística. |

---

## 7. Recomendações de engenharia (deixar a fila robusta, previsível e observável)

1. **Unificar a fila num único resolver server-side.** Criar `resolve_queue_for_device()` que devolve a
   **fila final ordenada** (campanha → playlist/pasta por horário → spots por intervalo/prioridade), com
   `position`, `eligible`, `reason`. O player consome essa fila pronta. Torna a arquitetura **testável e determinística**.
2. **Eliminar o caminho legado** `/devices/{id}/playlist` ou fazê-lo delegar ao mesmo resolver, removendo divergência.
3. **ETag/versão na fila** (`schedule_version` consolidado por device, somando playlist+campaign+device+folder).
   Player envia `If-None-Match`; backend responde **304** → resolve cache + "não reiniciar player" de forma barata.
4. **Corrigir o N+1** em `resolve_for_device` com batch-load (`IN`) de spots/tracks (ver `ANALISE_PERFORMANCE_SPOTS.md`, P1).
5. **Tornar logs observáveis em teste** — endpoint de diagnóstico ou `pytest + caplog` para asserir os logs
   estruturados (scheduler/fila/spot/comando/sse/cache). Hoje não há como validar logs por E2E HTTP.
6. **Expor "próximo item" e timestamps** no debug (`next_at`, `last_played_at` por schedule) para validar
   intervalo de spot e avanço de fila sem depender do relógio do player.
7. **Semente de shuffle determinística** (por `device_id + schedule_version`) → ordem aleatória reproduzível
   e testável, sem repetição indevida.
8. **Projeto Playwright-Electron** separado (`_electron.launch`) apontando ao build desktop para cobrir
   minimizar/maximizar real (TASK 36).

---

## 8. Como os `test.fixme()` se justificam (honestidade)

Cada `fixme` aponta uma limitação **real**, não preguiça:
- **OSD (27), shuffle runtime (06), no-reload (20/21):** comportamento client-side do player — já há testes
  de componente em `frontend/src/__tests__/` (`audio_manager.test.js`, `player_sse.test.js`, `restore_fullscreen.test.js`).
- **Pasta por horário no player (04/05):** falta endpoint que exponha pasta resolvida (ver §5.1).
- **Polling fallback (32):** exige simular queda de SSE no player real.
- **Logs (35):** não observável por HTTP (ver §7.5).
- **Janela Electron (36):** exige Playwright-Electron com binário do app.
- **Duração/Período (16/17):** `fixme` condicional — só dispara se o schema não expuser o campo (processamento assíncrono).
