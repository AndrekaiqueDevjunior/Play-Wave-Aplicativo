# PlayWave Player — Android APK (Capacitor)

## Compatibilidade
- Android 8.0+ (API 26+)
- Android TV (API 26+)
- TV Box Android
- Tablets Android

## Pré-requisitos

```bash
# Node.js 18+
# Java 17+ (JDK)
# Android Studio com Android SDK
# Android SDK Tools + Build-tools 34

# Verificar
java --version
echo $ANDROID_HOME
```

## Instalação do Capacitor

```bash
cd frontend

# Instalar Capacitor CLI e core
npm install @capacitor/core @capacitor/cli
npm install @capacitor/android
npm install @capacitor/splash-screen @capacitor/status-bar
npm install capacitor-keep-awake

# Inicializar projeto Android
npx cap add android
```

## Build

```bash
# 1. Compilar frontend
cd frontend
VITE_PLAYER_MODE=capacitor npm run build

# 2. Sincronizar com Capacitor
npx cap sync android

# 3. Abrir no Android Studio para build
npx cap open android

# OU build direto pela linha de comando (Debug APK)
cd android
./gradlew assembleDebug

# Release APK (requer keystore)
./gradlew assembleRelease
```

## Saída dos builds

```
frontend/android/app/build/outputs/apk/debug/app-debug.apk
frontend/android/app/build/outputs/apk/release/app-release.apk
```

## Configurações Android necessárias

### AndroidManifest.xml — adicionar:

```xml
<!-- Impede sleep da tela -->
<uses-permission android:name="android.permission.WAKE_LOCK" />
<!-- Acesso a rede -->
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<!-- Armazenamento offline -->
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

<!-- Configurar Activity para fullscreen e landscape -->
<activity
    android:name=".MainActivity"
    android:configChanges="orientation|keyboardHidden|keyboard|screenSize|locale|smallestScreenSize|screenLayout|uiMode"
    android:label="@string/title_activity_main"
    android:launchMode="singleTask"
    android:screenOrientation="landscape"
    android:theme="@style/AppTheme.NoActionBarLaunch"
    android:windowSoftInputMode="adjustResize">
```

### res/values/styles.xml — modo imersivo:

```xml
<style name="AppTheme.NoActionBarLaunch" parent="Theme.SplashScreen">
    <item name="android:windowFullscreen">true</item>
    <item name="android:windowTranslucentStatus">true</item>
    <item name="android:windowTranslucentNavigation">true</item>
</style>
```

## Android TV / TV Box

Para Android TV, adicionar em `AndroidManifest.xml`:

```xml
<!-- Declara como app de TV Leanback -->
<uses-feature android:name="android.hardware.touchscreen" android:required="false" />
<uses-feature android:name="android.software.leanback" android:required="false" />

<!-- Intent para TV -->
<intent-filter>
    <action android:name="android.intent.action.MAIN" />
    <category android:name="android.intent.category.LEANBACK_LAUNCHER" />
</intent-filter>
```

## Keep Awake / Impedir Sleep

No `MainActivity.java` (ou `MainActivity.kt`):

```java
import android.view.WindowManager;

@Override
protected void onCreate(Bundle savedInstanceState) {
    super.onCreate(savedInstanceState);
    // Impede desligamento da tela
    getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    // Fullscreen imersivo
    getWindow().getDecorView().setSystemUiVisibility(
        View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY |
        View.SYSTEM_UI_FLAG_FULLSCREEN |
        View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
    );
}
```

## Variáveis de ambiente

Crie `frontend/.env.android`:

```env
VITE_API_URL=http://SEU_SERVIDOR:8000
VITE_PLAYER_MODE=capacitor
VITE_DEVICE_PLATFORM=android
```

## Kiosk Mode (Android TV)

Para modo kiosk completo em Android TV, considere:
1. **App de launcher custom** (substitui a launcher padrão)
2. **MDM (Mobile Device Management)** como Fully Kiosk Browser
3. **Device Owner Mode** via ADB

```bash
# Definir como Device Owner (requer factory reset ou ADB)
adb shell dpm set-device-owner com.playwave.player/.AdminReceiver
```
