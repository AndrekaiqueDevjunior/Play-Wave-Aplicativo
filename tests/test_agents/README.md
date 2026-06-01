# 🤖 AGENTES DE TESTE - BUGS CRÍTICOS

**Agentes automatizados para testar e validar correções dos bugs P0/P1/P2.**

---

## 📋 ÍNDICE

1. [Instalação](#instalacao)
2. [Agente #1 - Campanha Não Passa](#agente-1)
3. [Agente #2 - Player Reinicia](#agente-2)
4. [Agente #3 - Agendamento Duplicado](#agente-3)
5. [Agente #4 - Spot Bloqueia Playlist](#agente-4)
6. [Agente #5 - Pasta Não Funciona](#agente-5)
7. [Agente #6 - Comandos Não Funcionam](#agente-6)
8. [Agente #7 - Validação de Prioridade](#agente-7)

---

<a name="instalacao"></a>
## 🚀 INSTALAÇÃO

### Backend (Python)

```bash
cd tests/test_agents
pip install -r requirements.txt
```

### Frontend (Playwright)

```bash
cd tests/test_agents
npm install
npx playwright install
```

### Configuração

Criar `.env` na pasta `tests/test_agents`:

```env
# Backend
API_BASE_URL=http://localhost:8000
API_USERNAME=admin@playwave.com
API_PASSWORD=admin123

# Frontend
FRONTEND_URL=http://localhost:5173
PLAYER_URL=http://localhost:5173/player

# Configurações de teste
TEST_DEVICE_ID=
TEST_CAMPAIGN_ID=
TEST_PAIRING_CODE=
```

---

<a name="agente-1"></a>
## 🤖 AGENTE #1: CAMPANHA NÃO PASSA NO PLAYER

**Bug:** Conteúdo da campanha não aparece no player.

### Cenários de Teste

1. ✅ Criar campanha com status "active"
2. ✅ Adicionar 3 mídias válidas
3. ✅ Associar dispositivo à campanha
4. ✅ Verificar playlist no endpoint do player
5. ✅ Validar filtros de agendamento
6. ✅ Simular player consumindo playlist

### Executar

```bash
# Backend API
python test_agents/agent_1_campanha_nao_passa.py

# Frontend E2E
npx playwright test agent_1_campanha_nao_passa.spec.js
```

### Validações

- [ ] Playlist retorna mídias?
- [ ] Mídias passam por `isMediaCurrentlyPlayable()`?
- [ ] Campanha tem período ativo?
- [ ] Dispositivo está associado?

---

<a name="agente-2"></a>
## 🤖 AGENTE #2: PLAYER REINICIA AO EDITAR CAMPANHA

**Bug:** Qualquer alteração na campanha causa restart do player.

### Cenários de Teste

1. ✅ Player rodando normalmente
2. ✅ Editar **apenas nome** da campanha
3. ✅ Verificar se `campaign_version` mudou
4. ✅ Validar heartbeat do player
5. ✅ Confirmar se player detectou mudança

### Executar

```bash
# Backend API
python test_agents/agent_2_player_reinicia.py

# Frontend E2E
npx playwright test agent_2_player_reinicia.spec.js --headed
```

### Validações

- [ ] `campaign_version` incrementa?
- [ ] Player recebe versão diferente?
- [ ] Player reinicia automaticamente?
- [ ] Apenas mudanças estruturais devem incrementar?

---

<a name="agente-3"></a>
## 🤖 AGENTE #3: HIERARQUIA DE AGENDAMENTO

**Bug:** Confusão sobre agendamento na campanha vs dispositivo vs mídia.

### Cenários de Teste

1. ✅ Criar campanha com período global
2. ✅ Adicionar mídia com período específico
3. ✅ Validar hierarquia de filtros
4. ✅ Testar casos de sobreposição

### Executar

```bash
python test_agents/agent_3_hierarquia_agendamento.py
```

### Validações

- [ ] Campanha fora do período → nenhuma mídia passa?
- [ ] Mídia fora do período → só ela não passa?
- [ ] Documentação clara da hierarquia?

---

<a name="agente-4"></a>
## 🤖 AGENTE #4: SPOT BLOQUEIA PLAYLIST

**Bug:** Quando configura spot, só toca spot em loop, não volta para playlist.

### Cenários de Teste

1. ✅ Criar playlist com 5 músicas
2. ✅ Criar spot a cada 60 segundos
3. ✅ Simular playback por 5 minutos
4. ✅ Validar transição SPOT → RADIO
5. ✅ Verificar AudioManager

### Executar

```bash
# Backend
python test_agents/agent_4_spot_bloqueia_playlist.py

# Simulação de player
node test_agents/agent_4_spot_simulator.js
```

### Validações

- [ ] Spot toca a cada X segundos?
- [ ] Após spot terminar, volta para playlist?
- [ ] Playlist continua de onde parou?
- [ ] Não fica preso em loop de spot?

---

<a name="agente-5"></a>
## 🤖 AGENTE #5: PASTA NÃO FUNCIONA

**Bug:** Criar pasta de música e agendar, mas não toca nada.

### Cenários de Teste

1. ✅ Criar pasta "Manhã"
2. ✅ Adicionar 3 faixas na pasta
3. ✅ Agendar pasta: 06:00-12:00, Seg-Sex
4. ✅ Simular horário 10:00 de segunda
5. ✅ Verificar `resolveActiveFolderForNow()`

### Executar

```bash
# Backend
python test_agents/agent_5_pasta_nao_funciona.py

# Testes de resolver
npm test agent_5_folder_resolver.test.js
```

### Validações

- [ ] Pasta tem faixas?
- [ ] Agendamento está correto?
- [ ] Resolver retorna pasta ativa?
- [ ] Faixas estão em status ativo?

---

<a name="agente-6"></a>
## 🤖 AGENTE #6: COMANDOS NÃO FUNCIONAM

**Bug:** Enviar comando no gerenciador, player não executa.

### Cenários de Teste

1. ✅ Player pareado e rodando
2. ✅ Enviar comando "sync"
3. ✅ Verificar polling de commands
4. ✅ Validar ACK do comando
5. ✅ Testar comandos destrutivos

### Executar

```bash
# Backend
python test_agents/agent_6_comandos_nao_funcionam.py

# Frontend E2E com player real
npx playwright test agent_6_comandos.spec.js --headed
```

### Validações

- [ ] Comando criado no backend?
- [ ] Player faz polling?
- [ ] `pollCommandsRunningRef` não travado?
- [ ] `executeCommand()` sem erros?
- [ ] ACK registrado?

---

<a name="agente-7"></a>
## 🤖 AGENTE #7: VALIDAÇÃO DE PRIORIDADE

**Bug:** Dúvida sobre o que é prioridade.

### Cenários de Teste

1. ✅ Criar 2 campanhas ativas simultaneamente
2. ✅ Campanha A (prioridade 10)
3. ✅ Campanha B (prioridade 5)
4. ✅ Verificar qual passa no player

### Executar

```bash
python test_agents/agent_7_prioridade.py
```

### Validações

- [ ] Maior prioridade = exibida?
- [ ] Documentação clara?
- [ ] Exemplos práticos?

---

## 🎯 EXECUTAR TODOS OS AGENTES

### Sequencial

```bash
./run_all_agents.sh
```

### Paralelo (mais rápido)

```bash
./run_all_agents_parallel.sh
```

### Apenas P0 (bugs bloqueadores)

```bash
./run_p0_agents.sh
```

---

## 📊 RELATÓRIOS

Os agentes geram relatórios em:

```
tests/test_agents/reports/
├── agent_1_report.json
├── agent_2_report.json
├── agent_3_report.json
├── agent_4_report.json
├── agent_5_report.json
├── agent_6_report.json
├── agent_7_report.json
└── summary.html
```

### Ver Relatório

```bash
# Abrir relatório HTML
open tests/test_agents/reports/summary.html

# Ver JSON no terminal
cat tests/test_agents/reports/agent_1_report.json | jq
```

---

## 🔧 TROUBLESHOOTING

### Agente falha ao conectar backend

```bash
# Verificar se backend está rodando
curl http://localhost:8000/api/v1/health

# Verificar credenciais no .env
cat tests/test_agents/.env
```

### Playwright não encontra player

```bash
# Verificar se frontend está rodando
curl http://localhost:5173

# Instalar navegadores
npx playwright install chromium
```

### Permissões de comandos (Linux)

```bash
chmod +x run_all_agents.sh
chmod +x run_p0_agents.sh
```

---

## 📝 ESTRUTURA DOS RELATÓRIOS

Cada agente gera JSON:

```json
{
  "agent_id": 1,
  "bug_name": "Campanha não passa no player",
  "priority": "P0",
  "timestamp": "2026-06-01T15:15:00Z",
  "status": "FAILED",
  "scenarios": [
    {
      "name": "Criar campanha",
      "status": "PASSED",
      "duration_ms": 234
    },
    {
      "name": "Playlist vazia",
      "status": "FAILED",
      "error": "Playlist retornou 0 mídias",
      "expected": "3 mídias",
      "actual": "0 mídias"
    }
  ],
  "recommendations": [
    "Verificar se dispositivo está associado à campanha",
    "Verificar período de agendamento da campanha"
  ]
}
```

---

## ✅ CRITÉRIOS DE SUCESSO

### Bug considerado **CORRIGIDO** quando:

1. ✅ Todos os cenários passam
2. ✅ Nenhum erro crítico nos logs
3. ✅ Comportamento esperado confirmado
4. ✅ Edge cases validados

### Bug considerado **PENDENTE** quando:

- ⚠️ Algum cenário falha
- ⚠️ Comportamento inconsistente
- ⚠️ Precisa investigação adicional

---

**Criado em:** 01/06/2026  
**Versão:** 1.0.0  
**Mantido por:** Equipe PlayWave
