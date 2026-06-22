# SPEC 014 — Player

Status: implementada

## Comportamento esperado

### Preload

`Player.jsx` ja calculava `nextMedia = playlist[(currentIndex + 1) % playlist.length]` (usado apenas no overlay de debug). Agora essa mesma referencia e passada para `<MediaRenderer nextMedia={nextMedia} ... />` nos dois call sites (fase `loading` com midia ja resolvida, e fase `playing`).

Dentro de `MediaRenderer`, o novo subcomponente `MediaPreloader`:

- Resolve tipo (`resolveMediaType`) e URL (`resolveMediaUrl`) de `nextMedia` da mesma forma que a midia atual.
- Renderiza um elemento oculto (`position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none`) do tipo correspondente:
  - `video` → `<video preload="auto" muted>` oculto.
  - `audio` → `<audio preload="auto" muted>` oculto.
  - `image` → `<img>` oculto.
- Nao renderiza nada para tipos `youtube`/`vimeo`/`external_url` (iframes nao precisam de preload de arquivo) nem quando `nextMedia` e `null`/`undefined` (playlist com 1 item).
- Usa `key={preload-${media.id}}` para que o React substitua o elemento quando a proxima midia muda, sem reaproveitar um elemento de uma midia diferente.

### Memoizacao

`MediaRenderer` agora e `export default React.memo(function MediaRenderer(...) { ... })`, usando a comparacao shallow padrao do `React.memo` em todas as props (`media`, `nextMedia`, `onEnded`, `onError`, `onDebug`, `progress`, `videoMuted`). Quando o `Player.jsx` re-renderiza por causa de heartbeat/spot/radio/audio manager mas nenhuma dessas props muda de fato (mesma referencia/valor), o React pula a re-execucao de `MediaRenderer` — sem recalcular `renderContent()` nem reanexar listeners de video.

### Barra de progresso sem re-render do video

A barra de progresso (antes: `style={{ width: ... }}` ligado diretamente ao prop `progress` no JSX) agora e atualizada via `useEffect(() => { progressBarRef.current.style.width = ... }, [progress])`, escrevendo no DOM atraves de uma ref. Isso preserva a atualizacao visual em tempo real (a cada 250ms) sem que essa mudanca dependa de recriar o JSX do `<video>` — o memo e a escrita via ref trabalham juntos: o memo deixa passar o re-render quando `progress` muda (e necessario para o `useEffect` rodar), mas o conteudo de `renderContent()` permanece o mesmo elemento DOM porque a `key={media.id}` nao mudou.

## Logs

Nenhum log novo foi necessario — os eventos `PLAYER_VIDEO_DEBUG`/`PLAYER_VIDEO_ERROR` existentes (`loadstart`, `canplay`, `stalled`, `waiting`, `playing`, `error`, `ended`, etc.) continuam cobrindo o ciclo de vida do elemento de video visivel. O elemento de preload e deliberadamente "silencioso" (sem listeners, sem autoplay) — ele so existe para acionar o download/cache do navegador, nao participa do ciclo de reproducao nem dos logs de debug.

## Checklist de auditoria

- [x] Conferir `frontend/src/components/player/MediaRenderer.jsx` (renderContent, listeners de video, progress bar).
- [x] Conferir os dois call sites em `frontend/src/pages/Player.jsx` (fase `loading` e fase `playing`).
- [x] Confirmar que `current` e `nextMedia` mantêm identidade de objeto estável entre renders (lookup em array, não recriação).
- [x] Confirmar que `advanceMedia`/`handleMediaError` já são `useCallback` com dependências estáveis durante o tick de progresso.
- [x] Confirmar que `setVideoDebug` (setState) é referencialmente estável entre renders.
