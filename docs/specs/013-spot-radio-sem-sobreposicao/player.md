# SPEC 013 — Player

Status: implementada

## Comportamento esperado

Ao um spot ficar elegivel (`Player.jsx` tick de 5s ou `PlayerAudio.jsx` tick de 30s) e `AudioManager.playSpot(url, policy, spotItem)` ser chamado:

1. Se ja ha outro spot tocando (`isSpotPlaying()`), ignora (guard pre-existente, inalterado).
2. Se o `spotId` esta em quarentena por falha recente, ignora (guard pre-existente, inalterado).
3. Resolve `bgPlayer` (radio ou media de acordo com o estado anterior).
4. **Novo**: se `policy === "wait_silence"` e `bgPlayer` esta ativo (`_isBackgroundActivelyPlaying`), represa o spot em `_pendingSpot` e retorna sem tocar.
5. Caso contrario, segue o fluxo de sempre: aplica a politica (`interrupt` faz fade-out; `wait_silence` com fundo ja parado so confirma volume zero; `fade_mix` reduz volume para 0.25), registra handler de `ended`/`error` no elemento de spot, carrega a URL e toca via `_fadeIn` (com watchdog).

Quando a faixa de fundo emite `ended`:

- Se `_pendingSpot` existe, `_playPendingSpotThenAdvance()` avanca `queue.radioIndex` e chama `playSpot` de novo — agora o fundo esta `ended=true`, entao cai direto no fluxo normal de tocar.
- Caso contrario, segue o fluxo original (`nextTrack()`).

Quando a faixa de fundo falha (`error`, nao `ended` natural):

- `_handleRadioTrackFailure` agora tambem verifica `_pendingSpot` e o consome antes do skip normal — o fundo ja esta silencioso (falhou), entao e seguro tocar o spot represado nesse momento.

## Estado interno novo

- `AudioManager._pendingSpot`: `null` ou `{ spotUrl, insertionPolicy, spotItem }`. Limpo em: inicio de `_playPendingSpotThenAdvance`, e em `silence()` (evita disparo de spot apos silenciar deliberadamente, ex: troca de pasta agendada sem midia).

## Logs

- `SPOT_QUEUED` — novo evento, emitido quando o spot e represado (`reason: "wait_track_end"`).
- `PLAY_REQUEST` / `PLAY_SUCCESS` / `PLAY_REJECTED` / `PLAY_TIMEOUT` — eventos existentes do watchdog, continuam disparando normalmente quando o spot represado finalmente toca.

Eventos do documento original (`SPOT_ELIGIBLE`, `SPOT_STARTED`, `SPOT_FINISHED`, `RADIO_RESUMED`, `SPOT_SKIPPED_REASON`) nao foram criados como eventos dedicados — o log estruturado existente (`_logAudio`) e os eventos de estado (`_notify({ current: ... })`) ja cobrem a mesma informacao de forma consistente com o padrao de logging ja usado no `AudioManager`. Adicionar nomes de evento extras sem consumidor real seria trabalho nao utilizado.

## Checklist de auditoria

- [x] Conferir `frontend/src/lib/audioManager.js` (`playSpot`, `_onTrackEnded`, `isSpotPlaying`).
- [x] Conferir os dois call sites: `frontend/src/pages/Player.jsx:1544` e `frontend/src/pages/PlayerAudio.jsx:203`.
- [x] Confirmar que nenhum dos dois precisa mudar — a fila/retry de cada um ja e compativel com "a chamada pode nao tocar imediatamente".
- [x] Confirmar que `playMediaAudio` ja bloqueia quando ha spot tocando (`if (this.state.current === AUDIO_STATE.SPOT) return;`) — sem mudanca necessaria.
