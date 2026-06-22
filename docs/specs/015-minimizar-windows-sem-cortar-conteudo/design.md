# SPEC 015 — Design

Status: implementada

## Fluxo esperado (WAIT_CONTENT_END)

```text
windowExposureScheduler (intervalo) OU desktopExposureTimeScheduler (horario)
  -> chega o instante configurado (setTimeout dispara)
  -> scheduler chama contentGuard.isContentBusy()
       SE show_warning ativo na config/evento:
         -> onWarning({ secondsBefore, text, mediaId }) — Player.jsx exibe overlay
       SE conteudo ativo (fase playing + playlist nao vazia):
         -> contentGuard.onceContentEnd(runMinimize) — registra callback, NAO minimiza ainda
       SE conteudo OCIOSO:
         -> runMinimize() chamado direto (sem espera)
  -> Quando o conteudo atual termina de fato (advanceMedia em Player.jsx,
     chamado tanto pelo timer de duration quanto pelo onEnded do <video>):
       -> contentGuardRef.current.notifyContentEnded()
       -> dispara todos os callbacks represados (inclui o runMinimize pendente)
  -> runMinimize() executa o caminho ja existente (persist + executeShowDesktop
     + beginRestoreCountdown, ou executeCommand("show_desktop") + reschedule)
```

## Por que um `contentGuard` compartilhado, e nao logica duplicada em cada scheduler

Os dois schedulers (`windowExposureScheduler.js` por intervalo e `desktopExposureTimeScheduler.js` por horario) tem mecanismos de disparo completamente diferentes (um timer simples vs. uma maquina de estados com `recover()`), mas ambos precisam da MESMA decisao no momento do disparo: "ha conteudo tocando agora? se sim, espere." Em vez de duplicar essa logica (e o conhecimento de como o `Player.jsx` representa "conteudo tocando") em dois lugares, foi criado um modulo dedicado (`frontend/src/player-core/contentGuard.js`) que:

- Nao sabe nada sobre minimizar/Electron/comandos — apenas observa o estado de reproducao que o `Player.jsx` ja produz.
- Expoe uma API minima (`update`, `isContentBusy`, `getRemainingMs`, `notifyContentEnded`, `onceContentEnd`) que qualquer scheduler futuro pode consumir sem acoplamento.
- E instanciado uma unica vez por sessao do player (`contentGuardRef.current = createContentGuard()`) e injetado nos dois schedulers via parametro opcional — quem nao passar `contentGuard` mantem o comportamento antigo (minimiza imediatamente), garantindo retrocompatibilidade total com testes e usos existentes.

## Decisao tecnica: `onceContentEnd` baseado em evento real, nao em polling de tempo restante

A alternativa mais simples seria: calcular o tempo restante da midia atual (`getRemainingMs()`) e agendar um `setTimeout` extra para depois desse tempo. Essa abordagem foi descartada como mecanismo principal porque:

- Para midia de duracao natural (video/audio sem `duration` configurada), o tempo restante e desconhecido (`endsAt: null`) — nao ha como agendar um timeout preciso.
- Mesmo para midia com duracao conhecida, depender de um segundo timer paralelo ao timer real do `Player.jsx` (`advanceMedia` via `setTimeout(duration)`) cria risco de dessincronia (ex.: falha de rede atrasa o avanco real, mas o timer de minimizar dispara no horario "teorico").

Por isso `onceContentEnd` se inscreve para ser notificado pelo MESMO evento que o `Player.jsx` já usa internamente para avançar a playlist (`advanceMedia`), seja ele disparado por timer de duracao OU pelo `onEnded` nativo do elemento de video/audio. `getRemainingMs()` foi mantido na API do `contentGuard` como informacao auxiliar (ex.: para logs/diagnostico futuro), mas nao e o mecanismo que decide quando minimizar.

## Decisao tecnica: aviso visual disparado no instante da decisao, nao N segundos antes do fim real

O documento mestre descreve "X segundos antes do fim, exibe aviso visual". Implementar isso literalmente exigiria saber o instante exato em que o conteudo vai terminar — disponivel para midia com `duration` configurada (`endsAt` calculado), mas desconhecido para midia de duracao natural.

Em vez de ter dois comportamentos diferentes de aviso dependendo do tipo de midia (o que seria confuso e dificil de testar), o aviso e disparado no MESMO momento em que a decisao de minimizar é tomada (ao chegar o horario/intervalo configurado) — se o conteudo ainda esta tocando, o aviso aparece nesse instante e permanece visivel por `warning_seconds_before` segundos (minimo 5s), o que cobre razoavelmente o caso comum (midia com duracao configurada de alguns minutos) sem exigir logica condicional por tipo de midia. Essa simplificacao foi documentada explicitamente para que uma iteracao futura possa refina-la se o cliente achar o timing impreciso.

## Pontos de auditoria realizados

- [x] Confirmar bridge Electron completo (`frontend/electron/main.js:405-475`) — `minimize_window`/`restore_window`/`show_desktop` ja implementados e corretos.
- [x] Confirmar `VALID_COMMANDS` no backend ja inclui `minimize_player`/`restore_player`/`show_desktop` (nomes diferentes do documento mestre, mas equivalentes).
- [x] Confirmar `frontend/src/player-core/commands.js` ja roteia esses comandos para a bridge nativa.
- [x] Confirmar UI do gerenciador (`deviceCommands.js`) ja tem grupo "window" com os comandos.
- [x] Confirmar `Device` model ja tem `desktop_exposure_*` (enabled/interval/duration/restore_fullscreen) com endpoint PATCH funcional.
- [x] Confirmar os dois schedulers existentes (`windowExposureScheduler.js`, `desktopExposureTimeScheduler.js`) e como sao instanciados/agendados em `Player.jsx`.
- [x] Confirmar que nenhum dos dois verificava estado de reproducao antes de disparar — causa raiz do bug.
- [x] Confirmar como `Player.jsx` rastreia "conteudo tocando" (`phase`, `playlist`, `currentIndex`, `startTimeRef`, `advanceMedia`) para desenhar o `contentGuard` em torno desses sinais existentes, sem reinventar estado novo.

## Arquivos impactados

- `frontend/src/player-core/contentGuard.js` — novo modulo (politica WAIT_CONTENT_END).
- `frontend/src/player-core/windowExposureScheduler.js` — parametros opcionais `contentGuard`/`onWarning`, gate antes de `runExposure`.
- `frontend/src/player-core/desktopExposureTimeScheduler.js` — parametros opcionais `contentGuard`/`onWarning`, `fire()` separado de `runMinimize()`.
- `frontend/src/pages/Player.jsx` — instancia `contentGuardRef`, atualiza o guard na troca de midia, notifica fim de conteudo em `advanceMedia`, injeta `contentGuard`/`onWarning` nos dois schedulers, overlay de aviso.
- `backend/core/models.py` — campos novos em `Device` (`desktop_exposure_show_warning`, `desktop_exposure_warning_seconds_before`, `desktop_exposure_warning_text`, `desktop_exposure_warning_media_id`) e propriedade `desktop_exposure_config` atualizada.
- `backend/core/schemas_completos.py` — `DeviceDesktopExposureConfigUpdate`/`DeviceDesktopExposureConfig` com os novos campos.
- `backend/api/v1/devices.py` — endpoint PATCH persiste os novos campos.
- `backend/alembic/versions/20260618_1100_desktop_exposure_warning.py` — migration aditiva.
- `frontend/src/pages/DispositivoDetalhe.jsx` — UI de configuracao do aviso (checkbox `show_warning` + campos `warning_seconds_before`/`warning_text`), reaproveitando o mesmo card/mutation que ja configura intervalo/duracao/restore_fullscreen.
- `frontend/src/__tests__/content_guard.test.js` — testes novos do modulo `contentGuard`.
- `frontend/src/__tests__/window_exposure_scheduler.test.js` / `desktop_exposure_time_scheduler.test.js` — testes novos de integracao com `contentGuard`.
- `backend/tests/test_device_desktop_exposure_config.py` — testes novos dos campos de aviso.

Nao foram necessarias mudancas em:

- `frontend/electron/main.js` / `preload.js` — bridge ja correta.
- `frontend/src/player-core/commands.js` — roteamento de comando ja correto.
- `frontend/src/utils/deviceCommands.js` — UI de comandos manuais ja existente, sem mudanca necessaria.

## Riscos

- O aviso visual nao tem garantia de aparecer exatamente N segundos antes do fim real para midia de duracao natural (ver decisao tecnica acima) — pode aparecer mais cedo que o ideal nesses casos. Mitigado: o overlay fica visivel por tempo suficiente e o comportamento e documentado como simplificacao deliberada.
- Se dois schedulers (intervalo + horario) tiverem disparos represados simultaneamente esperando o mesmo `notifyContentEnded()`, ambos serao liberados juntos — o segundo a executar pode encontrar o `state` do primeiro scheduler ja em `MINIMIZING`/`MINIMIZED` e logar/pular adequadamente (comportamento pre-existente, nao alterado por esta SPEC).
- `warning_media_id` foi adicionado como UUID solto (sem `ForeignKey`) por simplicidade — se uma midia referenciada for excluida, o campo continua apontando para um id inexistente sem erro. Aceitavel porque o player hoje so usa o texto do aviso, nao a midia.
- Migration aditiva pendente de deploy na VPS — sem isso, o backend antigo continua servindo `desktop_exposure_config` sem os campos novos (frontend trata `show_warning: undefined` como falso, sem quebrar).
