# SPEC 015 — Player

Status: implementada

## Comportamento esperado

### contentGuard

`frontend/src/player-core/contentGuard.js` expoe:

- `update({ phase, hasPlaylist, endsAt })` — chamado por `Player.jsx` toda vez que a fase ou a midia atual muda. `endsAt` (timestamp absoluto em ms) e calculado quando a midia tem `duration` configurada; `null` para video/audio de duracao natural.
- `isContentBusy()` — `true` apenas quando `phase === "playing"` e `hasPlaylist === true`.
- `getRemainingMs()` — estimativa do tempo restante, ou `null` quando desconhecido/sem conteudo ativo. Informativo (logs/diagnostico), nao usado para decidir o disparo.
- `notifyContentEnded()` — chamado por `Player.jsx` dentro de `advanceMedia()`, no inicio da funcao, antes de qualquer outra logica de avanco. Dispara e limpa todos os callbacks represados.
- `onceContentEnd(callback)` — se nao ha conteudo ativo, chama `callback` na hora. Se ha, guarda o callback para ser disparado no proximo `notifyContentEnded()`. Retorna funcao de cancelamento.

### Integracao em Player.jsx

- `contentGuardRef = useRef(createContentGuard())` — instancia unica por sessao do player, criada uma vez.
- No efeito de progresso/avanco de midia (`useEffect` que controla `progress`/`startTimeRef`), `contentGuardRef.current.update(...)` e chamado em todos os caminhos: fora da fase `playing`, com duracao natural, e com duracao configurada (calculando `endsAt`).
- `advanceMedia()` chama `contentGuardRef.current.notifyContentEnded()` como primeira linha — cobre os tres motivos de avanco: timer de duracao expirado, `onEnded` nativo do `<video>`/`<audio>` (via `MediaRenderer`), e falha de midia (`handleMediaError` → `advanceMedia("failed:...")`).
- Os dois `useEffect` que criam `windowExposureScheduler`/`desktopExposureTimeScheduler` passam `contentGuard: contentGuardRef.current` e `onWarning: handleMinimizeWarning`.
- `handleMinimizeWarning` (`useCallback`) seta o estado `minimizeWarning` com `{ secondsBefore, text, mediaId, shownAt }`.
- Um `useEffect` dedicado limpa `minimizeWarning` automaticamente apos `max(secondsBefore, 5)` segundos.
- O JSX renderiza um overlay simples (`<div>` com texto, posicionado no rodape) quando `minimizeWarning` esta preenchido, na fase `playing`.

### Schedulers

Ambos os schedulers (`windowExposureScheduler.js`, `desktopExposureTimeScheduler.js`) seguem o mesmo padrao no momento do disparo:

1. Se nao ha `contentGuard` configurado, minimiza imediatamente (comportamento legado, usado por testes/instancias sem essa dependencia).
2. Se a config/evento tem `show_warning` ativo e `onWarning` foi fornecido, chama `onWarning(...)` com os campos resolvidos.
3. Se `contentGuard.isContentBusy()`, apenas loga que vai esperar (informativo).
4. Em qualquer caso, registra `contentGuard.onceContentEnd(runMinimize)` — se nao havia conteudo ativo, o callback roda na hora (graças ao comportamento de `onceContentEnd` quando ocioso); se havia, fica represado.
5. `stop()` cancela a inscricao pendente (`cancelWaitForEnd()`), evitando minimizacao tardia apos o scheduler ser parado/reagendado.

## Logs

Reaproveitados os logs existentes de cada scheduler (`[windowExposureScheduler] ...`, `[desktopExposureTime] ...`), com uma linha nova quando a espera por fim de conteudo comeca:

- `[windowExposureScheduler] conteúdo ativo — aguardando fim antes de minimizar`
- `[desktopExposureTime] conteúdo ativo — aguardando fim antes de minimizar <nome do evento>`

Nenhum log novo foi necessario no `contentGuard` em si — ele e uma estrutura de dados pura, sem efeitos colaterais de log; quem loga e o scheduler que o consome.

## Checklist de auditoria

- [x] Conferir `frontend/src/player-core/windowExposureScheduler.js` (disparo por intervalo).
- [x] Conferir `frontend/src/player-core/desktopExposureTimeScheduler.js` (disparo por horario, maquina de estados).
- [x] Conferir `frontend/src/pages/Player.jsx` — efeito de progresso/avanco de midia, `advanceMedia`, criacao dos dois schedulers.
- [x] Confirmar que `advanceMedia` e chamado tanto pelo timer quanto pelo `onEnded` do `MediaRenderer` (cobertura completa do "conteudo terminou").
- [x] Confirmar que `contentGuard` nao precisa saber nada sobre Electron/comandos — mantido como modulo puro e testavel isoladamente.
