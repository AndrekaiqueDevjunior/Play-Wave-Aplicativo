# SPEC 010 — Design

## Visão geral

```
[Admin DispositivoDetalhe]
   └── CRUD eventos ─────────► [Backend /devices/{id}/desktop-exposure-events]
                                      │
                                      ├── persiste em device_desktop_exposure_events
                                      ├── inclui eventos na playlist response
                                      └── publica SSE (invalidate playlist)
                                                  │
                                                  ▼
                                        [Player.jsx]
                                          └── desktopExposureTimeScheduler
                                                 ├── calcula próximo horário
                                                 ├── setTimeout até o horário
                                                 ├── ao disparar → __ELECTRON__.player.showDesktop(duration)
                                                 ├── persiste ação pendente (storage.js)
                                                 └── ao restaurar → limpa ação + loga
```

A **execução física** (minimizar/restaurar/fullscreen) reutiliza a primitiva já existente
`player:show_desktop` do Electron (SPEC 009). Esta SPEC adiciona apenas a **camada de
agendamento por horário + persistência/recuperação + modelo de N eventos**.

## Componentes

### 1. Backend
- Nova tabela `device_desktop_exposure_events` (1:N com `devices`).
- Endpoints CRUD + inclusão dos eventos na playlist response e SSE (reusa `_publish_device_playlist_invalidated`).
- Schemas Pydantic com validação de `time` (HH:MM) e `duration_seconds` (1–300).

### 2. Player — `desktopExposureTimeScheduler.js` (novo)
Responsável por:
- Receber a lista de eventos + timezone do dispositivo.
- Calcular o **próximo disparo** (menor "próximo horário" entre os eventos ativos).
- Agendar um único `setTimeout` até esse horário.
- No disparo: transitar a máquina de estados e chamar `showDesktop(duration, true)`.
- Reagendar o próximo após cada disparo / reconfig / mudança de fase.
- Só dispara quando `phase === "playing"` (ou `no_campaign`) e `isElectron`.

### 3. Player — persistência/recuperação (`storage.js`)
- Ao iniciar exposição: salvar `{ actionId, startedAt, durationSeconds, status:"running" }`.
- Ao restaurar: marcar `status:"done"` / remover.
- No boot do Player: ler ação pendente:
  - `elapsed >= duration` → limpar (já normalizado pelo boot fullscreen).
  - `elapsed < duration` → chamar `showDesktop(remaining)` para honrar o tempo restante.

### 4. Máquina de estados (no scheduler/player)
```
RUNNING ──(horário)──► MINIMIZING ──► MINIMIZED ──► WAITING_TIMER
   ▲                                                      │
   └────────────── RUNNING ◄── RESTORING ◄────(timer fim)─┘
```
- Disparo só é aceito em `RUNNING`. Em qualquer outro estado, novo disparo é ignorado (evita conflito com SPEC 009 e com sobreposição de horários).

### 5. Log de execução
- Local: `logger.log` em cada transição.
- Remoto: reportar via ACK de comando existente (ou endpoint de log do device), com
  `event_id`, `started_at`, `restored_at`, `recovered:boolean`.

## Reuso explícito

| Necessidade | Reutiliza |
|-------------|-----------|
| Minimizar + restaurar + fullscreen snapshot | `player:show_desktop` IPC ([main.js:308](../../../frontend/electron/main.js#L308)) |
| Bridge renderer→main | `__ELECTRON__.player.showDesktop` ([preload.js:27](../../../frontend/electron/preload.js#L27)) |
| Propagar config | playlist response + SSE invalidation (padrão 009) |
| Persistência local | `frontend/src/player-core/storage.js` |
| Padrão de scheduler | `windowExposureScheduler.js` (estrutura schedule/stop) |

## Decisões

- **Tabela dedicada** (não JSON) para os eventos: facilita validação, índices por `device_id` e CRUD granular.
- **Horário em string `HH:MM`** + interpretação no timezone do dispositivo (relógio do SO).
- **Sem disparo retroativo**: se ligou depois do horário, agenda só o próximo (evita "tela minimiza ao ligar").
- **Recuperação** baseada em `startedAt + duration` salvo localmente — independe do backend.
