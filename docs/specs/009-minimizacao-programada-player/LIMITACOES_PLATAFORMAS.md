# SPEC 009 - Limitações por Plataforma

**Status:** Documentado

**Data:** 2 de junho de 2026

---

## Resumo Executivo

SPEC 009 (Minimização Programada do Player) foi implementada para **Windows e Linux com Electron**.

Plataformas Android e Smart TV têm limitações técnicas que impedem implementação na fase 1. Alternativas e roadmap estão documentados aqui.

---

## Plataformas Suportadas

### ✅ Windows (Electron)

**Status:** Totalmente suportado

**Comandos disponíveis:**
- ✅ `minimize_window` → `mainWindow.minimize()`
- ✅ `restore_window` → `mainWindow.restore()`
- ✅ `show_desktop` → `mainWindow.minimize()` + auto-restore

**Funcionalidades:**
- ✅ Scheduler local com intervalo configurável
- ✅ Preservação de fullscreen/kiosk state
- ✅ Sincronização via SSE
- ✅ Config persistida por dispositivo

**Validado em:**
- Windows 10 Professional
- Windows 11 Professional

---

### ✅ Linux (Electron)

**Status:** Totalmente suportado (teórico, não testado em produção)

**Comandos disponíveis:**
- ✅ `minimize_window` → `mainWindow.minimize()`
- ✅ `restore_window` → `mainWindow.restore()`
- ✅ `show_desktop` → `mainWindow.minimize()` + auto-restore

**Compatibilidade:**
- Electron IPC é cross-platform
- APIs Electron são idênticas no Linux

**Restrições conhecidas:**
- Window manager pode ignorar `minimize()` em tiling WMs
- Mitigação: Usar `setSkipTaskbar(true)` + `setVisible(false)` como fallback

**Recomendação:** Testar em distribuições suportadas (Ubuntu 20.04+, Debian 11+) antes de rollout

---

## Plataformas Não Suportadas na Fase 1

### ❌ Android (WebRTC/React Native)

**Status:** Bloqueado por limitações técnicas

**Razão:**

Android não é Electron. O player Android usa WebRTC (browser-based) ou React Native.

| Aspecto | Requisito SPEC 009 | Android WebRTC | Android React Native |
|---------|-------------------|-----------------|----------------------|
| Window minimize | Electron IPC | ❌ (browser) | ⚠️ (framework) |
| Window state management | mainWindow.* | ❌ (não existe) | ⚠️ (Activity model) |
| IPC bridge | preload.js context | ❌ (renderer bound) | ⚠️ (native bridge) |
| Fullscreen API | Electron API | ✅ (W3C) | ⚠️ (android.view) |
| Scheduler access | Local JS | ✅ | ✅ |

**Bloqueadores:**

1. **WebRTC Browser (Chrome, Firefox):**
   - Browser não controla "desktop" do dispositivo
   - `window.minimize()` não existe em navegadores
   - Não há equivalente de fullscreen + app minimize
   - **Solução:** Usar Activity Manager do Android (requer framework Native)

2. **React Native Framework:**
   - React Native não expõe `AppState` para minimize automático
   - UIViewController (iOS) ou Activity (Android) controla visibilidade
   - Requer acesso a native module
   - **Solução:** Custom native module para `android.app.ActivityManager`

**Roadmap Alternativo - Fase 2:**

Se SPEC 009 precisar suportar Android, 3 caminhos possíveis:

#### Opção A: Android Device Owner + Lock Task Mode (Recomendado)

**Caso de uso:** Kiosk público

```java
// Android 5.0+
DevicePolicyManager.setLockTaskPackages(...)
DevicePolicyManager.lockNow()  // muda de app
```

**Pros:**
- Oficial, suportado, seguro
- Multi-device management

**Cons:**
- Requer device enrollment
- Não funciona em pessoal (sem MDM)

#### Opção B: Custom Native Module

**Caso de uso:** Player Android corporativo com app dedicado

```kotlin
// android/app/src/main/kotlin/...
class WindowExposureModule : ReactContextBaseJavaModule() {
    override fun minimizeApp() {
        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        activityManager.moveTaskToBack(taskId, false)
    }
}
```

**Pros:**
- Sem restrições, full control

**Cons:**
- Requer Android development team
- Manutenção de native code

#### Opção C: Webview Wrapper + JsBridge

**Caso de uso:** Webview Android com controle app

```javascript
// android/app/src/main/java/WebViewActivity.java
window.androidBridge = {
  minimizeApp: () -> activity.moveTaskToBack(true)
}
```

**Pros:**
- Integração com WebRTC
- Reutiliza código JS

**Cons:**
- Requer app wrapper nativo
- Não funciona em browsers genéricos

---

### ❌ Smart TV (Android TV, WebOS, Tizen)

**Status:** Bloqueado por limitações técnicas

**Razão:**

Smart TVs não têm "desktop" no sentido tradicional. UI é fullscreen app-based.

| Aspecto | Smart TV | Requisito SPEC 009 |
|---------|----------|------------------|
| Multi-window | ❌ (apps fullscreen) | ✅ (window manage) |
| Window minimize | ❌ (não existe) | ✅ (core feature) |
| Window restore | ❌ (app switching) | ✅ (core feature) |
| Desktop exposure | ❌ (app home) | ✅ (background access) |

**Bloqueadores:**

1. **Android TV:**
   - Sem desktop, apenas app launcher
   - `minimize` → app sai de tela (indistinguível de close)
   - Não há janelas sobreponíveis
   - Fluxo é app → home → outro app

2. **WebOS/Tizen:**
   - Proprietário, APIs fechadas
   - Sem acesso a window manager
   - Apps são isolados de UI do sistema

**Roadmap Alternativo - Fase 2:**

Para Smart TV, objetivo seria "show home screen periodically":

```javascript
// Android TV (com permissão)
const intent = new android.content.Intent(android.content.Intent.ACTION_MAIN);
intent.addCategory(android.content.Intent.CATEGORY_HOME);
context.startActivity(intent);

// Após N segundos: voltar à app
const pendingIntent = PendingIntent.getActivity(...);
AlarmManager.set(AlarmManager.RTC, futureTime, pendingIntent);
```

**Pros:**
- Funciona em Android TV
- Objetivo similar (mostrar home)

**Cons:**
- Experiência diferente (não é "desktop expose")
- Perde contexto de app ao voltar

---

## Comportamento Esperado por Plataforma

### Quando Player Recebe `show_desktop` (Comando)

| Plataforma | Resposta | Comportamento |
|------------|----------|---------------|
| Windows Electron | ✅ OK | Minimiza, mostra desktop, restaura |
| Linux Electron | ✅ OK | Minimiza, mostra desktop, restaura |
| Android | ❌ `platform_unsupported` | Nenhuma ação, comando ignorado |
| Smart TV | ❌ `platform_unsupported` | Nenhuma ação, comando ignorado |
| iOS | ❌ `platform_unsupported` | Nenhuma ação, comando ignorado |

### Quando Player Tenta Agendar Scheduler Local

| Plataforma | Behavior | Log |
|------------|----------|-----|
| Windows Electron | ✅ Executa | `[scheduler] scheduling show_desktop in ${interval}s` |
| Linux Electron | ✅ Executa | `[scheduler] scheduling show_desktop in ${interval}s` |
| Android | ⏭️ Salta | `[scheduler] skipped (platform_unsupported)` |
| Smart TV | ⏭️ Salta | `[scheduler] skipped (platform_unsupported)` |
| iOS | ⏭️ Salta | `[scheduler] skipped (platform_unsupported)` |

---

## Documentação de Retorno ao Usuário

Quando usuário tenta ativar SPEC 009 em plataforma não suportada:

### UI Admin - Mensagem de Aviso

```html
<Alert type="warning" icon="info">
  <strong>Comportamento do Player</strong> (Desktop Exposure)
  
  Esta funcionalidade suporta apenas:
  • Windows (Electron)
  • Linux (Electron)
  
  Seu dispositivo está rodando <strong>Android</strong>.
  A configuração será ignorada pelo player.
  
  <Link href="/docs/spec-009-limitations">Saiba mais</Link>
</Alert>
```

### Backend - Campo de Suporte

```python
# Adicionar na API de detalhes do device
GET /devices/{device_id}
{
  "id": "...",
  "platform": "android",
  "capabilities": {
    "desktop_exposure_supported": false,  # ← novo
    "reason": "platform_not_supported"
  }
}
```

---

## Roadmap Futuro

### Fase 2 (2026 Q3-Q4)

- [ ] Android Device Owner mode (MDM-only)
- [ ] Custom native module para Android
- [ ] Documentação de setup para cada plataforma
- [ ] Testes em Android TV (via emulador)

### Fase 3+ (2027+)

- [ ] WebOS/Tizen APIs (se houver demanda)
- [ ] iOS App Switcher control (se houver demanda)
- [ ] Config global/por-grupo (ao invés de por-device)

---

## Matriz de Suporte

| Plataforma | Fase 1 | Fase 2 | Fase 3+ | Detalhes |
|------------|--------|--------|---------|----------|
| **Windows Electron** | ✅ | N/A | N/A | Totalmente suportado |
| **Linux Electron** | ✅ | ⬜ | N/A | Código pronto, testar em prod |
| **Android WebRTC** | ❌ | ⬜ | ⬜ | Requer native module |
| **Android React Native** | ❌ | ⬜ | ⬜ | Requer native module |
| **Android Device Owner** | ❌ | ⬜ | ⬜ | Requer MDM enrollment |
| **Smart TV (Android TV)** | ❌ | ⬜ | ⬜ | Requer custom behavior |
| **Smart TV (WebOS/Tizen)** | ❌ | ❌ | ⬜ | APIs proprietárias fechadas |
| **iOS** | ❌ | ❌ | ⬜ | Sandboxing App Store |

Legend:
- ✅ Suportado
- ⬜ Em discussão/roadmap
- ❌ Não planeado / Bloqueado

---

## Teste de Comportamento

### Teste 1: Windows Electron (Esperado: Funciona)

```bash
# Setup
export PLAYER_PLATFORM=electron
export PLAYER_OS=win32

# Ativação
PATCH /devices/{id}/desktop-exposure-config
{
  "enabled": true,
  "interval_seconds": 30,
  "duration_seconds": 5
}

# Resultado esperado
✅ Janela minimiza a cada 30s por 5s
```

### Teste 2: Android WebRTC (Esperado: Ignorado)

```bash
# Setup
export PLAYER_PLATFORM=webrtc
export PLAYER_OS=android

# Ativação
PATCH /devices/{id}/desktop-exposure-config
{
  "enabled": true,
  "interval_seconds": 30,
  "duration_seconds": 5
}

# Resultado esperado
⏭️ Config salva no backend
⏭️ Player recebe SSE event
❌ Player ignora (platform_unsupported)
✅ Log no console: [scheduler] skipped (platform_unsupported)
```

---

## Conclusão

**SPEC 009 foi projetada e implementada para Windows/Linux Electron.**

Suporte a Android e Smart TV requer:
1. Arquitetura diferente (não é Electron)
2. Native code (não é JavaScript puro)
3. Decisão de produto (qual behavior é aceitável?)

Todas essas plataformas retornarão `platform_unsupported` quando tentarem executar window-control commands, o que é seguro e esperado.

**Recomendação:** Documentar limitações no release notes e oferecer roadmap claro para futuro.

---

**Documento criado:** 2026-06-02

**Responsável:** PlayWave Development Team
