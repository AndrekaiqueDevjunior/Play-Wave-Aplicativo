# SPEC 013 — Requirements

Status: implementada
Data: 2026-06-17

## Contexto

Cliente reportou que o spot da radio nao aguarda a musica terminar — em alguns casos toca por cima da musica, misturando o som. O sistema ja possuia um campo de politica de insercao (`insertion_policy`), mas o modo "esperar silencio" nao esperava de fato: fazia fade-out do fundo e tocava o spot na mesma chamada, sem checar se a musica ainda estava ativa.

## Objetivo

O spot deve obedecer a politica configurada, com padrao seguro: nao misturar audio, nao tocar por cima da musica, aguardar o fim da musica (ou fazer fade controlado, conforme politica) e retomar a radio corretamente apos o spot.

## Regra de negocio

Politica padrao: `wait_silence` (equivalente a `WAIT_TRACK_END` do documento original).

Politicas suportadas (nomenclatura real do codigo, mantida sem migration):

1. `wait_silence` — aguarda o fim da faixa atual (evento `ended`) antes de tocar o spot. Se o fundo ja estiver pausado/em silencio quando o spot for solicitado, toca imediatamente.
2. `interrupt` — interrompe a musica com fade-out e toca o spot imediatamente (equivalente a `INTERRUPT_WITH_FADE`).
3. `fade_mix` — reduz o volume da musica (ducking, 25%) e toca o spot por cima, apenas quando explicitamente configurado (equivalente a `DUCKING`).

Nao existe modo `IMMEDIATE` separado — `interrupt` cobre o caso de tocar sem esperar.

## Requisitos funcionais

### RF013-01 — Sem sobreposicao no modo padrao

Quando `insertion_policy = wait_silence` e a musica de fundo esta ativa (nao pausada, nao terminada), o spot NAO deve iniciar imediatamente.

Criterios:

- O spot e represado (`_pendingSpot`) em vez de tocado.
- Nenhum `play()` e chamado no elemento de spot enquanto a musica esta ativa.
- O estado do AudioManager permanece `RADIO` (ou `MEDIA_AUDIO`) durante a espera.

### RF013-02 — Disparo no fim da faixa

Quando a faixa de fundo emite `ended`, se houver spot represado, ele deve tocar antes de avancar para a proxima faixa da fila.

Criterios:

- `_pendingSpot` e consumido e tocado no handler de `ended`.
- A fila de radio avanca para a proxima faixa (`radioIndex++`) antes/durante o spot, garantindo que ao retomar a radio toque a faixa seguinte, nao a mesma que acabou de terminar.
- Apos o spot terminar, a radio retoma normalmente (fluxo `_resumeAfterSpot` existente).

### RF013-03 — Fallback sem deadlock

Se a faixa de fundo falhar (evento `error`) em vez de terminar naturalmente, o spot represado deve tocar mesmo assim — o fundo ja esta silencioso, entao a janela de oportunidade do `wait_silence` foi alcancada.

Criterios:

- `_handleRadioTrackFailure` verifica `_pendingSpot` e o consome antes de pular para a proxima faixa.
- Nenhum spot fica represado indefinidamente.

### RF013-04 — Politicas `interrupt` e `fade_mix` inalteradas

As politicas que ja tocavam imediatamente continuam tocando imediatamente (nao houve regressao).

Criterios:

- `interrupt`: fade-out do fundo, depois toca o spot, sem importar se a musica estava ativa.
- `fade_mix`: musica continua tocando com volume reduzido (0.25) durante o spot.

### RF013-05 — Nunca dois audios tocando ao mesmo tempo (fora de `fade_mix`)

Fora do modo `fade_mix` (ducking explicito), o player nunca deve ter radio e spot audiveis simultaneamente em volume normal.

Criterios:

- `wait_silence` so toca o spot quando o fundo esta pausado/terminado.
- `interrupt` faz fade-out (silencia) o fundo antes do `play()` do spot.

## Compatibilidade

- Nao alterar nomes do enum `AudioSpotInsertionPolicy` no backend (`interrupt`/`wait_silence`/`fade_mix`) — apenas corrigir o comportamento do player para `wait_silence`.
- Nao alterar contrato de `spot_resolver.py`/`audio_spot_scheduler.py` — eligibilidade continua sendo responsabilidade do backend; timing exato de playback e responsabilidade do player.
- Nao quebrar `PlayerAudio.jsx` (pagina secundaria que tambem chama `playSpot`) — o fix e no `AudioManager`, usado por ambos os call sites.

## Criterios de aceite

- [x] Spot nao mistura com musica no modo padrao (`wait_silence`).
- [x] Spot aguarda a musica terminar no modo padrao.
- [x] Radio retoma corretamente apos spot (avanca para a proxima faixa, nao repete a que terminou).
- [x] Logs mostram a decisao do player (`SPOT_QUEUED` quando represado).
- [x] Nao ha loop infinito de spot represado.
- [x] Nao ha dois audios tocando ao mesmo tempo fora do modo `fade_mix`.
