# SPEC 014 — API Contract

Status: implementada — sem mudanca de contrato

## Contrato (inalterado)

Esta SPEC nao introduz nem altera endpoints, schemas ou models. A correcao e inteiramente client-side (componente `MediaRenderer` e prop `nextMedia` passada pelo `Player.jsx`).

## Entrega de midia (confirmado, ja adequado)

`GET /uploads/{file_path:path}` (`backend/main.py:137-174`):

- Suporta `Range` request header — responde `206 Partial Content` com o trecho solicitado.
- Header `Accept-Ranges: bytes` presente.
- Header `Cache-Control: public, max-age=604800` (7 dias) — o preload desta SPEC se beneficia diretamente desse cache: ao tocar a midia preload-ada, o browser reaproveita o que ja baixou em vez de refazer a requisicao completa.

## Metadata de midia (confirmado, ja adequado para o escopo desta SPEC)

Model `Media` (`backend/core/models.py`) ja armazena, populado via ffprobe no upload (`backend/api/v1/media.py`):

- `duration_seconds`
- `resolution`
- `has_audio`
- `mime_type`
- `extra_metadata` (JSON com saida completa do ffprobe, incluindo streams/codec/bitrate quando disponivel)

Nao ha campos dedicados `bitrate`/`fps` na tabela — ficam dentro de `extra_metadata`. Adicionar colunas dedicadas para essas metricas e fora de escopo desta SPEC (ver `README.md`), pois nao havia evidencia de que a falta delas causasse o travamento relatado.

## Por que nao houve mudanca de contrato

O bug nao estava na entrega do arquivo (que ja suporta range/cache corretamente) nem na modelagem de metadata, mas na ausencia de uma estrategia de preload no client e na falta de memoizacao do componente de video, que fazia o `MediaRenderer` ser recalculado a cada re-render do `Player.jsx` (a cada 250ms via tick de progresso, e a cada atualizacao de audio/spot/radio). Ambos os fixes vivem inteiramente em `frontend/src/components/player/MediaRenderer.jsx` e `frontend/src/pages/Player.jsx`.
