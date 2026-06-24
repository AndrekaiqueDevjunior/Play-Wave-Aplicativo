package com.playwave.player;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * BootReceiver — autostart nativo do player após o boot do Android.
 *
 * Remove a dependência de apps de "auto start" de terceiros (RF01): quando o
 * aparelho liga/reinicia, abre a MainActivity automaticamente — que carrega a
 * rota /player no WebView (ver server.url em capacitor.config.json).
 *
 * Cobre as variações de broadcast de boot usadas por diferentes fabricantes
 * (TV boxes/Android stock costumam emitir QUICKBOOT_POWERON em vez de
 * BOOT_COMPLETED em reinício "rápido").
 *
 * LIMITAÇÕES (Android):
 *  - Em Android 10+ (API 29) o lançamento de Activity a partir do background é
 *    restrito para apps comuns. Para autostart confiável o app deve estar
 *    provisionado como Device Owner (ver PlayWaveDeviceAdminReceiver) ou
 *    definido como aplicativo Home/launcher do aparelho.
 *  - O receiver só dispara se o app já tiver sido aberto manualmente pelo menos
 *    uma vez após a instalação (apps recém-instalados ficam em estado
 *    "stopped" e não recebem broadcasts implícitos). Device Owner é isento.
 */
public class BootReceiver extends BroadcastReceiver {
    private static final String TAG = "PlayWaveBoot";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || intent.getAction() == null) return;
        final String action = intent.getAction();

        final boolean isBoot =
            Intent.ACTION_BOOT_COMPLETED.equals(action)
                || "android.intent.action.QUICKBOOT_POWERON".equals(action)
                || "com.htc.intent.action.QUICKBOOT_POWERON".equals(action);

        if (!isBoot) return;

        Log.i(TAG, "Boot detectado (" + action + ") — iniciando PlayWave Player");

        Intent launch = new Intent(context, MainActivity.class);
        launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        launch.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP);
        try {
            context.startActivity(launch);
        } catch (Exception e) {
            Log.e(TAG, "Falha ao iniciar Activity no boot: " + e.getMessage(), e);
        }
    }
}
