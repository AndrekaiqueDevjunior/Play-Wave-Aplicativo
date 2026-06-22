# SPEC 014 — Requirements

Status: implementada
Data: 2026-06-18

## Contexto

Cliente reportou que videos rodam normalmente no preview do gerenciador, mas travam/picotam no player real, principalmente animacoes. A auditoria identificou que o player nunca pre-carregava a proxima midia da fila e que o componente de video re-renderizava a cada 250ms (tick de progresso) e a cada atualizacao de audio/spot/radio do player principal, mesmo sem mudanca real de conteudo.

## Objetivo

O player deve reproduzir video de forma fluida, com preload da proxima midia e sem re-render desnecessario do componente de video durante a reproducao normal.

## Requisitos funcionais

### RF014-01 — Preload da proxima midia

Enquanto a midia atual esta tocando, a proxima midia da fila deve comecar a ser baixada pelo navegador em segundo plano (elemento oculto), para que a troca aconteca com o arquivo ja em cache.

Criterios:

- Existe um elemento de preload (`video`/`img`/`audio`, conforme o tipo) renderizado fora da area visivel para a proxima midia da fila.
- O preload usa a mesma URL resolvida (`resolveMediaUrl`) que sera usada quando a midia se tornar atual — garante reuso do cache HTTP do navegador.
- Quando a midia atual avanca, o elemento de preload da midia que **acabou de se tornar atual** e substituido pelo preload da **nova proxima midia** (sem ficar presa na midia anterior).
- Nenhum preload e criado quando nao ha proxima midia (playlist com 1 item) ou quando o tipo nao e video/imagem/audio (ex: iframe de YouTube/Vimeo nao precisa).

### RF014-02 — Memoizacao do componente de video

O componente que renderiza a midia atual (`MediaRenderer`) nao deve re-renderizar quando nenhuma das suas props mudou de fato.

Criterios:

- `MediaRenderer` e exportado como `React.memo`.
- Re-renders do `Player.jsx` causados por estado nao relacionado (heartbeat, resolver de spot/radio, audio manager) nao forcam `MediaRenderer` a recalcular `renderContent()` quando `media`, `nextMedia`, `videoMuted` e os callbacks (`onEnded`/`onError`/`onDebug`) permanecem com a mesma referencia.

### RF014-03 — Barra de progresso sem re-render do video

A barra de progresso (atualizada a cada 250ms) nao deve forcar recalculo dos listeners de video nem da arvore de `renderContent()`.

Criterios:

- A largura da barra de progresso e atualizada via DOM direto (ref), nao via re-render de JSX que recria o elemento de video.
- O valor visual da barra continua correto e atualizado em tempo real.

## Compatibilidade

- Nao alterar contrato de entrega de midia do backend (`backend/main.py` Range requests) — ja adequado.
- Nao alterar o model `Media` nem ffprobe metadata — fora de escopo, sem evidencia de causar o bug relatado.
- Nao alterar `CampanhaPreview.jsx` (preview do gerenciador) — o bug e especifico do player, e o preview ja funciona corretamente segundo o relato do cliente.
- Nao quebrar o fluxo de autoplay/mute/gesture existente em `MediaRenderer` (forcar muted em Android/iOS/SmartTV/Capacitor, fallback de autoplay bloqueado).

## Criterios de aceite

- [x] Preload da proxima midia implementado e validado por teste automatizado.
- [x] `MediaRenderer` memoizado, validado por teste automatizado (mesmo no DOM quando props nao mudam).
- [x] Barra de progresso atualiza corretamente sem recriar o elemento de video.
- [x] Nenhuma regressao nas suites de teste relacionadas (audio, OSD, spot/radio resolver).
- [ ] Validacao visual real em hardware de loja (TV/mini-PC Windows) com animacao pesada — nao executada nesta sessao.
