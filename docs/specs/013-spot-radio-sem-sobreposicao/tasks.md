# SPEC 013 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 012 concluida — gate liberado.

## Diagnostico

- [x] Localizar enum de politica de insercao: `AudioSpotInsertionPolicy` em `backend/core/models.py:756-759` (`interrupt`, `wait_silence`, `fade_mix`).
- [x] Localizar resolver de elegibilidade backend: `backend/services/spot_resolver.py` e `backend/services/audio_spot_scheduler.py` — confirmados como apenas elegibilidade/intervalo, sem logica de overlap (correto, responsabilidade e do client).
- [x] Localizar implementacao real no player: `frontend/src/lib/audioManager.js playSpot()`.
- [x] Confirmar o bug: branch `wait_silence` fazia fade-out e tocava imediatamente, igual a `interrupt` — nunca esperava o evento `ended` da musica.
- [x] Localizar os dois call sites: `frontend/src/pages/Player.jsx:1544` (player principal) e `frontend/src/pages/PlayerAudio.jsx:203` (pagina secundaria).
- [x] Confirmar que `isSpotPlaying()` so previne spot-sobre-spot, nao protege contra spot tocando junto com radio.
- [x] Confirmar que nao havia testes automatizados cobrindo ausencia de overlap (so cobertura de presenca do campo).

## Backend

- [x] Nenhuma alteracao necessaria — enum, schema e resolvers ja adequados.
- [x] Decisao registrada: nao renomear enum para nomenclatura do documento original (sem ganho funcional, custo de migration).

## Player

- [x] Adicionar `_pendingSpot` e `_isBackgroundActivelyPlaying()` ao `AudioManager`.
- [x] `playSpot()`: politica `wait_silence` represa o spot quando o fundo esta ativo, em vez de tocar imediatamente.
- [x] `_onTrackEnded('radio')`: consome `_pendingSpot` (via `_playPendingSpotThenAdvance`) antes de avancar normalmente.
- [x] `_playPendingSpotThenAdvance()`: avanca `radioIndex`, toca o spot represado, com fallback para `_playRadioByIndex()` se o spot falhar ao tocar.
- [x] `_handleRadioTrackFailure()`: consome `_pendingSpot` quando a faixa falha (fundo ja silencioso) em vez de deixar o spot preso.
- [x] `silence()`: limpa `_pendingSpot` para evitar disparo indevido apos silenciar deliberadamente.
- [x] Log `SPOT_QUEUED` ao represar.
- [x] Confirmado: `interrupt` e `fade_mix` mantem comportamento original (tocam imediatamente).

## Testes

- [x] `'interrupt' toca o spot imediatamente mesmo com a musica ainda audivel`.
- [x] `'wait_silence' NAO toca o spot por cima da musica ativa — represa como _pendingSpot`.
- [x] `'wait_silence' toca o spot represado quando a musica atual emite 'ended'`.
- [x] `'wait_silence' toca o spot imediatamente quando o fundo ja esta em silencio (pausado)`.
- [x] `'fade_mix' toca o spot imediatamente e reduz volume do fundo (ducking)`.
- [x] Suite completa `audio_manager.test.js`: 29/29 passando (23 pre-existentes + 6 novos).
- [x] Suites relacionadas sem regressao: `audio_conflict_resolver.test.jsx`, `spotScheduleResolver.test.js`, `osd_audio_player.test.jsx` (17 testes, todos passando).
- [ ] Teste end-to-end real (Playwright/hardware) com captura de audio fisico — nao executado nesta SPEC; cobertura atual e unitaria com mocks de `<audio>`.

## Criterios de aceite

- [x] Spot nao mistura com musica no modo padrao (`wait_silence`) — validado por teste unitario.
- [x] Spot aguarda a musica terminar no modo padrao — validado por teste unitario (`'ended'` dispara o spot represado).
- [x] Radio retoma corretamente apos spot — `radioIndex` avanca antes do spot tocar, `_resumeAfterSpot` usa o indice atualizado.
- [x] Logs mostram a decisao do player — `SPOT_QUEUED` emitido ao represar.
- [x] Nao ha loop infinito de spot represado — `_pendingSpot` e sempre consumido (no `ended`, no `error` do fundo, ou limpo em `silence()`).
- [x] Nao ha dois audios tocando ao mesmo tempo fora do modo `fade_mix` — `wait_silence` so toca quando `_isBackgroundActivelyPlaying` e falso.

## Riscos e pendencias

- [ ] Validar em ambiente real (Windows/Electron com hardware de audio) que o `ended` do elemento `<audio>` de radio dispara de forma confiavel para arquivos hospedados no CDN do PlayWave — testes atuais usam mocks.
- [ ] Se no futuro a radio passar a usar streaming continuo (sem fim de faixa natural), `_pendingSpot` precisaria de um timeout de seguranca — nao aplicavel hoje (faixas sao arquivos finitos).
