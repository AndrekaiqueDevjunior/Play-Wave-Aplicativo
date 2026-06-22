# SPEC 011 — Design

Status: diagnostico inicial concluido

## Fluxo principal

```text
App abre
  -> detectar modo AUTO_BOOT/kiosk
  -> carregar storage local do player
  -> se existir sessao aparentemente valida
       -> restaurar sessao
       -> heartbeat inicial
       -> sync programacao
       -> iniciar player
  -> senao, se existir device_id ou pairing_code
       -> chamar backend para revalidar/restaurar
       -> salvar nova sessao/config
       -> heartbeat inicial
       -> sync programacao
       -> iniciar player
  -> senao, se backend indisponivel e cache valido
       -> iniciar com last_known_config
       -> marcar offline
       -> iniciar sync em background
  -> senao
       -> mostrar tela de pareamento
```

## Decisoes tecnicas

### Arquivos impactados conhecidos

- `frontend/electron/main.js`: origem do modal manual e limpeza de storage no startup.
- `frontend/electron/preload.js`: injecao de credenciais pre-pareadas e `notifyPaired()`.
- `frontend/electron/config.json`: credenciais opcionais para player pre-pareado.
- `frontend/src/pages/Player.jsx`: decisao inicial `loading` vs `waiting`, pareamento, cache offline e heartbeat.
- `frontend/src/player-core/storage.js`: `PairingStorage`, `PlaylistCache`, `PlayerState`.
- `frontend/src/api/dispositivos.js`: endpoints de pareamento, playlist e heartbeat usados pelo Player.
- `backend/api/v1/devices.py`: validacao de token, pareamento, playlist e heartbeat.
- `backend/core/models.py`: campos de device ja existentes para registrar status do player.

### Player e fonte da verdade

O backend continua sendo a fonte da verdade da programacao. O cache local so serve para boot resiliente quando ja houve uma sincronizacao valida anterior.

### Modal manual

O modal de decisao manual deve ser tratado como comportamento de desenvolvimento/suporte, nao como fluxo padrao de producao.

### Storage local

A auditoria deve identificar o mecanismo atual: `localStorage`, `IndexedDB`, storage Electron, Capacitor Preferences ou outro. A implementacao deve preferir a abstracao ja existente no projeto.

Campos sensiveis como token nao devem ser logados. Se o projeto ja tiver camada segura para storage, usar essa camada.

### Estado de boot

O player deve ter estado explicito de boot para evitar telas brancas e corridas entre sync, pareamento e renderizacao:

- `initializing`
- `restoring_session`
- `revalidating`
- `offline_mode`
- `pairing_required`
- `ready`
- `failed`

### Offline cache

O cache offline so pode ser usado quando:

- possui `device_id`;
- possui programacao/configuracao salva;
- possui timestamp de ultima sync valida;
- nao foi explicitamente invalidado por pareamento revogado.

### Pareamento revogado

Se o backend responder que a sessao foi invalidada por alteracao de pareamento, o player deve apagar credenciais antigas e ir para pareamento. Esse comportamento conversa com a SPEC de revogacao de pareamento ja existente no projeto.

## Pontos de auditoria obrigatorios

Antes de implementar, preencher:

- [x] arquivo/componente que exibe "manter sessao atual" / "comecar do zero": `frontend/electron/main.js`, `handleSessionOnStartup()`;
- [x] arquivo onde o player decide tela inicial: `frontend/src/pages/Player.jsx`, estado inicial `phase`;
- [x] mecanismo atual de storage local: `frontend/src/player-core/storage.js`;
- [x] endpoints atuais de pareamento, sync e heartbeat: `frontend/src/api/dispositivos.js` e `backend/api/v1/devices.py`;
- [x] como o player identifica device/token: `PairingStorage.load()` + headers `X-Device-Token` e `X-Device-Token-Version`;
- [x] se Electron/Windows injeta alguma configuracao de kiosk: `frontend/electron/main.js` usa `PLAYER_KIOSK`; `preload.js` injeta `backendUrl` e `prepaired`;
- [ ] se ha reload total durante boot;
- [~] como logs do player sao enviados ou persistidos: console/log local existe; eventos estruturados de auto boot ainda faltam.

## Riscos

- Restaurar cache antigo sem validar versao pode tocar programacao desatualizada.
- Apagar storage ao falhar rede pode forcar pareamento indevido.
- Usar apenas frontend para resolver sessao pode mascarar pareamento revogado.
- Boot offline precisa ser claro para suporte, senao parece que dispositivo esta online.
