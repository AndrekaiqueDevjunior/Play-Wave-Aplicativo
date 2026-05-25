# SPEC 004 — Pareamento e Revogacao

Status: especificacao inicial
Data: 2026-05-22
Projeto: PlayWave

## Objetivo

Garantir que regenerar o codigo de pareamento de um dispositivo invalide de forma efetiva qualquer player antigo ainda rodando, forcando-o a parear novamente. Hoje o backend ja revoga o `device_token` ao regenerar, mas o player cacheia playlist em IndexedDB e segue tocando sem reagir a falha de autenticacao — e o backend nao valida `token_version`, entao se um token vazar/duplicar nao ha segunda barreira.

## Contexto

O cliente reclamou: "ao alterar o codigo de pareamento, o player continua funcionando". Auditoria em 2026-05-22 confirmou:

- `POST /devices/{id}/pairing-code/regenerate` ja seta `device.device_token = NULL`, incrementa `pairing_version` e `token_version`, marca `requires_repairing = true` e revoga `DeviceSession` ativas (linhas 938-989 de `backend/api/v1/devices.py`).
- Migration `20260521_0900_device_pairing_token_version.py` ja criou as colunas `pairing_version`, `token_version`, `requires_repairing` em `devices`.
- Porem `get_device_by_token` (linhas 83-103) valida apenas:
  - token existe no banco;
  - `device.is_blocked == False`;
  - `device.requires_repairing == False`.
- Nao compara `token_version` recebido vs persistido — defesa em profundidade ausente.
- O player guarda token em `localStorage` e cache de playlist em `IndexedDB` (`PlaylistCache`). Quando o token vira invalido:
  - chamada de playlist/heartbeat retorna 401;
  - o codigo do player nao trata 401 como "preciso reparear" — ele apenas registra erro e segue tocando do cache;
  - watchdog 120s sem heartbeat forca reload, mas reload tenta o mesmo token e cai no mesmo loop.
- Resultado pratico: TV antiga continua exibindo playlist em cache por horas/dias mesmo apos o operador "trocar o codigo".

## Escopo

Esta SPEC cobre:

- validacao de `token_version` no backend (header obrigatorio em rotas autenticadas por device);
- player enviar `token_version` no header `X-Device-Token-Version` em todas as requests;
- player tratar 401/403 com `error_code = TOKEN_VERSION_MISMATCH` ou `REQUIRES_REPAIRING` como sinal de "preciso reparear":
  - limpar `PairingStorage` (localStorage);
  - limpar `PlaylistCache` (IndexedDB);
  - resetar UI para tela de pareamento;
- novo endpoint `POST /devices/{id}/revoke-all-players` para revogar TODOS os players de um device sem precisar regenerar codigo;
- contador `revoked_at` (timestamp) para auditoria;
- botao no gerenciador "Forcar reparamento" alem do "Regenerar codigo";
- mensagem amigavel na tela de erro/pareamento explicando que o codigo mudou.

Esta SPEC nao cobre:

- pareamento multi-dispositivo (mesmo codigo em multiplas TVs) — escopo de SPEC futura;
- revogacao em lote por tenant — escopo de central de comandos;
- 2FA no pareamento — fora de escopo;
- auditoria avancada de mudancas de pareamento — vira parte de SPEC de auditoria.

## Arquivos analisados

### Backend

- `backend/api/v1/devices.py` (especialmente `get_device_by_token` linhas 83-103, `regenerate_pairing_code` linhas 938-989, `revoke_token` proximo a 990+).
- `backend/core/models.py` (`Device` linhas 109-165, especialmente `pairing_version` linha 116, `token_version` linha 117, `requires_repairing` linha 118).
- `backend/crud/entidades/crud_device.py`.
- `backend/alembic/versions/20260521_0900_device_pairing_token_version.py`.

### Frontend (gerenciador)

- `frontend/src/pages/DispositivoDetalhe.jsx` (botao regenerar codigo).
- `frontend/src/api/dispositivos.js` (`regenerarCodigoPareamento`, `revogarTokenDispositivo`).

### Player

- `frontend/src/pages/Player.jsx` (fase pairing/loading/playing).
- `frontend/src/api/http.js` (interceptor de request — alvo da mudanca de header).
- `frontend/src/api/dispositivos.js` (todas as funcoes que passam `token`).
- `frontend/src/player-core/storage.js` (`PairingStorage`, `PlaylistCache`).
- `frontend/src/player-core/network.js` (`fetchWithRetry` — alvo de tratamento de 401).

## Estado atual encontrado

### Ja existe

- Colunas `pairing_version`, `token_version`, `requires_repairing` no model `Device`.
- `regenerate_pairing_code` revoga token e revoga sessoes.
- `revoke_token` endpoint (verificar exato comportamento).
- Player armazena token em `PairingStorage` (localStorage).
- Player armazena playlist em `PlaylistCache` (IndexedDB).
- `get_device_by_token` ja recusa devices com `requires_repairing = true`.

### Existe parcialmente

- `token_version` armazenado mas nunca comparado.
- Player envia apenas `X-Device-Token`, nao envia `X-Device-Token-Version`.
- Player ao receber 401/403 nao tem branch dedicado para "preciso reparear" — cai em erro generico.
- Watchdog reload mantem o mesmo token, nao limpa storage.

### Falta ou precisa consolidar

- Header `X-Device-Token-Version` obrigatorio.
- Validacao de `token_version` em `get_device_by_token`.
- Codigo de erro padronizado nas respostas 401/403 (`TOKEN_VERSION_MISMATCH`, `REQUIRES_REPAIRING`, `TOKEN_REVOKED`, `DEVICE_BLOCKED`).
- Tratamento dedicado no `fetchWithRetry` para 401/403 + codigo especifico.
- Funcao `forceRepair()` no player que limpa storages e reseta UI.
- Endpoint para revogar todos os players sem regenerar codigo.
- Auditoria de quem regenerou codigo / quando.

## Requisitos funcionais

### RF004-01 — Backend valida `token_version`

Toda request autenticada por device token deve validar que o `token_version` enviado pelo player bate com o valor atual em `Device.token_version`.

Critérios:

- Header obrigatorio `X-Device-Token-Version: <int>`.
- Se ausente: tratar como versao 1 (compat com players antigos por 1 release, depois recusar).
- Se diferente do `device.token_version`: retornar 401 com `error_code = TOKEN_VERSION_MISMATCH`.
- Validacao centralizada na dependency `get_device_by_token`.
- Erro retornado em JSON: `{ "detail": "...", "error_code": "TOKEN_VERSION_MISMATCH", "current_version": int, "received_version": int }`.

### RF004-02 — Player envia `token_version` em toda request

O player deve persistir `token_version` junto com `device_token` e envia-lo como header.

Critérios:

- `PairingStorage` armazena `pw_player_token_version`.
- `http.js` interceptor injeta `X-Device-Token-Version` quando token presente.
- Endpoint de pareamento que devolve token tambem devolve `token_version`.
- Backend `GET /devices/by-code/{code}/status` ao confirmar pareamento ja retorna `token_version`.

### RF004-03 — Player trata 401/403 com codigo especifico como reparamento

Quando uma request retorna 401 ou 403 com `error_code` em `[TOKEN_VERSION_MISMATCH, REQUIRES_REPAIRING, TOKEN_REVOKED, DEVICE_BLOCKED]`, o player deve:

Critérios:

- Chamar `forceRepair(reason)` (nova funcao).
- `forceRepair` limpa `PairingStorage` (todas as keys `pw_player_*`).
- `forceRepair` limpa `PlaylistCache` (todos os entries do device).
- `forceRepair` reseta state React para fase `pairing`.
- `forceRepair` exibe mensagem amigavel: "Este player precisa ser pareado novamente. Codigo antigo foi revogado pelo administrador."
- Para `DEVICE_BLOCKED`: mensagem "Este dispositivo foi bloqueado. Entre em contato com o administrador."
- Player NAO tenta reusar token nem cache em nenhum cenario de `forceRepair`.

### RF004-04 — Endpoint de revogacao sem regenerar codigo

Criar endpoint para revogar todos os tokens ativos de um device, mantendo o `pairing_code` valido.

Critérios:

- `POST /devices/{id}/force-repair` (admin).
- Acao: incrementa `token_version`, seta `device_token = NULL`, marca `requires_repairing = true`, revoga sessions.
- NAO altera `pairing_code`.
- Util quando operador quer expulsar um player roubado/clonado mas o codigo continua o mesmo.
- Diferenca do `regenerate_pairing_code` que ja existe: este nao muda o codigo visivel no dashboard.
- Auditar `requested_by`, `requested_at`, motivo opcional.

### RF004-05 — Mensagem clara na regeneracao de codigo

Quando o operador clicar em "Regenerar codigo de pareamento", o gerenciador deve mostrar warning explicito.

Critérios:

- Modal: "Esta acao revoga todos os players atualmente pareados. Voce vai precisar reparear cada TV manualmente."
- Lista players atualmente ativos (`DeviceSession` ativas) e quantos serao afetados.
- Confirmacao requer clicar "Sim, revogar e gerar novo codigo".
- Apos regenerar: toast "Codigo regenerado. Os players antigos foram revogados."

### RF004-06 — Auditoria de pareamento

Toda regeneracao de codigo ou revogacao forcada deve ser registrada.

Critérios:

- Tabela `device_pairing_events`:
  - `id`, `device_id`, `event_type` (`code_regenerated` | `force_repair` | `token_revoked`), `previous_token_version`, `new_token_version`, `previous_pairing_code`, `new_pairing_code`, `requested_by`, `reason`, `created_at`.
- Endpoint admin para listar historico: `GET /devices/{id}/pairing-events`.
- Exibido no gerenciador como timeline no card de detalhes do device.

### RF004-07 — Backoff em pareamento repetido

Para evitar abuso, polling de status de pareamento deve ter limite.

Critérios:

- Player polling `/devices/by-code/{code}/status` a cada 3s atualmente.
- Backend rate-limita por IP ou por codigo: max 60 requests/min por codigo.
- Codigo expirado (15min sem confirmacao): retorna `error_code = PAIRING_CODE_EXPIRED`.
- Player exibe "Codigo expirou. Gerando novo..." e solicita novo.

### RF004-08 — Watchdog respeita reparamento

O watchdog do player que recarrega apos 120s sem heartbeat NAO deve recarregar quando player esta em `forceRepair`.

Critérios:

- `forceRepair` desativa watchdog.
- Watchdog reativa apenas apos pareamento concluido (volta para fase `loading`).

## Requisitos nao funcionais

- Mudanca de header e backward-compatible por 1 release (header ausente = versao 1).
- Limpar IndexedDB deve ser idempotente (chamar varias vezes nao quebra).
- `forceRepair` deve concluir em < 1s (limpeza local rapida).
- Endpoint `force-repair` deve responder em < 200ms (transacao curta).
- Auditoria nao bloqueia critical path — inserir em tabela `device_pairing_events` em commit separado se necessario.

## Decisoes de compatibilidade

- Compat de 1 release com player sem header `X-Device-Token-Version`: backend assume `token_version=1` quando header ausente.
- Apos compat-period, header obrigatorio — players antigos sao forcadamente repareados.
- `revoke_token` existente continua funcionando como atalho — alias semantico de `force-repair` sem auditoria forte.
- `regenerate_pairing_code` mantem comportamento atual + agora retorna lista de tokens revogados para audit.

## Riscos

- TVs em locais sem acesso fisico facil: regenerar codigo deixa offline ate alguem ir ate la fazer o pareamento.
- Reparamento manual em lote (ex: 100 TVs) eh dor operacional — mitigar com SPEC futura de "pre-pareamento por API".
- Se `token_version` nao for incrementado consistentemente (bug no codigo), todos os tokens viram invalidos.
- Player cacheado em browser antigo (Safari/iOS) pode ter problema para limpar IndexedDB — testar.
- Operador pode regenerar codigo sem entender impacto. Mitigado por modal de confirmacao com lista de impacto.

## Fora de escopo imediato

- Pareamento multi-fator (2FA).
- Pareamento com vinculacao a usuario especifico.
- Pareamento sem codigo manual (por NFC/QR).
- Revogacao em lote por tenant/grupo.
- Pre-pareamento via API (provisionamento programatico).
- Rotacao automatica de tokens.
