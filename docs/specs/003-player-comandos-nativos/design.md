# SPEC 003 — Design Tecnico

## Resumo

A implementacao toca em tres camadas:

1. **Player Electron** — `preload.js` reescrito para expor API via `contextBridge`; `main.js` ganha IPC handlers reais que chamam `child_process` para reboot/shutdown.
2. **Player Capacitor (Android)** — novo plugin Java `PlayWaveNativePlugin` registrado em `MainActivity.java`, com hooks para `recreate()`, `PowerManager.reboot()` e shutdown via Device Owner. APK Android passa a exigir provisionamento como Device Owner para reboot/shutdown.
3. **Backend** — sem mudanca de modelo (lifecycle ja existe). Adiciona job Celery de expiracao automatica e padroniza payload de resultado.

O `commands.js` no JS do player praticamente nao muda — ele ja chama `window.PlayWaveNative` ou `window.__ELECTRON__?.player`. Apenas o `__ELECTRON__` passa a ser objeto em vez de boolean.

## Arquitetura atual relacionada

### Backend

- `backend/api/v1/devices.py`: criar comando, listar pendentes, ACK lifecycle.
- `backend/core/models.py`: model `DeviceCommand` com lifecycle completo.
- `backend/crud/entidades/crud_device_command.py`: queries e transicoes de estado.
- `backend/tasks/`: tasks Celery existentes.
- `backend/core/celery.py`: configuracao do beat scheduler.

### Frontend (gerenciador)

- `frontend/src/pages/DispositivoDetalhe.jsx`: botoes de comando e historico.
- `frontend/src/api/dispositivos.js`: cliente HTTP de comandos.

### Player

- `frontend/src/pages/Player.jsx`: poll de comandos a cada 10s, ACK em sequencia.
- `frontend/src/player-core/commands.js`: handlers locais por comando.
- `frontend/src/player-core/platform.js`: deteccao de plataforma.

### Electron

- `frontend/electron/main.js`: processo principal, IPC, kiosk, watchdog.
- `frontend/electron/preload.js`: bridge entre renderer e main (precisa ser inspecionado/reescrito).

### Android

- `frontend/android/app/src/main/java/com/playwave/player/MainActivity.java`: Activity Capacitor.
- `frontend/android/app/src/main/AndroidManifest.xml`: permissoes.

## Fluxo: comando de shutdown end-to-end

1. Operador clica "Desligar Dispositivo" em `DispositivoDetalhe.jsx`.
2. Frontend chama `POST /devices/{id}/command` com `{ command_type: "shutdown_device" }`.
3. Backend cria `DeviceCommand(status=PENDING, expires_at=now+10min)`.
4. Backend publica evento SSE `command:new` no canal `pw:device:{device_id}:events`.
5. Player recebe SSE (ou polling a cada 10s).
6. Player chama `GET /devices/{id}/commands/pending`. Backend marca como `SENT`.
7. Player itera comandos:
   - chama `POST /commands/{id}/received` → `RECEIVED`.
   - chama `POST /commands/{id}/started` → `EXECUTING`.
   - chama `executeCommand("shutdown_device", ctx)`.
   - handler local chama `window.__ELECTRON__.player.shutdownDevice()`.
   - **antes do shutdown real acontecer**, faz `POST /commands/{id}/ack` com `success=true`, plataforma e timestamp.
   - main.js executa `exec("shutdown -h now")`, processo morre.
8. Backend marca como `COMPLETED` e arquiva.

## Fluxo: comando expirado

1. Comando criado com `expires_at = now + 10min`.
2. Player offline / cai antes de consumir.
3. Job Celery `expire_stale_commands` roda a cada 60s.
4. Atualiza em batch `UPDATE device_commands SET status='expired' WHERE status IN ('pending','sent','received') AND expires_at < now()`.
5. Endpoint `/commands/pending` filtra `expires_at > now()` para evitar entregar comando ja expirado.
6. Gerenciador mostra "Expirou" com timestamp.

## Fluxo: comando nao suportado

1. Operador envia `shutdown_device` para device cujo player roda em web puro.
2. Lifecycle normal ate `started`.
3. Handler em `commands.js` chama `callNativePowerCommand("shutdownDevice")`.
4. Nenhum bridge nativo presente — lanca `Error("shutdown_device nao suportado na plataforma web")`.
5. `executeCommand` captura erro e retorna `{ success: false, errorMessage: "...", result: { platform: "web", command: "shutdown_device", failed_at: "..." } }`.
6. Player faz ACK com payload padronizado.
7. Backend marca `FAILED` com `error_message` e `result.platform_unsupported = true`.
8. Gerenciador mostra "Nao suportado em web" com badge cinza.

## Design do `preload.js` (Electron)

Substituir injecao de boolean por API estruturada via `contextBridge`.

Pseudocodigo:

```
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("__ELECTRON__", {
  platform: process.platform,
  player: {
    restartApp:     () => ipcRenderer.invoke("player:restart_app"),
    restartDevice:  () => ipcRenderer.invoke("player:restart_device"),
    shutdownDevice: () => ipcRenderer.invoke("player:shutdown_device"),
    takeScreenshot: () => ipcRenderer.invoke("player:take_screenshot"),
    fullscreenToggle: () => ipcRenderer.send("player:fullscreen-toggle"),
  },
});
```

Importante:

- `ipcRenderer.invoke` (com `Promise`) em vez de `ipcRenderer.send` para comandos com retorno/erro.
- `process.platform` exposto para o JS escolher mensagem amigavel.
- Manter `nodeIntegration: false` e `contextIsolation: true`.

## Design do `main.js` (Electron)

Adicionar handlers:

```
const { ipcMain, app, BrowserWindow } = require("electron");
const { exec } = require("child_process");

function runShell(cmd) {
  return new Promise((resolve, reject) => {
    exec(cmd, (err, stdout, stderr) => {
      if (err) reject(new Error(`${cmd} failed: ${stderr || err.message}`));
      else resolve(stdout);
    });
  });
}

ipcMain.handle("player:restart_app", async () => {
  app.relaunch();
  app.quit();
});

ipcMain.handle("player:restart_device", async () => {
  const cmd = process.platform === "win32" ? "shutdown /r /t 0" : "shutdown -r now";
  await runShell(cmd);
});

ipcMain.handle("player:shutdown_device", async () => {
  const cmd = process.platform === "win32" ? "shutdown /s /t 0" : "shutdown -h now";
  await runShell(cmd);
});

ipcMain.handle("player:take_screenshot", async () => {
  const image = await mainWindow.webContents.capturePage();
  return image.toPNG().toString("base64");
});
```

Manter `ipcMain.on("player:restart", ...)` legado funcionando como sinonimo de `player:restart_app`.

## Design do plugin Capacitor (Android)

Novo arquivo `frontend/android/app/src/main/java/com/playwave/player/PlayWaveNativePlugin.java`:

```
@CapacitorPlugin(name = "PlayWaveNative")
public class PlayWaveNativePlugin extends Plugin {
    @PluginMethod
    public void restartApp(PluginCall call) {
        getActivity().recreate();
        call.resolve();
    }

    @PluginMethod
    public void restartDevice(PluginCall call) {
        try {
            PowerManager pm = (PowerManager) getContext().getSystemService(Context.POWER_SERVICE);
            pm.reboot(null);
            call.resolve();
        } catch (SecurityException e) {
            call.reject("DEVICE_OWNER_REQUIRED", e);
        }
    }

    @PluginMethod
    public void shutdownDevice(PluginCall call) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) getContext().getSystemService(Context.DEVICE_POLICY_SERVICE);
            ComponentName admin = new ComponentName(getContext(), PlayWaveDeviceAdminReceiver.class);
            if (!dpm.isDeviceOwnerApp(getContext().getPackageName())) {
                call.reject("DEVICE_OWNER_REQUIRED", "App nao provisionado como Device Owner");
                return;
            }
            // Implementacao real depende de SDK e fabricante.
            // Sem API oficial publica para shutdown completo em Android stock.
            // Alternativa: dpm.lockNow() + scheduling de shutdown via Tasker/MDM externo.
            dpm.lockNow();
            call.resolve();
        } catch (Exception e) {
            call.reject("SHUTDOWN_FAILED", e);
        }
    }

    @PluginMethod
    public void takeScreenshot(PluginCall call) {
        // Captura via View.draw(Canvas) ou MediaProjection.
        // ...
        JSObject ret = new JSObject();
        ret.put("base64", base64png);
        call.resolve(ret);
    }
}
```

Notas:

- `shutdownDevice` real em Android stock sem MDM eh limitado — `lockNow()` desliga a tela mas nao o dispositivo. Documentar essa limitacao no requisito.
- Em TV Boxes com firmware customizado, pode haver intent `android.intent.action.ACTION_REQUEST_SHUTDOWN` (oculto). Documentar fallback.

Adicionar em `MainActivity.java`:

```
public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(PlayWaveNativePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
```

Adicionar em `AndroidManifest.xml`:

```
<uses-permission android:name="android.permission.REBOOT"
    tools:ignore="ProtectedPermissions" />
<uses-permission android:name="android.permission.SHUTDOWN"
    tools:ignore="ProtectedPermissions" />
```

E o `receiver` do Device Admin:

```
<receiver
    android:name=".PlayWaveDeviceAdminReceiver"
    android:permission="android.permission.BIND_DEVICE_ADMIN"
    android:exported="true">
    <meta-data
        android:name="android.app.device_admin"
        android:resource="@xml/device_admin_policies" />
    <intent-filter>
        <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
    </intent-filter>
</receiver>
```

## Design do bridge JS (`commands.js`)

`commands.js` ja procura `window.PlayWaveNative || window.AndroidPlayer || window.__ELECTRON__?.player`. Manter exatamente assim. A unica adaptacao eh garantir que o nome do metodo seja consistente entre as tres camadas — `restartApp`, `restartDevice`, `shutdownDevice`, `takeScreenshot` (camelCase). Atualizar o handler do plugin Capacitor para tambem expor o objeto em `window.PlayWaveNative` (Capacitor expoe via `Capacitor.Plugins.PlayWaveNative` — criar wrapper em `platform.js`).

Adicionar em `platform.js`:

```
import { Capacitor } from "@capacitor/core";

if (Capacitor.isPluginAvailable("PlayWaveNative")) {
  const native = Capacitor.Plugins.PlayWaveNative;
  window.PlayWaveNative = {
    restartApp:     () => native.restartApp(),
    restartDevice:  () => native.restartDevice(),
    shutdownDevice: () => native.shutdownDevice(),
    takeScreenshot: () => native.takeScreenshot(),
  };
}
```

## Design do ACK antes de morrer

Para nao perder o trace, o handler em `commands.js` precisa registrar o ACK ANTES de invocar shutdown/restart, porque o processo do player morre durante a operacao.

Alteracao em `Player.jsx`:

```
async function executarComando(cmd) {
  await marcarComandoIniciado(deviceId, cmd.id, token);

  // Pre-ACK otimista para comandos destrutivos que matam o processo.
  const DESTRUTIVO = ["restart_app", "restart_device", "shutdown_device"];
  if (DESTRUTIVO.includes(cmd.command_type)) {
    await ackComando(deviceId, cmd.id, token, true, null, {
      platform: Platform.name,
      command_type: cmd.command_type,
      ack_phase: "pre_execution",
      acked_at: new Date().toISOString(),
    });
  }

  const result = await executeCommand(cmd, ctx);

  // Para comandos nao destrutivos, ACK pos-execucao normal.
  if (!DESTRUTIVO.includes(cmd.command_type)) {
    await ackComando(deviceId, cmd.id, token, result.success, result.errorMessage, result.result);
  }
}
```

Trade-off: comando destrutivo aparece como `success` ate o player voltar e dizer o contrario. Aceitavel porque heartbeat pos-reboot confirma. Se reboot falhar, comando seguinte (`heartbeat` ausente por X minutos) sinaliza problema separadamente.

## Design da expiracao de comandos

Criar task Celery:

```
@celery_app.task
def expire_stale_commands():
    now = datetime.utcnow()
    db.execute(
        update(DeviceCommand)
        .where(
            DeviceCommand.status.in_([
                DeviceCommandStatus.PENDING,
                DeviceCommandStatus.SENT,
                DeviceCommandStatus.RECEIVED,
                DeviceCommandStatus.EXECUTING,
            ]),
            DeviceCommand.expires_at < now,
        )
        .values(status=DeviceCommandStatus.EXPIRED, error_message="Comando expirou sem ACK do player")
    )
    db.commit()
```

Adicionar em `celery.py` beat schedule:

```
"expire-stale-commands": {
    "task": "tasks.commands.expire_stale_commands",
    "schedule": 60.0,
},
```

E ajustar endpoint `/commands/pending` para excluir `expires_at < now`:

```
def get_pending_commands(self, db, device_id, limit=20):
    return db.query(DeviceCommand).filter(
        DeviceCommand.device_id == device_id,
        DeviceCommand.status == DeviceCommandStatus.PENDING,
        or_(DeviceCommand.expires_at.is_(None), DeviceCommand.expires_at > datetime.utcnow()),
    ).order_by(DeviceCommand.requested_at).limit(limit).all()
```

## Status calculado vs persistido

Persistidos sao os 8 estados do enum. UI mostra:

| Estado banco | Label UI | Cor |
|---|---|---|
| PENDING | Aguardando envio | cinza |
| SENT | Enviado | azul claro |
| RECEIVED | Recebido pelo player | azul |
| EXECUTING | Executando | amarelo |
| COMPLETED / EXECUTED | Concluido | verde |
| FAILED | Falhou | vermelho |
| EXPIRED | Expirou | cinza escuro |
| CANCELLED | Cancelado | roxo |

`FAILED` com `result.platform_unsupported = true` mostra label especial "Nao suportado".

## Decisoes tecnicas

- Usar `ipcRenderer.invoke` (Promise) em vez de `ipcRenderer.send` (fire-and-forget).
- Manter alias `player:restart` por compatibilidade com versoes antigas do bundle.
- ACK pre-execucao para comandos destrutivos (restart/shutdown).
- Default `expires_at = now + 10 minutos`.
- Job de expiracao Celery roda a cada 60 segundos.
- Plugin Capacitor exige `@capacitor/core` >= 5.x.
- Provisionamento Device Owner via ADB (documentar fluxo, nao automatizar).
- Logs do Electron em `app.getPath("userData") + "/logs/main.log"`.

## Pontos parcialmente existentes

- `device_commands` lifecycle ja esta migrado (migration `20260521_0915`).
- Endpoints `/received`, `/started`, `/ack` ja implementados.
- `commands.js` ja faz polling e ACK.
- `main.js` ja tem skeleton de IPC (apenas `player:restart` e `fullscreen-toggle`).
- `preload.js` referenciado mas precisa inspecao para confirmar se ja existe ou nao (provavelmente arquivo vazio ou minimal).
- `expires_at` ja existe no model, mas nenhum lugar seta default ou expira automaticamente.

## Lacunas de design

- Smart TVs (Tizen/webOS) nao tem caminho nativo nesta SPEC — caem em `command_not_implemented`.
- Comando `take_screenshot` no Android requer permissao `MediaProjection` que abre dialog para o usuario, o que quebra modo kiosk silencioso. Implementacao adiada para SPEC futura.
- Auditoria avancada de quem disparou comando sensivel fica para SPEC de auditoria.
- Comando em lote (todos os players de uma campanha) fica para Central de Comandos.

## Riscos e mitigacoes

### Risco: shutdown -h em Linux exige privilegio

Mitigacao:

- Documentar `sudoers` minimo necessario: `playwave ALL=NOPASSWD: /sbin/shutdown`.
- Detectar falha de permissao no `runShell` e retornar `error_code = "PERMISSION_DENIED"`.

### Risco: Android sem API publica de shutdown

Mitigacao:

- Implementar `lockNow()` como fallback (apaga a tela, dispositivo continua ligado).
- Documentar que reboot funciona em maioria dos casos com Device Owner, shutdown depende do fabricante.
- Aceitar que em TV Boxes Android sem ROM custom, "shutdown" eh equivalente a "blank screen".

### Risco: ACK pre-execucao mente sobre sucesso

Mitigacao:

- Heartbeat seguinte confirma indiretamente: se player nao volta apos restart_device, gerar alerta separado.
- Marcar comandos destrutivos com flag `is_destructive` no model para que UI mostre estado especial.

### Risco: comando expira durante execucao longa

Mitigacao:

- `expires_at` aplica-se apenas aos estados `pending/sent/received`. Comando em `executing` nao expira.
- Para comandos potencialmente longos (download, screenshot), aumentar `expires_at` no momento de criar.

### Risco: provisionamento Device Owner exige reset de fabrica

Mitigacao:

- Documentar que provisionamento via ADB so funciona em dispositivo sem conta Google configurada.
- Procedimento operacional: factory reset + ADB setup antes de entregar TV pro cliente.
- Alternativa: provisionamento via QR code (Android 7+), documentar.

## Criterio de pronto tecnico

- `preload.js` expoe `window.__ELECTRON__.player.*` via `contextBridge`.
- `main.js` responde aos 4 canais IPC novos.
- Plugin Capacitor compila e registra em MainActivity.
- APK provisionado como Device Owner executa reboot real (validado em ao menos 1 TV Box).
- Comando shutdown em Windows desliga a maquina.
- Comando shutdown em Linux desliga a maquina (com `sudoers` configurado).
- Comando em web puro retorna `failed` com `platform_unsupported: true`.
- Job Celery `expire_stale_commands` rodando e marcando expired.
- Gerenciador mostra status colorido por estado, com timestamps de cada transicao.
- ACK pre-execucao registrado para comandos destrutivos.
- Documentacao de provisionamento Device Owner em `docs/PROVISIONAMENTO_ANDROID.md` (criar como parte da spec).
