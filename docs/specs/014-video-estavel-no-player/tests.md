# SPEC 014 — Tests

Status: implementada — testes unitarios passando, validacao visual em hardware pendente

## Testes automatizados (executados)

Arquivo novo: `frontend/src/__tests__/media_renderer.test.jsx`

| Teste | Resultado |
|---|---|
| Renderiza `<video>` oculto para a proxima midia quando ela e video | passou |
| Renderiza `<img>` oculto para a proxima midia quando ela e imagem | passou |
| Nao renderiza preload quando nao ha proxima midia | passou |
| Troca o preload quando `nextMedia` muda (nao fica preso na midia antiga) | passou |
| Nao recria o `<video>` principal quando as props sao as mesmas (re-render do pai sem mudanca real) | passou |
| Atualiza a largura da barra de progresso quando `progress` muda | passou |
| Recria o `<video>` principal quando `media.id` muda (troca real de conteudo) | passou |

Comando executado:

```bash
cd frontend && npx vitest run src/__tests__/media_renderer.test.jsx
```

Resultado: `7 passed (7)`.

Suites relacionadas (sem regressao):

```bash
npx vitest run src/__tests__/media_renderer.test.jsx src/__tests__/osd_audio_player.test.jsx \
  src/__tests__/audio_manager.test.js src/__tests__/audio_conflict_resolver.test.jsx \
  src/__tests__/spotScheduleResolver.test.js src/__tests__/media_schedule.test.js
```

Resultado: `68 passed (68)`.

Suite completa do frontend:

```bash
npx vitest run
```

Resultado: `147 passed`, `3 failed` (todos pre-existentes e confirmados via `git stash` antes desta SPEC):

- `player_sse.test.js` — falha de parse (JSX em arquivo `.test.js`, nao `.test.jsx`) — nao relacionado.
- `playbackQueueManager.test.js` — 3 testes (`shuffle`, `persistencia localStorage`, `jumpToIndex`) — nao relacionado, arquivo nao tocado por esta SPEC.

## Testes manuais sugeridos (nao executados nesta SPEC)

### TM014-01 — Troca de video sem buffering visivel

Pre-condicao: player Electron rodando com playlist contendo pelo menos 2 videos, em rede com latencia/banda limitada (throttling).

Passos:

1. Iniciar reproducao do primeiro video.
2. Observar o painel de rede (DevTools/Electron) — a URL do segundo video deve aparecer como requisicao em andamento antes do primeiro terminar.
3. Ao trocar para o segundo video, nao deve haver tela preta/loading prolongado.

Resultado esperado: transicao perceptivelmente mais rapida que antes do preload.

### TM014-02 — Animacao pesada sem travamento

Pre-condicao: midia de video com animacao complexa (alto bitrate/fps), em hardware de loja real (mini-PC Windows ou equivalente).

Passos:

1. Reproduzir a midia isoladamente.
2. Reproduzir a midia com radio + spot agendado simultaneamente (cenario real de loja).

Resultado esperado: sem picotamento perceptivel; comparar com o comportamento anterior a esta SPEC, se possivel em A/B.

### TM014-03 — Console sem erros de preload

Passos: abrir o player com `?debug=true`, observar console por uma sessao completa de playlist (varias voltas).

Resultado esperado: nenhum erro relacionado aos elementos de preload (`MediaPreloader`); apenas os logs normais de `PLAYER_VIDEO_DEBUG` da midia visivel.

## Evidencias de teste

- Ambiente: desenvolvimento local (Vitest, jsdom, `react-dom/client` + `act` para render real de componentes).
- Build/commit: branch `fix/dev-env`, alteracoes em `frontend/src/components/player/MediaRenderer.jsx`, `frontend/src/pages/Player.jsx`, `frontend/src/__tests__/media_renderer.test.jsx`.
- Data: 2026-06-18.
- Resultado: 7/7 testes novos passando; 68/68 testes relacionados sem regressao; 147/150 na suite completa (3 falhas pre-existentes e nao relacionadas).
- Observacoes: validacao visual em hardware real de loja (TM014-01/02/03) depende de ambiente fisico e nao foi executada nesta sessao.
