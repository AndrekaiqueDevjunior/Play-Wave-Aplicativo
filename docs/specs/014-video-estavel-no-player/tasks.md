# SPEC 014 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 013 concluida — gate liberado.

## Diagnostico

- [x] Auditar `frontend/src/components/player/MediaRenderer.jsx` — componente real de video do player.
- [x] Auditar `frontend/src/pages/Player.jsx` — dois call sites de `<MediaRenderer>`, calculo de `current`/`nextMedia`, tick de progresso (250ms), heartbeat (30s), spot tick (5s), radio resolver (60s).
- [x] Confirmar ausencia de preload-next-media — `nextMedia` so era usado no overlay de debug.
- [x] Confirmar ausencia de `React.memo` em `MediaRenderer` — qualquer re-render do Player recalculava `renderContent()`.
- [x] Auditar backend (`backend/main.py:137-174`, `backend/api/v1/media.py`) — Range requests, Cache-Control e metadata ffprobe ja adequados, descartados como causa.
- [x] Auditar `frontend/electron/main.js` — sem flags de hardware acceleration desabilitadas, descartado como causa.
- [x] Confirmar ausencia de `window.location.reload()` no caminho normal do player.

## Backend

- [x] Nenhuma alteracao necessaria — entrega de midia e metadata ja adequadas.

## Player

- [x] Criar `MediaPreloader` em `MediaRenderer.jsx`: elemento oculto (video/audio/img) para `nextMedia`.
- [x] Passar `nextMedia` para `<MediaRenderer>` nos dois call sites de `Player.jsx` (fase `loading` e fase `playing`).
- [x] Envolver `MediaRenderer` em `React.memo` (comparador padrao/shallow).
- [x] Mover a barra de progresso para atualizacao via ref/DOM direto (`useEffect` + `style.width`), preservando o comportamento visual com o memo ativo.
- [x] Decisao registrada: comparador customizado do memo (excluindo `progress`) foi tentado e revertido — quebrava a atualizacao da barra de progresso, pois o componente nunca re-executava o `useEffect` correspondente.

## Testes

- [x] `renderiza um <video> oculto para a proxima midia quando ela e video`.
- [x] `renderiza um <img> oculto para a proxima midia quando ela e imagem`.
- [x] `nao renderiza preload quando nao ha proxima midia`.
- [x] `troca o preload quando nextMedia muda (nao fica preso na midia antiga)`.
- [x] `nao recria o elemento <video> principal quando as props sao as mesmas (re-render do pai sem mudanca real)`.
- [x] `atualiza a largura da barra de progresso quando progress muda`.
- [x] `recria o video principal quando media.id muda (troca real de conteudo)`.
- [x] Suite nova `media_renderer.test.jsx`: 7/7 passando.
- [x] Suites relacionadas sem regressao: `osd_audio_player.test.jsx`, `audio_manager.test.js`, `audio_conflict_resolver.test.jsx`, `spotScheduleResolver.test.js`, `media_schedule.test.js` (68 testes no total, todos passando).
- [x] Suite completa do frontend: 147/150 passando — as 3 falhas restantes (`player_sse.test.js` parse error de JSX em arquivo `.test.js`, `playbackQueueManager.test.js` 3 testes) sao pre-existentes, confirmadas via `git stash`/rerun antes desta SPEC, sem relacao com os arquivos alterados aqui.
- [ ] Teste manual/visual em hardware real de loja (TV/mini-PC Windows) com video pesado/animacao — nao executado nesta sessao.

## Criterios de aceite

- [x] Preload da proxima midia implementado e testado.
- [x] `MediaRenderer` memoizado e testado.
- [x] Barra de progresso continua funcionando corretamente com o memo ativo.
- [x] Nenhuma regressao nas suites de teste relacionadas.
- [ ] Validacao visual real em hardware de loja — pendente.

## Riscos e pendencias

- [ ] Validar consumo de memoria/banda do preload em dispositivos de hardware fraco (2 elementos de video simultaneos: 1 visivel + 1 oculto).
- [ ] Se `Player.jsx` for refatorado no futuro e `current`/`nextMedia`/callbacks deixarem de ter identidade estavel entre renders, o ganho do `React.memo` desaparece silenciosamente — vale revisao quando houver refactor proximo a essa area.
- [ ] Endpoint de diagnostico de midia dedicado (sugerido no documento mestre) nao foi criado — avaliar em SPEC futura se o preload nao for suficiente para resolver o relato do cliente em campo.
