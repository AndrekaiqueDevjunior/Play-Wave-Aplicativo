package com.playwave.player;

import android.app.admin.DevicePolicyManager;
import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Bundle;
import android.util.Log;
import android.view.WindowManager;
import android.webkit.WebSettings;
import android.webkit.WebView;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        // SPEC 003 — registra o plugin nativo ANTES de super.onCreate para
        // garantir que esteja disponível quando o WebView for criado.
        registerPlugin(PlayWaveNativePlugin.class);

        super.onCreate(savedInstanceState);

        // RNF02 — player de TV/display não pode deixar a tela apagar. O bloco
        // "KeepAwake" em capacitor.config.json referencia um plugin que NÃO está
        // instalado (não há @capacitor-community/keep-awake nas dependências), e
        // o WakeLock web (platform.js) é liberado quando a aba fica oculta.
        // FLAG_KEEP_SCREEN_ON é a garantia nativa e robusta para kiosk.
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);

        WebView webView = getBridge().getWebView();
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        // RF02/RF03 — permite autoplay (inclusive muted) sem gesto do usuário.
        // SEM isso o System WebView do Android exibe o BOTÃO DE PLAY nativo sobre
        // o vídeo e não inicia a reprodução até um toque — causa raiz do "play
        // antes do vídeo" relatado pelo cliente.
        settings.setMediaPlaybackRequiresUserGesture(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE);

        pinAsHomeIfDeviceOwner();
    }

    /**
     * RF01 — quando o app está provisionado como Device Owner, fixa o PlayWave
     * como Home padrão SEM o seletor de launcher do Android. Assim o boot cai
     * direto no player de forma 100% automática (sem o passo manual de
     * "escolher app de início").
     *
     * Sem Device Owner este método não faz nada (e não falha) — o autostart
     * recai sobre o HOME launcher comum (manifest) + o passo manual de definir
     * o PlayWave como app de início padrão.
     *
     * Provisione com:
     *   adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver
     */
    private void pinAsHomeIfDeviceOwner() {
        try {
            DevicePolicyManager dpm =
                (DevicePolicyManager) getSystemService(Context.DEVICE_POLICY_SERVICE);
            if (dpm == null || !dpm.isDeviceOwnerApp(getPackageName())) return;

            ComponentName admin = new ComponentName(this, PlayWaveDeviceAdminReceiver.class);

            // Idempotente: limpa preferências antigas deste pacote antes de
            // reescrever, evitando entradas duplicadas a cada onCreate.
            dpm.clearPackagePersistentPreferredActivities(admin, getPackageName());

            IntentFilter homeFilter = new IntentFilter(Intent.ACTION_MAIN);
            homeFilter.addCategory(Intent.CATEGORY_HOME);
            homeFilter.addCategory(Intent.CATEGORY_DEFAULT);

            dpm.addPersistentPreferredActivity(
                admin,
                homeFilter,
                new ComponentName(this, MainActivity.class)
            );
            Log.i("PlayWaveBoot", "PlayWave fixado como Home padrão (Device Owner)");
        } catch (Exception e) {
            Log.e("PlayWaveBoot", "Falha ao fixar como Home: " + e.getMessage(), e);
        }
    }
}
