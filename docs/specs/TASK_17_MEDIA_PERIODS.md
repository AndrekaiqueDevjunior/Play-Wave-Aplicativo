# TASK 17 — Definir Período de Exibição na Mídia

**Status:** ✅ COMPLETO

**Data de Conclusão:** 2026-06-04

**Prioridade:** P1

---

## Problema

Cliente quer definir data/hora/dias da semana diretamente na mídia ao subir, sem precisar usar campanhas ou pastas.

---

## Solução Implementada

### 1. Modelo (backend/core/models.py)

Adicionado campos de período ao modelo `Media`:

```python
class Media(Base):
    # Campos existentes...
    starts_at = Column(DateTime, nullable=True)      # Data inicial
    ends_at = Column(DateTime, nullable=True)        # Data final
    
    # Novos campos (TASK 17)
    start_time = Column(String(10), nullable=True)   # HH:MM format
    end_time = Column(String(10), nullable=True)     # HH:MM format
    days_of_week = Column(JSON, nullable=True)       # ["mon", "tue", "wed", ...]
```

### 2. Migration (20260604_1500_media_period_fields.py)

```sql
ALTER TABLE media ADD COLUMN start_time VARCHAR(10);
ALTER TABLE media ADD COLUMN end_time VARCHAR(10);
ALTER TABLE media ADD COLUMN days_of_week JSON;
```

### 3. Schemas (backend/core/schemas_completos.py)

Adicionado campos aos schemas:
- `MediaBase`: Campos de período
- `MediaCreate`: Campos opcionais
- `MediaUpdate`: Campos opcionais
- `MediaResponse`: Campos de período

### 4. Validação (backend/services/media_period_validator.py)

Novo módulo com funções:

**`is_media_in_period(media, now)`**: Verifica se mídia está no período correto
```python
# Retorna True se:
- Data inicial passou (ou não definida)
- Data final não passou (ou não definida)
- Horário atual está dentro do range (ou não definido)
- Dia da semana é permitido (ou não definido)
```

**`get_media_availability_status(media, now)`**: Retorna status de disponibilidade
```python
# Retorna: "vigente", "futura", "expirada", "fora_horario"
```

### 5. Integração na API (backend/api/v1/devices.py)

Integrado validação de período no `_media_is_valid_for_player()`:
```python
def _media_is_valid_for_player(media: Media, *, now: Optional[datetime] = None) -> bool:
    # ... validações existentes ...
    
    # TASK 17: Validar período
    from services.media_period_validator import is_media_in_period
    if not is_media_in_period(media, now=now):
        return False
    
    return True
```

Adicionado diagnóstico de rejeição por período:
```python
# Razões de rejeição
"status_available"       # Mídia não está disponível
"period_vigente"         # Fora de horário hoje
"period_futura"          # Ainda não começou
"period_expirada"        # Já terminou
"period_fora_horario"    # Fora do horário ou dia da semana errado
```

---

## Como Usar

### Criar mídia com período

```bash
curl -X POST http://localhost:8000/midias \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Promo Verão",
    "type": "video",
    "file_url": "...",
    "starts_at": "2026-06-01",
    "ends_at": "2026-08-31",
    "start_time": "08:00",
    "end_time": "22:00",
    "days_of_week": ["mon", "tue", "wed", "thu", "fri"]
  }'
```

### Campos de Período

| Campo | Formato | Descrição | Exemplo |
|-------|---------|-----------|---------|
| `starts_at` | YYYY-MM-DD | Data inicial (inclusive) | "2026-06-01" |
| `ends_at` | YYYY-MM-DD | Data final (inclusive) | "2026-08-31" |
| `start_time` | HH:MM | Hora inicial (24h) | "08:00" |
| `end_time` | HH:MM | Hora final (24h) | "22:00" |
| `days_of_week` | ["mon", ...] | Dias permitidos | ["mon", "tue"] |

### Validação

Todos os campos são opcionais:
- Sem `starts_at`: sem limite inferior de data
- Sem `ends_at`: sem limite superior de data
- Sem `start_time`/`end_time`: disponível 24h
- Sem `days_of_week`: disponível qualquer dia

---

## Exemplo: Promo de Fim de Semana

```json
{
  "name": "Promo Sábado e Domingo",
  "starts_at": "2026-06-01",
  "ends_at": "2026-08-31",
  "days_of_week": ["sat", "sun"],
  "start_time": "10:00",
  "end_time": "20:00"
}
```

**Será exibido:**
- Apenas sábado e domingo
- De 10:00 até 20:00
- De 1º de junho até 31 de agosto

---

## Diagnóstico no Debug-Playback

Endpoint `GET /devices/{device_id}/debug-playback` mostra:

```json
{
  "campaign": {
    "media_valid": [
      {"id": "...", "name": "Promo Válida"}
    ],
    "media_ignored": [
      {
        "id": "...",
        "name": "Promo Fim de Semana",
        "reason": "period_fora_horario"
      },
      {
        "id": "...",
        "name": "Promo Futura",
        "reason": "period_futura"
      }
    ]
  }
}
```

---

## Critérios de Aceite

| Critério | ✅ Status |
|----------|---------|
| Usuário define data inicial | ✅ IMPLEMENTADO |
| Usuário define data final (opcional) | ✅ IMPLEMENTADO |
| Usuário define horário (opcional) | ✅ IMPLEMENTADO |
| Usuário define dias da semana (opcional) | ✅ IMPLEMENTADO |
| Player ignora mídia fora do período | ✅ IMPLEMENTADO |
| Debug mostra por que mídia foi ignorada | ✅ IMPLEMENTADO |

---

## Próximas Fases (Fora do Escopo)

1. **Frontend**:
   - Interface para editar períodos em upload/edição
   - Badge mostrando status (vigente, futura, expirada)
   - Calendar picker para datas

2. **Analytics**:
   - Relatório de mídias por período
   - Previsão: "essa promo vai tocar em X dispositivos"

3. **Validação**:
   - Avisar se período foi 100% no passado
   - Avisar se período nunca será atingido (ex: segunda-feira com horário 25:00)

---

## Arquivos Modificados/Criados

```
✅ backend/core/models.py (+3 campos)
✅ backend/alembic/versions/20260604_1500_media_period_fields.py (nova)
✅ backend/core/schemas_completos.py (+3 campos)
✅ backend/services/media_period_validator.py (novo, 120+ linhas)
✅ backend/api/v1/devices.py (+validação integrada)
```

---

## Status

**✅ TASK 17 — COMPLETA**

Período de exibição agora configurável na mídia com diagnóstico claro no debug-playback.
