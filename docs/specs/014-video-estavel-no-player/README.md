# SPEC 014 — Video Estavel no Player

Status: implementada — diagnostico e correcao concluidos, testes automatizados passando
Data: 2026-06-18
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-008)

## Objetivo

Garantir que o player reproduza video de forma fluida, sem travamentos/picotamentos perceptiveis na troca de midia, mesmo quando o mesmo arquivo roda bem no preview do gerenciador.

## Regra de sequenciamento

Esta SPEC entrou em implementacao apos a `SPEC 013 — Spot da Radio sem Sobreposicao` ser concluida (29/29 testes unitarios passando).

## Diagnostico resumido

O documento mestre listava 12 hipoteses tecnicas. A auditoria do codigo real confirmou 3 causas concretas e descartou as demais:

**Confirmadas e corrigidas nesta SPEC:**

1. **Sem preload da proxima midia** — o player so comecava a baixar o video/imagem seguinte no instante exato da troca. Em conexao lenta ou arquivo grande, isso aparece como tela preta/buffering nos primeiros segundos de cada item.
2. **`MediaRenderer` sem memoizacao** — o componente nao era `React.memo`, entao qualquer re-render do `Player.jsx` (heartbeat 30s, spot tick 5s, resolver de radio 60s) recalculava `renderContent()` e reanexava os listeners de video, mesmo quando midia/progresso nao tinham mudado de fato.
3. **Risco de competicao por frames** — `Player.jsx` atualizava `progress` via `setState` a cada 250ms, forcando re-render de toda a arvore (~1700 linhas) inclusive quando isso nao precisava afetar o elemento `<video>`.

**Descartadas (ja corretas, sem evidencia de problema):**

- HTTP Range Requests: backend ja suporta (206 Partial Content, `Accept-Ranges: bytes`, `Cache-Control` de 7 dias) — `backend/main.py:137-174`.
- Metadata de video: `duration_seconds`, `resolution`, `has_audio`, `mime_type` ja sao extraidos via ffprobe no upload (`backend/api/v1/media.py`). Faltam `bitrate`/`fps` dedicados, mas estao disponiveis em `extra_metadata` (ffprobe completo) — nao e a causa do travamento relatado, fora de escopo.
- Hardware acceleration no Electron: nenhuma flag desabilita GPU (`app.disableHardwareAcceleration()` ausente) — Electron usa aceleracao por padrao, sem regressao identificada.
- `window.location.reload()`: nao ha chamada no caminho de execucao normal do player (so em fluxos de erro/reparo).
- Remount do `<video>` por `key={media.id}`: e necessario e correto (troca real de conteudo) — o problema nao era o remount em si, mas a ausencia de preload antes dele.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho tecnico do preload e da memoizacao.
- `api-contract.md` — confirmacao de que nao houve mudanca de contrato backend.
- `player.md` — comportamento do `MediaRenderer`/`Player.jsx`.
- `tasks.md` — backlog executado.
- `tests.md` — plano de testes e evidencias.

## Fora de escopo

- Adicionar `bitrate`/`fps` como colunas dedicadas no model `Media` (hoje em `extra_metadata`).
- Tunar flags de GPU/hardware acceleration no Electron — nenhuma evidencia de regressao.
- Endpoint de diagnostico de midia dedicado (sugerido no documento mestre) — pode ser avaliado em uma SPEC futura se o preload nao for suficiente.
- SPEC 015 (Minimizar Windows sem Cortar Conteudo) — depende desta SPEC estar concluida.
