# PR 4 - Teste Manual: Bugs

## Bug 1: Testar restore depois de app sair de fullscreen

### Descrição
Verificar se o `show_desktop` com `restore_fullscreen=true` consegue restaurar fullscreen corretamente, mesmo que o app tenha saído de fullscreen durante o tempo de desktop exposure.

### Cenário A: Restaurar quando fullscreen ativo (caminho feliz)

**Preparação:**
1. Iniciar app Electron em modo fullscreen (`PLAYER_KIOSK=true`)
2. Conectar device no painel admin
3. Iniciar uma campanha (qualquer mídia)
4. Habilitar "Comportamento do Player" com intervalo 30s, duração 5s

**Passos:**
1. Aguardar primeiro `show_desktop` ser enviado (~30s)
2. Validar que janela foi minimizada
3. Aguardar ~5s para desktop exposure
4. Validar que janela voltou a fullscreen
5. Verificar no dev-tools que não houve erro de restore

**Resultado esperado:**
- ✅ Janela minimiza e restaura fullscreen corretamente
- ✅ Media continua tocando após restore
- ✅ Nenhum erro no console

### Cenário B: User sai de fullscreen durante desktop exposure

**Preparação:**
Mesma do cenário A, mas com duração de 10s.

**Passos:**
1. Aguardar `show_desktop`
2. Validar que janela minimizou
3. **Enquanto janela está minimizada (primeiros 3s):** pressionar `F11` ou clique no botão de fullscreen do SO para sair de fullscreen
4. Aguardar até completar os 10s
5. Validar que janela restaura

**Resultado esperado:**
- ✅ Janela restaura (sai da minimize)
- ✅ Estado de fullscreen é restaurado (volta a fullscreen)
- ✅ Media continua tocando

**Observações:**
- Se não conseguir sair de fullscreen manualmente (bloqueado por kiosk), ignorar este cenário
- O código usa `lastWindowState` snapshot - validar que esse snapshot foi capturado corretamente

---

## Bug 2: Testar player sem campanha

### Descrição
Verificar que o scheduler não executa quando player não tem campanha (phase === "loading"), e que player continua funcional.

### Cenário A: Player aguardando campanha

**Preparação:**
1. Iniciar app Electron
2. Conectar device e deixar sem campanha ativa
3. Abrir dev-tools (`F12`)
4. Ativar localStorage debug: `localStorage.setItem('pw_player_debug', 'true')`

**Passos:**
1. Verificar que player está em `phase: "loading"` na tela
2. Verificar console que mostra: `[player] phase: loading`
3. Habilitar config desktop exposure no admin
4. **Não enviar show_desktop manualmente**
5. Aguardar 10s
6. Validar que scheduler NÃO executou (não há minimize)

**Resultado esperado:**
- ✅ Player fica em loading sem campanha
- ✅ Scheduler detecta `phase === "loading"` e não agenda
- ✅ Nenhum comando automático de show_desktop é enviado
- ✅ Console mostra: `[windowExposureScheduler] scheduling... → return (blocked by phase)`

**Prova no código:**
- `windowExposureScheduler.js` linha 24-33: checks `phase === "loading"` e retorna
- `Player.jsx` linha 678-692: scheduler recebe phase como dependência

### Cenário B: Começar campanha + scheduler funciona

**Preparação:**
Mesmo setup anterior.

**Passos:**
1. Com desktop exposure ativo, criar/iniciar uma campanha
2. Aguardar que player mude para `phase: "playing"`
3. Aguardar intervalo configurado (ex: 30s)
4. Validar que `show_desktop` foi executado

**Resultado esperado:**
- ✅ Quando campanha começa, scheduler ativa normalmente
- ✅ Desktop exposure ocorre no intervalo esperado
- ✅ Nenhuma execução durante loading, só durante playing

---

## Resultados dos Testes Unitários

Arquivo: `src/__tests__/restore_fullscreen.test.js`
- [x] `should snapshot fullscreen state before desktop exposure` - PASS
- [x] `should restore fullscreen state after desktop exposure` - PASS
- [x] `should restore fullscreen even if user exited fullscreen during exposure` - PASS
- [x] `should not restore if restore_fullscreen=false` - PASS
- [x] `should handle multiple show_desktop calls (cancel previous restore)` - PASS

Arquivo: `src/__tests__/scheduler_no_campaign.test.js`
- [x] `should not schedule when phase is 'loading'` - PASS
- [x] `should not schedule when phase is 'waiting' (pairing)` - PASS
- [x] `should schedule when phase is 'playing'` - PASS
- [x] `should reschedule when phase changes from loading to playing` - PASS
- [x] `should stop scheduling when phase changes back to loading` - PASS
- [x] `should not schedule if config disabled` - PASS
- [x] `should require valid intervals and durations` - PASS

**Resultado final: 102/102 testes passaram ✅**

## Conclusões

### Bug 1: Restore após fullscreen (VALIDADO - NÃO HÁ BUG)

O código em `main.js` implementa corretamente o snapshot de estado:
- Linha 316: `restoreState = snapshotWindowState()` captura estado ANTES de qualquer mudança
- Linha 333: `restoreWindowState(restoreState)` restaura a partir do snapshot capturado
- **Comportamento seguro:** Mesmo que usuário saia de fullscreen durante expose, o restore usa snapshot original

**Teste de validação:** `should restore fullscreen even if user exited fullscreen during exposure` - PASS

### Bug 2: Scheduler sem campanha (VALIDADO - NÃO HÁ BUG)

O código em `windowExposureScheduler.js` implementa corretamente a verificação:
- Linha 24-33: Checks `phase === "loading"` e retorna sem agendar
- Linha 692: Scheduler é re-chamado quando phase muda (dependency array)
- **Comportamento seguro:** Scheduler não executa quando player está em loading (sem campanha)

**Testes de validação:**
- `should not schedule when phase is 'loading'` - PASS
- `should reschedule when phase changes from loading to playing` - PASS

## Checklist de Conclusão

- [x] Testes unitários para restore fullscreen - PASS
- [x] Testes unitários para scheduler no loading - PASS
- [x] Análise de código confirmou implementações seguras
- [x] Não há bugs lógicos encontrados nos dois cenários
