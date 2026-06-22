# SPEC 013 — API Contract

Status: implementada — sem mudanca de contrato

## Contrato (inalterado)

Esta SPEC nao introduz nem altera endpoints. O contrato de `insertion_policy` ja existente foi mantido.

## Campo `insertion_policy`

Presente em `AudioSpot` e, como override opcional, em `AudioSpotSchedule`.

```json
{
  "insertion_policy": "wait_silence"
}
```

Valores aceitos (enum `AudioSpotInsertionPolicy`, `backend/core/models.py:756-759`):

- `interrupt`
- `wait_silence` (default)
- `fade_mix`

Precedencia de resolucao (`backend/services/spot_resolver.py:_resolve_insertion_policy`):

1. `AudioSpotSchedule.insertion_policy` (override), se definido.
2. `AudioSpot.insertion_policy`.
3. Fallback `"wait_silence"`.

## Payload retornado ao player

`GET` de playlist/schedule (via `_to_player_payload` em `spot_resolver.py` e equivalente em `audio_spot_scheduler.py`) inclui:

```json
{
  "id": "schedule-uuid",
  "spot_id": "spot-uuid",
  "spot_name": "Promocao Black Friday",
  "file_url": "https://cdn.../spot.mp3",
  "interval_seconds": 600,
  "insertion_policy": "wait_silence",
  "priority": 0,
  "is_active": true
}
```

O player consome este payload e decide **quando exatamente** tocar o spot dentro da janela de elegibilidade — essa decisao (esperar `ended` ou tocar imediatamente) e o que esta SPEC corrigiu, inteiramente no client (`AudioManager.playSpot`), sem precisar de novo campo ou endpoint.

## Por que nao foi necessaria migration

O bug nao estava na modelagem de dados (o campo e os valores ja existiam e sao suficientes), mas na interpretacao do valor `wait_silence` pelo player. Renomear o enum para `WAIT_TRACK_END`/`INTERRUPT_WITH_FADE`/`DUCKING` (nomenclatura do documento original) exigiria:

- Migration Alembic alterando o tipo enum no Postgres.
- Atualizar `schemas_completos.py`.
- Atualizar todos os call sites que comparam strings (`"interrupt"`, `"wait_silence"`, `"fade_mix"`) no frontend.

Sem ganho funcional, pois a semantica final e identica. Mantido como nao-objetivo desta SPEC (ver `README.md`).
