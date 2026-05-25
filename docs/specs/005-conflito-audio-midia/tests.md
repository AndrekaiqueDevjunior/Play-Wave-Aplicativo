# SPEC 005 — Plano de Testes

## Backend (pytest)

### Resolver hierarquico

```python
@pytest.mark.parametrize("media_p,campaign_p,device_p,tenant_p,expected", [
    ("mix",      None, None, "auto", "mix"),
    (None, "radio_only", None, "auto", "radio_only"),
    (None, None, "mix",       "auto", "mix"),
    (None, None, None,        "media_audio_only", "media_audio_only"),
    (None, None, None,         None, "auto"),   # fallback hardcoded
])
def test_resolver_hierarchy(media_p, campaign_p, device_p, tenant_p, expected):
    ...
```

### Resolver com `auto`

```python
@pytest.mark.parametrize("has_audio,has_radio,expected_muted,expected_audio", [
    (True,  True,  False, False),  # video com audio + radio → video toca
    (True,  False, False, False),  # video com audio sem radio → video toca
    (False, True,  True,  True),   # midia sem audio + radio → radio toca
    (False, False, True,  False),  # midia sem audio sem radio → silencio
])
def test_resolver_auto_logic(has_audio, has_radio, expected_muted, expected_audio):
    ...
```

### Backfill

- `test_backfill_video_muted_true_with_radio_becomes_muted_video_with_radio`.
- `test_backfill_video_muted_false_with_radio_becomes_mix`.
- `test_backfill_video_muted_false_without_radio_becomes_auto`.
- `test_backfill_idempotent`: rodar 2x, mesmo resultado.

### Deteccao de audio (ffprobe)

- `test_detect_audio_streams_video_with_audio`: video real com trilha → True.
- `test_detect_audio_streams_video_without_audio`: video silencioso → False.
- `test_detect_audio_streams_invalid_file`: arquivo corrompido → False com warning.
- `test_detect_audio_streams_missing_ffprobe`: ffprobe ausente → True (fallback conservador) com warning.

### Endpoint recompute

- `test_recompute_only_for_video`: imagem retorna 400.
- `test_recompute_updates_has_audio`: chama detect, atualiza DB.
- `test_recompute_invalidates_affected_campaigns`: campanhas com policy `auto` que usam essa midia tem cache invalidado.

### Endpoint payload do player

- `test_playlist_includes_audio_policy_effective_per_media`.
- `test_playlist_includes_audio_policy_default_at_campaign_level`.
- `test_playlist_includes_audio_fade_ms_at_campaign_level`.
- `test_legacy_video_muted_still_present_for_compat`.

### Cache busting

- `test_update_tenant_policy_invalidates_campaigns_with_null_policy`.
- `test_update_device_policy_invalidates_associated_campaigns_with_null_policy`.
- `test_update_campaign_policy_invalidates_only_this_campaign`.
- `test_update_media_policy_invalidates_all_campaigns_using_this_media`.
- `test_update_media_has_audio_invalidates_only_auto_policy_campaigns`.

## Player (Vitest)

### Hook `useAudioConflictResolver`

Cobertura matriz: 5 politicas × {has_audio T/F} × {has_radio T/F} × {spot T/F} = 40 casos.

```javascript
describe("useAudioConflictResolver", () => {
  test.each([
    // policy, has_audio, has_radio, expected_muted, expected_audio
    ["auto", true,  true,  false, false],
    ["auto", true,  false, false, false],
    ["auto", false, true,  true,  true],
    ["auto", false, false, true,  false],
    ["radio_only", true,  true,  true,  true],
    ["radio_only", false, true,  true,  true],
    ["radio_only", true,  false, true,  false],
    ["media_audio_only", true,  true,  false, false],
    ["media_audio_only", false, true,  true,  false],
    ["mix", true,  true,  false, true],
    ["mix", false, true,  true,  true],
    ["muted_video_with_radio", true,  true,  true, true],
    ["muted_video_with_radio", false, true,  true, true],
  ])("policy=%s has_audio=%s has_radio=%s → muted=%s audio=%s", (policy, ha, hr, mu, ae) => {
    const { result } = renderHook(() => useAudioConflictResolver({
      currentMedia: { id: "m1", audio_policy_effective: policy, has_audio: ha, type: "video" },
      audioPlaylist: hr ? { tracks: [{ id: "t1" }] } : null,
    }));
    expect(result.current.videoMuted).toBe(mu);
    expect(result.current.audioEnabled).toBe(ae);
  });
});
```

### Spot tem prioridade

```javascript
test("spot overrides everything", () => {
  const { result } = renderHook(() => useAudioConflictResolver({
    currentMedia: { id: "m1", audio_policy_effective: "radio_only", has_audio: false },
    audioPlaylist: { tracks: [] },
    currentSpot: { audio_id: "s1" },
  }));
  expect(result.current).toEqual({ videoMuted: true, audioEnabled: true, audioDucked: false });
});
```

### Sem currentMedia

```javascript
test("no media: audio plays if radio available", () => {
  const { result } = renderHook(() => useAudioConflictResolver({
    currentMedia: null,
    audioPlaylist: { tracks: [{ id: "t1" }] },
  }));
  expect(result.current.audioEnabled).toBe(true);
  expect(result.current.videoMuted).toBe(true);
});
```

### `AudioPlayer.jsx` fade

```javascript
test("fade in from 0 to target volume over fadeMs", async () => {
  const { rerender } = render(
    <AudioPlayer playlist={{ tracks: [{ src: "test.mp3" }] }} enabled={false} volume={0.7} fadeMs={200} />
  );
  const audio = document.querySelector("audio");
  audio.play = jest.fn(() => Promise.resolve());

  rerender(<AudioPlayer playlist={...} enabled={true} volume={0.7} fadeMs={200} />);

  await waitFor(() => {
    expect(audio.volume).toBeCloseTo(0.7, 1);
  }, { timeout: 300 });
});
```

### `Player.jsx` integration (MSW)

- `test_player_uses_resolver_decision_for_video_muted`.
- `test_player_uses_resolver_decision_for_audio_enabled`.
- `test_player_fallback_to_video_muted_when_no_audio_policy_effective`.
- `test_player_logs_audio_decision_on_media_change`.

## E2E Manual

### Caso 1: Policy `auto` funciona

Setup:
- Tenant: `audio_policy_default = auto`.
- Campanha: 3 midias:
  1. Video com audio nativo.
  2. Imagem.
  3. Video silencioso.
- Radio configurada na campanha.

Esperado:
- Ao trocar para midia 1: radio para com fade, video toca com som.
- Ao trocar para midia 2: video desliga (eh imagem), radio retoma com fade.
- Ao trocar para midia 3: video sem audio, radio continua tocando (has_audio=False).

### Caso 2: Override por midia

Setup:
- Campanha policy = `mix`.
- 2 midias:
  1. Video instrumental (sem voz) → midia override = `mix`.
  2. Video com voz importante → midia override = `media_audio_only`.

Esperado:
- Midia 1: audio do video + radio simultaneos.
- Midia 2: radio para, apenas audio da midia toca.

### Caso 3: Mudanca em tempo real

Setup:
- Player tocando campanha.

Acoes:
1. Admin muda `tenant.audio_policy_default` de `auto` para `radio_only`.
2. Backend invalida cache, publica SSE.
3. Player recarrega playlist.
4. **Esperado:** Proxima troca de midia respeita nova politica. Midia atual termina com politica antiga (sem corte brusco).

### Caso 4: Fade duration ajustavel

Setup:
- Tenant: `audio_fade_ms = 1000`.

Esperado:
- Transicoes de audio levam 1 segundo (visivel pelo volume crescente).
- Diminuir para 50ms: transicao quase instantanea.
- Setar 0: sem fade.

### Caso 5: Recompute has_audio

Setup:
- Midia video antiga com `has_audio = NULL`.

Acoes:
1. Admin abre MediaFormModal.
2. Indicador mostra "nao detectado".
3. Clica "Recalcular".
4. Backend roda ffprobe, retorna True ou False.

Esperado:
- Campo atualiza.
- Campanhas com policy `auto` que usam essa midia tem cache invalidado.
- Player recarrega e comportamento muda conforme detecao.

### Caso 6: Compatibilidade com player antigo

Setup:
- Player de versao anterior a esta SPEC (sem `audio_policy_effective` no payload — quer dizer, codigo nao le esse campo).
- Backend novo enviando ambos `video_muted` e `audio_policy_effective`.

Esperado:
- Player antigo continua usando `video_muted`.
- Comportamento antigo preservado.

## Carga / Performance

- Resolver no backend para 100 midias × 5 niveis = ~500 lookups. Deve ser sub-ms.
- Hook no player nao chama nada custoso (apenas useMemo). Re-renderiza em < 1ms.

## Criterios de aceite finais

- [ ] Cliente confirma: video com audio + radio nao mais misturado conforme politica escolhida.
- [ ] Hierarquia funciona: override por midia tem prioridade sobre campanha.
- [ ] Transicoes audio suaves com fade 200ms.
- [ ] Admin pode escolher politica em 4 niveis.
- [ ] Mudanca de politica via SSE reflete na proxima troca de midia.
- [ ] Backfill cobre 100% das campanhas existentes sem regressao.
- [ ] Detecao automatica `has_audio` para uploads novos via ffprobe.
- [ ] Documentacao explicativa publicada.
