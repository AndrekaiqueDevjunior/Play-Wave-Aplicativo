package com.playwave.player;

import android.app.admin.DevicePolicyManager;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.Canvas;
import android.os.PowerManager;
import android.util.Base64;
import android.view.View;

import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import java.io.ByteArrayOutputStream;

/**
 * Plugin Capacitor para comandos nativos do player Android.
 *
 * SPEC 003 — corrige bug do "shutdown_device não funciona": antes não havia
 * plugin nativo, então `window.PlayWaveNative` era undefined e todo comando
 * caía em "platform_unsupported". Agora exposto via Capacitor.Plugins.
 *
 * Comandos:
 *  - restartApp()      → Activity.recreate() — soft reload (Capacitor mantém).
 *  - restartDevice()   → PowerManager.reboot() — exige REBOOT + Device Owner.
 *  - shutdownDevice()  → DPM.lockNow() — Android stock não expõe shutdown
 *                        completo sem firmware custom; fallback bloqueia tela.
 *  - takeScreenshot()  → captura View do WebView e devolve PNG base64.
 *
 * Veja docs/PROVISIONAMENTO_ANDROID.md para provisionar como Device Owner.
 */
@CapacitorPlugin(name = "PlayWaveNative")
public class PlayWaveNativePlugin extends Plugin {

    @PluginMethod
    public void restartApp(PluginCall call) {
        try {
            getActivity().runOnUiThread(() -> getActivity().recreate());
            call.resolve();
        } catch (Exception e) {
            call.reject("RESTART_APP_FAILED", e.getMessage(), e);
        }
    }

    @PluginMethod
    public void restartDevice(PluginCall call) {
        try {
            PowerManager pm = (PowerManager) getContext().getSystemService(Context.POWER_SERVICE);
            if (pm == null) {
                call.reject("POWER_MANAGER_UNAVAILABLE", "PowerManager not available");
                return;
            }
            pm.reboot(null);
            // Em geral o processo morre antes deste resolve; mantemos por simetria.
            call.resolve();
        } catch (SecurityException e) {
            call.reject(
                "DEVICE_OWNER_REQUIRED",
                "Reboot exige Device Owner ou root. Veja docs/PROVISIONAMENTO_ANDROID.md",
                e
            );
        } catch (Exception e) {
            call.reject("REBOOT_FAILED", e.getMessage(), e);
        }
    }

    @PluginMethod
    public void shutdownDevice(PluginCall call) {
        try {
            DevicePolicyManager dpm = (DevicePolicyManager) getContext()
                .getSystemService(Context.DEVICE_POLICY_SERVICE);
            String pkg = getContext().getPackageName();

            if (dpm == null) {
                call.reject("DPM_UNAVAILABLE", "DevicePolicyManager not available");
                return;
            }

            if (!dpm.isDeviceOwnerApp(pkg)) {
                call.reject(
                    "DEVICE_OWNER_REQUIRED",
                    "App não provisionado como Device Owner. Provisione via: "
                        + "adb shell dpm set-device-owner " + pkg
                        + "/.PlayWaveDeviceAdminReceiver"
                );
                return;
            }

            // Android stock não expõe API pública de shutdown completo.
            // Fallback prático: lockNow() + sinalizar limitação.
            dpm.lockNow();

            JSObject ret = new JSObject();
            ret.put("note", "screen_locked");
            ret.put(
                "limitation",
                "Shutdown completo não suportado em Android stock; tela bloqueada."
            );
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("SHUTDOWN_FAILED", e.getMessage(), e);
        }
    }

    @PluginMethod
    public void takeScreenshot(PluginCall call) {
        try {
            View view = getBridge().getWebView().getRootView();
            view.setDrawingCacheEnabled(true);
            Bitmap bitmap;
            try {
                bitmap = Bitmap.createBitmap(view.getDrawingCache());
            } finally {
                view.setDrawingCacheEnabled(false);
            }

            if (bitmap == null) {
                // Fallback usando draw().
                bitmap = Bitmap.createBitmap(
                    view.getWidth(),
                    view.getHeight(),
                    Bitmap.Config.ARGB_8888
                );
                Canvas canvas = new Canvas(bitmap);
                view.draw(canvas);
            }

            ByteArrayOutputStream stream = new ByteArrayOutputStream();
            bitmap.compress(Bitmap.CompressFormat.PNG, 90, stream);
            String base64 = Base64.encodeToString(stream.toByteArray(), Base64.NO_WRAP);

            JSObject ret = new JSObject();
            ret.put("base64", base64);
            call.resolve(ret);
        } catch (Exception e) {
            call.reject("SCREENSHOT_FAILED", e.getMessage(), e);
        }
    }
}
