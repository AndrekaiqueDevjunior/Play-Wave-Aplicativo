# SPEC 010 — Exposição Temporária do Desktop por Horário (Player Windows)

Status: especificacao inicial
Data: 2026-06-03
Projeto: PlayWave

## Objetivo

Permitir que o administrador configure **horários específicos** (ex.: 08:00, 10:00, 14:00)
em que o Player Windows minimiza temporariamente para exibir a área de trabalho do Windows
e, após uma duração definida por evento, **retorna sozinho** à tela cheia, continuando a
campanha do ponto em que estava — **sem encerrar nem reiniciar** a campanha/playlist.

## Contexto

Alguns clientes precisam ver, em horários determinados, informações do desktop do PC (ERP,
sistema interno, dashboard local, navegador) sem encerrar a campanha do PlayWave. Hoje isso
exige intervenção manual.

A **SPEC 009** já entregou exposição de desktop **por intervalo** ("a cada X segundos,
minimiza por Y segundos") e a **primitiva de controle de janela no Electron** (`show_desktop`:
minimiza, agenda restauração, restaura fullscreen/kiosk a partir de um snapshot). A auditoria
em 2026-06-03 confirmou que essa primitiva é sólida e reutilizável.

Esta SPEC adiciona uma **função nova e independente**: disparo por **horário do dia**, com
**vários eventos nomeados** por dispositivo e **recuperação após reinício** do Player no meio
da contagem. A função por intervalo (SPEC 009) permanece intacta.

## Escopo

Esta SPEC cobre:

- Modelo de dados de **N eventos** de exposição por dispositivo (nome, horário HH:MM, duração, ativo);
- CRUD desses eventos no backend + propagação ao Player (playlist response + SSE);
- **Scheduler por horário** no Player (dispara no horário exato, suporta múltiplos eventos);
- **Persistência e recuperação** de exposição em andamento ao reiniciar o Player (CA-009);
- **Máquina de estados** explícita no Player;
- UI de administração para criar/listar/editar/remover eventos;
- **Log de execução** de cada exposição (CA-010).

Esta SPEC nao cobre:

- Exposição por intervalo (já entregue na SPEC 009 — coexiste);
- Android / Smart TV (sem `window.minimize()` — ver `009/LIMITACOES_PLATAFORMAS.md`);
- Config global por tenant ou por grupo de dispositivos (SPEC futura).

## Arquivos analisados

### Backend

- `backend/api/v1/devices.py` (config 009, `VALID_COMMANDS`, playlist response, SSE invalidation)
- `backend/core/schemas_completos.py` (`DeviceDesktopExposureConfig*`)
- `backend/alembic/versions/20260601_1800_desktop_exposure_config.py`

### Frontend / Player

- `frontend/electron/main.js` (IPC `player:show_desktop`, snapshot/restore) — **reutilizar**
- `frontend/electron/preload.js` (`__ELECTRON__.player.showDesktop`)
- `frontend/src/player-core/windowExposureScheduler.js` (scheduler por intervalo — referência)
- `frontend/src/player-core/storage.js` (persistência local — base p/ recuperação)
- `frontend/src/pages/Player.jsx` (fiação do scheduler, fases, SSE)
- `frontend/src/pages/DispositivoDetalhe.jsx` (UI de config 009 — base p/ nova seção)

## Estado atual encontrado

### Ja existe

- Primitiva Electron `player:show_desktop(duration, restoreFullscreen)`: minimiza, agenda
  restauração via `setTimeout`, restaura fullscreen/kiosk/alwaysOnTop a partir de snapshot.
- Bridge `__ELECTRON__.player.showDesktop / minimizeWindow / restoreWindow`.
- Propagação de config por **playlist response** e por **SSE** (padrão a reutilizar).
- Pipeline de comando (`commandPoller` + `commands.js`) com ACK.

### Existe parcialmente

- Scheduler local (`windowExposureScheduler.js`) — porém **só por intervalo**, single-config,
  sem nome, sem horário do dia, sem recuperação após restart.

### Falta ou precisa consolidar

- Modelo de **lista de eventos** por dispositivo (hoje é 1 config única).
- Scheduler **por horário do dia** com suporte a múltiplos horários.
- **Persistência + recuperação** de exposição em andamento no restart.
- **Máquina de estados** explícita e **log de execução**.

## Requisitos funcionais

### RF010-01 — Eventos por horário (múltiplos, nomeados)

Cada dispositivo pode ter **N eventos** de exposição. Cada evento tem: `name`,
`time` (HH:MM, timezone do dispositivo), `duration_seconds`, `enabled`.

Critérios:
- Suportar múltiplos horários (ex.: 08:00→15s, 10:00→30s, 14:00→10s) — **RN-007**.
- Eventos desabilitados não disparam.

### RF010-02 — Disparo no horário exato

A exposição ocorre exatamente no horário configurado — **RN-001**.

Critérios:
- Tolerância de disparo ≤ 2s do horário alvo.
- Se o Player ligar após o horário do dia já ter passado, **não** dispara retroativo (apenas agenda o próximo).

### RF010-03 — Minimizar sem encerrar campanha

Ao disparar: Player → minimizado, desktop visível — **RN-002**. A campanha **não** é
encerrada (**RN-003**) e a playlist **não** é reiniciada (**RN-004**).

### RF010-04 — Retorno automático

Ao fim da duração: Player → tela cheia (**RN-005**) e a campanha continua do estado atual
(**RN-006**), sem ação do usuário (**CA-008**).

### RF010-05 — Recuperação após reinício

Se o Player reiniciar durante a contagem, ao subir novamente ele verifica se há ação pendente:
- Tempo expirou → restaura/normaliza imediatamente;
- Tempo não expirou → continua a contagem pelo tempo restante. (**CA-009**)

### RF010-06 — Máquina de estados

Player segue: `RUNNING → MINIMIZING → MINIMIZED → WAITING_TIMER → RESTORING → RUNNING`.

### RF010-07 — Administração

UI permite criar, listar, editar e remover eventos por dispositivo (nome, horário, duração, ativo).

### RF010-08 — Log de execução

Cada execução (início e retorno) é registrada em log do Player e reportada ao backend — **CA-010**.

## Requisitos nao funcionais

- **Compatibilidade**: somente Electron Windows/Linux. Em outras plataformas, a função é no-op silencioso.
- **Performance**: no máximo 1 timer agendado por vez para o "próximo evento"; sem polling novo no backend.
- **Resiliência**: não depende do foco da aba; sobrevive a reinício (RF010-05).
- **Observabilidade**: logs claros de cada transição de estado.
- **Segurança**: CRUD protegido por permissão admin/mesmo-tenant (padrão SPEC 009).

## Decisoes de compatibilidade

- A função por intervalo (SPEC 009) **permanece** e é independente desta. Um dispositivo pode
  ter ambas configuradas; se conflitarem no tempo, a exposição em andamento ignora novo disparo
  (a máquina de estados só aceita disparo em `RUNNING`).
- Dispositivos antigos sem eventos: lista vazia, nenhum disparo.

## Riscos

- **Disparo perdido se Player desligado no horário**: aceitável — não há disparo retroativo (RF010-02).
- **Conflito com exposição por intervalo (009)**: mitigação — máquina de estados só dispara em `RUNNING`.
- **Relógio do dispositivo errado**: horário é local do dispositivo; documentar dependência do relógio do SO.

## Fora de escopo imediato

- Janela de validade por data (start_date/end_date) e dias da semana — pode entrar como extensão.
- Config por grupo/tenant.
