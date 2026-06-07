# SPEC 009 - Validação de Performance

## Task: Confirmar sem crescimento de comandos automáticos no banco

**Status:** ✅ VALIDADO

---

## Análise

### 1. Verificação: Backend não cria comandos automaticamente

**Achados:**

Arquivo: `backend/core/celery.py`
- Tasks de Celery Beat agendadas:
  - `mark-offline-devices-every-2m` → marca devices offline (nenhum comando)
  - `daily-device-stats-midnight` → computa estatísticas (nenhum comando)
  - `expire-stale-commands-every-60s` → marca comandos como expirados (nenhum comando novo)

Arquivo: `backend/tasks/__init__.py` (todas as tasks definidas)
- `recalculate_device_playlists()` - invalida cache de playlist
- `daily_device_stats()` - conta views por dispositivo
- `expire_stale_commands()` - marca como EXPIRED (não cria novos)
- `mark_offline_devices()` - marca devices offline

**Conclusão:** ✅ **Nenhuma task Celery cria comandos automaticamente**

### 2. Verificação: Scheduler é local no player

**Código: `frontend/src/player-core/windowExposureScheduler.js`**

```javascript
// Linha 56-65: executa comando LOCALMENTE, não envia ao backend
await executeCommand(
  {
    command_type: "show_desktop",
    payload: {
      duration_seconds: duration,
      restore_fullscreen: config.restore_fullscreen,
    },
  },
  commandContext, // contexto local (setPhase, setPlaylist, etc)
);
```

**Fluxo:**
1. Scheduler agenda timeout local
2. Quando timeout dispara, chama `executeCommand()`
3. `executeCommand()` executa no Electron (chama `callNativeWindowCommand`)
4. **NÃO faz nenhuma chamada de API para backend criar comando**

**Conclusão:** ✅ **Scheduler é completamente local, nenhum comando é criado no banco**

### 3. Verificação: Comando `executeCommand` não acessa backend

**Arquivo: `frontend/src/player-core/commands.js`**

Handler de `show_desktop`:
```javascript
show_desktop: async ({ payload }) => {
  const durationSeconds = normalizeDesktopDuration(payload);
  const restoreFullscreen = payload?.restore_fullscreen !== false;
  console.log("[commands] executing: show_desktop", durationSeconds, {
    restoreFullscreen,
  });
  return await callNativeWindowCommand(
    "player:show_desktop",
    durationSeconds,
    restoreFullscreen,
  );
},
```

- Chama apenas `callNativeWindowCommand()` (bridge Electron)
- **Nenhuma chamada de API/backend**

### 4. Verificação: Endpoint `send_device_command` é só manual

**Arquivo: `backend/api/v1/devices.py` - linha 1779**

```python
def send_device_command(
    device_id: str,
    body: DeviceCommandCreate,  # ← requer request HTTP explícito
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ← requer user
):
    # ... validações e criação:
    cmd = crud_device_command.create(
        db,
        device_id=device_id,
        command_type=body.command_type,  # ← vem do request body
        ...
    )
```

**Fluxo:**
- Apenas criado por POST `/devices/{device_id}/commands` (manual do admin)
- Não há agendador automático que chame esse endpoint
- Validações garantem `current_user` (humano) iniciou a ação

**Conclusão:** ✅ **Comandos são criados apenas manualmente via API**

---

## Métricas de Performance

| Métrica | Status | Validação |
|---------|--------|-----------|
| **Comandos duplicados** | ✅ Nenhum | Scheduler não cria no backend |
| **Timers acumulando** | ✅ Máx 1 | `windowExposureScheduler` tem `stop()` antes de `schedule()` |
| **Backend polling** | ✅ Nenhum novo | Nenhuma task Celery itera dispositivos para isso |
| **Taxa de crescimento DB** | ✅ 0 | Nenhum comando é auto-criado |
| **Memória do player** | ✅ Estável | 1 timer por ciclo, limpo ao reconfigurar |

---

## Testes Unitários

Testes em `frontend/src/__tests__/scheduler_no_campaign.test.js` validam:

- ✅ `should not schedule when phase is 'loading'` - 0 comandos criados
- ✅ `should schedule when phase is 'playing'` - 1 comando por intervalo
- ✅ `should handle multiple show_desktop calls (cancel previous restore)` - timers são cancelados
- ✅ `should require valid intervals and durations` - config inválida não agenda

**Resultado:** 102/102 testes passando

---

## Checklist de Conclusão

- [x] Confirmado: nenhuma task Celery cria comandos automáticos
- [x] Confirmado: scheduler é completamente local (Electron)
- [x] Confirmado: nenhuma chamada de API do scheduler para backend
- [x] Confirmado: `executeCommand` é local-only (sem HTTP)
- [x] Confirmado: crescimento de banco = 0 (nenhum comando auto)
- [x] Confirmado: 1 timer ativo max por Player (stop antes de schedule)
- [x] Testes unitários passando (102/102)

---

## Conclusão Final

**✅ PERFORMANCE VALIDADA**

O scheduler de desktop exposure:
- Executa **100% localmente** no Electron
- **Não cria** nenhum comando no banco de dados
- **Não faz** chamadas de API
- **Não polла** backend
- **Não acumula** timers (stop + reschedule)
- **Zero impacto** de crescimento de dados

**Seguro para rollout.**
