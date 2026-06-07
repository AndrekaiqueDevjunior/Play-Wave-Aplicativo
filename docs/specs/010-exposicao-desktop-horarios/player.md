# SPEC 010 — Player

## Novo módulo: `frontend/src/player-core/desktopExposureTimeScheduler.js`

Assinatura (espelha o estilo de `windowExposureScheduler.js`):

```js
export function createDesktopExposureTimeScheduler({
  executeShowDesktop,   // (durationSeconds) => Promise   — chama __ELECTRON__.player.showDesktop
  persist,              // (action|null) => void          — storage.js
  loadPending,          // () => action|null
  isElectron = false,
  now = () => new Date(),
  logger = console,
}) {
  // schedule({ events, phase, timezone })  → agenda o PRÓXIMO evento
  // stop()                                 → limpa timer
  // recover()                              → no boot, retoma ação pendente
  // isScheduled()
}
```

### Cálculo do próximo disparo
- Para cada evento `enabled`, calcular o próximo `Date` correspondente a `time` (HH:MM) no
  dia de hoje; se já passou, usar amanhã. (Respeitar `weekdays` quando presente.)
- Agendar `setTimeout` para o **menor** próximo `Date`.
- Só agenda se `isElectron` e `phase ∈ {playing, no_campaign}`.

### Disparo (máquina de estados)
```
RUNNING → MINIMIZING → MINIMIZED → WAITING_TIMER → RESTORING → RUNNING
```
- Só dispara em `RUNNING`. Ao disparar:
  1. `state = MINIMIZING`; `persist({ actionId, startedAt, durationSeconds, status:"running" })`.
  2. `await executeShowDesktop(duration)` (o Electron minimiza e agenda a restauração).
  3. `state = WAITING_TIMER`.
  4. Após `duration`: `state = RESTORING` → o Electron já restaura via seu próprio timer →
     `persist(null)`; log `restored`; `state = RUNNING`; reagenda próximo.

### Recuperação no boot — `recover()`
```js
const pending = loadPending();
if (!pending) return;
const elapsed = (now() - new Date(pending.startedAt)) / 1000;
if (elapsed >= pending.durationSeconds) {
  persist(null);                       // já normalizado pelo boot fullscreen
  logger.log("[exposure] recovered: expired, cleared");
} else {
  const remaining = Math.ceil(pending.durationSeconds - elapsed);
  executeShowDesktop(remaining);       // honra tempo restante (CA-009)
  logger.log("[exposure] recovered: resuming", remaining, "s");
}
```

## Fiação em `Player.jsx`

- Novo estado `desktopExposureEvents` (default `[]`), populado por:
  - playlist response (`res.desktop_exposure_events`) — ver [Player.jsx:487](../../../frontend/src/pages/Player.jsx#L487);
  - SSE (`data.desktop_exposure_events`) — ver [Player.jsx:832](../../../frontend/src/pages/Player.jsx#L832).
- `useRef` para o scheduler (espelha `desktopExposureSchedulerRef`).
- `useEffect` cria o scheduler (com `executeShowDesktop` ligado à bridge) e chama `recover()` no mount.
- `useEffect` reagenda em mudanças de `desktopExposureEvents` / `phase` / `deviceId`.
- Cleanup chama `stop()`.

## Electron / Capacitor

- **Electron**: nenhuma mudança obrigatória — reutiliza `player:show_desktop`.
  - (Opcional) suportar `showDesktop` com duração já "restante" para recuperação — já suportado, é só passar o valor.
- **Capacitor (Android)**: no-op silencioso (sem `window.minimize()` — ver `009/LIMITACOES_PLATAFORMAS.md`).

## Log de execução (CA-010)

- Local: `logger.log` em cada transição (`MINIMIZING`, `RESTORING`, `recovered`).
- Remoto (opcional nesta entrega): reportar `{ event_id, started_at, restored_at, recovered }`
  via ACK de comando ou endpoint de log do device.
