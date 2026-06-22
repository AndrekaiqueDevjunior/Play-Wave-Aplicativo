# SPEC 011 — Player

Status: implementacao parcial

## Comportamento esperado no boot

O player deve inicializar em modo autonomo quando estiver em producao/kiosk.

Sequencia minima:

1. Ler flags de ambiente/configuracao (`AUTO_BOOT`, kiosk, Electron, build production).
2. Carregar credenciais/config local.
3. Decidir se pode restaurar sem modal.
4. Revalidar no backend quando necessario.
5. Usar cache offline apenas se backend nao responder e cache for valido.
6. Entrar na tela player.
7. Sincronizar programacao.
8. Iniciar reproducao.
9. Registrar heartbeat/log de boot.

## Regras de UI

- Nao exibir modal de escolha em producao/kiosk.
- Tela de pareamento aparece apenas quando nao ha caminho automatico seguro.
- Em boot offline, mostrar estado discreto de offline/sincronizando, sem bloquear reproducao se houver cache valido.

## Estado atual encontrado

- `Player.jsx` carrega `PairingStorage.load()` no primeiro render.
- Se existem `saved.id` e `saved.token`, `phase` inicia como `loading`; se nao, inicia como `waiting`.
- `waiting` registra/renova codigo de pareamento via `pairRequest()` e faz polling em `getPairStatus()`.
- Ao parear, salva credenciais e chama `window.__ELECTRON__?.notifyPaired?.()`.
- `loading` chama `getDevicePlaylist(deviceId, token)`.
- Se a playlist falha por erro de autenticacao, o Player limpa `PairingStorage` e volta para `waiting`.
- Se a playlist falha por erro de rede/outro erro, tenta `PlaylistCache.get(deviceId)` e entra em `playing` se houver midias cacheadas.
- Heartbeat roda depois que ha `deviceId` e `deviceToken`.
- SSE `pairing:revoked` aciona `forceRepair()`, limpando storage e voltando ao pareamento.

## Causa principal encontrada

O bloqueio de boot automatico nao esta principalmente no React. Ele esta em `frontend/electron/main.js`, onde `handleSessionOnStartup()` abre um `dialog.showMessageBox()` para usuario escolher entre manter sessao ou apagar tudo quando `paired=true`.

Tambem ha risco de perda de sessao/cache valido porque `handleSessionOnStartup()` limpa storage em primeira execucao ou troca de versao do app.

## Implementacao parcial

- `frontend/electron/main.js` ganhou flag `AUTO_BOOT`.
- Em auto boot, `handleSessionOnStartup()` preserva storage em primeira execucao, troca de versao e estado `paired=false`.
- Em auto boot, `handleSessionOnStartup()` retorna sem exibir o modal "Sessão anterior encontrada".
- Fluxo de desenvolvimento/suporte continua permitindo apagar sessao manualmente quando `AUTO_BOOT` estiver desligado.

## Regras de cache

- Nunca sobrescrever cache valido com resposta vazia causada por erro de rede.
- Limpar credenciais quando backend confirmar pareamento invalidado.
- Ao receber `schedule_version` diferente, recarregar programacao sem reload total de pagina.

## Logs locais

Eventos:

```text
PLAYER_AUTO_BOOT_STARTED
PLAYER_AUTO_BOOT_SESSION_FOUND
PLAYER_AUTO_BOOT_REVALIDATING
PLAYER_AUTO_BOOT_OFFLINE_CACHE_USED
PLAYER_AUTO_BOOT_SUCCESS
PLAYER_AUTO_BOOT_FAILED
PLAYER_AUTO_BOOT_PAIRING_REQUIRED
```

Cada log deve conter, quando disponivel:

- `device_id`
- `tenant_id`
- `boot_mode`
- `platform`
- `player_version`
- `schedule_version`
- `reason`

Nao logar token, senha, codigo secreto completo ou payload sensivel.

## Checklist de auditoria do player

- [x] Identificar componente/pagina principal do player: `frontend/src/pages/Player.jsx`.
- [x] Identificar modal de escolha de sessao: `frontend/electron/main.js`.
- [x] Identificar storage local atual: `frontend/src/player-core/storage.js`.
- [x] Identificar cliente HTTP/API do player: `frontend/src/lib/api.js`, `frontend/src/api/dispositivos.js`, `frontend/src/api/http.js`.
- [x] Identificar fluxo de pareamento: `pairRequest()`, `getPairStatus()`, `PairingStorage.save()`.
- [x] Identificar fluxo de sync de programacao: `getDevicePlaylist()` em `loadPlaylist()`.
- [~] Identificar logs existentes: console logs existem; logs estruturados `PLAYER_AUTO_BOOT_*` faltam.
- [x] Identificar diferenca entre build web, Electron e Windows kiosk: Electron usa `PLAYER_KIOSK`, preload e `.pw_state`.
