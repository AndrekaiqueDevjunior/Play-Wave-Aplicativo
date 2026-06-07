# TASK 06 — Opção de Reprodução (Sequencial/Aleatório/Loop)

**Status:** ✅ COMPLETO (Backend + Frontend + Player Core)

**Data de Conclusão:** 2026-06-04

---

## Resumo

Implementação completa de modos de reprodução para pastas e playlists sonoras, permitindo ao usuário escolher entre sequencial, aleatório, aleatório sem repetição e loop.

---

## Critérios de Aceite

| Critério | Status | Detalhes |
|----------|--------|----------|
| Usuário escolhe modo na playlist | ✅ | Interface com checkboxes no AudioPlaylistsFormModal e AudioFolderManager |
| Usuário escolhe modo por pasta | ✅ | Novos campos `shuffle_enabled` e `loop_enabled` em AudioFolder |
| Player respeita o modo configurado | ✅ | PlaybackQueueManager integrado ao AudioPlayer |
| Evita repetir sempre a mesma música | ✅ | Suporte a shuffle sem repetição com tracking de faixas já tocadas |
| Estado da fila persiste após refresh | ✅ | localStorage salva estado atual, índice e seed de shuffle |

---

## Arquitetura

### Backend

**Modelos (backend/core/models.py)**
- `AudioPlaylist`: `shuffle_enabled` (Bool, default=False), `loop_enabled` (Bool, default=True)
- `AudioFolder`: `shuffle_enabled` (Bool, default=False), `loop_enabled` (Bool, default=True)

**Schemas (backend/core/schemas_completos.py)**
- `AudioFolderBase`, `AudioFolderUpdate`, `AudioFolderResponse`: Campos adicionados
- `AudioPlaylistBase`, `AudioPlaylistUpdate`, `AudioPlaylistResponse`: Já suportavam (compatibilidade)
- **Novo Enum**: `PlaybackModeEnum` com opções:
  - `SEQUENTIAL`: Tocar em ordem
  - `SHUFFLE`: Tocar aleatoriamente
  - `SHUFFLE_NO_REPEAT`: Tocar aleatoriamente sem repetir até completar todas
  - `LOOP`: Loop ao fim (complementa os outros)

**Migration (backend/alembic/versions/20260604_1400_shuffle_loop_modes.py)**
- ADD COLUMN `loop_enabled` BOOLEAN DEFAULT true
- ADD COLUMN `shuffle_enabled` BOOLEAN DEFAULT false

### Frontend

**Componentes**

1. **AudioFolderManager.jsx** (c:\...\components\audio\)
   - Novos inputs: checkboxes para "Embaralhado" e "Loop"
   - Salvam em `form.shuffle_enabled` e `form.loop_enabled`
   - Carregam valores ao editar pasta existente

2. **AudioPlaylistsFormModal.jsx** (c:\...\components\audio\)
   - Já possuía interface completa com Switch para shuffle e loop
   - Sem mudanças necessárias (validação: compatível)

**Player Core**

3. **PlaybackQueueManager.js** (NEW - c:\...\player-core\)
   
   Módulo responsável por:
   - Gerenciar fila de reprodução
   - Embaralhamento determinístico (com seed para reproducibilidade)
   - Rastreamento de faixas já tocadas (shuffle sem repetição)
   - Persistência em localStorage
   - Respeito a `loop_enabled`

   **Métodos principais:**
   ```javascript
   getNext()                    // Próxima faixa (sequencial ou com loop)
   getNextNoRepeat()            // Próxima sem repetição
   skipToNext()                 // Pula para próxima respeitando modo
   skipToPrevious()             // Volta para anterior
   jumpToIndex(idx)             // Pula para índice específico
   updateOptions(opts)          // Atualiza shuffle/loop em tempo real
   saveState()                  // Persiste em localStorage
   restoreState()               // Restaura após refresh
   updateTracks(newTracks)      // Atualiza lista de faixas
   getQueueInfo()               // Retorna estado atual
   ```

4. **AudioPlayer.jsx** (MODIFICADO)
   - Integrado PlaybackQueueManager
   - `handleEnded()` agora usa `queueManager.skipToNext()`
   - `handleError()` também usa queue manager
   - Suporta restauração de posição após refresh

---

## Fluxo de Dados

```
[Usuário configurar Pasta/Playlist]
          ↓
[Frontend: AudioFolderManager / AudioPlaylistsFormModal]
          ↓
[Backend: PUT /audio/folders/{id} ou POST /audio/playlists]
          ↓
[Banco: Salvar shuffle_enabled + loop_enabled]
          ↓
[Player: Recebe config da playlist/pasta]
          ↓
[PlaybackQueueManager: Embaralha se shuffle=true, respeita loop]
          ↓
[AudioPlayer: Toca faixa, salva estado em localStorage]
          ↓
[Ao terminar: handleEnded() → queueManager.skipToNext()]
          ↓
[Restaura estado se página recarregar]
```

---

## Testes

**Testes Unitários** (frontend/src/__tests__/playbackQueueManager.test.js)

- ✅ Sequential playback sem loop (para ao fim)
- ✅ Sequential playback com loop (volta ao início)
- ✅ Shuffle com determinismo (mesmo seed = mesma ordem)
- ✅ Shuffle sem repetição (toca todas sem repetir)
- ✅ Persistência em localStorage (restaura após novo QueueManager)
- ✅ jumpToIndex (pula para faixa específica)
- ✅ updateTracks (reseta fila com novos tracks)
- ✅ clearState (limpa localStorage)
- ✅ skipToNext/skipToPrevious (respeita modo)

**Como rodar:**
```bash
cd frontend
npm test -- playbackQueueManager
```

---

## Exemplo de Uso

### Backend: Criar Pasta com Shuffle

```bash
curl -X POST /audio/folders \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manhã Alegatória",
    "shuffle_enabled": true,
    "loop_enabled": true,
    "start_time": "06:00",
    "end_time": "12:00"
  }'
```

### Frontend: Componente Usa PlaybackQueueManager

```javascript
import PlaybackQueueManager from '@/player-core/playbackQueueManager';

const qm = new PlaybackQueueManager(tracks, {
  shuffle_enabled: folder.shuffle_enabled,
  loop_enabled: folder.loop_enabled,
  playback_mode: 'shuffle_no_repeat'
});

// Obter próxima faixa
const track = qm.getNext();

// Atualizar opções em tempo real
qm.updateOptions({
  shuffle_enabled: true,
  loop_enabled: false
});
```

---

## Comportamento do Player

### Sequencial (shuffle=false, loop=true)
```
Track 1 → Track 2 → Track 3 → Track 1 → ...
```

### Aleatório (shuffle=true, loop=true)
```
Track 3 → Track 1 → Track 4 → Track 2 → Track 3 → ...
(Ordem embaralhada, repetida em ciclos)
```

### Aleatório Sem Repetição (shuffle_no_repeat=true, loop=true)
```
Ciclo 1: Track 4 → Track 1 → Track 3 → Track 2
Ciclo 2: Track 2 → Track 4 → Track 1 → Track 3
(Sem repetir até completar todas)
```

### Sem Loop (loop=false)
```
Track 1 → Track 2 → Track 3 → [PAUSA]
(Pausa ao fim)
```

---

## Persistência

Estado salvo em localStorage sob chave `playwave_queue_state`:

```json
{
  "queueIds": ["1", "2", "3", "4"],
  "currentIndex": 2,
  "playedIndices": [0, 1, 2],
  "shuffleSeed": 0.123456,
  "shuffle_enabled": true,
  "loop_enabled": true,
  "playback_mode": "shuffle_no_repeat",
  "timestamp": 1717554000000
}
```

- **Validação**: Se tracks mudarem (IDs diferentes), estado é descartado
- **Timeout**: Implícito (localStorage persiste até usuário limpar cache)
- **Benefício**: Ao recarregar página, player continua de onde parou

---

## Compatibilidade

- ✅ Playlists antigas (sem os novos campos) funcionam com defaults
- ✅ AudioPlayer mantém fallback para comportamento legado
- ✅ Sem quebra de API (campos opcionais)
- ✅ Sem alteração em endpoints existentes

---

## Próximas Fases (Fora do Escopo)

1. **UI Avançada de Shuffle**:
   - Botão "Shuffle" no player web para toggle rápido
   - Indicador visual de modo ativo

2. **Histórico de Reprodução**:
   - Salvar quais faixas foram tocadas (para relatórios)
   - Endpoint: GET /audio/tracks/{id}/play-history

3. **Queue Server-Side**:
   - Sincronizar fila entre múltiplos players
   - Endpoint: POST /audio/playlists/{id}/queue-state

4. **Smart Shuffle**:
   - Algoritmo que evita artistas/gêneros repetidos consecutivamente
   - Integração com dados de metadados

---

## Arquivos Modificados

| Arquivo | Mudanças |
|---------|----------|
| `backend/core/models.py` | +2 campos em AudioFolder |
| `backend/alembic/versions/20260604_1400_shuffle_loop_modes.py` | Nova migration |
| `backend/core/schemas_completos.py` | +PlaybackModeEnum, campos em schemas |
| `frontend/src/components/audio/AudioFolderManager.jsx` | +UI, +state |
| `frontend/src/components/audio/AudioPlayer.jsx` | +QueueManager integration |
| `frontend/src/player-core/playbackQueueManager.js` | NEW |
| `frontend/src/__tests__/playbackQueueManager.test.js` | NEW (10 testes) |

---

## Status de Aceitação

```
✅ Backend pronto para produção
✅ Frontend pronto para produção
✅ Player Core pronto para produção
✅ Testes unitários passando
✅ Documentação completa
```

**TASK 06 — 100% COMPLETA**
