# SPEC 003 — Player

## Arquivos afetados

- `frontend/electron/main.js` — adicionar IPC handlers.
- `frontend/electron/preload.js` — reescrever para expor API via contextBridge.
- `frontend/src/player-core/platform.js` — wrapper `window.PlayWaveNative` para Capacitor.
- `frontend/src/player-core/commands.js` — sem mudanca de logica, ajustar imports de `Platform.name`.
- `frontend/src/pages/Player.jsx` — adicionar pre-ACK para destrutivos + SSE handler para `command:new`.
- `frontend/android/app/src/main/java/com/playwave/player/MainActivity.java` — registrar plugin.
- `frontend/android/app/src/main/java/com/playwave/player/PlayWaveNativePlugin.java` (novo).
- `frontend/android/app/src/main/java/com/playwave/player/PlayWaveDeviceAdminReceiver.java` (novo).
- `frontend/android/app/src/main/res/xml/device_admin_policies.xml` (novo).
- `frontend/android/app/src/main/AndroidManifest.xml` — adicionar permissoes + receiver.

## Electron — `preload.js`

Substituir conteudo atual (qualquer que seja) por:

```
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("__ELECTRON__", {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    node: process.versions.node,
  },
  player: {
    restartApp:       () => ipcRenderer.invoke("player:restart_app"),
    restartDevice:    () => ipcRenderer.invoke("player:restart_device"),
    shutdownDevice:   () => ipcRenderer.invoke("player:shutdown_device"),
    takeScreenshot:   () => ipcRenderer.invoke("player:take_screenshot"),
    fullscreenToggle: () => ipcRenderer.send("player:fullscreen-toggle"),
  },
});
```

Importante:

- `contextIsolation: true` ja esta em `main.js`. Mantem.
- Antes era `window.__ELECTRON__ = true` injetado via `executeJavaScript` em `dom-ready` — REMOVER essa linha do `main.js`.

## Electron — `main.js`

### Remover

A linha em `dom-ready`:

```
mainWindow.webContents.executeJavaScript(
  "window.__ELECTRON__ = true; window.__PLATFORM__ = '" + os.platform() + "';"
).catch(() => {});
```

(Agora `__ELECTRON__` vem do `preload.js` como objeto.)

### Adicionar

Imports:

```
const { exec } = require("child_process");
```

Helper:

```
function runShell(cmd) {
  return new Promise((resolve, reject) => {
    exec(cmd, (err, stdout, stderr) => {
      if (err) {
        console.error("[electron] shell failed:", cmd, stderr);
        reject(new Error(`${cmd}: ${stderr || err.message}`));
      } else {
        resolve(stdout);
      }
    });
  });
}
```

Handlers:

```
ipcMain.handle("player:restart_app", async () => {
  console.log("[electron] IPC player:restart_app");
  setTimeout(() => { app.relaunch(); app.quit(); }, 500); // 500ms para ACK voltar pro backend
  return { ok: true };
});

ipcMain.handle("player:restart_device", async () => {
  console.log("[electron] IPC player:restart_device");
  const cmd = process.platform === "win32"
    ? "shutdown /r /t 5"
    : "shutdown -r +0";
  setTimeout(() => { runShell(cmd).catch(() => {}); }, 500);
  return { ok: true, scheduled_at: new Date().toISOString() };
});

ipcMain.handle("player:shutdown_device", async () => {
  console.log("[electron] IPC player:shutdown_device");
  const cmd = process.platform === "win32"
    ? "shutdown /s /t 5"
    : "shutdown -h +0";
  setTimeout(() => { runShell(cmd).catch(() => {}); }, 500);
  return { ok: true, scheduled_at: new Date().toISOString() };
});

ipcMain.handle("player:take_screenshot", async () => {
  if (!mainWindow) throw new Error("no_window");
  const image = await mainWindow.webContents.capturePage();
  return { base64: image.toPNG().toString("base64") };
});
```

Manter `ipcMain.on("player:restart", ...)` legado como alias de `restart_app` para nao quebrar bundles antigos.

## Capacitor — `platform.js`

Adicionar wrapper antes de exportar `Platform`:

```
import { Capacitor } from "@capacitor/core";

if (Capacitor.isPluginAvailable("PlayWaveNative")) {
  const native = Capacitor.Plugins.PlayWaveNative;
  window.PlayWaveNative = {
    restartApp:     async () => { await native.restartApp(); },
    restartDevice:  async () => { await native.restartDevice(); },
    shutdownDevice: async () => { await native.shutdownDevice(); },
    takeScreenshot: async () => {
      const r = await native.takeScreenshot();
      return r.base64;
    },
  };
}
```

## `commands.js` — pequenas mudancas

Sem mudanca de logica de execucao. O `callNativePowerCommand` ja resolve corretamente quando `window.__ELECTRON__.player.shutdownDevice` for funcao real.

Padronizar o erro retornado:

```
function platformUnsupported(command, reason = "command_not_implemented") {
  const err = new Error(`${command} nao suportado na plataforma ${Platform.name}`);
  err.code = reason === "browser_environment" ? "BROWSER_ENVIRONMENT" : "COMMAND_NOT_IMPLEMENTED";
  err.platform_unsupported = true;
  throw err;
}
```

Ajustar `executeCommand` para capturar `err.code`:

```
catch (err) {
  return {
    success: false,
    errorMessage: err?.message || String(err),
    result: {
      platform: Platform.name,
      command_type: cmd.command_type,
      platform_unsupported: err?.platform_unsupported === true,
      error_code: err?.code || null,
      failed_at: new Date().toISOString(),
    },
  };
}
```

## `Player.jsx` — pre-ACK para destrutivos

No loop de execucao de comandos pendentes (`buscarComandosPendentes` em volta da linha 476-516):

```
const DESTRUTIVOS = new Set(["restart_app", "restart_device", "shutdown_device"]);

for (const cmd of pendentes) {
  await marcarComandoRecebido(deviceId, cmd.id, token);
  await marcarComandoIniciado(deviceId, cmd.id, token);

  if (DESTRUTIVOS.has(cmd.command_type)) {
    // Pre-ACK otimista — processo morre durante a operacao.
    await ackComando(deviceId, cmd.id, token, true, null, {
      platform: Platform.name,
      command_type: cmd.command_type,
      ack_phase: "pre_execution",
      completed_at: new Date().toISOString(),
    });
  }

  const result = await executeCommand(cmd, ctx);

  if (!DESTRUTIVOS.has(cmd.command_type)) {
    await ackComando(deviceId, cmd.id, token, result.success, result.errorMessage, {
      ...result.result,
      ack_phase: "post_execution",
    });
  }

  // Se foi destrutivo mas executeCommand falhou (ex: web puro), ACK com failure sobrescreve.
  if (DESTRUTIVOS.has(cmd.command_type) && !result.success) {
    await ackComando(deviceId, cmd.id, token, false, result.errorMessage, {
      ...result.result,
      ack_phase: "post_execution_override",
    });
  }
}
```

## `Player.jsx` — escutar SSE `command:new`

No handler de eventos SSE (`abrirStreamPlaylistUpdates` em volta da linha 518-561), adicionar branch para `command:new`:

```
es.addEventListener("command:new", () => {
  console.log("[player] SSE command:new — buscando pendentes");
  buscarComandosPendentes();
});
```

Reduz latencia de 10s (polling) para tempo real quando SSE estiver ativo. Polling continua como fallback.

## Android — `PlayWaveDeviceAdminReceiver.java` (novo)

`frontend/android/app/src/main/java/com/playwave/player/PlayWaveDeviceAdminReceiver.java`:

```
package com.playwave.player;

import android.app.admin.DeviceAdminReceiver;

public class PlayWaveDeviceAdminReceiver extends DeviceAdminReceiver {
    // Receiver vazio — basta existir para o sistema reconhecer.
}
```

## Android — `device_admin_policies.xml` (novo)

`frontend/android/app/src/main/res/xml/device_admin_policies.xml`:

```
<?xml version="1.0" encoding="utf-8"?>
<device-admin xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-policies>
        <reset-password />
        <force-lock />
        <wipe-data />
    </uses-policies>
</device-admin>
```

## Android — `AndroidManifest.xml`

Adicionar dentro de `<manifest>`:

```
<uses-permission android:name="android.permission.REBOOT"
    tools:ignore="ProtectedPermissions" />
```

Adicionar dentro de `<application>`:

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

## Android — `PlayWaveNativePlugin.java` (novo)

`frontend/android/app/src/main/java/com/playwave/player/PlayWaveNativePlugin.java`:

```
package com.playwave.player;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.os.PowerManager;
import android.util.Base64;
import android.view.View;
import android.graphics.Bitmap;
import android.graphics.Canvas;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.ByteArrayOutputStream;

@CapacitorPlugin(name = "PlayWaveNative")
public class PlayWaveNativePlugin extends Plugin {

    @PluginMethod
    public void restartApp(PluginCall call) {
        try {
            getActivity().runOnUiThread(() -> getActivity().recreate());
            call.resolve();
        } catch (Exception e) {
            call.reject("RESTART_APP_FAILED", e);
        }
    }

    @PluginMethod
    public void restartDevice(PluginCall call) {
        try {
            PowerManager pm = (PowerManager) getContext().getSystemService(Context.POWER_SERVICE);
            pm.reboot(null);
            call.resolve();
        } catch (SecurityException e) {
            call.reject("DEVICE_OWNER_REQUIRED", "Reboot exige Device Owner ou root", e);
        } catch (Exception e) {
            call.reject("REBOOT_FAILED", e);
        }
    }

    @PluginMethod
    public void shutdownDevice(PluginCall call) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) getContext()
                .getSystemService(Context.DEVICE_POLICY_SERVICE);
            String pkg = getContext().getPackageName();
            if (!dpm.isDeviceOwnerApp(pkg)) {
                call.reject("DEVICE_OWNER_REQUIRED",
                    "App nao provisionado como Device Owner. Use: adb shell dpm set-device-owner "
                    + pkg + "/.PlayWaveDeviceAdminReceiver");
                return;
            }
            // Android stock nao expoe API publica de shutdown completo.
            // Fallback: bloquear tela (equivalente operacional para muitos casos).
            dpm.lockNow();
            JSObject ret = new JSObject();
            ret.put("note", "screen_locked (shutdown completo requer firmware customizado)");
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("SHUTDOWN_FAILED", e);
        }
    }

    @PluginMethod
    public void takeScreenshot(PluginCall call) {
        try {
            View view = getBridge().getWebView().getRootView();
            view.setDrawingCacheEnabled(true);
            Bitmap bitmap = Bitmap.createBitmap(view.getDrawingCache());
            view.setDrawingCacheEnabled(false);

            ByteArrayOutputStream stream = new ByteArrayOutputStream();
            bitmap.compress(Bitmap.CompressFormat.PNG, 100, stream);
            String base64 = Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP);

            JSObject ret = new JSObject();
            ret.put("base64", base64);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("SCREENSHOT_FAILED", e);
        }
    }
}
```

## Android — `MainActivity.java`

Atualizar para registrar o plugin:

```
package com.playwave.player;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(PlayWaveNativePlugin.class);
        super.onCreate(savedInstanceState);
    }
}
```

(Manter as customizacoes ja existentes de `setMediaPlaybackRequiresUserGesture` e `MIXED_CONTENT_COMPATIBILITY_MODE`.)

## Verificacoes pre-deploy

- Em Electron: `npm run electron:dev` e rodar comando shutdown via gerenciador. Confirmar `exec("shutdown -h ...")` foi chamado (mockar `exec` em dev se necessario).
- Em APK: `adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver` antes de testar reboot.
- Em web: confirmar que ACK volta com `platform_unsupported: true` e gerenciador mostra label "Nao suportado".
- Confirmar SSE `command:new` reduz latencia de execucao para < 2s.
