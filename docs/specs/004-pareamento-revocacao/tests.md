# SPEC 004 — Plano de Testes

## Backend (pytest)

### Validacao de token_version

- `test_request_with_correct_token_version_passes`: header bate, 200 OK.
- `test_request_with_mismatched_token_version_returns_401`: response inclui `error_code=TOKEN_VERSION_MISMATCH`, `current_version`, `received_version`.
- `test_request_without_version_header_compat_period`: warning no log, request aceita.
- `test_request_without_version_header_after_compat_period`: 401 `TOKEN_VERSION_REQUIRED` (flag `STRICT_TOKEN_VERSION_VALIDATION` em settings).
- `test_blocked_device_returns_403`: `error_code=DEVICE_BLOCKED`.
- `test_requires_repairing_device_returns_401`: `error_code=REQUIRES_REPAIRING`.

### Endpoint regenerate

- `test_regenerate_increments_versions`: `token_version` e `pairing_version` ambos sobem.
- `test_regenerate_clears_device_token`: `device.device_token` vira `NULL`.
- `test_regenerate_revokes_sessions`: `DeviceSession` ativas viram `revoked`.
- `test_regenerate_creates_pairing_event`: row inserida em `device_pairing_events` com previous/new values.
- `test_regenerate_publishes_sse_event`: `pairing:revoked` publicado no canal correto (mock Redis).
- `test_regenerate_returns_previous_pairing_code`: response inclui codigo anterior.

### Endpoint force-repair

- `test_force_repair_increments_token_version_only`: `token_version` sobe, `pairing_version` NAO sobe.
- `test_force_repair_keeps_pairing_code`: `device.pairing_code` permanece.
- `test_force_repair_revokes_sessions`: sessions viram revoked.
- `test_force_repair_creates_pairing_event`: row inserida em `device_pairing_events` com `event_type=force_repair`.
- `test_force_repair_accepts_optional_reason`: reason persiste no evento.

### Endpoint pairing-events

- `test_list_pairing_events_default_pagination`: limit 50.
- `test_list_pairing_events_max_limit`: limit > 200 retorna 422.
- `test_list_pairing_events_filter_by_event_type`: ?event_type=code_regenerated retorna apenas esses.
- `test_list_pairing_events_orders_desc`: mais recente primeiro.
- `test_list_pairing_events_only_admin`: usuario nao-admin recebe 403.

### Auditoria

- `test_pair_confirm_creates_paired_event_first_time`: `event_type=paired` quando `pairing_version=1`.
- `test_pair_confirm_creates_re_paired_event_after_regenerate`: `event_type=re_paired` quando `pairing_version>1`.
- `test_block_device_creates_event`: row com `device_blocked`.

## Player (Vitest/JS)

### `storage.js`

- `test_pairing_storage_saves_token_version`: `setTokenVersion(2)` persiste em localStorage.
- `test_pairing_storage_returns_null_when_absent`: `tokenVersion()` retorna `null` se nunca setou.
- `test_pairing_storage_clear_removes_token_version`: `clear()` apaga a key.

### `repair.js`

- `test_force_repair_clears_pairing_storage`: localStorage limpo apos chamada.
- `test_force_repair_clears_playlist_cache`: IndexedDB limpo (mock).
- `test_force_repair_calls_callback`: callback registrado recebe `reason`.
- `test_force_repair_hard_reload_if_no_callback`: chama `window.location.reload` se nao ha callback.
- `test_force_repair_antiloop_limits_to_3_in_5min`: 4a chamada espera 30s.
- `test_force_repair_resets_counter_after_5min`: contador zera.

### `http.js` interceptors

- `test_request_interceptor_injects_token_and_version`: ambos headers presentes na request.
- `test_request_interceptor_skips_if_no_token`: nenhum header injetado se localStorage vazio.
- `test_response_401_with_repair_error_code_triggers_force_repair`: spy em `forceRepair`.
- `test_response_401_without_error_code_does_not_trigger`: erro generico nao dispara repair.
- `test_response_500_does_not_trigger_repair`: erro de servidor passa direto.

### `Player.jsx` (integration com MSW)

- `test_force_repair_callback_resets_to_pairing_phase`: state volta para `phase=pairing`.
- `test_force_repair_callback_displays_warning_message`: banner amarelo com mensagem.
- `test_sse_pairing_revoked_triggers_force_repair`: spy em `forceRepair`.
- `test_watchdog_disabled_during_pairing`: nao recarrega em `phase=pairing`.

## E2E Manual

### Caso 1: Regenerar codigo expulsa player

1. Parear TV de teste com codigo "TV-AB12".
2. TV comeca a tocar playlist.
3. Logar como admin no gerenciador.
4. Abrir DispositivoDetalhe da TV.
5. Confirmar "Sessoes ativas: 1".
6. Clicar "Regenerar codigo".
7. Modal abre, listar 1 sessao ativa.
8. Preencher motivo "Teste E2E".
9. Confirmar.
10. **Esperado:** Toast "Codigo regenerado. 1 player foi desconectado."
11. **Esperado em < 5s:** TV de teste volta para tela de pareamento com banner amarelo "O codigo de pareamento foi atualizado pelo administrador. Pareie novamente."
12. **Esperado:** TV exibe NOVO codigo de pareamento (diferente do anterior).
13. Pairing events lista deve mostrar nova row `code_regenerated` com motivo "Teste E2E".

### Caso 2: Force-repair mantem codigo

1. Parear TV com codigo "TV-CD34".
2. TV tocando.
3. Gerenciador: clicar "Forcar reparamento".
4. Modal: ver codigo "TV-CD34" listado como "permanece igual".
5. Confirmar.
6. **Esperado:** TV volta para pareamento com banner.
7. **Esperado:** Codigo na tela da TV ainda eh "TV-CD34" (mesmo codigo).
8. Operador pode reparear com "TV-CD34" sem mudar nada.

### Caso 3: Bloqueio de dispositivo

1. TV pareada e tocando.
2. Gerenciador: clicar "Bloquear dispositivo".
3. **Esperado:** TV exibe "Dispositivo bloqueado. Entre em contato com o administrador."
4. Player nao consegue retomar mesmo com token valido.

### Caso 4: Compat-period

1. Build de player ANTERIOR a esta SPEC (sem `X-Device-Token-Version`).
2. Player faz request normal.
3. **Esperado:** Backend aceita, logs mostram warning.
4. Apos toggling `STRICT_TOKEN_VERSION_VALIDATION=true`: mesma request → 401 `TOKEN_VERSION_REQUIRED`.

### Caso 5: Anti-loop

1. Simular backend rejeitando todas requests com `TOKEN_VERSION_MISMATCH` (broken state).
2. Player tenta reparear → loop entre `forceRepair` e nova falha.
3. **Esperado:** Apos 3 forceRepairs em 5min, player espera 30s antes da proxima.
4. Em logs do player: "too many repairs in 5min — backing off".

## Carga (opcional)

- Simular 50 players ativos.
- Disparar regenerate em 10 deles simultaneamente.
- Verificar tempo total de resposta < 2s.
- Verificar contagem correta de `device_pairing_events` (10 rows).

## Criterios de aceite finais

- [ ] Cliente confirma: regenerar codigo expulsa player antigo em < 10s.
- [ ] Force-repair disponivel como acao separada.
- [ ] Historico de pareamento visivel no gerenciador.
- [ ] Mensagens amigaveis na tela de pareamento explicam o que aconteceu.
- [ ] Anti-loop previne degradacao em cenarios de erro permanente.
- [ ] Compat-period documentado e funcionando.
