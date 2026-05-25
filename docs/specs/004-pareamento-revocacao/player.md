# SPEC 004 — Player

## Arquivos afetados

- `frontend/src/player-core/storage.js` — persistir `token_version`.
- `frontend/src/player-core/repair.js` (novo) — `forceRepair`, registry de callbacks.
- `frontend/src/api/http.js` — interceptor que injeta `X-Device-Token-Version` e captura erros de auth.
- `frontend/src/api/dispositivos.js` — sem mudanca obrigatoria (interceptor cuida do header).
- `frontend/src/pages/Player.jsx` — registrar `onForceRepair` callback, exibir mensagens amigaveis.

## `storage.js` — `PairingStorage`

Adicionar key `pw_player_token_version`:

```javascript
const KEYS = {
  code:         "pw_player_code",
  deviceId:     "pw_player_device_id",
  deviceToken:  "pw_player_device_token",
  tokenVersion: "pw_player_token_version",   // NOVO
};

export const PairingStorage = {
  // ... metodos existentes
  tokenVersion() {
    const v = localStorage.getItem(KEYS.tokenVersion);
    return v ? parseInt(v, 10) : null;
  },
  setTokenVersion(version) {
    if (version != null) {
      localStorage.setItem(KEYS.tokenVersion, String(version));
    }
  },
  save({ code, deviceId, deviceToken, tokenVersion }) {
    if (code) localStorage.setItem(KEYS.code, code);
    if (deviceId) localStorage.setItem(KEYS.deviceId, deviceId);
    if (deviceToken) localStorage.setItem(KEYS.deviceToken, deviceToken);
    if (tokenVersion != null) {
      localStorage.setItem(KEYS.tokenVersion, String(tokenVersion));
    }
  },
  clear() {
    Object.values(KEYS).forEach((k) => localStorage.removeItem(k));
  },
};
```

## `repair.js` (novo)

```javascript
import { PairingStorage, PlaylistCache } from "./storage.js";

let _onForceRepair = null;
let _lastRepairAt = 0;
let _repairCount = 0;
const REPAIR_LIMIT_MS = 5 * 60 * 1000;
const REPAIR_MAX_COUNT = 3;

export function onForceRepair(callback) {
  _onForceRepair = callback;
}

export async function forceRepair(reason) {
  console.warn("[repair] forceRepair triggered:", reason);

  // Anti-loop: max 3 repairs em 5min.
  const now = Date.now();
  if (now - _lastRepairAt < REPAIR_LIMIT_MS) {
    _repairCount++;
    if (_repairCount > REPAIR_MAX_COUNT) {
      console.error("[repair] too many repairs in 5min — backing off");
      await new Promise((r) => setTimeout(r, 30_000));
      _repairCount = 0;
    }
  } else {
    _repairCount = 1;
  }
  _lastRepairAt = now;

  // 1. Desativa watchdog se houver.
  if (window.__pwWatchdog) {
    clearTimeout(window.__pwWatchdog);
    window.__pwWatchdog = null;
  }

  // 2. Pega deviceId ANTES de limpar.
  const deviceId = PairingStorage.deviceId();

  // 3. Limpa storage local (idempotente).
  try { PairingStorage.clear(); } catch {}
  if (deviceId) {
    try { await PlaylistCache.clear(deviceId); } catch {}
  }

  // 4. Avisa React.
  if (_onForceRepair) {
    _onForceRepair(reason);
  } else {
    // Sem callback registrado: hard reload.
    setTimeout(() => window.location.reload(), 200);
  }
}

export class RepairTriggeredError extends Error {
  constructor(errorCode) {
    super(`forceRepair triggered: ${errorCode}`);
    this.name = "RepairTriggeredError";
    this.errorCode = errorCode;
  }
}
```

## `http.js` — interceptors

Adicionar antes do interceptor existente de injecao de JWT (que continua igual para rotas admin):

```javascript
import { PairingStorage } from "../player-core/storage.js";
import { forceRepair, RepairTriggeredError } from "../player-core/repair.js";

const REPAIR_ERROR_CODES = new Set([
  "TOKEN_REVOKED",
  "TOKEN_VERSION_MISMATCH",
  "TOKEN_VERSION_REQUIRED",
  "REQUIRES_REPAIRING",
  "DEVICE_BLOCKED",
]);

http.interceptors.request.use((config) => {
  const token = PairingStorage.token();
  const tokenVersion = PairingStorage.tokenVersion();

  if (token && !config.headers["X-Device-Token"]) {
    config.headers["X-Device-Token"] = token;
  }
  if (tokenVersion && !config.headers["X-Device-Token-Version"]) {
    config.headers["X-Device-Token-Version"] = String(tokenVersion);
  }
  return config;
});

http.interceptors.response.use(
  (res) => res,
  async (err) => {
    const status = err.response?.status;
    const errorCode = err.response?.data?.error_code;

    if ((status === 401 || status === 403) && REPAIR_ERROR_CODES.has(errorCode)) {
      await forceRepair(errorCode);
      return Promise.reject(new RepairTriggeredError(errorCode));
    }
    return Promise.reject(err);
  }
);
```

Nota: `dispositivos.js` ja passa `X-Device-Token` manualmente em algumas funcoes. Manter — interceptor nao sobrescreve se ja presente.

## `dispositivos.js` — `solicitarPareamento` + `verificarStatusPareamento`

Persistir `token_version` apos confirmar pareamento:

```javascript
export async function verificarStatusPareamento(code) {
  const { data } = await http.get(`/devices/by-code/${code}/status`);
  if (data?.status === "paired") {
    PairingStorage.save({
      code,
      deviceId: data.device_id,
      deviceToken: data.device_token,
      tokenVersion: data.token_version,    // NOVO
    });
  }
  return data;
}
```

## `Player.jsx` — registrar callback e exibir mensagens

```javascript
import { onForceRepair } from "../player-core/repair.js";

const REPAIR_MESSAGES = {
  TOKEN_VERSION_MISMATCH: "O codigo de pareamento foi atualizado pelo administrador. Pareie novamente.",
  REQUIRES_REPAIRING: "Este dispositivo precisa ser pareado novamente.",
  TOKEN_REVOKED: "Sessao expirada. Pareie novamente.",
  TOKEN_VERSION_REQUIRED: "Versao do player desatualizada. Atualize o aplicativo.",
  DEVICE_BLOCKED: "Dispositivo bloqueado. Entre em contato com o administrador.",
  PAIRING_CODE_EXPIRED: "Codigo expirou. Solicitando novo...",
};

function PlayerComponent() {
  // ...
  const [forceRepairReason, setForceRepairReason] = useState(null);

  useEffect(() => {
    onForceRepair((reason) => {
      console.warn("[Player] forceRepair callback:", reason);
      setForceRepairReason(reason);
      setPhase("pairing");
      setPairingState(null);
      setPlaylist(null);
      setCurrentIndex(0);
    });
  }, []);

  const repairMessage = forceRepairReason ? REPAIR_MESSAGES[forceRepairReason] : null;

  // No render da fase "pairing":
  if (phase === "pairing") {
    return (
      <PairingScreen
        code={pairingState?.code}
        warningMessage={repairMessage}
        onCodeReceived={(c) => setPairingState(c)}
      />
    );
  }
  // ...
}
```

Tela de pareamento exibe `warningMessage` em destaque (banner amarelo) quando presente, alem do codigo de pareamento normal.

## SSE — escutar `pairing:revoked`

No handler de eventos SSE em `Player.jsx`:

```javascript
es.addEventListener("pairing:revoked", (ev) => {
  const data = JSON.parse(ev.data);
  console.warn("[Player] SSE pairing:revoked", data);
  forceRepair(data.reason);
});
```

Trata-se de notificacao otimista — se SSE estiver offline, a proxima request 401 cobre.

## Watchdog — desabilitar durante pairing

O watchdog atual recarrega a pagina apos 120s sem heartbeat. Precisa nao disparar durante `phase === "pairing"`:

```javascript
const watchdog = setTimeout(() => {
  if (phase === "pairing") return;  // skip durante pairing
  if (Date.now() - lastHeartbeatAt > 120_000) {
    console.warn("[Player] watchdog reload");
    window.location.reload();
  }
}, 5000);
```

## Verificacoes pre-deploy

- Em dev: chamar regenerate via gerenciador → player ativo deve voltar para tela de pareamento em < 5s (via SSE) ou no proximo polling (10s) via 401.
- Validar que IndexedDB esta limpo apos forceRepair (DevTools → Application → IndexedDB → `pw_player`).
- Validar que localStorage tem apenas keys nao-`pw_player_*` apos forceRepair.
- Reparear normalmente e verificar que `token_version` agora aparece no localStorage.
- Bater endpoint com curl sem `X-Device-Token-Version` → backend retorna 401 (apos compat-period).
