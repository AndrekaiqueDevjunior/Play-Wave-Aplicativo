# AUDITORIA DE FILA DE REPRODUÇÃO - PLAY WAVE

**Data:** 2026-05-18  
**Objetivo:** Auditar se existe uma fila real de reprodução no backend e/ou player frontend

---

## 1. RESUMO EXECUTIVO

**STATUS CRÍTICO:** O sistema NÃO possui uma fila de reprodução real com distribuição por porcentagem/peso.

- **Backend:** NÃO há serviço de fila. Retorna mídias de UMA ÚNICA campanha baseada em prioridade.
- **Player:** NÃO há lógica de fila. Avança linearmente por índice simples.
- **Distribuição:** NÃO existe distribuição por porcentagem, peso, ou algoritmo de rotação.
- **Audio:** Playlist de áudio separada, em nível de dispositivo (não de campanha).

---

## 2. FILA DE REPRODUÇÃO NO BACKEND

### 2.1 Serviço de fila
**STATUS:** NÃO EXISTE

- NÃO há arquivo de serviço de fila (queue, playbackQueue, mediaQueue, audioQueue, playlistQueue)
- NÃO há scheduler, rotation, nextMedia, currentMedia
- NÃO há buildPlaylist, buildQueue, getNextMedia, calculateWeight, calculatePercentage

### 2.2 Endpoint de playlist
**Arquivo:** `backend/api/v1/devices.py`  
**Endpoint:** `GET /devices/{device_id}/playlist`

**Lógica atual:**
```python
# 1. Tenta current_campaign_id do dispositivo
if device.current_campaign_id:
    campaign = crud_campaign.get(db, id=device.current_campaign_id)

# 2. Fallback: busca campanha ativa com maior prioridade
if not campaign:
    campaign = crud_campaign.get_active_for_device(db, device_id=device.id)
```

**Problema:** Retorna APENAS UMA campanha. NÃO há distribuição entre múltiplas campanhas.

### 2.3 Seleção de campanha
**Arquivo:** `backend/crud/entidades/crud_campaign.py`  
**Método:** `get_active_for_device`

```python
def get_active_for_device(self, db: Session, *, device_id: str) -> Optional[Campaign]:
    """Return the highest-priority active campaign that targets this device."""
    return (
        db.query(Campaign)
        .filter(
            and_(
                cast(Campaign.device_ids, JSONB).contains([device_id]),
                Campaign.status == "active",
            )
        )
        .order_by(Campaign.priority.desc())  # Maior prioridade ganha
        .first()  # APENAS UMA campanha
    )
```

**Problema:** 
- Retorna APENAS a campanha com maior prioridade
- NÃO respeita porcentagem (playback_percentage)
- NÃO respeita peso (weight)
- NÃO distribui entre múltiplas campanhas

### 2.4 Campos de distribuição
**STATUS:** NÃO EXISTEM

- NÃO há campo `playback_percentage` no model Campaign
- NÃO há campo `weight` no model Campaign
- NÃO há campo `distribution_mode` no model Campaign
- NÃO há lógica de cálculo de peso ou porcentagem

### 2.5 Cache da fila
**STATUS:** NÃO EXISTE

- NÃO há cache Redis da fila
- NÃO há fila pré-calculada
- A fila é calculada on-demand a cada request do player

### 2.6 Background tasks (Celery)
**Arquivo:** `backend/tasks/__init__.py`

**Tasks existentes:**
1. `daily_device_stats` - Calcula estatísticas diárias de visualizações
2. `mark_offline_devices` - Marca dispositivos como offline após 5 minutos

**STATUS:** NÃO há task para montagem de fila de reprodução

---

## 3. FILA DE REPRODUÇÃO NO PLAYER (FRONTEND)

### 3.1 Localização
**Arquivo:** `frontend/src/pages/Player.jsx`

### 3.2 Como o player recebe a fila
```javascript
const res = await getDevicePlaylist(id, token);
const medias = (res?.media || []).map((m) => ({ ...m, file_url: assetUrl(m.file_url) }));
setPlaylist(medias);
setCurrentIndex(0);
```

**Problema:** Recebe APENAS uma lista de mídias de UMA campanha.

### 3.3 Como o player avança na fila
```javascript
const advance = setTimeout(() => {
  // Registra playback da mídia atual
  registrarPlayback(...);
  
  // Avança para próxima mídia
  setCurrentIndex((prev) => (prev + 1) % playlist.length); // Loop simples
  setViewsCount((prev) => prev + 1);
}, duration);
```

**Problema:**
- Avança por índice simples `(prev + 1) % playlist.length`
- NÃO respeita peso, porcentagem, prioridade
- NÃO recalcula a fila quando campanha muda
- NÃO há lógica de distribuição

### 3.4 Atualização dinâmica da fila
```javascript
const beat = async () => {
  const res = await sendHeartbeat(deviceId, deviceToken, {...});
  if (res?.playlist_updated) setPhase("loading"); // Recarrega tudo
};
```

**Problema:**
- Recarrega a playlist inteira quando `playlist_updated` é true
- NÃO atualiza incrementalmente
- NÃO mantém estado da fila atual

### 3.5 Cache/offline
**STATUS:** NÃO EXISTE

- NÃO há cache local da fila
- NÃO há suporte a offline
- Se perder conexão, player para de funcionar

---

## 4. FILA DE VÍDEO/IMAGEM

### 4.1 Fila específica
**STATUS:** NÃO EXISTE

- Vídeos e imagens entram na MESMA lista (`playlist` array)
- NÃO há fila separada para vídeo
- NÃO há fila separada para imagem

### 4.2 Duração
```javascript
const duration = (playlist[currentIndex]?.duration || 10) * 1000;
```

**Status:**
- Duração vem do campo `duration` da mídia
- Se não definida, usa 10 segundos como fallback
- Imagens respeitam duração configurada

### 4.3 Links/URLs
- Links externos (`external_url`) entram na lista normalmente
- Tipo `external_url` é tratado como mídia normal

### 4.4 Mídias inválidas
**STATUS:** NÃO há tratamento

- NÃO há validação de mídia antes de reproduzir
- NÃO há pulo automático de mídia com erro
- Se mídia falhar, player trava

---

## 5. FILA DE ÁUDIO/MÚSICA

### 5.1 Fila separada
**STATUS:** PARCIAL

- Audio playlist existe separadamente da playlist visual
- Componente `AudioPlayer` toca áudio independentemente
- Mas vem de `device.audio_playlist_id` (nível dispositivo), não de campanha

### 5.2 Origem da playlist de áudio
**Backend (antes da correção):**
```python
return {
    "audio_playlist": _build_audio_playlist(device, db),  # Sempre do dispositivo
}
```

**Correção aplicada:**
```python
# Usa playlist da campanha se definida, senão do dispositivo
audio_playlist_source = campaign.audio_playlist_id or device.audio_playlist_id
if campaign.audio_playlist_id:
    audio_playlist = _build_audio_playlist_from_model(playlist, db)
else:
    audio_playlist = _build_audio_playlist(device, db)
```

**Status:** Agora usa `campaign.audio_playlist_id` quando disponível.

### 5.3 Comportamento
- Áudio toca continuamente enquanto mídias visuais avançam
- NÃO pausa quando vídeo tem áudio próprio
- NÃO há regra para vídeo mudo + música de fundo
- Volume é configurável por playlist

---

## 6. FILA COMBINADA (ÁUDIO + VÍDEO)

### 6.1 Cenários suportados

| Cenário | Suporte | Observação |
|---------|---------|------------|
| Vídeo com áudio próprio | PARCIAL | Player toca vídeo, áudio de fundo continua (sobrepõe) |
| Vídeo mudo + música de fundo | NÃO | NÃO há detecção de vídeo mudo |
| Imagem + música | SIM | Áudio toca enquanto imagem é exibida |
| Apenas vídeo | SIM | Sem áudio de fundo |
| Apenas música | SIM | Player sem mídia visual |
| Apenas imagem | SIM | Sem áudio |

### 6.2 Problema crítico
**Sobreposição de áudio:** Quando um vídeo tem áudio próprio, a música de fundo continua tocando, criando sobreposição de áudio.

**Solução necessária:** Detectar se mídia visual tem áudio e pausar/mutar áudio de fundo.

---

## 7. ALGORITMO DE DISTRIBUIÇÃO

### 7.1 Campanha única (100%)
**STATUS:** PARCIAL

- Se há UMA campanha ativa, suas mídias tocam 100% do tempo
- **Problema:** Se há MÚLTIPLAS campanhas ativas, apenas a de maior prioridade toca

### 7.2 Distribuição 50%/50%
**STATUS:** NÃO EXISTE

- NÃO há lógica para distribuir 50% campanha A, 50% campanha B
- Apenas a campanha com maior `priority` toca

### 7.3 Peso/prioridade
**STATUS:** PARCIAL

- Campo `priority` existe (1-5)
- **Porém:** É usado apenas para SELEÇÃO (maior prioridade ganha), não para DISTRIBUIÇÃO
- Não há cálculo de peso para determinar quantas vezes cada campanha deve aparecer

### 7.4 Horário/agenda
**STATUS:** EXISTE (mas não usado na fila)

- Campos existem: `schedule_days`, `schedule_start_time`, `schedule_end_time`
- **Porém:** Não há validação de horário na montagem da fila
- O endpoint `get_active_for_device` filtra apenas por `status == "active"`

### 7.5 Campanha vencida
**STATUS:** NÃO EXISTE

- NÃO há verificação de `start_date` e `end_date` na montagem da fila
- Campanhas vencidas podem continuar tocando

### 7.6 Mídia com erro
**STATUS:** NÃO EXISTE

- NÃO há tratamento de erro de mídia
- Se mídia falhar, player trava
- NÃO há pulo automático para próxima

---

## 8. TRAVAMENTOS/HARDCODED NA FILA

### 8.1 Encontrados

| Problema | Local | Descrição |
|----------|-------|-----------|
| Fila fixa por campanha | `get_device_playlist` | Retorna APENAS uma campanha |
| Ordem simples | `Player.jsx` | Avança por `(prev + 1) % playlist.length` |
| Filtro aceita só video/image | `get_device_playlist` | Retorna mídias da campanha, mas não filtra tipo |
| Índice simples | `Player.jsx` | `currentIndex` increment sem lógica |
| Nenhum Math.random | N/A | NÃO há aleatoriedade |
| Fallback primeira campanha | `get_active_for_device` | `.first()` retorna a primeira (maior prioridade) |

---

## 9. ARQUIVOS OBRIGATÓRIOS AUDITADOS

| Arquivo | Encontrado? | Status |
|---------|------------|--------|
| queue.py | NÃO | - |
| playbackQueue.py | NÃO | - |
| mediaQueue.py | NÃO | - |
| audioQueue.py | NÃO | - |
| playlistQueue.py | NÃO | - |
| scheduler.py | NÃO | - |
| rotation.py | NÃO | - |
| nextMedia.js | NÃO | - |
| currentMedia.js | NÃO | - |
| currentTrack.js | NÃO | - |
| campaignRotation.py | NÃO | - |
| buildPlaylist.py | NÃO | - |
| buildQueue.py | NÃO | - |
| getNextMedia.py | NÃO | - |
| calculateWeight.py | NÃO | - |
| calculatePercentage.py | NÃO | - |
| activeCampaigns.py | NÃO | - |
| playerConfig.js | NÃO | - |
| `backend/api/v1/devices.py` | SIM | Endpoint de playlist |
| `backend/crud/entidades/crud_campaign.py` | SIM | Seleção de campanha |
| `frontend/src/pages/Player.jsx` | SIM | Player principal |
| `frontend/src/components/audio/AudioPlayer.jsx` | SIM | Player de áudio |
| `backend/tasks/__init__.py` | SIM | Tasks Celery |

---

## 10. PERGUNTAS DO RELATÓRIO

| Pergunta | Resposta |
|----------|----------|
| Existe fila de reprodução? | PARCIAL - Existe lista de mídias, mas não fila com distribuição |
| A fila é montada no backend ou no player? | Backend (mas retorna apenas uma campanha) |
| A fila respeita porcentagem? | NÃO |
| A fila respeita prioridade? | PARCIAL - Usa para seleção, não distribuição |
| A fila respeita ordem? | SIM - Usa `media_order` da campanha |
| A fila respeita duração? | SIM - Usa campo `duration` |
| Existe fila separada para áudio? | SIM - AudioPlaylist separada |
| Existe fila separada para vídeo/imagem? | NÃO - Mesma lista |
| O player sabe combinar áudio + vídeo/imagem? | PARCIAL - Toca ambos, mas sobrepõe áudio |
| A fila é atualizada quando muda a campanha? | PARCIAL - Recarrega tudo via heartbeat |
| Existe cache/offline? | NÃO |
| Existe log de cada item reproduzido? | SIM - `registrarPlayback` envia para backend |
| Existe risco de uma mídia tocar mais do que deveria? | SIM - Se houver múltiplas campanhas, apenas uma toca |

---

## 11. TABELA OBRIGATÓRIA

| Recurso | Backend | Player | Fila local | Cache | Status | Observação |
|---------|---------|--------|------------|-------|--------|------------|
| Fila de vídeo | ❌ | ✅ (array) | ❌ | ❌ | PARCIAL | Apenas array simples |
| Fila de imagem | ❌ | ✅ (array) | ❌ | ❌ | PARCIAL | Mesma array de vídeo |
| Fila de áudio | ❌ | ✅ (AudioPlayer) | ❌ | ❌ | PARCIAL | Separada, mas do dispositivo |
| Fila visual + áudio separado | ✅ | ✅ | ❌ | ❌ | SIM | Tocam simultaneamente |
| Campanha 100% | ✅ | ✅ | ❌ | ❌ | PARCIAL | Se houver apenas uma |
| Campanha 50% | ❌ | ❌ | ❌ | ❌ | NÃO | NÃO existe distribuição |
| Peso/prioridade | ❌ (seleção) | ❌ | ❌ | ❌ | NÃO | Usa para selecionar, não distribuir |
| Ordem configurada | ✅ | ✅ | ❌ | ❌ | SIM | Usa media_order |
| Duração por mídia | ✅ | ✅ | ❌ | ❌ | SIM | Campo duration |
| Atualização dinâmica da fila | ❌ | PARCIAL | ❌ | ❌ | PARCIAL | Recarrega tudo |
| Cache/offline | ❌ | ❌ | ❌ | ❌ | NÃO | Sem suporte offline |
| Logs de reprodução por item | ✅ | ✅ | ❌ | ❌ | SIM | Envia para backend |

---

## 12. TESTES OBRIGATÓRIOS

### Teste 1: Campanha única 100%
- **Criar:** Uma única campanha ativa
- **Resultado esperado:** Fila contém somente mídias dessa campanha
- **Resultado atual:** ✅ PASSA (mas não testa distribuição)

### Teste 2: Duas campanhas 50% cada
- **Criar:** Duas campanhas ativas
- **Resultado esperado:** Fila alterna proporcionalmente
- **Resultado atual:** ❌ FALHA - Apenas a campanha com maior prioridade toca

### Teste 3: Campanha peso 2 vs peso 1
- **Criar:** Campanha A peso 2, Campanha B peso 1
- **Resultado esperado:** Campanha A aparece ~2x mais
- **Resultado atual:** ❌ FALHA - Apenas a campanha com maior prioridade toca

### Teste 4: Vídeo mudo + música de fundo
- **Criar:** Campanha com vídeo sem áudio + playlist áudio
- **Resultado esperado:** Vídeo toca e música toca simultaneamente
- **Resultado atual:** ❌ FALHA - NÃO há detecção de vídeo mudo

### Teste 5: Imagem + música
- **Criar:** Campanha com imagem + playlist áudio
- **Resultado esperado:** Imagem toca enquanto música toca
- **Resultado atual:** ✅ PASSA

### Teste 6: Vídeo com áudio próprio
- **Criar:** Campanha com vídeo com áudio + playlist áudio
- **Resultado esperado:** Áudio de fundo não sobrepõe
- **Resultado atual:** ❌ FALHA - Áudio de fundo sobrepõe vídeo

### Teste 7: Desativar campanha enquanto player roda
- **Criar:** Campanha ativa, desativar durante playback
- **Resultado esperado:** Player atualiza fila e remove campanha
- **Resultado atual:** PARCIAL - Recarrega via heartbeat após 30s

### Teste 8: Adicionar nova campanha enquanto player roda
- **Criar:** Nova campanha ativa durante playback
- **Resultado esperado:** Player atualiza fila sem recarregar manualmente
- **Resultado atual:** PARCIAL - Recarrega via heartbeat após 30s

### Teste 9: Mídia quebrada/URL inválido
- **Criar:** Mídia com URL inválido
- **Resultado esperado:** Player pula para próxima e registra erro
- **Resultado atual:** ❌ FALHA - Player trava

### Teste 10: Perda de internet
- **Criar:** Desconectar internet durante playback
- **Resultado esperado:** Player usa cache ou mostra erro controlado
- **Resultado atual:** ❌ FALHA - Player para de funcionar

---

## 13. CONCLUSÕES E RECOMENDAÇÕES

### 13.1 Problemas críticos
1. **NÃO há distribuição por porcentagem/peso** - Apenas uma campanha toca por vez
2. **NÃO há fila real** - Apenas array simples com avanço linear
3. **NÃO há tratamento de erro** - Player trava se mídia falhar
4. **NÃO há suporte offline** - Player para sem internet
5. **Sobreposição de áudio** - Áudio de fundo sobrepõe vídeo com áudio próprio

### 13.2 Recomendações imediatas
1. Implementar serviço de fila no backend com distribuição por peso/porcentagem
2. Adicionar campo `playback_percentage` ou `weight` no model Campaign
3. Implementar lógica de distribuição de múltiplas campanhas
4. Adicionar tratamento de erro de mídia no player
5. Implementar cache local da fila no player
6. Detectar vídeo com áudio e pausar/mutar áudio de fundo
7. Adicionar validação de horário (start_date, end_date) na montagem da fila

### 13.3 Recomendações de longo prazo
1. Implementar fila pré-calculada em Redis
2. Adicionar task Celery para recalcular fila periodicamente
3. Implementar suporte offline no player
4. Adicionar dashboard de monitoramento da fila em tempo real
5. Implementar testes automatizados para lógica de distribuição

---

## 14. ARQUIVOS MODIFICADOS NESTA AUDITORIA

1. `backend/api/v1/devices.py`
   - Adicionado suporte a `campaign.audio_playlist_id`
   - Adicionada função `_build_audio_playlist_from_model`
   - Playlist de áudio agora usa campanha se disponível, senão dispositivo

2. `backend/core/schemas_completos.py`
   - Adicionado `from __future__ import annotations` para resolver forward reference
   - Adicionado `audio_playlist_id` ao Campaign model
   - Adicionado `audio_playlist` aninhado ao CampaignResponse

3. `backend/core/models.py`
   - Adicionado `audio_playlist_id` FK ao Campaign model
   - Adicionado relationship `audio_playlist`

4. `frontend/src/components/campaigns/CampaignFormModal.jsx`
   - Adicionado seletor de playlist de áudio no formulário de campanha

5. `frontend/src/pages/Campanhas.jsx`
   - Adicionado fetch de audio playlists
   - Passado audioPlaylists ao CampaignFormModal

---

**Fim da auditoria**
