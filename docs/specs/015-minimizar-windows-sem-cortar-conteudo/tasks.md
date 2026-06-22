# SPEC 015 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [x] SPEC 014 concluida — gate liberado.

## Diagnostico

- [x] Auditar bridge Electron (`frontend/electron/main.js`) — `minimize_window`/`restore_window`/`show_desktop` ja implementados e corretos, sem mudanca necessaria.
- [x] Auditar `VALID_COMMANDS` no backend e roteamento em `frontend/src/player-core/commands.js` — `minimize_player`/`restore_player`/`show_desktop` ja existem e funcionam.
- [x] Auditar `Device` model — campos `desktop_exposure_enabled/interval_seconds/duration_seconds/restore_fullscreen` ja existem com endpoint PATCH funcional.
- [x] Auditar os dois schedulers client-side existentes: `windowExposureScheduler.js` (intervalo) e `desktopExposureTimeScheduler.js` (horario, maquina de estados com `recover()`).
- [x] Confirmar causa raiz: nenhum dos dois schedulers verificava se havia midia tocando antes de disparar a minimizacao.
- [x] Confirmar ausencia de campos de aviso visual (`show_warning`, `warning_seconds_before`, `warning_text`, `warning_media_id`) no model `Device`.

## Decisao de escopo (confirmada com o usuario)

- [x] Adaptar os schedulers existentes via dependencia opcional `contentGuard`, em vez de criar comandos `minimize_screen`/`restore_screen` novos — reaproveita toda a maquina de estados/persistencia/recovery ja testada.
- [x] Incluir o aviso visual configuravel nesta mesma SPEC (campos novos + migration + overlay), em vez de deixar para depois.

## Backend

- [x] Adicionar colunas `desktop_exposure_show_warning`, `desktop_exposure_warning_seconds_before`, `desktop_exposure_warning_text`, `desktop_exposure_warning_media_id` ao model `Device` (`backend/core/models.py`).
- [x] Estender a propriedade `desktop_exposure_config` para expor os novos campos.
- [x] Estender `DeviceDesktopExposureConfigUpdate`/`DeviceDesktopExposureConfig` (`backend/core/schemas_completos.py`) com validacao (`warning_seconds_before` 0-120, `warning_text` max 255).
- [x] Atualizar `update_device_desktop_exposure_config` (`backend/api/v1/devices.py`) para persistir os novos campos via PATCH parcial.
- [x] Criar migration aditiva `20260618_1100_desktop_exposure_warning.py` (ADD COLUMN + CHECK constraint), encadeada apos `20260607_1130` (head identificado na auditoria de multiplas heads do Alembic).

## Player

- [x] Criar `frontend/src/player-core/contentGuard.js` — modulo puro com `update`/`isContentBusy`/`getRemainingMs`/`notifyContentEnded`/`onceContentEnd`.
- [x] Adaptar `windowExposureScheduler.js` — parametros opcionais `contentGuard`/`onWarning`; le `warning_seconds_before` de `desktopExposureConfig` no momento do disparo (evita staleness de closure).
- [x] Adaptar `desktopExposureTimeScheduler.js` — parametros opcionais `contentGuard`/`onWarning`; separar `fire()` (gate de estado RUNNING + decisao de esperar) de `runMinimize()` (execucao real).
- [x] Integrar em `Player.jsx`: `contentGuardRef`, `update()` no efeito de progress/media-advance (3 caminhos: sem playlist, duracao natural, duracao configurada), `notifyContentEnded()` em `advanceMedia`.
- [x] Injetar `contentGuard`/`onWarning` nos dois `useEffect` que criam os schedulers.
- [x] Estado `minimizeWarning` + `useEffect` de auto-dismiss (`max(secondsBefore, 5)` segundos) + overlay JSX simples no rodape do player.
- [x] Remover `eslint-disable-next-line react-hooks/exhaustive-deps` desnecessarios introduzidos durante a implementacao (lint confirmou que nao eram necessarios).

## Frontend Gerenciador

- [x] Adicionar campos de aviso (`show_warning`, `warning_seconds_before`, `warning_text`) ao estado `desktopExposureConfig` em `DispositivoDetalhe.jsx`.
- [x] Sincronizar os novos campos a partir de `device.desktop_exposure_config` no `useEffect` existente.
- [x] Adicionar checkbox "Exibir aviso antes de minimizar" + inputs condicionais (segundos antes, texto do aviso) reaproveitando o card/mutation existente — sem criar formulario novo.
- [x] Atualizar o botao "Redefinir" para incluir os novos campos nos valores padrao.

## Testes

- [x] `contentGuard` — 14 testes unitarios (`content_guard.test.js`): `isContentBusy`, `onceContentEnd` (imediato/represado/multiplo/cancelamento/erro isolado), `getRemainingMs`.
- [x] `windowExposureScheduler` — 4 testes novos de integracao com `contentGuard` (espera conteudo ativo, dispara imediato sem conteudo, `onWarning`, `stop()` cancela espera) + 3 testes pre-existentes sem regressao.
- [x] `desktopExposureTimeScheduler` — 5 testes novos de integracao com `contentGuard` (compatibilidade sem guard, espera conteudo ativo, dispara imediato sem conteudo, `onWarning`, `stop()` cancela espera) + 13 testes pre-existentes sem regressao.
- [x] Backend — 3 testes novos em `test_device_desktop_exposure_config.py` (campos default, campos quando setados, persistencia via PATCH) + 1 teste de validacao de range + 4 testes pre-existentes preservados. Validados por analise de sintaxe (`ast.parse`) e revisao manual — `pytest` nao executavel neste ambiente (FastAPI nao instalado, sem venv do projeto disponivel).
- [x] Lint (`eslint`) de todos os arquivos frontend alterados — sem erros novos, apenas warnings pre-existentes confirmados via `git diff --stat` (linhas nao tocadas por esta SPEC).
- [x] Suite completa do frontend: 170/173 passando — as 3 falhas (`player_sse.test.js`, `playbackQueueManager.test.js`) sao pre-existentes e nao relacionadas, confirmadas em SPECs anteriores.

## Criterios de aceite

- [x] Minimizacao nao acontece no meio do video/conteudo — validado por teste automatizado.
- [x] Aviso aparece antes, quando configurado — validado por teste automatizado (`onWarning` chamado com os campos corretos) e UI de configuracao criada.
- [x] Janela minimiza/restaura corretamente no Windows — bridge Electron inalterado, ja validado em SPECs 009/010.
- [x] Gerenciador permite configurar o aviso — UI adicionada em `DispositivoDetalhe.jsx`.
- [ ] Validacao end-to-end real em hardware Windows com conteudo de duracao natural (video sem duration) — nao executada nesta sessao.
- [ ] Migration aplicada em producao (VPS) — pendente de deploy.

## Riscos e pendencias

- [ ] Deploy da migration `20260618_1100_desktop_exposure_warning` na VPS.
- [ ] Validar em campo se o timing do aviso (disparado no instante da decisao, nao N segundos antes do fim real) e aceitavel para o cliente, especialmente com video de duracao natural longa.
- [ ] Avaliar renderizacao real de `warning_media_id` como overlay de imagem/video (hoje so o texto e exibido) caso o cliente peca.
- [ ] Cenario raro de dois schedulers (intervalo + horario) represados simultaneamente disparando juntos — nao mitigado, ver `design.md`.
