# SPEC 015 — Minimizar Windows sem Cortar Conteudo

Status: implementada — testes automatizados de frontend passando, testes backend nao executaveis neste ambiente (sem fastapi instalado), deploy/migration pendente
Data: 2026-06-18
Projeto: PlayWave
Origem: `SPEC DRIVEN DEVELOPMENT/2026-06-correcoes-player-radio-windows.md` (SPEC-007)

## Objetivo

Garantir que a minimizacao programada da janela no Windows espere o conteudo atual (video/campanha/playlist) terminar antes de minimizar — politica padrao `WAIT_CONTENT_END` — em vez de cortar no meio, com aviso visual configuravel opcional antes de minimizar.

## Regra de sequenciamento

Esta SPEC entrou em implementacao apos a `SPEC 014 — Video Estavel no Player` ser concluida (7/7 testes novos + 68/68 relacionados passando).

## Diagnostico resumido

Diferente das SPECs 011-014, esta funcionalidade ja tinha bastante infraestrutura parcial implementada (SPEC 009 e SPEC 010 do historico do projeto):

**Ja existia e funcionava (mantido sem alteracao):**

- Bridge Electron completo: `ipcMain.handle("player:minimize_window"/"restore_window"/"show_desktop")` em `frontend/electron/main.js`, com preservacao de estado kiosk/fullscreen.
- Comando `show_desktop` no backend (`VALID_COMMANDS`), aceito e roteado pelo player (`frontend/src/player-core/commands.js`).
- Configuracao por device (`desktop_exposure_enabled/interval_seconds/duration_seconds/restore_fullscreen`) com endpoint `PATCH /devices/{id}/desktop-exposure-config`.
- Dois schedulers client-side ja maduros e testados:
  - `windowExposureScheduler.js` (SPEC 009) — dispara por **intervalo** fixo.
  - `desktopExposureTimeScheduler.js` (SPEC 010) — dispara por **horario do dia**, com maquina de estados e `recover()` que sobrevive a restart do player.

**Faltava (causa real do bug relatado pelo cliente):**

- Nenhum dos dois schedulers verificava se havia midia tocando no momento exato do disparo — ambos minimizavam imediatamente ao chegar a hora/intervalo configurado, cortando video/campanha no meio.
- Nao existia campo de politica (`WAIT_CONTENT_END` nem qualquer outra) — o comportamento era sempre "imediato".
- Nao existiam campos de aviso visual (`show_warning`, `warning_seconds_before`, `warning_media_id`, `warning_text`) no model `Device` nem UI/overlay correspondente.

## Decisao de escopo (confirmada com o usuario)

Em vez de criar comandos novos `minimize_screen`/`restore_screen` do zero (como o documento mestre descreve literalmente), foi adaptada a infraestrutura existente: os dois schedulers (`windowExposureScheduler.js` e `desktopExposureTimeScheduler.js`) passaram a aceitar uma dependencia opcional `contentGuard` que implementa a politica `WAIT_CONTENT_END`. Isso reaproveita toda a maquina de estados, persistencia (`PlayerState`) e logica de sobrevivencia a restart que ja existiam e ja estavam testados em producao, em vez de duplicar essa logica em um terceiro sistema paralelo.

O aviso visual configuravel foi incluido nesta mesma SPEC (campos novos no `Device` + migration + overlay simples no player), conforme decisao do usuario.

## Documentos

- `requirements.md` — requisitos funcionais, regras e aceite.
- `design.md` — desenho tecnico do `contentGuard` e integracao com os schedulers.
- `api-contract.md` — novos campos de `desktop_exposure_config` (aviso visual).
- `player.md` — comportamento do `contentGuard`/`Player.jsx`/overlay de aviso.
- `tasks.md` — backlog executado.
- `tests.md` — plano de testes e evidencias.

## Fora de escopo

- Criar comandos `minimize_screen`/`restore_screen` como entidades separadas de `show_desktop`/`minimize_player`/`restore_player` — reaproveitado o caminho existente.
- Resolver `desktop_exposure_events` (agenda por horario) viajando do backend — o array de eventos ja e gerenciado client-side via `PlayerState`; nenhuma mudanca de contrato nesse ponto foi necessaria para o fix do WAIT_CONTENT_END.
- Selecionar uma midia real (`warning_media_id`) para exibir como arte de aviso — o campo existe no banco/contrato, mas o player hoje so renderiza um overlay de texto simples; resolver a midia por id e renderiza-la fica para uma iteracao futura caso o cliente peça.
- SPEC 016 (Faixas de Audio Arquivar/Excluir) — depende desta SPEC estar concluida.
