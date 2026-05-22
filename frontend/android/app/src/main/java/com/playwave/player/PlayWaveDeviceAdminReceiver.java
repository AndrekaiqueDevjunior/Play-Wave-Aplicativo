package com.playwave.player;

import android.app.admin.DeviceAdminReceiver;

/**
 * Device Admin Receiver para o PlayWave.
 *
 * Necessário para provisionar o app como Device Owner via ADB:
 *   adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver
 *
 * Como Device Owner, o app ganha acesso a APIs sensíveis como
 * PowerManager.reboot() e DevicePolicyManager.lockNow() sem prompt.
 *
 * Veja docs/PROVISIONAMENTO_ANDROID.md.
 */
public class PlayWaveDeviceAdminReceiver extends DeviceAdminReceiver {
    // Vazio é suficiente — apenas precisa existir para o sistema reconhecer.
}
