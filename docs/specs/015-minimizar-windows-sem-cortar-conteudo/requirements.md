# SPEC 015 — Requirements

Status: implementada
Data: 2026-06-18

## Contexto

Cliente reportou que a funcao de minimizar tela no Windows e necessaria para uso em loja, mas minimiza por cima dos conteudos, sem esperar o termino do que esta passando. A auditoria confirmou que os dois schedulers existentes (`windowExposureScheduler.js` por intervalo, `desktopExposureTimeScheduler.js` por horario) disparavam a minimizacao imediatamente ao chegar a hora configurada, sem checar se havia midia tocando.

## Objetivo

A minimizacao programada deve respeitar o conteudo atual: se houver midia tocando, espera o fim antes de minimizar (politica padrao `WAIT_CONTENT_END`). Opcionalmente, exibe um aviso visual configuravel alguns segundos antes.

## Requisitos funcionais

### RF015-01 — Nunca minimizar no meio do conteudo

Quando o horario/intervalo de minimizacao chega e ha midia tocando (fase `playing` com playlist nao vazia), a minimizacao deve ser represada até o conteudo atual terminar.

Criterios:

- Nenhuma chamada a `show_desktop` (e portanto nenhuma chamada a `mainWindow.minimize()`) ocorre enquanto o conteudo atual esta ativo.
- Quando o conteudo termina (evento real de avanco de midia, nao um timer arbitrario), a minimizacao represada e executada.
- Funciona tanto para midia com duracao configurada (timer) quanto para video/audio de duracao natural (evento `ended`).

### RF015-02 — Minimizar imediatamente quando nao ha conteudo protegido

Fora da fase `playing` (ex.: tela de pareamento, loading) ou com playlist vazia (apenas radio, sem midia visual), a minimizacao deve ocorrer imediatamente no horario/intervalo configurado, sem espera artificial.

Criterios:

- `contentGuard.isContentBusy()` retorna falso nesses casos e a minimizacao nao e represada.

### RF015-03 — Aviso visual configuravel antes de minimizar

Quando a configuracao tiver `show_warning=true`, um aviso deve ser exibido antes da minimizacao efetiva.

Criterios:

- Novos campos em `desktop_exposure_config`: `show_warning` (bool), `warning_seconds_before` (int, 0-120), `warning_text` (string opcional), `warning_media_id` (uuid opcional, sem FK).
- O aviso e disparado no mesmo instante em que a minimizacao seria represada (ou imediatamente, se nao houver conteudo ativo) — nao exatamente "N segundos antes do fim real", pois para midia de duracao natural o fim exato e desconhecido de antemao (ver `design.md` para a justificativa dessa simplificacao deliberada).
- O player exibe um overlay com o texto configurado (ou um texto padrao) por, no minimo, 5 segundos ou `warning_seconds_before`, o que for maior.

### RF015-04 — Compatibilidade retroativa

Schedulers que nao recebem `contentGuard` (ex.: testes antigos, uso futuro fora do Player) continuam minimizando imediatamente no horario/intervalo, sem quebrar.

Criterios:

- `contentGuard` e `onWarning` sao parametros opcionais (default `null`) em ambos os schedulers.
- Todos os testes existentes (sem `contentGuard`) continuam passando sem alteracao.

### RF015-05 — Cancelamento limpo

Se o scheduler for parado (`stop()`) ou reagendado (`schedule()` chamado de novo) enquanto espera o fim do conteudo, a espera pendente deve ser cancelada sem disparar a minimizacao depois.

Criterios:

- `stop()` cancela a inscricao pendente em `contentGuard.onceContentEnd`.
- Nenhuma minimizacao "atrasada" dispara depois que o scheduler foi parado/reagendado.

## Compatibilidade

- Nao alterar o bridge Electron (`frontend/electron/main.js`) — minimize/restore/show_desktop ja funcionam corretamente, o bug era inteiramente de timing no lado do scheduler.
- Nao alterar o comando `show_desktop` nem seu payload (`duration_seconds`, `restore_fullscreen`).
- Nao remover nem renomear `desktop_exposure_enabled/interval_seconds/duration_seconds/restore_fullscreen` — apenas adicionar campos novos.
- Migration aditiva (`ADD COLUMN`), sem alterar colunas existentes.

## Criterios de aceite

- [x] Minimizacao nao acontece no meio do video/conteudo — validado por teste automatizado (`contentGuard` + ambos os schedulers).
- [x] Scheduler espera o conteudo terminar antes de minimizar.
- [x] Aviso aparece antes, quando configurado — validado por teste automatizado (`onWarning` chamado com os campos corretos).
- [x] Sem conteudo ativo, minimiza imediatamente (sem espera artificial).
- [x] `stop()` cancela espera pendente sem disparar minimizacao tardia.
- [ ] Janela minimiza/restaura corretamente no Windows real — depende do bridge Electron existente, ja validado em SPECs anteriores (009/010), nao re-testado em hardware nesta sessao.
- [ ] Migration aplicada em producao (VPS) — pendente de deploy.
