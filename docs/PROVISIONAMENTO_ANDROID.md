# Provisionamento Android como Device Owner

Documento técnico — SPEC 003 (Player Comandos Nativos).

## Por que isso é necessário?

Os comandos `restart_device` e `shutdown_device` da SPEC 003 invocam APIs
sensíveis do Android (`PowerManager.reboot()` e
`DevicePolicyManager.lockNow()`) que **só funcionam quando o app PlayWave está
registrado como Device Owner**.

Sem isso, todo comando de energia retorna `error_code: DEVICE_OWNER_REQUIRED`
e o gerenciador exibe "Não suportado".

## O que muda no app

Já entregue na SPEC 003:

- `PlayWaveDeviceAdminReceiver` (`frontend/android/app/src/main/java/com/playwave/player/`)
- `device_admin_policies.xml` (`frontend/android/app/src/main/res/xml/`)
- `PlayWaveNativePlugin` registrado em `MainActivity`
- Manifest com `<uses-permission REBOOT>` e `<receiver>` do Device Admin

O APK já vem pronto para ser provisionado.

## Pré-requisitos

- TV/dispositivo Android com **factory reset feito**.
- Nenhuma conta Google configurada (provisionamento via ADB **não funciona**
  se já houver conta).
- Cabo USB ou rede para conectar via ADB.
- `adb` instalado na máquina do técnico (`apt install android-tools-adb` no
  Linux ou Android Studio Platform Tools no Windows/macOS).
- APK PlayWave instalado no dispositivo (via `adb install` ou Play Store).

## Provisionamento via ADB (recomendado para frotas pequenas)

### Passo 1 — Habilitar ADB no dispositivo

1. Settings → About phone → tocar 7× em "Build number" para habilitar Developer Options.
2. Settings → Developer Options → USB Debugging = ON.
3. Conectar USB e autorizar a chave da máquina quando aparecer o prompt.

### Passo 2 — Confirmar device conectado

```bash
adb devices
```

Deve listar 1 dispositivo `device` (não `unauthorized` nem `offline`).

### Passo 3 — Instalar APK (se ainda não estiver)

```bash
adb install -r frontend/dist-apk/playwave-player.apk
```

### Passo 4 — Provisionar como Device Owner

```bash
adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver
```

**Saída esperada:**

```
Success: Device owner set to package ComponentInfo{com.playwave.player/com.playwave.player.PlayWaveDeviceAdminReceiver}
Active admin set to component {com.playwave.player/com.playwave.player.PlayWaveDeviceAdminReceiver}
```

### Passo 5 — Validar

Abrir o player, parear no gerenciador, e disparar comando `restart_device`. O
dispositivo deve reiniciar em segundos.

## Erros comuns

### "Not allowed to set the device owner because there are already several users"

- Causa: dispositivo tem mais de um perfil de usuário.
- Solução: factory reset + repetir provisionamento ANTES de configurar
  qualquer conta.

### "Not allowed to set the device owner because there are already some accounts on the device"

- Causa: conta Google já configurada (mais comum).
- Solução: factory reset + pular a etapa de conta Google na configuração
  inicial. Para tablets/TVs com app store custom, deixe a etapa do Google
  para depois do provisionamento.

### "Unknown admin"

- Causa: APK não tem o `<receiver>` no Manifest ou foi instalado uma versão
  antiga (pré SPEC 003).
- Solução: garantir que o APK foi rebuildado depois da SPEC 003
  (`npm run build:apk` com `frontend/android/app/src/main/java/com/playwave/player/PlayWaveDeviceAdminReceiver.java` presente).

### `restartDevice` ainda retorna `DEVICE_OWNER_REQUIRED` após provisionar

- Verificar que o pacote provisionado bate exatamente: `com.playwave.player`.
- Reabrir o app pelo menos uma vez para que o plugin nativo capture o estado
  novo.

## Provisionamento via QR Code (Android 7+ / TVs em escala)

Alternativa para frotas grandes — usar Enterprise Mobility Management (EMM)
externo (Hexnode, Knox Mobile Enrollment, SureMDM etc.) que entrega um QR code
durante a setup wizard.

Configuração do QR code precisa apontar para:

```json
{
  "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME":
    "com.playwave.player/.PlayWaveDeviceAdminReceiver",
  "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION":
    "https://playwave.com.br/downloads/playwave-player.apk",
  "android.app.extra.PROVISIONING_DEVICE_ADMIN_SIGNATURE_CHECKSUM":
    "<base64 do SHA-256 do APK>"
}
```

Implementação completa de QR provisioning está fora do escopo desta SPEC.

## Despareamento (despromover Device Owner)

Só possível via factory reset.

```bash
adb shell dpm remove-active-admin com.playwave.player/.PlayWaveDeviceAdminReceiver
```

Comando acima **só remove o admin ativo**, não o Device Owner. Para remover
Device Owner é necessário factory reset.

## Limitações conhecidas

### Shutdown completo em Android stock

Android **não expõe** API pública de shutdown completo do dispositivo, mesmo
para Device Owner. A SPEC 003 implementa `shutdownDevice()` chamando
`DevicePolicyManager.lockNow()` como fallback — **apaga a tela**, mas o
dispositivo continua ligado.

Para shutdown físico real é necessário:

- Firmware customizado da fabricante (Samsung Knox, Zebra, etc.) que exponha
  intent custom.
- Hardware com controle de energia via relé externo (cenário industrial).
- Wake-on-LAN para religar (se aceitar a operação).

Documentação do limite vai no ACK: o player retorna
`result.note: "screen_locked"` e o gerenciador mostra "Concluído" mas o
operador deve saber pela documentação que é uma limitação do Android.

### Reboot pode falhar em TV Boxes baratos

Algumas ROMs de TV Box (não certificadas) restringem `PowerManager.reboot()`
mesmo com Device Owner. Nesses casos o ACK retorna `REBOOT_FAILED`.

Solução: testar antes de homologar o modelo de TV Box para o cliente.

## Checklist pré-deploy

Para cada TV que receberá o PlayWave:

- [ ] Factory reset feito antes de tudo.
- [ ] ADB habilitado durante o provisionamento (depois pode desabilitar).
- [ ] APK PlayWave instalado (`adb install`).
- [ ] `adb shell dpm set-device-owner com.playwave.player/.PlayWaveDeviceAdminReceiver` retornou `Success`.
- [ ] Comando `restart_device` enviado pelo gerenciador funcionou (TV reiniciou).
- [ ] Comando `shutdown_device` enviado — tela bloqueou (limitação documentada).
- [ ] App pareado e tocando playlist normalmente.
- [ ] ADB desabilitado (Settings → Developer Options) para evitar uso indevido.
