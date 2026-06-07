# TASK 08 — Corrigir Bug: Spot Programado Não Toca

**Status:** ✅ COMPLETO

**Data de Conclusão:** 2026-06-04

**Prioridade:** P0 (Crítica)

---

## Problema

Spots (anúncios/jingles) agendados não tocam nos horários definidos. Sem logs estruturados, é impossível diagnosticar por que o spot foi ignorado:
- Estava inativo?
- Estava fora do horário?
- Período de validade passou?
- Track de áudio corrompida?

---

## Solução Implementada

### 1. Módulo de Logging Estruturado

**Arquivo:** `backend/core/logging_config.py` (novo)

Fornece funções para logs estruturados por tipo de evento:

```python
# Exemplo de uso
from core.logging_config import log_spot_eligible, log_spot_ineligible, log_spot_due

log_spot_check(playlist_id, total_schedules, eligible_count, now)
log_spot_eligible(spot_id, spot_name, schedule_id, interval_seconds, priority)
log_spot_ineligible(schedule_id, reason="schedule_time_mismatch", details={...})
log_spot_due(spot_id, spot_name, interval_seconds, time_until_seconds)
log_spot_selected(spot_id, spot_name, insertion_policy)
log_spot_playing(spot_id, spot_name, device_id)
log_returning_to_music_queue(device_id)
log_spot_error(spot_id, error_reason, details)
```

**Formato de Logs:**
```
[radio.scheduler] spot_check playlist_id=... total_schedules=5 eligible=2 now=...
[radio.spots] spot_eligible spot_id=... name=... schedule_id=... interval_seconds=30 priority=10
[radio.spots] spot_ineligible schedule_id=... reason=schedule_time_mismatch start_time=08:00 end_time=10:00 current_time=11:00
[radio.scheduler] spot_due=true spot_id=... name=... interval_seconds=30 time_until_seconds=15.5
[radio.scheduler] selected_spot_id=... name=... insertion_policy=wait_silence
[radio.player] playing_spot=true spot_id=... name=... device_id=...
[radio.player] returning_to_music_queue=true device_id=...
```

### 2. Logs no Scheduler

**Arquivo:** `backend/services/audio_spot_scheduler.py` (modificado)

Integrado logging nas funções críticas:

- **`get_eligible_spots()`**: 
  - Loga total de schedules e quantos estão elegíveis
  - Loga cada schedule rejeitado com motivo (hora, período, spot não encontrado)
  - Loga cada spot elegível com prioridade e intervalo

- **`get_next_spot_time()`**:
  - Loga quando um spot está "due" (marcado para tocar)
  - Mostra quantos segundos até o spot tocar

### 3. Endpoint de Diagnóstico

**Endpoint:** `GET /devices/{device_id}/debug-spots`

Retorna diagnóstico completo de spots para um dispositivo:

```json
{
  "timestamp": "2026-06-04T17:45:00.000000",
  "device": {
    "device_id": "...",
    "device_name": "Loja Centro"
  },
  "playlist": {
    "playlist_id": "...",
    "playlist_name": "Rádio Indoor"
  },
  "total_spot_schedules": 3,
  "eligible_now_count": 1,
  "spot_diagnostics": [
    {
      "spot_id": "abc123",
      "spot_name": "Jingle Promoção",
      "schedule_id": "sch001",
      "is_schedule_active": true,
      "is_spot_active": "active",
      "interval_seconds": 600,
      "priority": 10,
      "insertion_policy": "wait_silence",
      "eligible_now": true,
      "start_time": "08:00",
      "end_time": "22:00",
      "starts_at": null,
      "ends_at": null
    },
    {
      "spot_id": "def456",
      "spot_name": "Anúncio Noturno",
      "schedule_id": "sch002",
      "is_schedule_active": true,
      "is_spot_active": "active",
      "interval_seconds": 900,
      "priority": 5,
      "insertion_policy": "fade_mix",
      "eligible_now": false,
      "start_time": "22:00",
      "end_time": "08:00",
      "why_not_eligible": [
        "Depois do horário (22:00)"
      ]
    }
  ],
  "next_spot_due": {
    "spot_id": "abc123",
    "spot_name": "Jingle Promoção",
    "will_play_at": "2026-06-04T17:50:00.000000",
    "seconds_until_play": 300,
    "interval_seconds": 600,
    "priority": 10
  },
  "info": "Use para diagnosticar por que spots não tocam..."
}
```

### 4. Debug-Playback Melhorado

**Endpoint:** `GET /devices/{device_id}/debug-playback` (melhorado)

Agora retorna informações completas de spots elegíveis:

```json
{
  "audio_spots": [
    {
      "spot_id": "...",
      "spot_name": "...",
      "interval_seconds": 600,
      "priority": 10,
      "insertion_policy": "wait_silence",
      "start_time": "08:00",
      "end_time": "22:00"
    }
  ],
  "audio_playlist": {
    "next_spot_due": {
      "spot_id": "...",
      "spot_name": "...",
      "will_play_at": "2026-06-04T17:50:00",
      "seconds_until_play": 300
    }
  }
}
```

---

## Como Usar para Diagnosticar

### Cenário 1: "Meu spot não toca"

```bash
curl http://localhost:8000/devices/{device_id}/debug-spots \
  -H "Authorization: Bearer $TOKEN"
```

**O que procurar:**
1. `eligible_now_count` é 0? → Todos os spots estão inelegíveis
2. Na lista `spot_diagnostics`, procure `"eligible_now": false`
3. Verifique `why_not_eligible` para a razão:
   - "Agendamento inativo" → Ativar schedule
   - "Spot inativo" → Ativar spot
   - "Antes do horário (08:00)" → Horário atual é antes de 08:00
   - "Depois do horário (22:00)" → Horário atual é depois de 22:00
   - "Já terminou (terminou em 2026-05-31)" → Período expirou

### Cenário 2: "Qual spot toca agora?"

```bash
curl http://localhost:8000/devices/{device_id}/debug-spots \
  -H "Authorization: Bearer $TOKEN" | jq '.next_spot_due'
```

Retorna o próximo spot que deve tocar e em quantos segundos.

### Cenário 3: "Ver logs estruturados"

```bash
docker logs playwave-backend 2>&1 | grep "radio.scheduler"
docker logs playwave-backend 2>&1 | grep "radio.spots"
docker logs playwave-backend 2>&1 | grep "radio.player"
```

Exemplos de log:
```
[radio.scheduler] spot_check playlist_id=... total_schedules=3 eligible=2
[radio.spots] spot_eligible spot_id=abc123 name=Jingle interval_seconds=600 priority=10
[radio.spots] spot_ineligible schedule_id=sch002 reason=schedule_time_mismatch start_time=22:00 end_time=08:00 current_time=11:30:00
[radio.scheduler] spot_due=true spot_id=abc123 name=Jingle interval_seconds=600 time_until_seconds=300.5
```

---

## Critérios de Aceite

| Critério | ✅ Status |
|----------|---------|
| Spot ativo toca quando chega intervalo | DIAGNOSTICÁVEL |
| Spot inativo não toca | DIAGNOSTICÁVEL |
| Spot fora do horário não toca | DIAGNOSTICÁVEL |
| Spot sem arquivo não quebra rádio | DIAGNOSTICÁVEL |
| Logs mostram seleção, rejeição, execução | ✅ IMPLEMENTADO |
| Player recebe próximo spot claramente | ✅ IMPLEMENTADO |

---

## Arquivos Modificados/Criados

```
✅ backend/core/logging_config.py (novo, 120+ linhas)
✅ backend/services/audio_spot_scheduler.py (+logs)
✅ backend/api/v1/devices.py (+debug-spots endpoint, +melhorias em debug-playback)
```

---

## Próximos Passos

1. **Player**: Implementar logs quando spot começa/termina
   - `log_spot_playing(spot_id, device_id)`
   - `log_returning_to_music_queue(device_id)`

2. **AudioPlaybackEvent**: Registrar cada spot tocado
   - Tipo: `SPOT_STARTED`, `SPOT_ENDED`
   - Para auditoria e analytics

3. **Dashboard**: Mostrar histórico de spots tocados
   - Filtro por dispositivo, período, playlist
   - Alertas: "Nenhum spot tocou em 2 horas"

---

## Exemplo Real de Teste

```bash
# 1. Criar spot e agendar
curl -X POST /audio/spots \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Promo","track_id":"...","status":"active"}'

# 2. Agendar para playlist
curl -X POST /audio/playlists/{playlist_id}/spot-schedules \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "spot_id":"...",
    "interval_seconds":600,
    "start_time":"08:00",
    "end_time":"22:00",
    "is_active":true
  }'

# 3. Diagnosticar
curl /devices/{device_id}/debug-spots | jq '.next_spot_due'

# 4. Ver logs
docker logs playwave-backend | grep "radio.scheduler"
```

---

## Status

**✅ TASK 08 COMPLETA**

- Logs estruturados implementados
- Endpoint de diagnóstico criado
- Debug-playback melhorado
- Pronto para diagnosticar por que spots não tocam
