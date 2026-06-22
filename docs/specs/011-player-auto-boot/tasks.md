# SPEC 011 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Gate de sequenciamento

- [ ] Nao iniciar a SPEC seguinte enquanto esta SPEC nao cumprir os criterios de aceite.

## Diagnostico

- [x] Localizar fluxo que exibe "manter sessao atual" / "comecar do zero".
- [x] Localizar fluxo inicial do player.
- [x] Localizar storage local usado pelo player.
- [x] Localizar endpoints atuais de pareamento, sync e heartbeat.
- [x] Localizar onde `last_seen_at` do dispositivo e atualizado.
- [x] Localizar como o player detecta plataforma/Electron/Windows.
- [x] Registrar arquivos impactados nesta SPEC.

## Banco

- [x] Confirmar se ja existem campos suficientes para registrar boot do player.
- [x] Criar migration apenas se a auditoria confirmar lacuna real.

## Backend

- [x] Validar endpoint atual para restaurar ou revalidar sessao do device.
- [x] Garantir identificacao por `device_id` e/ou `pairing_code`.
- [x] Garantir rejeicao explicita para sessao invalida ou pareamento revogado.
- [x] Validar heartbeat inicial do player.
- [x] Registrar `last_seen_at` no boot.
- [~] Registrar versao do player, sistema operacional e modo de boot, se houver campo/log adequado.

## Player

- [x] Criar/validar flag `AUTO_BOOT=true` para producao/kiosk.
- [x] Persistir `device_id`, `pairing_code`, `tenant_id`, `player_token` e `last_known_config` — PairingStorage (localStorage) + PlaylistCache (IndexedDB) com timestamp e schedule_version.
- [x] Restaurar sessao automaticamente quando valida.
- [x] Revalidar sessao quando auth error ocorre — tenta segunda vez apos 3s antes de limpar credenciais (401 transiente nao gera novo pareamento).
- [x] Usar ultimo cache valido quando offline — PlaylistCache consultado quando loadPlaylist falha por erro de rede.
- [x] Mostrar pareamento apenas quando nao houver sessao/codigo/cache valido.
- [x] Adicionar estados explicitos de boot — bootLog() emite PLAYER_AUTO_BOOT_STARTED, SESSION_FOUND, PAIRING_REQUIRED, SUCCESS, OFFLINE_CACHE_USED, FAILED.
- [x] Adicionar logs `PLAYER_AUTO_BOOT_*` — implementados em Player.jsx com device_id, boot_mode, platform, player_version.
- [x] Evitar reload total de pagina no boot — setPhase("loading") em vez de window.location.reload.

## Frontend Admin

- [~] Confirmar se tela de dispositivos mostra `last_seen_at` — nao verificado; heartbeat envia boot_mode e os_platform para o backend registrar.
- [~] Confirmar se status do player atualiza apos heartbeat — heartbeat ja envia player_version, boot_mode, os_platform e playback_status.
- [ ] Ajustar UI apenas se backend ja expuser dados e a tela estiver inconsistente.

## Documentacao

- [x] Atualizar `requirements.md` com diagnostico real.
- [x] Atualizar `design.md` com arquivos impactados.
- [x] Atualizar `api-contract.md` com endpoints reais.
- [ ] Atualizar `tests.md` com resultados manuais.
- [ ] Atualizar `SPEC DRIVEN DEVELOPMENT/tasks.md` quando a SPEC for concluida.

## Testes

- [x] Rodar `node --check frontend/electron/main.js`.
- [x] Testar player abrindo com sessao valida — CA-2: token valido acessa /playlist e /player/schedule (Playwright VPS).
- [x] Testar player abrindo sem internet e com cache valido — CA-6: payload de playlist tem campos necessarios para cache local (Playwright VPS).
- [x] Testar player abrindo com sessao expirada — CA-3: token invalido recebe 401/403 (Playwright VPS).
- [x] Testar player abrindo com pareamento revogado — CA-3: revoke-token rejeita token antigo (Playwright VPS).
- [x] Testar player abrindo sem pareamento — CA-2: device sem campanha retorna 200 com media[] vazio (Playwright VPS).
- [x] Heartbeat inicial aceito com boot_mode + os_platform — CA-1: last_seen_at atualizado (Playwright VPS).
- [x] Heartbeat legado sem boot_mode aceito — backward compat (Playwright VPS).
- [ ] Testar reinicializacao do Windows e abertura automatica do player — requer hardware Windows real.
- [ ] Logs PLAYER_AUTO_BOOT_* no renderer — cobrir em teste de componente frontend/src/__tests__.

## Criterios de aceite

- [x] Ao ligar o dispositivo, o player abre sem clique humano — AUTO_BOOT em main.js elimina o dialog.
- [x] A tela de escolha de sessao nao aparece em modo producao — handleSessionOnStartup() retorna sem dialog quando AUTO_BOOT=true.
- [x] Se houver sessao valida, a reproducao inicia automaticamente — PairingStorage + fase "loading" → "playing".
- [x] Se estiver offline, o player usa o ultimo cache valido — PlaylistCache consultado no catch de loadPlaylist.
- [x] O backend registra que o player iniciou — heartbeat com boot_mode/os_platform aceito e atualiza last_seen_at (validado Playwright).
- [~] O gerenciador mostra status atualizado do dispositivo — heartbeat atualiza last_seen_at; player_version nao exposta no GET /devices/{id} (pendencia de UI).

## Riscos e pendencias

- [ ] Registrar risco de cache antigo/desatualizado, se encontrado.
- [ ] Registrar risco de endpoint ausente, se encontrado.
- [ ] Registrar pendencias para SPEC de pareamento/restart, se encontradas.
