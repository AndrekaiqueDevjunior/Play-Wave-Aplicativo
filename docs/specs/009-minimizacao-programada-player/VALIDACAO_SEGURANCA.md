# SPEC 009 - Validação de Segurança

## Task 1: Confirmar sem shell para window-control

**Status:** ✅ VALIDADO

---

## Análise: Window-Control Commands (SPEC 009)

### Comandos de Window-Control

**Três comandos adicionados em SPEC 009:**
1. `minimize_player` → `player:minimize_window`
2. `restore_player` → `player:restore_window`  
3. `show_desktop` → `player:show_desktop`

### Verificação de Segurança

Arquivo: `frontend/electron/main.js`

#### Comando 1: minimize_window (linha 281)

```javascript
ipcMain.handle("player:minimize_window", async () => {
  if (!mainWindow) throw new Error("no_window");
  console.log("[electron] IPC player:minimize_window");
  prepareWindowForDesktopExposure();
  mainWindow.minimize();  // ← API Electron nativa
  return { ok: true, ... };
});
```

**Segurança:** ✅ 
- Usa apenas `mainWindow.minimize()` (API Electron)
- Nenhuma chamada shell
- Nenhum input de usuário manipulado

#### Comando 2: restore_window (linha 293)

```javascript
ipcMain.handle("player:restore_window", async () => {
  if (!mainWindow) throw new Error("no_window");
  console.log("[electron] IPC player:restore_window");
  if (desktopExposureRestoreTimer) {
    clearTimeout(desktopExposureRestoreTimer);
    desktopExposureRestoreTimer = null;
  }
  restoreWindowState();  // ← operações Electron nativas
  return { ok: true, ... };
});
```

**Segurança:** ✅
- Usa apenas operações Electron (`mainWindow.restore()`, `mainWindow.show()`)
- Nenhuma chamada shell
- Nenhum input manipulado

#### Comando 3: show_desktop (linha 309)

```javascript
ipcMain.handle(
  "player:show_desktop",
  async (_, durationSeconds = 10, restoreFullscreen = true) => {
    if (!mainWindow) throw new Error("no_window");
    
    // Validação e sanitização de input
    const duration = Math.max(
      1,
      Math.min(300, Math.round(Number(durationSeconds) || 10))
    );  // ← clamp entre 1-300 segundos
    
    const restoreState = snapshotWindowState();
    
    // Operações Electron nativas apenas
    prepareWindowForDesktopExposure();  // setKiosk(false), setFullScreen(false)
    mainWindow.minimize();              // ← API Electron nativa
    
    if (restoreFullscreen) {
      desktopExposureRestoreTimer = setTimeout(() => {
        restoreWindowState(restoreState);  // ← APIs Electron nativas
      }, duration * 1000);
    }
    
    return { ok: true, ... };
  }
);
```

**Segurança:** ✅✅✅
- **Input validado:** `durationSeconds` clampado entre 1-300
- **Nenhuma shell:** apenas operações Electron
- **Sem injeção:** input numérico transformado em integer puro
- **Timer seguro:** `setTimeout()` com número puro, não string

---

## Análise Comparativa: Comandos Destrutivos (para contexto)

Arquivo: `frontend/electron/main.js`

#### Comando: restart_device (linha 366)

```javascript
ipcMain.handle("player:restart_device", async () => {
  const cmd = process.platform === "win32" 
    ? "shutdown /r /t 5"  // ← string literal, não input
    : "shutdown -r +1";   // ← string literal, não input
  setTimeout(() => {
    runShell(cmd).catch(() => {});  // ← usa shell, MAS comando é hardcoded
  }, 500);
  return { ok: true, ... };
});
```

**Segurança de restart_device:** ✅
- Shell é necessário para chamar `shutdown` do OS
- **Criticamente:** comando é **string literal hardcoded**
- **Nenhum input de usuário** no comando
- Parâmetro (`/r`, `-r`) é fixo, não vem de API

#### Comando: shutdown_device (linha 381)

```javascript
ipcMain.handle("player:shutdown_device", async () => {
  const cmd = process.platform === "win32"
    ? "shutdown /s /t 5"   // ← string literal
    : "shutdown -h +1";    // ← string literal
  setTimeout(() => {
    runShell(cmd).catch(() => {});  // ← usa shell, MAS comando é hardcoded
  }, 500);
  return { ok: true, ... };
});
```

**Segurança de shutdown_device:** ✅
- Shell necessário para chamar `shutdown` do OS
- **Comando é string literal hardcoded**
- Nenhum input de usuário

---

## Matriz de Segurança - Window Control vs Destructive

| Comando | Usa Shell? | Input do Usuário? | Segurança |
|---------|-----------|------------------|-----------|
| **minimize_window** | ❌ Não | ❌ Não | ✅✅✅ API nativa |
| **restore_window** | ❌ Não | ❌ Não | ✅✅✅ API nativa |
| **show_desktop** | ❌ Não | ✅ Sim (duration) | ✅✅ Input clamped/validado |
| restart_device | ✅ Sim | ❌ Não | ✅ Cmd hardcoded |
| shutdown_device | ✅ Sim | ❌ Não | ✅ Cmd hardcoded |

---

## Validação de Input: show_desktop

**Payload esperado:**
```json
{
  "duration_seconds": 5,
  "restore_fullscreen": true
}
```

**Processamento (linha 312-315):**
```javascript
const duration = Math.max(
  1,
  Math.min(300, Math.round(Number(durationSeconds) || 10))
);
```

**Ataques testados:**
- ❌ `"duration_seconds": -100` → clampado para 1
- ❌ `"duration_seconds": 999999` → clampado para 300
- ❌ `"duration_seconds": "'; DROP TABLE--"` → `Number()` retorna NaN → fallback 10
- ❌ `"duration_seconds": null` → `Number(null)` = 0 → fallback 10
- ❌ `"duration_seconds": {}` → `Number({})` = NaN → fallback 10

**Conclusão:** ✅ Input é à prova de injection

---

## Checklist de Segurança - Window Control

- [x] minimize_window usa apenas API Electron (sem shell)
- [x] restore_window usa apenas API Electron (sem shell)
- [x] show_desktop usa apenas API Electron (sem shell)
- [x] show_desktop não tem string interpolation
- [x] show_desktop input (duration) é clamped 1-300
- [x] Nenhum comando aceita input externo para shell
- [x] Comandos destrutivos (restart/shutdown) usam string literals
- [x] Nenhum eval, function constructor, ou dynamic code
- [x] Context isolation ativado no Electron (`contextIsolation: true`)
- [x] Preload bridge expõe apenas funções seguras

---

## Conclusão Final

**✅ SEGURANÇA VALIDADA: Window-Control**

Os três comandos de window-control (minimize, restore, show_desktop):
- ✅ Usam **100% APIs Electron nativas** (sem shell)
- ✅ Não aceitam comandos string de usuário
- ✅ Input numérico é validado/clamped
- ✅ Sem injection de comando possível
- ✅ Sem injeção de código possível

**Seguro para rollout.**

---

## Próximas Tarefas de Segurança

- [ ] Confirmar permissões admin/tenant no endpoint
- [ ] Confirmar payload sanitizado (backend API)
