// @ts-nocheck
/**
 * platform.js — Detecção de plataforma em tempo de execução.
 *
 * Detecta: web, electron, capacitor, android-tv, smart-tv (Tizen/WebOS)
 * Fornece: flags de capacidade (fullscreen, pointer, remote-control, etc.)
 *
 * SPEC 003 — registra wrapper `window.PlayWaveNative` quando o plugin nativo
 * Capacitor `PlayWaveNative` estiver disponível. Sem isso, `commands.js` cai
 * em "platform_unsupported" mesmo com o plugin instalado.
 */

const UA = typeof navigator !== "undefined" ? navigator.userAgent : "";

// SPEC 003 — bridge Capacitor → window.PlayWaveNative.
// Em ambientes onde @capacitor/core não está disponível (SSR, testes), o
// import dinâmico evita travar o bundle.
if (typeof window !== "undefined" && !window.PlayWaveNative) {
  try {
    // Lazy require — só executa em runtime do navegador.
    // eslint-disable-next-line @typescript-eslint/no-var-requires, global-require
    import("@capacitor/core")
      .then(({ Capacitor }) => {
        if (Capacitor && Capacitor.isPluginAvailable && Capacitor.isPluginAvailable("PlayWaveNative")) {
          const native = Capacitor.Plugins.PlayWaveNative;
          window.PlayWaveNative = {
            restartApp:      () => native.restartApp(),
            restartDevice:   () => native.restartDevice(),
            shutdownDevice:  () => native.shutdownDevice(),
            takeScreenshot:  async () => {
              const r = await native.takeScreenshot();
              return r?.base64 || null;
            },
          };
          console.log("[platform] PlayWaveNative bridge installed via Capacitor");
        }
      })
      .catch((err) => {
        // @capacitor/core ausente em ambiente puro (web/Electron) — esperado.
        if (process?.env?.NODE_ENV !== "production") {
          console.debug("[platform] Capacitor unavailable:", err?.message);
        }
      });
  } catch (err) {
    // ignore
  }
}

export const Platform = {
  get isElectron() {
    if (typeof window === "undefined") return false;
    if (window.__ELECTRON__) return true;
    // Fallback: Electron injeta "Electron/X.Y.Z" no userAgent
    return /Electron\//.test(navigator.userAgent);
  },

  isCapacitor:
    typeof window !== "undefined" &&
    (typeof window.Capacitor !== "undefined" || typeof window.capacitorExports !== "undefined"),

  isTizen: UA.includes("Tizen"),

  isWebOS: UA.includes("Web0S") || UA.includes("webOS"),

  isAndroidTV: UA.includes("Android") && (UA.includes("TV") || UA.includes("AFT")),

  isAndroid: UA.includes("Android"),

  isIOS: /iPad|iPhone|iPod/.test(UA),

  isDesktop:
    typeof window !== "undefined" &&
    !UA.includes("Android") &&
    !UA.includes("iPhone") &&
    !UA.includes("iPad"),

  get isSmartTV() {
    return this.isTizen || this.isWebOS || this.isAndroidTV;
  },

  get name() {
    if (this.isElectron)   return "electron";
    if (this.isCapacitor)  return "capacitor";
    if (this.isTizen)      return "tizen";
    if (this.isWebOS)      return "webos";
    if (this.isAndroidTV)  return "android-tv";
    if (this.isAndroid)    return "android";
    if (this.isIOS)        return "ios";
    return "web";
  },

  get supportsPointer() {
    return !this.isSmartTV || this.isElectron;
  },

  get supportsFullscreen() {
    return (
      typeof document !== "undefined" &&
      (document.fullscreenEnabled ||
        document.webkitFullscreenEnabled ||
        document.mozFullScreenEnabled)
    );
  },

  get supportsIndexedDB() {
    return typeof indexedDB !== "undefined";
  },

  get preferredStorage() {
    if (this.supportsIndexedDB) return "indexeddb";
    return "localstorage";
  },
};

/**
 * Tenta entrar em fullscreen.
 * Em Electron/Kiosk o fullscreen já é gerenciado pelo main process.
 */
export function requestFullscreen() {
  if (Platform.isElectron) return;
  const el = document.documentElement;
  const fn =
    el.requestFullscreen ||
    el.webkitRequestFullscreen ||
    el.mozRequestFullScreen ||
    el.msRequestFullscreen;
  if (fn) fn.call(el).catch(() => {});
}

/**
 * Keep-awake via NoSleep API-like approach (wakeLock ou video dummy).
 * Evita sleep em Android TV e Smart TVs.
 */
let wakeLockRef = null;
let _wakeLockWanted = false;

export async function acquireWakeLock() {
  _wakeLockWanted = true;
  if ("wakeLock" in navigator) {
    try {
      wakeLockRef = await navigator.wakeLock.request("screen");
      console.log("[platform] WakeLock acquired");
      wakeLockRef.addEventListener("release", () => {
        console.log("[platform] WakeLock released by browser");
        wakeLockRef = null;
      });
    } catch (e) {
      console.warn("[platform] WakeLock failed:", e.message);
    }
  }
}

export function releaseWakeLock() {
  _wakeLockWanted = false;
  wakeLockRef?.release?.();
  wakeLockRef = null;
}

// O navegador libera o WakeLock automaticamente quando a aba fica oculta
// (troca de janela, tela apaga, etc.) e NÃO o readquire sozinho — em TVs
// kiosk isso deixa o player com a tela apagada/parada até reiniciar
// manualmente. Reaquire ao voltar a ficar visível (padrão recomendado MDN).
if (typeof document !== "undefined") {
  document.addEventListener("visibilitychange", async () => {
    if (!_wakeLockWanted) return;
    if (document.visibilityState !== "visible") return;
    if (wakeLockRef) return;
    if (!("wakeLock" in navigator)) return;
    try {
      wakeLockRef = await navigator.wakeLock.request("screen");
      console.log("[platform] WakeLock re-acquired after visibilitychange");
      wakeLockRef.addEventListener("release", () => {
        console.log("[platform] WakeLock released by browser");
        wakeLockRef = null;
      });
    } catch (e) {
      console.warn("[platform] WakeLock re-acquire failed:", e.message);
    }
  });
}

export default Platform;
