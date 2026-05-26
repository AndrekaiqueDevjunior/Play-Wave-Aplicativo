# 🧪 TESTES DE INTEGRAÇÃO - PLAYWAVE
**Data:** 26 de Maio de 2026  
**Status:** Pronto para Testes

---

## ✅ IMPLEMENTAÇÕES CONCLUÍDAS

### 1. Resolução de Horários de Pastas ✅
**Arquivo:** `/frontend/src/pages/PlayerAudio.jsx` (linhas 165-211)

**Funcionalidade:**
- Detecta automaticamente qual pasta de áudio deve tocar no horário atual
- Troca pasta automaticamente ao mudar horário
- Respeita prioridade em caso de conflito
- Verifica a cada 1 minuto

**Como testar:**
1. Criar playlist de rádio com 2 pastas:
   - Pasta "Manhã": 06:00 - 12:00
   - Pasta "Tarde": 12:00 - 18:00
2. Abrir PlayerAudio.jsx
3. Verificar logs no console:
   ```
   [player-audio] Mudança de pasta detectada: {
     previous: 'nenhuma',
     current: 'Manhã',
     time: '10:30:00'
   }
   [player-audio] Carregando faixas da pasta: {
     folder: 'Manhã',
     mode: 'sequential',
     trackCount: 5
   }
   ```
4. Aguardar mudança de horário (ou simular alterando horário do sistema)
5. Verificar se pasta mudou automaticamente

**Critérios de aceite:**
- ✅ Pasta correta toca no horário configurado
- ✅ Troca automática ao mudar horário
- ✅ Logs detalhados no console
- ✅ Sem erros de execução

---

### 2. Reprodução de Spots Recorrentes ✅
**Arquivo:** `/frontend/src/pages/PlayerAudio.jsx` (linhas 213-275)

**Funcionalidade:**
- Toca spots automaticamente a cada X segundos
- Respeita horário de início/fim do spot
- Registra log de reprodução
- Verifica a cada 30 segundos

**Como testar:**
1. Criar spot com intervalo de 5 minutos (300 segundos)
2. Configurar horário: 08:00 - 20:00
3. Abrir PlayerAudio.jsx
4. Verificar logs no console:
   ```
   [player-audio] Tocando spot: {
     spot: 'Promoção do Dia',
     interval: 300,
     lastPlayed: 'nunca',
     now: '10:35:00'
   }
   ```
5. Aguardar 5 minutos
6. Verificar se spot toca novamente

**Critérios de aceite:**
- ✅ Spot toca no intervalo configurado
- ✅ Não toca fora do horário configurado
- ✅ Logs detalhados no console
- ✅ Evento de reprodução registrado no backend

---

### 3. Modo Shuffle ✅
**Arquivo:** `/frontend/src/pages/PlayerAudio.jsx` (linhas 122-128)

**Funcionalidade:**
- Embaralha faixas quando `shuffle_enabled = true`
- Usa algoritmo Fisher-Yates
- Respeita configuração por pasta

**Como testar:**
1. Criar playlist com `shuffle_enabled: true`
2. Adicionar 10 faixas
3. Abrir PlayerAudio.jsx
4. Verificar ordem de reprodução
5. Confirmar que não é sequencial

**Critérios de aceite:**
- ✅ Faixas tocam em ordem aleatória
- ✅ Não repete mesma faixa seguidamente
- ✅ Respeita configuração da playlist/pasta

---

### 4. Logs Detalhados de Comandos ✅
**Arquivo:** `/frontend/src/player-core/commands.js` (linhas 174-238)

**Funcionalidade:**
- Logs detalhados de início/fim de comando
- Informações de plataforma e contexto
- Stack trace completo em caso de erro
- Identificação de comandos não suportados

**Como testar:**
1. Abrir Player.jsx
2. Enviar comando via admin (sync, restart, shutdown)
3. Verificar logs no console:
   ```
   [commands] ========================================
   [commands] Executando comando: restart_device
   [commands] Plataforma: web
   [commands] Payload: {}
   [commands] Context: { deviceId: '123', phase: 'playing' }
   [commands] ========================================
   [commands] ▶️  Iniciando execução...
   [commands] ❌ ERRO ao executar: restart_device
   [commands] Mensagem: restart_device não suportado na plataforma web
   [commands] Platform unsupported: true
   [commands] Error code: BROWSER_ENVIRONMENT
   [commands] ========================================
   ```

**Critérios de aceite:**
- ✅ Logs claros e organizados
- ✅ Informações completas de erro
- ✅ Identificação de plataforma
- ✅ Stack trace quando necessário

---

## 🧪 ROTEIRO DE TESTES COMPLETO

### Teste 1: Filtro de Mídia por Período
**Objetivo:** Validar que mídias com starts_at/ends_at são filtradas corretamente

**Passos:**
1. Criar mídia com `starts_at` = amanhã
2. Adicionar em campanha
3. Abrir player
4. Verificar que mídia NÃO aparece
5. Alterar `starts_at` para hoje
6. Recarregar player
7. Verificar que mídia APARECE

**Resultado esperado:**
- Mídia futura não aparece
- Mídia passada não aparece
- Mídia no período correto aparece
- Logs: `[player] playlist response: { media: [...] }`

---

### Teste 2: Substituição de Mídia
**Objetivo:** Validar que substituir arquivo mantém vínculos

**Passos:**
1. Criar mídia "Video1.mp4"
2. Adicionar em campanha
3. Substituir arquivo por "Video2.mp4"
4. Verificar que campanha ainda tem a mídia
5. Verificar que `file_version` incrementou
6. Abrir player
7. Verificar que player baixa nova versão

**Resultado esperado:**
- Campanha mantém vínculo
- `file_version` = 2
- Player usa nova versão
- Cache key: `media_id:2:hash`

---

### Teste 3: Upload Múltiplo de Áudios
**Objetivo:** Validar upload de múltiplos arquivos

**Passos:**
1. Abrir página de áudio
2. Clicar em "Upload Múltiplo"
3. Selecionar 5 arquivos MP3
4. Iniciar upload
5. Verificar progresso
6. Verificar lista de áudios

**Resultado esperado:**
- Todos os 5 arquivos aparecem
- Duração detectada automaticamente
- Sem erros
- Feedback visual de progresso

---

### Teste 4: Pasta de Áudio por Horário
**Objetivo:** Validar troca automática de pasta

**Passos:**
1. Criar pasta "Manhã" (06:00-12:00) com 3 músicas
2. Criar pasta "Tarde" (12:00-18:00) com 3 músicas
3. Criar playlist de rádio
4. Adicionar ambas as pastas com horários
5. Abrir PlayerAudio às 10:00
6. Verificar que toca pasta "Manhã"
7. Aguardar até 12:00 (ou simular)
8. Verificar que mudou para pasta "Tarde"

**Resultado esperado:**
- Pasta "Manhã" toca das 06:00-12:00
- Pasta "Tarde" toca das 12:00-18:00
- Troca automática ao mudar horário
- Logs de mudança no console

---

### Teste 5: Spot Recorrente
**Objetivo:** Validar reprodução de spot a cada X minutos

**Passos:**
1. Criar spot "Promoção"
2. Configurar intervalo: 300 segundos (5 min)
3. Configurar horário: 08:00-20:00
4. Adicionar na playlist
5. Abrir PlayerAudio às 10:00
6. Verificar que spot toca
7. Aguardar 5 minutos
8. Verificar que spot toca novamente

**Resultado esperado:**
- Spot toca a cada 5 minutos
- Não toca fora do horário (antes 08:00 ou depois 20:00)
- Logs de reprodução
- Evento registrado no backend

---

### Teste 6: Modo Shuffle
**Objetivo:** Validar embaralhamento de faixas

**Passos:**
1. Criar playlist com 10 faixas
2. Ativar `shuffle_enabled`
3. Abrir PlayerAudio
4. Anotar ordem de reprodução
5. Recarregar player
6. Verificar que ordem mudou

**Resultado esperado:**
- Ordem aleatória
- Não repete mesma faixa seguidamente
- Todas as faixas tocam eventualmente

---

### Teste 7: Comandos do Player
**Objetivo:** Validar comandos remotos

**Passos:**
1. Abrir player
2. Enviar comando "sync" via admin
3. Verificar logs detalhados
4. Verificar que playlist recarregou
5. Enviar comando "restart_device"
6. Verificar erro de plataforma não suportada (se web)
7. Verificar ACK no backend

**Resultado esperado:**
- Comando "sync" funciona
- Logs detalhados aparecem
- Comando "restart_device" falha em web com erro claro
- ACK registrado no backend

---

### Teste 8: Pareamento
**Objetivo:** Validar invalidação de token

**Passos:**
1. Parear player com código "TV-ABCD"
2. Verificar que player funciona
3. Regenerar código via admin
4. Verificar que player recebe erro
5. Verificar que player volta para tela de pareamento
6. Parear novamente
7. Verificar que funciona

**Resultado esperado:**
- Player antigo para de funcionar
- Erro: `REQUIRES_REPAIRING`
- Player volta para pareamento
- Novo pareamento funciona

---

### Teste 9: Política de Áudio
**Objetivo:** Validar resolução de conflito de áudio

**Passos:**
1. Configurar campanha com vídeo COM áudio
2. Configurar rádio ativa
3. Configurar `audio_policy = AUTO`
4. Abrir player
5. Verificar que rádio pausa quando vídeo toca
6. Verificar que rádio retoma quando vídeo termina
7. Testar outros modos (RADIO_ONLY, MIX, etc)

**Resultado esperado:**
- AUTO: Rádio pausa durante vídeo com áudio
- RADIO_ONLY: Vídeo fica mudo, rádio continua
- MIX: Ambos tocam juntos
- MEDIA_AUDIO_ONLY: Rádio pausa, áudio do vídeo toca

---

### Teste 10: OSD (Nome da Música)
**Objetivo:** Validar exibição de nome da música

**Passos:**
1. Configurar `osd_show_current_audio = true`
2. Configurar posição: `top_right`
3. Configurar duração: 8 segundos
4. Abrir player
5. Iniciar reprodução de rádio
6. Verificar que nome aparece no canto superior direito
7. Verificar que desaparece após 8 segundos

**Resultado esperado:**
- Nome da música aparece
- Posição correta
- Duração correta
- Opacidade configurável

---

## 📊 CHECKLIST DE VALIDAÇÃO

### Backend
- [ ] Endpoint `/devices/{id}/playlist` retorna folder_schedules
- [ ] Endpoint `/devices/{id}/playlist` retorna spot_schedules
- [ ] Endpoint `/devices/{id}/playlist` filtra mídias por período
- [ ] Endpoint `/audio/tracks/upload-multiple` funciona
- [ ] Endpoint `/devices/{id}/command` cria comando
- [ ] Endpoint `/devices/{id}/commands/pending` retorna comandos
- [ ] Endpoint `/devices/{id}/regenerate-code` invalida token

### Frontend Admin
- [ ] Upload múltiplo de áudios funciona
- [ ] Criar pasta de áudio funciona
- [ ] Agendar pasta por horário funciona
- [ ] Criar spot funciona
- [ ] Configurar intervalo de spot funciona
- [ ] Enviar comando funciona

### Player
- [ ] Filtro de mídia por período funciona
- [ ] Troca de pasta por horário funciona
- [ ] Reprodução de spots funciona
- [ ] Modo shuffle funciona
- [ ] Comandos remotos funcionam
- [ ] Logs detalhados aparecem
- [ ] Pareamento funciona
- [ ] Invalidação de token funciona
- [ ] OSD funciona

---

## 🐛 BUGS CONHECIDOS E LIMITAÇÕES

### 1. Comandos de Shutdown/Restart
**Status:** Funciona apenas em ambientes nativos

**Plataformas:**
- ❌ Web Browser: Não suporta (limitação do navegador)
- ⚠️ Electron: Precisa implementar bridge em preload.js
- ⚠️ Capacitor: Precisa implementar plugin nativo
- ⚠️ Smart TV: Depende de APIs do fabricante

**Workaround:**
- Documentar limitação
- Exibir mensagem clara no admin
- Implementar bridges nativos (próxima fase)

---

### 2. Spots Podem Atrasar
**Status:** Comportamento esperado

**Causa:**
- Política `WAIT_SILENCE` aguarda música terminar
- Música longa pode atrasar spot

**Workaround:**
- Usar política `INTERRUPT` para spots urgentes
- Usar política `FADE_MIX` para transição suave
- Documentar comportamento

---

### 3. Shuffle Pode Repetir Eventualmente
**Status:** Comportamento esperado

**Causa:**
- Algoritmo Fisher-Yates é aleatório puro
- Não mantém histórico entre sessões

**Workaround:**
- Implementar histórico de reprodução (próxima fase)
- Evitar repetição das últimas N faixas
- Documentar comportamento

---

## 🎯 PRÓXIMOS PASSOS

### Hoje (26/05/2026)
1. ✅ Executar testes manuais 1-10
2. ⚠️ Corrigir bugs encontrados
3. ⚠️ Validar em múltiplos navegadores

### Amanhã (27/05/2026)
1. ⚠️ Implementar seleção múltipla
2. ⚠️ Implementar drag-and-drop
3. ⚠️ Criar testes automatizados

### Próxima Semana
1. ⚠️ Implementar bridges nativos
2. ⚠️ Testes em Electron
3. ⚠️ Testes em Capacitor
4. ⚠️ Documentação de usuário

---

## 📝 RELATÓRIO DE TESTES

### Template de Relatório

```markdown
## Teste: [Nome do Teste]
**Data:** [Data]
**Testador:** [Nome]
**Ambiente:** [Browser/Electron/APK]

### Resultado
- [ ] Passou
- [ ] Falhou
- [ ] Parcial

### Observações
[Descrever o que aconteceu]

### Bugs Encontrados
[Listar bugs, se houver]

### Screenshots
[Anexar screenshots, se relevante]
```

---

**Última atualização:** 26/05/2026 15:45
