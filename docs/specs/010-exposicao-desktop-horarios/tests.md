# SPEC 010 — Testes

## Backend (pytest)

- CRUD: criar/listar/atualizar/remover evento → 201/200/200/204.
- Validação: `time` fora de `HH:MM` → 422; `duration_seconds` fora de 1–300 → 422.
- Permissão: usuário de outro tenant (não admin) → 403.
- Playlist response inclui `desktop_exposure_events`.
- Mutação dispara SSE `desktop_exposure_events_updated`.
- Delete em cascata ao remover device.

## Player (vitest) — `desktopExposureTimeScheduler`

- Cálculo do próximo disparo: hoje se ainda não passou, amanhã se já passou.
- Múltiplos eventos: agenda o **menor** próximo horário.
- Não agenda em `phase ∈ {waiting, loading, pairing}` nem fora do Electron.
- Disparo só em `RUNNING`; novo disparo durante exposição é ignorado.
- Após restaurar, reagenda o próximo.
- `recover()`:
  - pending expirado → limpa, não minimiza;
  - pending não expirado → chama `executeShowDesktop(remaining)` com tempo restante correto.
- `weekdays`: respeita dias permitidos.

## Manual / E2E (Electron Windows)

Mapear para os Critérios de Aceite:
- CA-001 horário executa · CA-002 minimiza · CA-003 desktop visível · CA-004 timer ·
  CA-005 retorna sozinho · CA-006 fullscreen restaurado · CA-007 campanha continua ·
  CA-008 sem ação do usuário · CA-009 funciona após reinício (matar app no meio da contagem) ·
  CA-010 execução em logs.

### Roteiro CA-009 (recuperação)
1. Configurar evento para daqui a 1 min, duração 30s.
2. No disparo, **fechar o Player** após ~10s.
3. Reabrir o Player.
4. Esperado: Player retoma minimizado por ~20s restantes e depois restaura fullscreen.
