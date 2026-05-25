# SPEC 001 — Player

## Arquivos analisados

- `frontend/src/pages/Player.jsx`
- `frontend/src/components/player/MediaRenderer.jsx`
- `frontend/src/player-core/storage.js`
- `frontend/src/player-core/commands.js`
- `frontend/src/api/dispositivos.js`
- `backend/api/v1/devices.py`

## Estado atual

O player:

- pareia com device token;
- busca playlist em `/devices/{device_id}/playlist`;
- toca midias recebidas;
- usa `onEnded` para video/audio sem duracao manual;
- usa timer para midias com `duration`;
- guarda playlist em cache local;
- envia heartbeat;
- registra playback log;
- consulta comandos pendentes;
- escuta SSE de atualizacao.

## Contrato esperado de midia

O player deve receber:

- `id`
- `media_id`
- `name`
- `type`
- `file_url`
- `thumbnail_url`
- `duration`
- `duration_seconds`
- `display_duration_seconds`
- `play_until_end`
- `file_version`
- `file_hash`
- `mime_type`
- `status`
- `starts_at`
- `ends_at`

## Regras de reproducao

### Video

- Se `display_duration_seconds` for nulo, tocar ate o fim.
- Se `display_duration_seconds` existir, avancar ao atingir esse tempo.
- Se video falhar, registrar erro e pular para proxima midia valida.

### Audio

- Mesma regra de video para duracao.
- Para audio visual na playlist, renderizar player ou tela dedicada conforme UI atual.

### Imagem

- Usar `display_duration_seconds`.
- Fallback para `duration`.
- Se nao houver duracao, usar padrao seguro.

### Link/webview/html

- Usar `display_duration_seconds`.
- Se iframe falhar, registrar erro e seguir fila.

## Regras de cache

O player deve usar `file_hash` e `file_version` para decidir se o cache local ainda e valido.

Regras:

- Mesmo `media_id` com novo `file_version` deve baixar/recarregar novo arquivo.
- Mesmo `media_id` com novo `file_hash` deve invalidar cache antigo.
- Se download falhar, manter arquivo antigo apenas se politica permitir.
- Evitar tela preta durante atualizacao.

## Filtro de validade

Preferencialmente o backend nao deve enviar midias invalidas.

Mesmo assim, o player deve ser resiliente:

- nao tocar midia expirada se receber por erro;
- nao tocar midia antes de `starts_at`;
- nao tocar midia com `status` diferente de `available`;
- seguir para proxima midia valida.

## Heartbeat futuro recomendado

Adicionar ao heartbeat:

- `current_campaign_id`;
- `current_config_version`;
- `current_media_id`;
- `current_media_name`;
- `queue_version`;
- `storage_used`;
- `storage_free`;
- `app_version`;
- `os`;
- `screen_resolution`;
- `last_error`;
- `playback_status`.

## Pendencias

- Comparacao efetiva de `file_hash/file_version` no cache local.
- Registro estruturado de erro de midia.
- Status de cache por midia/dispositivo.
- Relatorio de midia falhada.
- Confirmacao de execucao por item da fila.
