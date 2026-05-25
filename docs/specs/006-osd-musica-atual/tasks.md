# SPEC 006 — Tasks

Status: `[ ]` pendente · `[~]` parcial · `[x]` concluido · `[!]` bloqueado/decisao.

## Banco

- [x] Criar migration `20260523_1000_osd_config.py`:
  - [x] `CREATE TYPE osd_position_enum`.
  - [x] `CREATE TYPE osd_font_size_enum`.
  - [x] `ALTER TABLE tenants ADD COLUMNs osd_*` (NOT NULL com defaults).
  - [x] `ALTER TABLE devices ADD COLUMNs osd_*` (nullable) + `current_audio_track_*`.

## Backend — models

- [x] Atualizar `Tenant` com 5 colunas osd_*.
- [x] Atualizar `Device` com 5 colunas osd_* (nullable) + 3 colunas current_audio_track_*.

## Backend — resolver

- [x] Criar `backend/services/osd_config_resolver.py` com `resolve_osd_config(device, tenant)`.
- [x] Testes unitarios do resolver.

## Backend — endpoints

- [x] `GET /devices/{id}/playlist` retorna bloco `osd_config` resolvido.
- [x] `POST /devices/{id}/heartbeat` aceita `current_audio_track_id`, `current_audio_track_name`, `current_audio_track_started_at`.
- [x] Heartbeat persiste em colunas `devices.current_audio_track_*`.
- [x] `GET /devices/{id}` (admin) retorna `osd_config_local` + `osd_config_effective` + `current_audio_track_*`.
- [x] `PATCH /devices/{id}/osd-config` (admin): aceita campos opcionais/nullable, invalida cache.
- [x] `PATCH /tenants/{id}/osd-config` (admin): aceita campos obrigatorios, invalida cache de devices que herdam.

## Backend — schemas Pydantic

- [x] Enum `OSDPosition`, `OSDFontSize`.
- [x] `OSDConfig` (todos obrigatorios).
- [x] `DeviceOSDConfigUpdate` (nullable).
- [x] `TenantOSDConfigUpdate` (obrigatorios).
- [x] Estender `HeartbeatRequest`.
- [x] Estender `PlayerPlaylistResponse` com `osd_config`.
- [x] Estender `DeviceResponse` (admin) com `osd_config_local`, `osd_config_effective`, `current_audio_track_*`.

## Backend — cache busting

- [x] Mudanca em `device.osd_*` invalida cache do device.
- [x] Mudanca em `tenant.osd_*` invalida cache de devices que tem o campo equivalente em NULL.
- [x] Helper `find_devices_inheriting_osd_field(tenant, field_name)`.

## Player — AudioPlayer

- [x] Adicionar prop `onTrackChange?: (track | null) => void`.
- [x] Implementar debounce 500ms via `useRef`.
- [x] Reportar `null` quando `enabled` vira false.
- [x] Nao re-reportar mesma faixa (compara ID).

## Player — PlayerOSD

- [x] Aceitar props `currentAudioTrack`, `audioEnabled`, `osdConfig`.
- [x] Renderizar slot novo com posicao/fonte/opacidade conforme `osdConfig`.
- [x] `useEffect` controla visibilidade: `duration_seconds > 0` faz hide apos N segundos; `0` mantem sempre.
- [x] Truncate de nome longo com `max-w-[30vw]` e `truncate`.
- [x] Fade in/out 300ms via CSS transition-opacity.
- [x] Z-index correto (acima da midia, abaixo de erros).
- [x] `pointer-events-none` quando fade out.

## Player — Player.jsx

- [x] Manter estado `currentAudioTrack`.
- [x] Passar callback ao AudioPlayer.
- [x] Ler `osd_config` da playlist e passar ao PlayerOSD.
- [x] Estender heartbeat para incluir `current_audio_track_*`.
- [x] Manter ref `trackStartedAtRef` para reportar timestamp.

## Frontend Admin — componente reusavel

- [x] Criar `frontend/src/components/shared/OSDConfigForm.jsx`.
- [x] Criar `frontend/src/components/shared/OSDConfigPreview.jsx`.
- [x] Criar subcomponentes `PositionPicker`, `NullableToggle`, `NullableSlider`, `NullableNumberInput`.

## Frontend Admin — telas

- [x] `ConfigEmpresa.jsx` ganha secao "Overlay de musica" com form + preview.
- [x] `DispositivoDetalhe.jsx` ganha card "Overlay OSD" com form (allowNull) + preview.
- [x] `DispositivoDetalhe.jsx` "Estado atual" mostra "Tocando agora" com nome + elapsed.
- [x] React Query refetch a cada 10s do device aberto para atualizar musica atual.

## Frontend Admin — API clients

- [x] `frontend/src/api/dispositivos.js`: `atualizarOSDConfigDispositivo(id, config)`.
- [x] `frontend/src/api/tenants.js`: `atualizarOSDConfigEmpresa(id, config)`.

## Testes

### Backend

- [x] Resolver hierarquico: device override tenant override default.
- [ ] Migration aplica defaults nos tenants existentes.
- [ ] `PATCH /devices/{id}/osd-config` com null no campo X reseta para herdar.
- [ ] `PATCH /tenants/{id}/osd-config` invalida cache de devices afetados.
- [ ] Heartbeat persiste track info em colunas.
- [ ] Heartbeat com `current_audio_track_id: null` zera as colunas.

### Player

- [x] AudioPlayer chama onTrackChange apos debounce 500ms.
- [x] AudioPlayer nao re-chama com mesma faixa.
- [x] AudioPlayer chama com null quando enabled vira false.
- [x] PlayerOSD renderiza overlay com config recebida.
- [x] PlayerOSD oculta apos `duration_seconds`.
- [x] PlayerOSD mantem visivel com `duration_seconds=0`.
- [x] Trunca nome longo sem quebrar.

### Frontend Admin

- [ ] OSDConfigForm com `allowNull` mostra opcao herdar.
- [ ] OSDConfigForm com `allowNull=false` exige todos os campos.
- [ ] OSDConfigPreview reflete config em tempo real.
- [ ] Salvar device config invalida `["device", id]` query.

### E2E Manual

- [ ] Tenant config = top_right, duration_seconds=5: TV mostra overlay 5s no canto sup direito.
- [ ] Trocar position via gerenciador: TV reflete em < 30s.
- [ ] Device override = bottom_left: TV move overlay.
- [ ] Disable em device: overlay some.
- [ ] Sem audio playlist na campanha: overlay nao aparece.
- [ ] Trocar faixa rapidamente (skip 3x em 1s): overlay aparece so com a faixa final (debounce).
- [ ] Nome de musica com 100 caracteres: trunca com "..." sem quebrar.
- [ ] DispositivoDetalhe mostra "Tocando agora: X (ha Ns)".

## Documentacao

- [ ] Atualizar manual do operador com nova funcionalidade.
- [ ] Screenshot da config em ConfigEmpresa e DispositivoDetalhe.

## Rollout

- [ ] Deploy backend (migration + endpoints).
- [ ] Deploy player.
- [ ] Deploy frontend admin.
- [ ] Operador define defaults globais no tenant.
- [ ] Validar com cliente em pelo menos 1 device.

## Pos-rollout

- [ ] Monitorar uso: quantos tenants ativam overlay vs deixam off.
- [ ] Feedback: querem mais configuracoes (cor, fonte custom)?
- [ ] SPEC futura: artista/album/capa se houver demanda.
