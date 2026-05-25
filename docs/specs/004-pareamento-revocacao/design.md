# SPEC 004 — Design Tecnico

## Resumo

A SPEC fecha o ciclo de revogacao de pareamento ja iniciado pelas migrations recentes. O backend ja revoga `device_token` ao regenerar codigo; falta:

1. Validar `token_version` (defesa em profundidade).
2. Player enviar `X-Device-Token-Version`.
3. Player reagir a 401/403 com codigo especifico chamando `forceRepair` (limpa storages, volta tela de pareamento).
4. Endpoint `force-repair` para revogar sem trocar codigo.
5. Auditoria via `device_pairing_events`.

Sem mudanca de fluxo principal — apenas defesas adicionais e UX.

## Arquitetura atual relacionada

### Backend

- `backend/api/v1/devices.py`:
  - `get_device_by_token` (dependency).
  - `regenerate_pairing_code` endpoint.
  - `revoke_token` endpoint.
  - `pair_request`, `pair_confirm`, `by-code/{code}/status`.
- `backend/core/models.py`: `Device` com `device_token`, `pairing_code`, `pairing_version`, `token_version`, `requires_repairing`.
- `backend/crud/entidades/crud_device.py`: queries.

### Frontend / Player

- `frontend/src/player-core/storage.js`:
  - `PairingStorage` em localStorage (`pw_player_code`, `pw_player_device_id`, `pw_player_device_token`).
  - `PlaylistCache` em IndexedDB.
- `frontend/src/api/http.js`: interceptor de request.
- `frontend/src/api/dispositivos.js`: passa `token` como header `X-Device-Token`.
- `frontend/src/pages/Player.jsx`: fases pairing/loading/playing/error.
- `frontend/src/player-core/network.js`: `fetchWithRetry` com retry de rede.

## Fluxo: regenerar codigo (depois desta SPEC)

1. Admin clica "Regenerar codigo" em `DispositivoDetalhe.jsx`.
2. Frontend chama `GET /devices/{id}/sessions/active` (pre-existente) para listar players ativos.
3. Frontend mostra modal: "X players serao desconectados. Confirmar?".
4. Admin confirma.
5. Frontend chama `POST /devices/{id}/pairing-code/regenerate`.
6. Backend:
   - Gera novo `pairing_code`.
   - `device.device_token = NULL`.
   - `device.pairing_version += 1`.
   - `device.token_version += 1`.
   - `device.requires_repairing = True`.
   - `device.status = WAITING_PAIRING`.
   - Revoga `DeviceSession` ativas.
   - Insere row em `device_pairing_events` com `event_type=code_regenerated`, ambos versions antigas e novas, `requested_by`.
   - Publica SSE `pairing:revoked` no canal do device.
7. Backend retorna `{ pairing_code, pairing_version, token_version, revoked_sessions_count }`.
8. Player antigo:
   - Recebe SSE `pairing:revoked` → chama `forceRepair("pairing_revoked")` imediatamente. OU
   - Proxima request retorna 401 com `error_code=TOKEN_VERSION_MISMATCH` → chama `forceRepair(error_code)`.
9. `forceRepair`:
   - `PairingStorage.clear()`.
   - `PlaylistCache.clear(deviceId)`.
   - Desativa watchdog.
   - `setPhase("pairing")`.
   - Inicia novo `pair_request`.
10. Gerenciador mostra `revoked_sessions_count` e zera "Sessions ativas".

## Fluxo: token_version validation

1. Player faz request com headers:
   ```
   X-Device-Token: abc123...
   X-Device-Token-Version: 5
   ```
2. `get_device_by_token` (dependency):
   - Busca device por `device_token = "abc123..."`.
   - Se nao acha: 401 `error_code=TOKEN_REVOKED`.
   - Se `device.is_blocked`: 403 `error_code=DEVICE_BLOCKED`.
   - Se `device.requires_repairing`: 401 `error_code=REQUIRES_REPAIRING`.
   - Se header `X-Device-Token-Version` ausente E `device.token_version > 1`: 401 `error_code=TOKEN_VERSION_REQUIRED` (compat-period).
   - Se header presente E version != `device.token_version`: 401 `error_code=TOKEN_VERSION_MISMATCH`.
   - Caso contrario: retorna device.

## Fluxo: force-repair sem trocar codigo

1. Admin clica "Forcar reparamento (manter codigo)".
2. Modal explica: "Codigo permanece o mesmo, mas todos os players antigos sao expulsos."
3. Frontend chama `POST /devices/{id}/force-repair` com body `{ reason: "..." }`.
4. Backend:
   - `device.device_token = NULL`.
   - `device.token_version += 1`.
   - `device.requires_repairing = True`.
   - NAO altera `pairing_code` nem `pairing_version`.
   - Revoga sessions.
   - Insere row em `device_pairing_events` com `event_type=force_repair`.
5. Player antigo proxima request → 401 → `forceRepair`.
6. Player faz `pair_request` com codigo atual (que ainda eh valido) e recebe novo `device_token` + novo `token_version`.

Util quando o operador quer expulsar player suspeito mas evitar reconfigurar todos os outros que tem o mesmo codigo memorizado.

## Schema Pydantic

### `DeviceTokenContext` (novo helper interno)

```
class DeviceTokenContext(BaseModel):
    device: Device
    token_version: int
    pairing_version: int
```

### `PairRequestResponse` (estender)

```
class PairRequestResponse(BaseModel):
    code: str
    expires_at: datetime
    status: Literal["pending", "paired", "expired"]
    device_id: str | None = None
    device_token: str | None = None
    token_version: int | None = None  # NOVO
    pairing_version: int | None = None  # NOVO
```

### `RegenerateCodeResponse`

```
class RegenerateCodeResponse(BaseModel):
    pairing_code: str
    pairing_version: int
    token_version: int
    revoked_sessions_count: int
```

### `ForceRepairRequest` (novo)

```
class ForceRepairRequest(BaseModel):
    reason: str | None = None
```

### `ForceRepairResponse`

```
class ForceRepairResponse(BaseModel):
    token_version: int
    revoked_sessions_count: int
```

### `DevicePairingEvent` (novo)

```
class DevicePairingEvent(BaseModel):
    id: str
    event_type: Literal["code_regenerated", "force_repair", "token_revoked", "paired"]
    previous_token_version: int | None
    new_token_version: int | None
    previous_pairing_code: str | None
    new_pairing_code: str | None
    requested_by: str | None
    reason: str | None
    created_at: datetime
```

## Headers HTTP

### Request (player → backend)

| Header | Obrigatorio | Descricao |
|---|---|---|
| `X-Device-Token` | sim | Token persistido no pareamento |
| `X-Device-Token-Version` | sim (compat 1 release) | Version inteira ≥ 1 |

### Response (backend → player) em caso de erro

JSON body:

```
{
  "detail": "Token version mismatch",
  "error_code": "TOKEN_VERSION_MISMATCH",
  "current_version": 7,
  "received_version": 5
}
```

`error_code` valores:

- `TOKEN_REVOKED` — token nao existe no DB.
- `TOKEN_VERSION_MISMATCH` — version do header != device.token_version.
- `TOKEN_VERSION_REQUIRED` — header ausente quando deveria estar presente.
- `REQUIRES_REPAIRING` — device.requires_repairing = true.
- `DEVICE_BLOCKED` — device.is_blocked = true.
- `PAIRING_CODE_EXPIRED` — codigo de pareamento sem confirmacao em 15min.

## Design do `http.js` (player)

Interceptor de request adiciona ambos os headers automaticamente:

```
http.interceptors.request.use((config) => {
  const token = PairingStorage.token();
  const tokenVersion = PairingStorage.tokenVersion();
  if (token) {
    config.headers["X-Device-Token"] = token;
    if (tokenVersion) {
      config.headers["X-Device-Token-Version"] = String(tokenVersion);
    }
  }
  return config;
});
```

Interceptor de response captura 401/403 com `error_code` especifico:

```
const REPAIR_ERROR_CODES = new Set([
  "TOKEN_REVOKED",
  "TOKEN_VERSION_MISMATCH",
  "TOKEN_VERSION_REQUIRED",
  "REQUIRES_REPAIRING",
  "DEVICE_BLOCKED",
]);

http.interceptors.response.use(
  (res) => res,
  (err) => {
    const status = err.response?.status;
    const errorCode = err.response?.data?.error_code;
    if ((status === 401 || status === 403) && REPAIR_ERROR_CODES.has(errorCode)) {
      forceRepair(errorCode);
      return Promise.reject(new RepairTriggeredError(errorCode));
    }
    return Promise.reject(err);
  }
);
```

## Design do `forceRepair`

Funcao exposta a partir do `player-core` (novo arquivo `repair.js` ou dentro de `storage.js`):

```
let _onForceRepair = null;

export function onForceRepair(callback) {
  _onForceRepair = callback;
}

export async function forceRepair(reason) {
  console.warn("[player] forceRepair triggered:", reason);

  // 1. Para watchdog.
  if (window.__pwWatchdog) clearTimeout(window.__pwWatchdog);

  // 2. Limpa storages.
  const deviceId = PairingStorage.deviceId();
  PairingStorage.clear();
  if (deviceId) {
    await PlaylistCache.clear(deviceId).catch(() => {});
  }

  // 3. Avisa React via callback.
  if (_onForceRepair) {
    _onForceRepair(reason);
  } else {
    // Fallback: hard reload.
    setTimeout(() => window.location.reload(), 200);
  }
}
```

`Player.jsx` registra callback:

```
useEffect(() => {
  onForceRepair((reason) => {
    setForceRepairReason(reason);
    setPhase("pairing");
    setPairingState(null);
  });
}, []);
```

E mostra mensagem amigavel na tela de pareamento conforme `forceRepairReason`:

```
const REPAIR_MESSAGES = {
  TOKEN_VERSION_MISMATCH: "O codigo de pareamento foi atualizado. Pareie novamente.",
  REQUIRES_REPAIRING: "Este dispositivo precisa ser pareado novamente.",
  TOKEN_REVOKED: "Sessao expirada. Pareie novamente.",
  DEVICE_BLOCKED: "Dispositivo bloqueado. Entre em contato com o administrador.",
  PAIRING_CODE_EXPIRED: "Codigo expirou. Solicitando novo...",
};
```

## Design do SSE `pairing:revoked`

Backend publica no canal `pw:device:{device_id}:events` quando codigo eh regenerado ou force-repair eh chamado.

Payload:

```
{
  "event": "pairing:revoked",
  "reason": "code_regenerated" | "force_repair",
  "revoked_at": "2026-05-22T10:00:00"
}
```

Player escuta e dispara `forceRepair(payload.reason)` imediatamente — nao precisa esperar proxima request falhar.

Trade-off: se SSE estiver offline, o 401 da proxima request cobre.

## Decisoes tecnicas

- `token_version` eh inteiro incremental — colisao impossivel.
- `pairing_version` separado de `token_version` porque pode-se trocar token sem trocar codigo (`force-repair`).
- Compat-period de 1 release: backend aceita header ausente como version 1 com warning no log.
- `forceRepair` eh callback-based para evitar dependencia circular React ↔ player-core.
- Limpeza de cache no `forceRepair` ignora erros (best-effort).
- Watchdog desativado durante `pairing` para evitar reload loop.

## Pontos parcialmente existentes

- Colunas no model `Device` ja existem.
- `regenerate_pairing_code` ja revoga token e sessions.
- `revoke_token` endpoint ja existe (manter como atalho semantico).
- Frontend ja tem botao "Regenerar codigo".

## Lacunas de design

- Pre-pareamento por API (provisionar TV remotamente sem ir fisicamente) eh problema operacional real mas fora desta SPEC.
- Multi-pareamento (mesmo codigo, varios devices) — nao suportado, fora de escopo.
- Migration de player antigo no campo: usuarios com APK instalado antes da SPEC vao precisar reabrir o app para atualizar.

## Riscos e mitigacoes

### Risco: compat-period termina e quebra player antigo

Mitigacao:

- Compat de 2 releases em vez de 1, com warning no painel admin.
- Mensagem clara no manifesto de release.
- Endpoint `/admin/system/players-without-token-version` para auditar quantos players ainda nao mandam o header.

### Risco: 401 → forceRepair gera loop infinito

Mitigacao:

- `forceRepair` so dispara para `error_code` em whitelist (RepairErrorCodes).
- Tela de pareamento NAO consulta endpoints autenticados ate ter token novo.
- Limite de 3 forceRepair em 5 minutos — depois espera 30s antes de tentar de novo.

### Risco: SSE entrega `pairing:revoked` para player ja desautenticado

Mitigacao:

- SSE eh apenas notificacao otimista; 401 cobre o caso.
- Idempotencia em `forceRepair` (cleanup ignora erros).

### Risco: limpeza de IndexedDB falha em browsers restritos

Mitigacao:

- Try/catch em `PlaylistCache.clear`.
- Fallback: hard reload da pagina apos limpar `PairingStorage`.

## Criterio de pronto tecnico

- Migration de `device_pairing_events` aplicada.
- Backend valida `token_version` em todas as rotas autenticadas por device.
- Erros 401/403 retornam JSON com `error_code` consistente.
- Player envia `X-Device-Token-Version` em toda request.
- Player reage a `error_code` em whitelist com `forceRepair`.
- Endpoint `POST /devices/{id}/force-repair` funcional.
- SSE `pairing:revoked` publicado e consumido.
- Gerenciador mostra timeline de eventos de pareamento.
- Botao "Regenerar codigo" mostra impacto antes.
- Botao "Forcar reparamento" disponivel separado.
- Testes E2E: regenerar codigo expulsa player rodando em < 5s.
