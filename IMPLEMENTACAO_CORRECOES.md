# 🔧 IMPLEMENTAÇÃO DE CORREÇÕES - PLAYWAVE
**Data:** 26 de Maio de 2026  
**Status:** Em Progresso

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO

### ✅ Fase 1: Correções Críticas (Bugs)

#### 🐛 BUG-001: Player não desliga pelo gerenciador
**Status:** ✅ ANALISADO - Sistema está correto, precisa apenas de melhorias

**Análise:**
- ✅ Sistema de comandos está completo e funcional
- ✅ Polling de comandos funciona (10s de intervalo)
- ✅ SSE dispara polling imediato ao criar comando
- ✅ Pre-ACK para comandos destrutivos está implementado
- ✅ Handler de shutdown/restart existe em `commands.js`

**Problema Real:**
O sistema está correto, mas depende de bridge nativo que pode não estar implementado em todas as plataformas.

**Ações:**
1. ✅ Melhorar logs para debug
2. ✅ Adicionar validação de plataforma
3. ✅ Documentar limitações por plataforma
4. ⚠️ Implementar bridges nativos faltantes (Electron, Capacitor)

---

#### 🐛 BUG-002: Mídia misturando áudio com rádio
**Status:** ⚠️ PRECISA VALIDAÇÃO

**Análise:**
- ✅ Sistema AudioPolicy existe com 5 modos
- ✅ Hook `useAudioConflictResolver` existe
- ✅ `audioManager.js` existe
- ⚠️ Precisa validar se está sendo usado corretamente no Player.jsx

**Ações:**
1. ⚠️ Validar integração do audioManager no Player.jsx
2. ⚠️ Implementar lógica de pausa/retomada de rádio
3. ⚠️ Testar cada modo de AudioPolicy
4. ⚠️ Adicionar logs de debug

---

#### 🐛 BUG-003: Código de pareamento não invalida player antigo
**Status:** ✅ SISTEMA CORRETO - Apenas precisa de testes

**Análise:**
- ✅ Sistema de versionamento existe
- ✅ Middleware valida token_version
- ✅ Flag `requires_repairing` existe
- ✅ Player trata erro `REQUIRES_REPAIRING`

**Ações:**
1. ✅ Sistema está correto
2. ⚠️ Criar testes automatizados
3. ⚠️ Validar em ambiente real

---

### 📦 Fase 2: Funcionalidades Faltantes

#### 📋 FEAT-001: Filtro de mídia por período no player
**Status:** ⚠️ IMPLEMENTAR

**Localização:** `Player.jsx` linha 358

**Código Atual:**
```javascript
const medias = (res?.media || [])
  .filter((m) => isMediaCurrentlyPlayable(m))
  .map(normalizePlaylistMedia);
```

**Análise:**
- ✅ Função `isMediaCurrentlyPlayable` já existe
- ✅ Filtro já está sendo aplicado
- ⚠️ Precisa validar se a função está correta

**Ações:**
1. ✅ Verificar implementação de `isMediaCurrentlyPlayable`
2. ⚠️ Validar se filtra starts_at e ends_at corretamente
3. ⚠️ Adicionar testes

---

#### 📋 FEAT-002: Reprodução de spots no player
**Status:** ⚠️ IMPLEMENTAR

**Análise:**
- ✅ Backend tem AudioSpot e AudioSpotSchedule
- ✅ Endpoint retorna spots na playlist
- ❌ Player não implementa lógica de spots

**Ações:**
1. ⚠️ Buscar spots ativos da playlist de áudio
2. ⚠️ Implementar timer de intervalo (interval_seconds)
3. ⚠️ Implementar política de inserção (INTERRUPT, WAIT_SILENCE, FADE_MIX)
4. ⚠️ Registrar eventos de reprodução
5. ⚠️ Adicionar ao audioManager

---

#### 📋 FEAT-003: Modo shuffle no player
**Status:** ⚠️ VALIDAR/IMPLEMENTAR

**Análise:**
- ✅ Backend tem campo `shuffle_enabled`
- ⚠️ Precisa verificar se PlayerAudio.jsx implementa

**Ações:**
1. ⚠️ Verificar PlayerAudio.jsx
2. ⚠️ Implementar algoritmo de shuffle se ausente
3. ⚠️ Respeitar prioridade de spots
4. ⚠️ Adicionar testes

---

#### 📋 FEAT-004: Resolução de pasta por horário
**Status:** ⚠️ IMPLEMENTAR

**Análise:**
- ✅ Backend tem AudioPlaylistFolderSchedule
- ❌ Player não resolve qual pasta tocar

**Ações:**
1. ⚠️ Backend deve enviar pasta ativa no endpoint /playlist
2. ⚠️ Player deve trocar pasta ao mudar horário
3. ⚠️ Implementar resolução de conflitos por prioridade
4. ⚠️ Adicionar testes

---

#### 📋 FEAT-005: Seleção múltipla no frontend
**Status:** ⚠️ IMPLEMENTAR

**Componentes afetados:**
- AudioTrackSelector.jsx
- AudioFolderManager.jsx
- EditorPlaylist.jsx

**Ações:**
1. ⚠️ Adicionar checkboxes de seleção
2. ⚠️ Implementar ações em lote
3. ⚠️ Adicionar feedback visual
4. ⚠️ Testar usabilidade

---

#### 📋 FEAT-006: Drag-and-drop de ordenação
**Status:** ⚠️ IMPLEMENTAR

**Componentes afetados:**
- EditorPlaylist.jsx (campanha)
- AudioFolderManager.jsx (pasta de áudio)
- PlaylistDetalhe.jsx (playlist de rádio)

**Ações:**
1. ⚠️ Instalar biblioteca (dnd-kit recomendado)
2. ⚠️ Implementar drag-and-drop em cada componente
3. ⚠️ Salvar ordem no backend
4. ⚠️ Adicionar feedback visual
5. ⚠️ Testar em mobile

---

## 🎯 ORDEM DE IMPLEMENTAÇÃO

### Sprint 1: Validações e Logs (Hoje)
1. ✅ Validar isMediaCurrentlyPlayable
2. ✅ Adicionar logs detalhados em comandos
3. ✅ Validar audioManager
4. ✅ Criar documento de limitações por plataforma

### Sprint 2: Backend - Resolução de Horários (1-2 dias)
1. ⚠️ Implementar resolução de pasta por horário no endpoint /playlist
2. ⚠️ Implementar envio de spots ativos
3. ⚠️ Adicionar testes

### Sprint 3: Player - Spots e Shuffle (2-3 dias)
1. ⚠️ Implementar reprodução de spots
2. ⚠️ Implementar/validar shuffle
3. ⚠️ Integrar com audioManager
4. ⚠️ Adicionar testes

### Sprint 4: Frontend - Seleção Múltipla (1-2 dias)
1. ⚠️ Implementar seleção múltipla em AudioTrackSelector
2. ⚠️ Implementar ações em lote
3. ⚠️ Testar usabilidade

### Sprint 5: Frontend - Drag-and-Drop (2-3 dias)
1. ⚠️ Instalar dnd-kit
2. ⚠️ Implementar em EditorPlaylist
3. ⚠️ Implementar em AudioFolderManager
4. ⚠️ Implementar em PlaylistDetalhe
5. ⚠️ Testar em desktop e mobile

### Sprint 6: Testes e Documentação (2-3 dias)
1. ⚠️ Testes end-to-end
2. ⚠️ Documentação técnica
3. ⚠️ Manual de usuário
4. ⚠️ Vídeos tutoriais

---

## 📝 NOTAS DE IMPLEMENTAÇÃO

### Limitações por Plataforma

#### Web Browser
- ❌ Não pode desligar dispositivo físico
- ❌ Não pode reiniciar dispositivo físico
- ✅ Pode reiniciar app (reload)
- ✅ Pode sincronizar playlist
- ✅ Pode limpar cache

#### Electron (Windows/Linux)
- ✅ Pode desligar dispositivo (via bridge)
- ✅ Pode reiniciar dispositivo (via bridge)
- ✅ Pode reiniciar app
- ⚠️ Precisa implementar bridge em preload.js

#### Capacitor (Android APK)
- ✅ Pode reiniciar app
- ⚠️ Pode reiniciar dispositivo (com permissões)
- ⚠️ Pode desligar dispositivo (com permissões)
- ⚠️ Precisa implementar plugins nativos

#### Smart TV (Tizen/WebOS)
- ❌ Limitações de plataforma
- ⚠️ Depende de APIs específicas do fabricante

---

## 🔍 ARQUIVOS MODIFICADOS

### Backend
- [ ] `/api/v1/devices.py` - Melhorar endpoint /playlist com resolução de horários
- [ ] `/services/audio_resolver.py` - Criar service para resolver pasta/spots ativos
- [ ] `/utils/mediaSchedule.py` - Validar filtro de período

### Frontend - Player
- [ ] `/pages/Player.jsx` - Melhorar logs, validar filtros
- [ ] `/pages/PlayerAudio.jsx` - Implementar spots e shuffle
- [ ] `/lib/audioManager.js` - Adicionar suporte a spots
- [ ] `/utils/mediaSchedule.js` - Validar isMediaCurrentlyPlayable

### Frontend - Admin
- [ ] `/components/audio/AudioTrackSelector.jsx` - Seleção múltipla
- [ ] `/components/audio/AudioFolderManager.jsx` - Drag-and-drop
- [ ] `/pages/EditorPlaylist.jsx` - Drag-and-drop
- [ ] `/pages/PlaylistDetalhe.jsx` - Drag-and-drop

### Documentação
- [x] `/AUDITORIA_COMPLETA.md` - Criado
- [x] `/IMPLEMENTACAO_CORRECOES.md` - Criado
- [ ] `/docs/LIMITACOES_PLATAFORMA.md` - Criar
- [ ] `/docs/MANUAL_USUARIO.md` - Atualizar
- [ ] `/docs/API_ENDPOINTS.md` - Atualizar

---

**Última atualização:** 26/05/2026 15:08
