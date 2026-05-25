# SPEC 006 — Plano de Testes

## Backend (pytest)

### Resolver

- `test_resolve_osd_config_all_device_values_present`: device tem todos campos preenchidos → resolved == device.
- `test_resolve_osd_config_inherits_from_tenant`: device tem todos NULL → resolved == tenant.
- `test_resolve_osd_config_partial_override`: device.position=top_left, resto NULL → resolved.position=top_left, resto=tenant.
- `test_resolve_osd_config_no_tenant_uses_default`: tenant ausente → resolved == DEFAULT_OSD_CONFIG.

### Migration

- `test_migration_creates_tenant_columns_with_defaults`.
- `test_migration_creates_device_columns_nullable`.
- `test_migration_creates_current_audio_track_columns`.

### Heartbeat

- `test_heartbeat_persists_current_audio_track`: payload com track_id/name/started_at → DB atualiza.
- `test_heartbeat_with_null_track_clears_columns`: payload com track_id=null → DB zera as 3 colunas.
- `test_heartbeat_without_track_fields_does_not_clear`: payload sem campos track → DB preserva valor atual.

### Endpoint device-osd-config

- `test_patch_device_osd_partial_update`: enviar `{position: "top_left"}` atualiza so isso, mantem outros NULL.
- `test_patch_device_osd_reset_field_with_null`: enviar `{position: null}` reseta para herdar.
- `test_patch_device_osd_invalidates_cache`: chama invalidacao Redis e SSE.
- `test_patch_device_osd_invalid_duration`: `duration_seconds=5000` → 422 (max 3600).

### Endpoint tenant-osd-config

- `test_patch_tenant_osd_requires_all_fields`: faltando campo → 422.
- `test_patch_tenant_osd_invalidates_inheriting_devices`: tenant muda position, devices com position=NULL → cache invalidado; devices com position setado nao.

### Endpoint playlist

- `test_playlist_includes_resolved_osd_config`.
- `test_playlist_osd_config_uses_device_when_set`.
- `test_playlist_osd_config_uses_tenant_when_device_null`.

### GET device admin

- `test_get_device_returns_osd_config_local_and_effective`.
- `test_get_device_returns_current_audio_track_fields`.

## Player (Vitest)

### AudioPlayer onTrackChange

- `test_audio_player_calls_on_track_change_with_debounce`: aguarda 500ms apos mudanca.
- `test_audio_player_skips_redundant_calls`: trocar para mesma faixa nao re-chama.
- `test_audio_player_calls_with_null_when_disabled`.
- `test_audio_player_clears_timeout_on_unmount`.

### PlayerOSD slot novo

- `test_renders_audio_overlay_when_track_present_and_enabled`.
- `test_hides_audio_overlay_when_no_track`.
- `test_hides_audio_overlay_when_audio_disabled`.
- `test_hides_audio_overlay_when_show_current_audio_false`.
- `test_position_class_applied`: prop position=top_left → element tem classe "top-16 left-5".
- `test_font_size_class_applied`.
- `test_opacity_applied_inline_style`.
- `test_truncates_long_track_name`: nome 100 chars → DOM com class "truncate".
- `test_duration_seconds_hides_after_n_seconds`: mocks timer, avanca, verifica `opacity-0`.
- `test_duration_0_keeps_visible`: nao seta timeout.
- `test_fade_in_300ms`: classe transition-opacity duration-300 presente.

## Frontend Admin (Vitest + RTL)

### OSDConfigForm

- `test_form_allow_null_shows_inherit_options`.
- `test_form_disable_null_requires_all_fields`.
- `test_form_change_propagates_via_onChange`.
- `test_position_picker_4_quadrants`.

### OSDConfigPreview

- `test_preview_renders_overlay_per_position`.
- `test_preview_hides_when_show_current_audio_false`.
- `test_preview_uses_opacity_from_config`.

### DispositivoDetalhe

- `test_renders_osd_config_card`.
- `test_save_calls_atualizarOSDConfigDispositivo`.
- `test_state_card_shows_current_audio_track`.

### ConfigEmpresa

- `test_renders_tenant_osd_section`.
- `test_save_calls_atualizarOSDConfigEmpresa`.

## E2E Manual

### Caso 1: Habilitar overlay para empresa toda

1. Operador entra em ConfigEmpresa.
2. Ajusta overlay: position=top_right, duration_seconds=8, opacity=0.6.
3. Salva.
4. Player de teste (sem config propria): overlay aparece por 8s ao trocar de faixa.

### Caso 2: Customizar 1 device

1. DispositivoDetalhe da TV A.
2. Override: position=bottom_left, font_size=large.
3. Salva.
4. TV A: overlay no canto inf esquerdo, fonte grande.
5. Outras TVs do tenant: continuam usando top_right.

### Caso 3: Desabilitar em 1 device

1. DispositivoDetalhe da TV B.
2. show_current_audio = NAO.
3. Salva.
4. TV B: overlay nunca aparece.

### Caso 4: Sempre visivel

1. ConfigEmpresa: duration_seconds=0.
2. Player: overlay aparece e fica visivel enquanto musica toca.
3. Ao terminar playlist: overlay some.

### Caso 5: Nome longo

1. Trocar para faixa com nome "Symphony No. 9 in D Minor, Op. 125 - I. Allegro ma non troppo, un poco maestoso".
2. Overlay: trunca com "..." sem quebrar layout.

### Caso 6: Mudanca via SSE

1. Player tocando, overlay no top_right.
2. Admin muda config do device para bottom_left.
3. SSE invalidate → player recarrega playlist.
4. Proxima troca de faixa: overlay aparece no bottom_left.

### Caso 7: Painel admin mostra musica

1. Player tocando "Hino X".
2. Admin abre DispositivoDetalhe da TV.
3. Card "Estado atual" mostra "Tocando agora: Hino X (ha 12s)".
4. Refetch automatico a cada 10s atualiza elapsed.

### Caso 8: Sem audio na campanha

1. Campanha sem audio_playlist.
2. Player toca apenas video.
3. Overlay nao aparece (sem musica).
4. DispositivoDetalhe: "Tocando agora: —".

### Caso 9: Compat player legado

1. Player de versao anterior (sem suporte a `osd_config` no payload).
2. Player ignora bloco `osd_config`.
3. Renderiza PlayerOSD antigo (sem overlay de musica).
4. Comportamento atual preservado.

## Performance

- Render do overlay nao deve impactar FPS do video.
- Fade in/out via CSS transitions (GPU-accelerated).
- Re-render de PlayerOSD apenas quando `currentAudioTrack.id` muda (memo).

## Criterios de aceite finais

- [ ] Cliente confirma: nome da musica aparece no canto da TV.
- [ ] Operador escolhe posicao/duracao/opacidade/fonte.
- [ ] Defaults aplicam para todos os devices.
- [ ] Override por device funciona.
- [ ] Mudanca aplica em < 30s no player rodando.
- [ ] Painel admin mostra musica atual de cada player.
- [ ] Overlay nao atrapalha midia principal.
- [ ] Trunca nomes longos com elegancia.
- [ ] Sem regressao no PlayerOSD existente (logo, relogio, media info).
