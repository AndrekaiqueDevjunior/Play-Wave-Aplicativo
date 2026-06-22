# SPEC 013 — Design

Status: implementada

## Fluxo esperado (politica `wait_silence`)

```text
Spot fica elegivel (backend resolve via spot_resolver / spotScheduleResolver)
  -> Player chama AudioManager.playSpot(url, "wait_silence", spotItem)
  -> AudioManager verifica _isBackgroundActivelyPlaying(bgPlayer)
       SE fundo ativo (tocando, nao terminado):
         -> guarda { spotUrl, insertionPolicy, spotItem } em _pendingSpot
         -> loga SPOT_QUEUED
         -> retorna sem tocar (current permanece RADIO/MEDIA_AUDIO)
       SE fundo ja silencioso:
         -> segue fluxo normal (fadeOut + fadeIn do spot) imediatamente
  -> Quando a faixa de fundo emite 'ended' (_onTrackEnded):
       SE ha _pendingSpot:
         -> _playPendingSpotThenAdvance(): avanca radioIndex, consome
            _pendingSpot, chama playSpot novamente (agora fundo.ended=true,
            entao toca direto)
       SENAO:
         -> nextTrack() (fluxo original, sem spot pendente)
  -> Spot toca, emite 'ended' -> _resumeAfterSpot() retoma radio na faixa
     ja avancada
```

## Decisao tecnica: por que represar em vez de poll/aguardar no caller

A alternativa seria fazer o caller (`Player.jsx` tick ou `PlayerAudio.jsx checkSpots`) ficar tentando `playSpot` a cada poucos segundos até o fundo ficar livre. Isso ja era, na pratica, o comportamento anterior (e o bug): cada tentativa redisparava o fade-out e tocava o spot, entao nunca esperava de verdade.

Em vez disso, a logica de "esperar o fim" foi centralizada no `AudioManager` (`_pendingSpot` + listener de `ended`), porque:

- O `AudioManager` e o unico lugar que sabe o estado real dos elementos `<audio>` (paused/ended/src).
- Os dois callers (`Player.jsx` e `PlayerAudio.jsx`) ja chamam `playSpot` de forma "fire and forget" a cada tick — nenhum precisou mudar.
- Evita reintroduzir um timer duplicado de polling so para verificar "a musica acabou?".

## Pontos de auditoria realizados

- [x] Identificar enum real do backend: `AudioSpotInsertionPolicy` (`interrupt`, `wait_silence`, `fade_mix`) em `backend/core/models.py:756-759`.
- [x] Identificar resolver de elegibilidade: `backend/services/spot_resolver.py` (so resolve QUAIS spots, nao QUANDO tocar exatamente — correto, pois timing de playback e client-side).
- [x] Identificar scheduler: `backend/services/audio_spot_scheduler.py` (mesma responsabilidade: elegibilidade/intervalo, nao overlap de audio).
- [x] Identificar implementacao real no player: `frontend/src/lib/audioManager.js playSpot()` — tinha os 3 branches de policy, mas `wait_silence` nao esperava nada.
- [x] Identificar os dois callers: `frontend/src/pages/Player.jsx` (player principal, tick a cada 5s) e `frontend/src/pages/PlayerAudio.jsx` (pagina secundaria, tick a cada 30s).
- [x] Confirmar guard existente `isSpotPlaying()` so previne spot-sobre-spot, nao radio-sobre-spot ou spot-sobre-radio.

## Arquivos impactados

- `frontend/src/lib/audioManager.js` — fix principal: `_pendingSpot`, `_isBackgroundActivelyPlaying`, `playSpot` (branch `wait_silence`), `_onTrackEnded`, `_playPendingSpotThenAdvance`, `_handleRadioTrackFailure`, `silence`.
- `frontend/src/__tests__/audio_manager.test.js` — testes novos cobrindo represamento, disparo no `ended`, fallback de fundo ja pausado, e nao-regressao de `interrupt`/`fade_mix`.

Nao foram necessarias mudancas em:

- `backend/core/models.py` / `schemas_completos.py` — enum ja adequado.
- `backend/services/spot_resolver.py` / `audio_spot_scheduler.py` — elegibilidade ja correta.
- `frontend/src/pages/Player.jsx` / `PlayerAudio.jsx` — call sites de `playSpot` nao mudam de assinatura.
- `frontend/src/player-core/spotScheduleResolver.js` — resolve elegibilidade local, sem relacao com overlap de audio.

## Riscos

- Se o fundo (`bgPlayer`) nunca disparar `ended` (ex: radio com streaming continuo sem fim de faixa), o spot represado ficaria preso para sempre. Mitigado: faixas de radio do PlayWave sao arquivos finitos (`AudioTrack.file_url`), nao streaming continuo — `ended` sempre dispara ao fim do arquivo.
- Se `_pendingSpot` for sobrescrito por um segundo spot elegivel antes do primeiro tocar (ex: dois spots ficam elegiveis quase juntos), o spot mais antigo e perdido silenciosamente. Aceitavel: ambos os callers (`Player.jsx`/`PlayerAudio.jsx`) so chamam `playSpot` uma vez por tick e respeitam `interval_seconds`/prioridade — colisao exata e extremamente rara e nao critica (na pior hipotese, um spot e pulado em vez de tocar atrasado).
- Pendencia: nao ha teste end-to-end real (Playwright/hardware) validando ausencia de overlap em audio fisico — apenas testes unitarios do `AudioManager` com mocks de elemento `<audio>`.
