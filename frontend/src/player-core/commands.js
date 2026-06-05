/**
 * commands.js — Motor de comandos remotos.
 *
 * Comandos suportados:
 *   sync              → recarrega playlist (soft)
 *   refresh_playlist  → recarrega playlist (soft)
 *   clear_cache       → limpa cache IndexedDB + recarrega
 *   reload_player     → recarrega playlist/config sem reiniciar processo
 *   restart_app       → tenta reiniciar/recarregar o app do player
 *   restart_device    → tenta reiniciar o dispositivo físico quando a plataforma suportar
 *   shutdown_device   → tenta desligar o dispositivo físico quando a plataforma suportar
 *   set_volume        → altera volume do áudio
 *   mute / unmute     → silencia / ativa áudio
 *
 * SPEC 003 — padroniza `error_code` no resultado do ACK para que o gerenciador
 * exiba badge correto ("Não suportado", etc) e o backend possa filtrar/auditar.
 */

import { PlaylistCache } from "./storage.js";
import Platform from "./platform.js";

/**
 * Erro lançado quando a plataforma atual não suporta o comando.
 * `error_code` é propagado pelo `executeCommand` para o resultado do ACK.
 */
class CommandUnsupportedError extends Error {
  constructor(
    command,
    { errorCode = "COMMAND_NOT_IMPLEMENTED", reason = null } = {},
  ) {
    super(`${command} não suportado na plataforma ${Platform.name}`);
    this.name = "CommandUnsupportedError";
    this.platformUnsupported = true;
    this.errorCode = errorCode;
    this.reason = reason;
  }
}

function platformUnsupported(command, opts) {
  throw new CommandUnsupportedError(command, opts);
}

/**
 * Chama comando nativo de power management
 * @param {string} command - Nome do comando
 * @returns {Promise<any>}
 */
async function callNativePowerCommand(command) {
  // @ts-ignore - Bridge nativo pode não estar definido em todas as plataformas
  const nativeBridge =
    window.PlayWaveNative ||
    window.AndroidPlayer ||
    window.__ELECTRON__?.player;
  const fn = nativeBridge?.[command];
  if (typeof fn !== "function") {
    // Distinguir browser puro de plataforma reconhecida sem handler.
    const errorCode =
      Platform.name === "web"
        ? "BROWSER_ENVIRONMENT"
        : "COMMAND_NOT_IMPLEMENTED";
    platformUnsupported(command, { errorCode });
  }
  return fn.call(nativeBridge);
}

async function callNativeWindowCommand(command, ...args) {
  const nativeBridge = window.__ELECTRON__?.player;
  const fn = nativeBridge?.[command];
  console.log(`[commands] callNativeWindowCommand: ${command}, isElectron=${Platform.isElectron}, hasPlayer=${!!nativeBridge}, hasFn=${typeof fn}`);
  if (typeof fn !== "function") {
    const errorCode = Platform.isElectron
      ? "COMMAND_NOT_IMPLEMENTED"
      : "BROWSER_ENVIRONMENT";
    platformUnsupported(command, {
      errorCode,
      reason: "window_control_requires_electron",
    });
  }
  return fn.call(nativeBridge, ...args);
}

function normalizeDesktopDuration(payload) {
  const raw = Number(payload?.duration_seconds ?? 10);
  if (!Number.isFinite(raw)) return 10;
  return Math.max(1, Math.min(300, Math.round(raw)));
}

export const COMMAND_HANDLERS = {
  /**
   * sync / refresh_playlist — recarrega dados sem reload da página.
   */
  sync: async ({ setPhase, setProgress }) => {
    console.log("[commands] executing: sync");
    setProgress(0);
    setPhase("loading");
  },

  refresh_playlist: async ({ setPhase, setProgress }) => {
    console.log("[commands] executing: refresh_playlist");
    setProgress(0);
    setPhase("loading");
  },

  reload_player: async ({ setPhase, setProgress }) => {
    console.log("[commands] executing: reload_player");
    setProgress(0);
    setPhase("loading");
  },

  /**
   * clear_cache — limpa IndexedDB e recarrega playlist.
   */
  clear_cache: async ({ deviceId, setPhase, setProgress }) => {
    console.log("[commands] executing: clear_cache");
    if (deviceId) {
      await PlaylistCache.clear(deviceId).catch(() => {});
    }
    setProgress(0);
    setPhase("loading");
  },

  /**
   * restart — soft reset: preserva pareamento, reinicia estado visual.
   * O AudioPlayer permanece montado (não desmonta).
   */
  restart: async ({ setPhase, setProgress }) => {
    console.log("[commands] executing: restart legacy -> restart_app");
    setProgress(0);
    setPhase("loading");
  },

  restart_app: async ({ setPhase, setProgress }) => {
    console.log("[commands] executing: restart_app");
    setProgress(0);
    setPhase("loading");
    if (Platform.isElectron || Platform.isCapacitor) {
      await callNativePowerCommand("restartApp");
    } else {
      // Fallback web puro: reload da página.
      setTimeout(() => window.location.reload(), 300);
    }
  },

  minimize_player: async () => {
    console.log("[commands] executing: minimize_player");
    return await callNativeWindowCommand("minimizeWindow");
  },

  minimize_window: async () => {
    console.log("[commands] executing: minimize_window");
    return await callNativeWindowCommand("minimizeWindow");
  },

  restore_player: async () => {
    console.log("[commands] executing: restore_player");
    return await callNativeWindowCommand("restoreWindow");
  },

  restore_window: async () => {
    console.log("[commands] executing: restore_window");
    return await callNativeWindowCommand("restoreWindow");
  },

  show_desktop: async ({ payload }) => {
    const durationSeconds = normalizeDesktopDuration(payload);
    const restoreFullscreen = payload?.restore_fullscreen !== false;
    console.log("[commands] executing: show_desktop", durationSeconds, {
      restoreFullscreen,
    });
    return await callNativeWindowCommand(
      "showDesktop",
      durationSeconds,
      restoreFullscreen,
    );
  },

  restart_device: async () => {
    console.log("[commands] executing: restart_device");
    await callNativePowerCommand("restartDevice");
  },

  shutdown_device: async () => {
    console.log("[commands] executing: shutdown_device");
    await callNativePowerCommand("shutdownDevice");
  },

  screenshot: async () => {
    console.log("[commands] executing: screenshot");
    return await callNativePowerCommand("takeScreenshot");
  },

  take_screenshot: async () => {
    console.log("[commands] executing: take_screenshot");
    return await callNativePowerCommand("takeScreenshot");
  },

  /**
   * set_volume — altera volume do AudioPlayer via payload.volume (0..1)
   */
  set_volume: async ({ payload, setAudioVolume }) => {
    const vol = parseFloat(payload?.volume ?? 0.7);
    if (!isNaN(vol)) {
      console.log("[commands] executing: set_volume", vol);
      setAudioVolume?.(Math.max(0, Math.min(1, vol)));
    }
  },

  mute: async ({ setVideoMuted, setAudioEnabled }) => {
    console.log("[commands] executing: mute");
    setVideoMuted?.(true);
    setAudioEnabled?.(false);
  },

  unmute: async ({ setVideoMuted, setAudioEnabled }) => {
    console.log("[commands] executing: unmute");
    setVideoMuted?.(false);
    setAudioEnabled?.(true);
  },
};

/**
 * Conjunto de comandos que matam o processo do player. Para esses, o caller
 * deve fazer um pre-ACK no backend ANTES de invocar `executeCommand` — caso
 * contrário o backend nunca recebe confirmação porque o processo morre.
 */
export const DESTRUCTIVE_COMMANDS = new Set([
  "restart_app",
  "restart_device",
  "shutdown_device",
]);

/**
 * executeCommand(cmd, context)
 * Executa um comando remoto e retorna { success, errorMessage, result }.
 *
 * `result` é o payload tipado para o ACK (CommandAckResult no backend), com
 * pelo menos:
 *   - platform: identificador da plataforma do player
 *   - command_type: tipo do comando
 *   - completed_at | failed_at: ISO timestamp
 *   - platform_unsupported (boolean): true quando handler ausente
 *   - error_code: enum padronizado (ver tabela em api-contract.md)
 */
export async function executeCommand(cmd, context) {
  console.log("[commands] ========================================");
  console.log("[commands] Executando comando:", cmd.command_type);
  console.log("[commands] Plataforma:", Platform.name);
  console.log("[commands] Payload:", cmd.payload);
  console.log("[commands] Context:", {
    deviceId: context.deviceId,
    phase: context.phase,
  });
  console.log("[commands] ========================================");

  const handler = COMMAND_HANDLERS[cmd.command_type];
  if (!handler) {
    console.warn("[commands] ⚠️  Comando desconhecido:", cmd.command_type);
    return {
      success: false,
      errorMessage: `Unknown command: ${cmd.command_type}`,
      result: {
        platform: Platform.name,
        command_type: cmd.command_type,
        platform_unsupported: false,
        error_code: "UNKNOWN_COMMAND",
        failed_at: new Date().toISOString(),
      },
    };
  }

  try {
    console.log("[commands] ▶️  Iniciando execução...");
    const handlerResult = await handler({ ...context, payload: cmd.payload });
    console.log(
      "[commands] ✅ Comando executado com sucesso:",
      cmd.command_type,
    );
    console.log("[commands] Resultado:", handlerResult);

    return {
      success: true,
      errorMessage: null,
      result: {
        platform: Platform.name,
        command_type: cmd.command_type,
        completed_at: new Date().toISOString(),
        ...(handlerResult && typeof handlerResult === "object"
          ? { handler: handlerResult }
          : {}),
      },
    };
  } catch (err) {
    console.error("[commands] ========================================");
    console.error("[commands] ❌ ERRO ao executar:", cmd.command_type);
    console.error("[commands] Mensagem:", err?.message);
    console.error("[commands] Stack:", err?.stack);
    console.error("[commands] Platform unsupported:", err?.platformUnsupported);
    console.error("[commands] Error code:", err?.errorCode);
    console.error("[commands] Reason:", err?.reason);
    console.error("[commands] ========================================");

    const isUnsupported = err?.platformUnsupported === true;
    return {
      success: false,
      errorMessage: err?.message || String(err),
      result: {
        platform: Platform.name,
        command_type: cmd.command_type,
        platform_unsupported: isUnsupported,
        error_code:
          err?.errorCode ||
          (isUnsupported ? "COMMAND_NOT_IMPLEMENTED" : "EXECUTION_FAILED"),
        reason: err?.reason || null,
        failed_at: new Date().toISOString(),
      },
    };
  }
}
