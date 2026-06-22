# SPEC 011 — Requirements

Status: implementacao parcial
Data: 2026-06-15

## Contexto

Cliente reportou que o app/player nao inicializa automaticamente em ambiente real de loja/TV. Ao abrir, o sistema pede uma decisao manual como "manter sessao atual" ou "comecar do zero", impedindo operacao autonoma depois de reboot do Windows ou reinicio do aplicativo.

## Estado atual encontrado

### Ja existe

- `frontend/src/pages/Player.jsx` inicia em `loading` quando `PairingStorage.load()` retorna `id` e `token`, pulando a tela de pareamento.
- `frontend/src/player-core/storage.js` persiste `pw_player_code`, `pw_player_device_id`, `pw_player_device_token`, `pw_player_token_version` e `pw_player_pairing_version`.
- `PlaylistCache` salva a ultima playlist/campanha em IndexedDB e o Player usa esse cache quando `GET /devices/{id}/playlist` falha por erro nao autenticacao.
- `frontend/electron/preload.js` injeta `window.__ELECTRON__.prepaired` a partir de `frontend/electron/config.json`, permitindo player pre-pareado.
- `frontend/electron/preload.js` expoe `notifyPaired()`, usado pelo Player para marcar o estado persistente do Electron como pareado.
- `backend/api/v1/devices.py` ja tem `POST /devices/{device_id}/heartbeat`.
- `backend/core/models.py` ja tem campos `last_seen_at`, `player_version`, `os`, `ip_address`, `storage_used`, `pairing_version`, `token_version` e `schedule_version` no model `Device`.
- A autenticacao de dispositivo ja rejeita `TOKEN_REVOKED`, `DEVICE_BLOCKED`, `REQUIRES_REPAIRING`, `TOKEN_VERSION_REQUIRED` e `TOKEN_VERSION_MISMATCH`.

### Parcial ou incorreto

- `frontend/electron/main.js` mostra modal nativo em `handleSessionOnStartup()` quando a versao e a mesma e `paired=true`.
- `frontend/electron/main.js` limpa storage silenciosamente quando detecta primeira execucao ou troca de versao. Isso pode destruir uma sessao/cache valido durante atualizacao.
- Nao existe flag explicita `AUTO_BOOT=true` documentada no Electron; ha `PLAYER_KIOSK` e comportamento de build/producao.
- O heartbeat atual nao recebe `boot_mode`; ele registra estado operacional periodico, mas nao distingue inicializacao automatica de heartbeat comum.

### Falta

- Validacao E2E no Electron/Windows confirmando que o modal nao aparece.
- Logs `PLAYER_AUTO_BOOT_*`.
- Teste automatizado cobrindo a decisao de startup do Electron.

### Implementado parcialmente

- `frontend/electron/main.js` agora define `AUTO_BOOT` a partir de `PLAYER_AUTO_BOOT=true`, `AUTO_BOOT=true` ou modo producao/kiosk.
- Em `AUTO_BOOT`, `handleSessionOnStartup()` nao abre `dialog.showMessageBox()`.
- Em `AUTO_BOOT`, `handleSessionOnStartup()` preserva storage quando nao existe `.pw_state` ou quando a versao do app mudou.
- Em `AUTO_BOOT`, estado `paired=false` nao causa limpeza automatica de storage; o renderer decide se deve parear ou restaurar.

## Objetivo

Ao ligar o dispositivo ou abrir o app, o player deve restaurar a ultima sessao valida, entrar direto no modo player/kiosk, sincronizar a programacao e iniciar reproducao sem clique humano.

## Regra de negocio

O player de exibicao nao pode depender de decisao manual para iniciar em producao.

Ordem de restauracao:

1. Se existir sessao anterior valida, restaurar sessao.
2. Se nao existir sessao valida, tentar revalidar usando `device_id` e/ou `pairing_code` salvo.
3. Se estiver offline, usar a ultima configuracao valida em cache.
4. Se nao houver sessao, codigo ou cache valido, exibir tela de pareamento.

## Requisitos funcionais

### RF011-01 — Boot automatico em modo producao

Quando `AUTO_BOOT=true` ou quando o player estiver empacotado em modo kiosk/producao, o player deve iniciar sem exibir modal de escolha de sessao.

Criterios:

- Modal "manter sessao atual" / "comecar do zero" nao aparece em producao.
- A tela de pareamento so aparece quando nao houver nenhuma credencial ou cache valido.
- O fluxo deve ser idempotente: abrir o app varias vezes nao duplica sessao nem reseta cache.

### RF011-02 — Persistencia local minima

O player deve manter localmente os dados necessarios para restaurar sessao.

Dados esperados:

- `device_id`
- `pairing_code`
- `tenant_id`
- `player_token` ou token equivalente
- `last_known_config`
- `last_schedule_version`, quando existir
- timestamp da ultima sincronizacao valida

Criterios:

- Dados sensiveis nao devem ser expostos em logs.
- Cache deve ser invalidado quando backend rejeitar a sessao.
- Cache offline so pode ser usado se foi gerado por uma sincronizacao valida anterior.

### RF011-03 — Revalidacao de sessao

Se a sessao local estiver ausente, expirada ou incompleta, o player deve chamar endpoint de restauracao/revalidacao antes de mostrar tela manual.

Criterios:

- Backend pode identificar o dispositivo por `device_id` e/ou `pairing_code`.
- Backend rejeita pareamento invalido ou sessao revogada.
- Rejeicao de sessao antiga por mudanca de pareamento deve levar o player para a tela de pareamento.

### RF011-04 — Boot offline com ultimo cache valido

Se o backend estiver indisponivel e houver `last_known_config` valido, o player deve iniciar com esse cache e marcar estado operacional como offline.

Criterios:

- Player nao fica preso em tela branca por falta de rede.
- Player tenta sincronizar novamente em segundo plano.
- Ao reconectar, compara versao da programacao antes de atualizar filas.

### RF011-05 — Heartbeat de inicializacao

Quando conseguir iniciar, o player deve registrar no backend que inicializou.

Dados esperados:

- `device_id`
- data/hora do boot
- versao do player
- sistema operacional/plataforma
- modo de boot: `session`, `pairing_code`, `offline_cache`, `manual_pairing`
- status: sucesso/falha

### RF011-06 — Logs de boot

O player deve registrar logs uteis para diagnostico.

Eventos minimos:

- `PLAYER_AUTO_BOOT_STARTED`
- `PLAYER_AUTO_BOOT_SESSION_FOUND`
- `PLAYER_AUTO_BOOT_REVALIDATING`
- `PLAYER_AUTO_BOOT_OFFLINE_CACHE_USED`
- `PLAYER_AUTO_BOOT_SUCCESS`
- `PLAYER_AUTO_BOOT_FAILED`
- `PLAYER_AUTO_BOOT_PAIRING_REQUIRED`

## Compatibilidade

- O fluxo atual de pareamento deve continuar funcionando quando nao houver dados locais validos.
- Ambientes web de desenvolvimento podem manter o modal manual quando `AUTO_BOOT` estiver desligado.
- Nenhuma campanha, playlist ou midia deve ser alterada por esta SPEC.

## Criterios de aceite

- [ ] Ao ligar o dispositivo, o player abre sem clique humano.
- [ ] A tela de escolha de sessao nao aparece em modo producao/kiosk.
- [ ] Se houver sessao valida, a reproducao inicia automaticamente.
- [ ] Se a sessao estiver expirada, o player tenta revalidar antes de pedir pareamento.
- [ ] Se estiver offline, o player usa o ultimo cache valido.
- [ ] Se nao houver credencial/cache valido, o player mostra pareamento.
- [ ] Backend registra que o player iniciou.
- [ ] Gerenciador mostra status atualizado do dispositivo, quando ja existir essa UI.
- [ ] Logs permitem diagnosticar por que o boot automatico falhou.
