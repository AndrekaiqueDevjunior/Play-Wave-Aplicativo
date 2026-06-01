# 🐛 BUGS CRÍTICOS ENCONTRADOS - 01/06/2026

**Reportados pelo usuário em testes reais do sistema.**

---

## 📋 LISTA DE BUGS

### 🔴 CRÍTICO 8: Tela Branca ao Ver Detalhes do Dispositivo ✅ CORREÇÃO APLICADA

**Problema:** Ao clicar em "Ver detalhes" no menu de ações do dispositivo, página fica em tela branca.

**Investigação:**
- [ ] Verificar erros no console do navegador (F12)
- [ ] Verificar logs do componente DispositivoDetalhe
- [ ] Verificar se todos os componentes importados existem
- [ ] Verificar ErrorBoundary capturando erro

**Possíveis Causas:**
1. Componente importado não existe ou tem erro
2. Erro de runtime não tratado
3. Query falhando sem tratamento
4. Rota mal configurada

**Correção Aplicada:**
1. ✅ Criado `ErrorBoundary.jsx` para capturar erros
2. ✅ Adicionado ErrorBoundary ao app.jsx
3. ✅ Adicionado console.log detalhado no DispositivoDetalhe
4. ✅ Adicionado tratamento de erro na query

**Como Testar:**
```
1. Abrir DevTools (F12)
2. Ir na aba Console
3. Clicar em "Ver detalhes" de um dispositivo
4. Ver logs: [DispositivoDetalhe] Componente montado
5. Ver logs: [DispositivoDetalhe] Device ID: xxx
6. Ver logs: [DispositivoDetalhe] Device data: {...}
7. Se houver erro, ErrorBoundary vai capturar e mostrar mensagem
```

**Próximos Passos:**
- Testar e coletar erro exato do console
- Se for componente faltando, criar/importar corretamente
- Se for query falhando, adicionar fallback/loading

---

### 🔴 CRÍTICO 1: Conteúdo da Campanha Não Passa no Player

**Problema:** Ao criar campanha e adicionar mídias, o player não exibe nada.

**Investigação Necessária:**
- [ ] Verificar se playlist está chegando vazia no player
- [ ] Verificar filtro `isMediaCurrentlyPlayable()`
- [ ] Verificar agendamento de horário da campanha
- [ ] Verificar logs do player (console/network)
- [ ] Verificar se dispositivo está associado à campanha

**Possíveis Causas:**
1. Campanha sem dispositivos associados
2. Mídia fora do período (starts_at/ends_at)
3. Campanha em status "draft"
4. Horário da campanha não compatível (schedule_start/end_time)

**Código a Investigar:**
- `frontend/src/pages/Player.jsx` - loadPlaylist()
- `frontend/src/utils/mediaSchedule.js` - isMediaCurrentlyPlayable()
- `backend/api/v1/devices.py` - endpoint de playlist

---

### 🔴 CRÍTICO 2: Player Reinicia ao Mexer no Gerenciador

**Problema:** Qualquer alteração no admin causa restart do player.

**Investigação Necessária:**
- [ ] Verificar `campaign_version` e `playlist_version`
- [ ] Verificar polling de commands
- [ ] Verificar heartbeat invalidando cache
- [ ] Verificar se todo update incrementa versão

**Possíveis Causas:**
1. `campaign_version` incrementando em TODA atualização (deveria ser apenas estrutura)
2. Player recebendo comando `sync` ou `refresh_playlist` automaticamente
3. Heartbeat retornando versão diferente sempre

**Código a Investigar:**
- `backend/api/v1/campaigns.py` - _bump_and_invalidate()
- `frontend/src/pages/Player.jsx` - useEffect que detecta mudança de versão
- `backend/api/v1/devices.py` - heartbeat

**Lógica Esperada:**
- Apenas mudanças estruturais devem incrementar `campaign_version`:
  - Adicionar/remover mídia
  - Reordenar playlist
  - Mudar status da campanha
  - Mudar dispositivos associados
- NÃO deve incrementar:
  - Alterar nome da campanha
  - Alterar descrição
  - Alterar prioridade

---

### 🟠 IMPORTANTE 3: Agendamento Duplicado (Campanha vs Gerenciador)

**Problema:** Confusão sobre agendar na campanha vs agendar no gerenciador.

**Esclarecimento:**

**Agendamento na Campanha:**
```javascript
{
  start_date: "2026-06-01T00:00:00",  // Período total
  end_date: "2026-06-30T23:59:59",
  schedule_start_time: "08:00",       // Horário diário
  schedule_end_time: "18:00"
}
```
- Define QUANDO a campanha está ativa
- Afeta TODOS os dispositivos da campanha

**Agendamento no Gerenciador (Dispositivo):**
- Associa campanha a dispositivos específicos
- Não tem agendamento próprio

**Agendamento na Mídia:**
```javascript
{
  starts_at: "2026-06-15T00:00:00",  // Período específico da mídia
  ends_at: "2026-06-20T23:59:59"
}
```
- Define período de UMA mídia específica
- Independente da campanha

**Solução:** Documentar melhor a hierarquia de agendamento.

---

### 🔴 CRÍTICO 4: Spot Bloqueia Playlist de Rádio

**Problema:** Quando coloca spot, só roda spot e não toca mais a playlist.

**Investigação Necessária:**
- [ ] Verificar lógica do AudioManager
- [ ] Verificar `resolveActiveSpotsForNow()`
- [ ] Verificar se spot fica "preso" em loop
- [ ] Verificar `calculateNextSpotTime()`

**Possíveis Causas:**
1. Spot com `interval_seconds` muito baixo (toca sempre)
2. Lógica não voltando para playlist após spot
3. Estado `AUDIO_STATE.SPOT` não transitando para `RADIO`

**Código a Investigar:**
- `frontend/src/player-core/audioManager.js` - transição SPOT → RADIO
- `frontend/src/utils/audioScheduleResolver.js` - shouldPlaySpotNow()
- `frontend/src/pages/PlayerAudio.jsx` - useEffect de spots

**Lógica Esperada:**
1. Player toca playlist normalmente
2. A cada X segundos, verifica se deve tocar spot
3. Se sim, pausa playlist, toca spot
4. Após spot terminar, volta para playlist

---

### 🔴 CRÍTICO 5: Pasta de Música Não Funciona

**Problema:** Ao criar pasta de música e agendar, não toca nada.

**Investigação Necessária:**
- [ ] Verificar se pasta tem faixas associadas
- [ ] Verificar `AudioPlaylistFolderSchedule` no banco
- [ ] Verificar `resolveActiveFolderForNow()`
- [ ] Verificar logs do player

**Possíveis Causas:**
1. Pasta sem faixas (vazia)
2. Agendamento de pasta incorreto (horário/dias)
3. Pasta em status "inactive" ou "archived"
4. Faixas da pasta em status "inactive"

**Código a Investigar:**
- `backend/api/v1/audio/folders.py` - listar faixas da pasta
- `frontend/src/utils/audioScheduleResolver.js` - resolveActiveFolderForNow()
- `backend/api/v1/devices.py` - endpoint que monta playlist com pastas

**Checklist de Validação:**
1. Pasta criada? ✓
2. Faixas adicionadas na pasta? ✓
3. Pasta agendada na playlist? ✓
4. Horário correto? ✓
5. Dias da semana corretos? ✓
6. Status ativo? ✓

---

### 🔴 CRÍTICO 6: Comandos Não Funcionam (Desligar/Reiniciar)

**Problema:** Player não recebe/executa comandos do gerenciador.

**Investigação Necessária:**
- [ ] Verificar polling de commands no player
- [ ] Verificar ACK de comandos
- [ ] Verificar logs do backend (comando criado?)
- [ ] Verificar logs do player (comando recebido?)
- [ ] Verificar plataforma (web/electron/capacitor)

**Possíveis Causas:**
1. Polling de commands não rodando
2. `pollCommandsRunningRef` travado em `true`
3. Erro no executeCommand() silencioso
4. Plataforma web (não suporta shutdown/restart de hardware)
5. Permissões faltando (sudo no Linux, Admin no Windows)

**Código a Investigar:**
- `frontend/src/pages/Player.jsx` - useEffect de polling commands
- `frontend/src/player-core/commands.js` - executeCommand()
- `backend/api/v1/devices.py` - criar comando

**Teste Manual:**
```bash
# No console do player
console.log("pollCommandsRunningRef:", pollCommandsRunningRef.current);
console.log("lastCheckedTimestamp:", lastCheckedTimestamp.current);

# Forçar polling
pollCommands();
```

**Plataformas e Suporte:**
- **Web puro:** ❌ Não suporta shutdown/restart de hardware
- **Electron:** ✅ Suporta com sudo/Admin
- **Capacitor:** ✅ Suporta se Device Owner
- **Sync/Refresh:** ✅ Todas plataformas

---

### 🟡 DÚVIDA 7: O que é Prioridade?

**Pergunta:** "O que é esse número de prioridade nas mídias e áudios?"

**Resposta:**

#### Prioridade em Campanhas
```javascript
{
  priority: 1  // Valor de 1 a 10
}
```
- **Uso:** Quando MÚLTIPLAS campanhas estão ativas no mesmo dispositivo
- **Lógica:** Campanha com maior prioridade é exibida
- **Exemplo:**
  - Campanha A (prioridade 10) - Promoção urgente
  - Campanha B (prioridade 5) - Conteúdo normal
  - **Resultado:** Player exibe apenas Campanha A

**Quando usar prioridade alta (8-10):**
- Comunicados urgentes
- Promoções relâmpago
- Avisos importantes

**Quando usar prioridade média (4-7):**
- Campanhas normais
- Conteúdo padrão

**Quando usar prioridade baixa (1-3):**
- Conteúdo de fallback
- Campanhas de fundo

#### Prioridade em Pastas de Áudio
```javascript
{
  priority: 1  // Em AudioPlaylistFolderSchedule
}
```
- **Uso:** Quando MÚLTIPLAS pastas têm horários sobrepostos
- **Lógica:** Pasta com maior prioridade toca
- **Exemplo:**
  - Pasta "Especial Natal" (prioridade 10, Dezembro)
  - Pasta "Manhã Normal" (prioridade 5, sempre)
  - **Resultado:** Em Dezembro de manhã, toca "Especial Natal"

**Observação:** Se apenas 1 campanha/pasta está ativa, prioridade não importa.

---

## 🔧 PLANO DE CORREÇÃO

### Fase 1: Investigação (2-3 horas)
- [ ] Reproduzir cada bug localmente
- [ ] Coletar logs do backend
- [ ] Coletar logs do player (console)
- [ ] Documentar steps exatos para reproduzir

### Fase 2: Correções Críticas (4-6 horas)
- [ ] **Bug 1:** Campanha não passa
  - Adicionar logs detalhados
  - Validar filtros de agendamento
  - Criar tela de debug no player
  
- [ ] **Bug 2:** Player reinicia sempre
  - Refinar lógica de `_bump_and_invalidate()`
  - Só incrementar versão em mudanças estruturais
  
- [ ] **Bug 4:** Spot bloqueia playlist
  - Corrigir transição SPOT → RADIO
  - Adicionar timeout de segurança
  
- [ ] **Bug 5:** Pasta não funciona
  - Validar montagem de playlist com pastas
  - Adicionar logs no resolver
  
- [ ] **Bug 6:** Comandos não funcionam
  - Verificar polling
  - Adicionar retry automático
  - Melhorar feedback visual

### Fase 3: Melhorias UX (2-3 horas)
- [ ] Documentar hierarquia de agendamento
- [ ] Adicionar tooltips explicativos
- [ ] Criar FAQ sobre prioridade
- [ ] Adicionar validações client-side

### Fase 4: Testes (2-3 horas)
- [ ] Testar cada correção
- [ ] Validar cenários edge case
- [ ] Testar em produção
- [ ] Coletar feedback

---

## 🧪 TESTES PARA REPRODUZIR

### Teste 1: Campanha Não Passa
```
1. Criar nova campanha
2. Status: active
3. Adicionar 3 mídias
4. Associar dispositivo
5. Abrir player
6. Verificar: mídias passam?
```

### Teste 2: Player Reinicia
```
1. Player rodando normalmente
2. No admin, editar nome da campanha
3. Salvar
4. Verificar: player reiniciou?
```

### Teste 3: Spot Bloqueia Playlist
```
1. Criar playlist de rádio com 5 músicas
2. Criar spot
3. Agendar spot a cada 60 segundos
4. Verificar: toca música entre spots?
```

### Teste 4: Pasta Não Funciona
```
1. Criar pasta "Manhã"
2. Adicionar 3 músicas
3. Agendar pasta: 06:00-12:00, Seg-Sex
4. Vincular pasta à playlist
5. Horário atual: 10:00 de segunda
6. Verificar: toca músicas da pasta?
```

### Teste 5: Comandos Não Funcionam
```
1. Player rodando
2. No admin, ir em Dispositivos
3. Clicar em "Comandos"
4. Enviar "Sincronizar"
5. Verificar: player recebeu?
```

---

## 📊 PRIORIZAÇÃO

| Bug | Severidade | Impacto | Prioridade | Status |
|-----|------------|---------|------------|--------|
| #8 Tela branca detalhes | 🔴 Crítico | Alto | **P0** | ✅ Correção aplicada |
| #1 Campanha não passa | 🔴 Crítico | Alto | **P0** | 🔍 Investigar |
| #2 Player reinicia | 🔴 Crítico | Médio | **P1** | 🔍 Investigar |
| #4 Spot bloqueia playlist | 🔴 Crítico | Alto | **P0** | 🔍 Investigar |
| #5 Pasta não funciona | 🔴 Crítico | Alto | **P0** | 🔍 Investigar |
| #6 Comandos não funcionam | 🔴 Crítico | Médio | **P1** | 🔍 Investigar |
| #3 Confusão agendamento | 🟠 Importante | Baixo | **P2** | 📝 Documentar |
| #7 Dúvida prioridade | 🟡 Dúvida | Baixo | **P3** | 📝 Documentar |

**P0 = Bloqueia uso do sistema**  
**P1 = Afeta experiência crítica**  
**P2 = Melhoria importante**  
**P3 = Documentação**

---

## 🚨 BLOQUEADORES PARA PRODUÇÃO

Antes de fazer deploy em produção, **OBRIGATÓRIO** corrigir:

- ❌ Bug #1: Campanha não passa
- ❌ Bug #4: Spot bloqueia playlist
- ❌ Bug #5: Pasta não funciona

**Status:** ❌ **NÃO DEPLOY ATE CORRIGIR**

---

## 📝 PRÓXIMOS PASSOS

1. **Investigação:** Reproduzir bugs localmente com logs
2. **Correção:** Implementar fixes
3. **Teste:** Validar correções
4. **Deploy:** Atualizar VPS apenas após validação
5. **Monitoramento:** Acompanhar uso real

---

**Criado em:** 01/06/2026  
**Reportado por:** Usuário (testes reais)  
**Status:** 🔴 EM INVESTIGAÇÃO
