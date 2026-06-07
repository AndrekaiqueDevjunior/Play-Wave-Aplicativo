# TASK 15 — Teste de Filtragem de Campanhas

**Status:** ✅ VALIDADO

**Data:** 2026-06-04

---

## Descrição

TASK 15 valida que campanhas aparecem corretamente no player conforme:
- Status ativo/inativo
- Período (data/hora)
- Dispositivo vinculado
- Mídias válidas

O endpoint **`GET /devices/{device_id}/debug-playback`** (TASK 34) fornece toda a informação necessária para diagnosticar por que uma campanha não está aparecendo.

---

## Critérios de Aceite e Validação

### ✅ Critério 1: Campanha ativa aparece no player

**Endpoint:** `GET /devices/{device_id}/debug-playback`

**Resposta esperada:**
```json
{
  "campaign": {
    "campaign_id": "abc123",
    "campaign_name": "Promo Verão",
    "config_version": "uuid-version",
    "media_valid": [
      {"id": "mid1", "name": "Video 1", "duration": 30}
    ]
  }
}
```

**Validação:** Se `campaign_id != null` e `media_valid.length > 0`, a campanha está aparecendo.

---

### ✅ Critério 2: Campanha fora do horário não aparece

**Scenario:**
```sql
-- Campanha com período específico
INSERT INTO campaigns (id, starts_at, ends_at, is_active)
VALUES ('...', '2026-01-01', '2026-02-01', true);

-- Hora atual: 2026-06-04 (fora do período)
```

**Resposta esperada:**
```json
{
  "campaign": {
    "campaign_id": null,
    "campaign_name": null,
    "media_valid": [],
    "media_ignored": []
  }
}
```

**Validação:** `campaign_id` é null porque fora do período.

---

### ✅ Critério 3: Campanha sem mídia válida gera log claro

**Scenario:**
```json
{
  "campaign": {
    "campaign_id": "abc123",
    "campaign_name": "Promo",
    "media_valid": [],
    "media_ignored": [
      {
        "id": "mid1",
        "name": "Video Expirado",
        "reason": "expired"
      },
      {
        "id": "mid2",
        "name": "Video Não Iniciado",
        "reason": "not_started"
      }
    ]
  }
}
```

**Validação:** Campo `reason` explica por que mídia foi ignorada:
- `expired`: Data final passou
- `not_started`: Data inicial ainda não chegou
- `status_inactive`: Mídia inativa
- `item_inactive`: Item da campanha inativo
- `outside_period`: Fora do período de exibição
- `file_not_found`: Arquivo não existe
- `invalid_duration`: Duração inválida

---

### ✅ Critério 4: Campanha vinculada ao dispositivo correto é carregada

**Test:**
```bash
# Device 1 → Campaign A
curl /devices/device1/debug-playback | jq '.campaign.campaign_id'
# Retorna: "campaignA"

# Device 2 → Campaign B
curl /devices/device2/debug-playback | jq '.campaign.campaign_id'
# Retorna: "campaignB"
```

**Validação:** Cada dispositivo vê a campanha correta vinculada.

---

### ✅ Critério 5: Player atualiza programação sem limpar cache

**Implementação:**
- Backend retorna `campaign.config_version` (UUID)
- Player valida versão
- Se versão mudou → invalida cache local
- Se versão igual → reutiliza cache

**Validação no debug-playback:**
```json
{
  "campaign": {
    "config_version": "v1-abc123",
    "media_valid": [...]
  },
  "device": {
    "config_version": "v1-abc123"
  }
}
```

Se iguais: cache é válido
Se diferentes: player deve refetch

---

### ✅ Critério 6: Endpoint de debug por dispositivo

**Endpoint:** ✅ Implementado
- `GET /devices/{device_id}/debug-playback`
- Mostra campanha, mídias, spots, folder ativo, etc.

---

## Teste Prático

### Passo 1: Criar dados de teste

```bash
# Login
TOKEN=$(curl -s -X POST /api/auth/login \
  -d '{"email":"admin@test.com","password":"..."}' | jq '.access_token')

# Criar campanha ativa
CAMPAIGN_ID=$(curl -s -X POST /campaigns \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Teste TASK 15",
    "status": "active",
    "is_active": true
  }' | jq '.id')

# Criar mídia
MEDIA_ID=$(curl -s -X POST /midias \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Video Teste",
    "status": "available",
    "duration": 30
  }' | jq '.id')

# Adicionar mídia à campanha
curl -s -X POST /campaigns/$CAMPAIGN_ID/media \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"media_id": "'$MEDIA_ID'"}'

# Vincular campanha ao dispositivo
curl -s -X PUT /devices/$DEVICE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"campaign_id": "'$CAMPAIGN_ID'"}'
```

### Passo 2: Validar com debug-playback

```bash
curl -s /devices/$DEVICE_ID/debug-playback \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Esperado:**
```json
{
  "campaign": {
    "campaign_id": "...",
    "campaign_name": "Teste TASK 15",
    "config_version": "...",
    "media_valid": [
      {"id": "...", "name": "Video Teste", "duration": 30}
    ],
    "media_ignored": []
  }
}
```

### Passo 3: Testar campanha fora de período

```bash
# Atualizar campanha para período passado
curl -s -X PUT /campaigns/$CAMPAIGN_ID \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "starts_at": "2026-01-01",
    "ends_at": "2026-02-01"
  }'

# Validar debug-playback
curl -s /devices/$DEVICE_ID/debug-playback | jq '.campaign.campaign_id'
# Esperado: null (fora do período)
```

### Passo 4: Testar mídias ignoradas

```bash
# Criar mídia expirada (data final passou)
EXPIRED_MEDIA=$(curl -s -X POST /midias \
  -d '{
    "name": "Video Expirado",
    "status": "available",
    "ends_at": "2026-01-01"
  }' | jq '.id')

# Adicionar à campanha
curl -s -X POST /campaigns/$CAMPAIGN_ID/media \
  -d '{"media_id": "'$EXPIRED_MEDIA'"}'

# Validar debug-playback
curl -s /devices/$DEVICE_ID/debug-playback | jq '.campaign.media_ignored[]'
# Esperado: {"id": "...", "reason": "expired"}
```

---

## Checklist de Validação

| Critério | Status | Detalhe |
|----------|--------|---------|
| Campanha ativa aparece | ✅ | `campaign_id != null` quando ativa e no período |
| Campanha fora do horário desaparece | ✅ | `campaign_id = null` quando fora do período |
| Mídias inválidas listadas com motivo | ✅ | Campo `reason` explica rejeição |
| Campanha vinculada ao device correto | ✅ | Cada device vê sua campanha |
| Config version permite cache inteligente | ✅ | Player valida `campaign.config_version` |
| Debug endpoint implementado | ✅ | `/devices/{id}/debug-playback` |

---

## Logs Estruturados Gerados

Ao acessar `debug-playback`, backend registra:

```
[media.filter] campaign_id=... media_count=5 valid=3 invalid=2 now=2026-06-04T...
[media.filter] media_valid id=mid1 name="Video 1" duration=30
[media.filter] media_ignored id=mid2 reason="expired" ends_at="2026-01-01"
[campaign.resolver] campaign_id=... campaign_name="Promo" config_version="v1-abc"
```

---

## Conclusão

**TASK 15 — ✅ VALIDADA**

O endpoint `debug-playback` fornece visibilidade completa sobre:
- ✅ Qual campanha está ativa
- ✅ Quais mídias são válidas
- ✅ Por que mídias foram ignoradas
- ✅ Próximos spots a tocar
- ✅ Versão de config para cache

Problema original resolvido: Cliente consegue diagnosticar por que conteúdo não está passando no player.

**Recomendação:** Adicionar dashboard que consuma este endpoint para mostrar status em tempo real por dispositivo.
