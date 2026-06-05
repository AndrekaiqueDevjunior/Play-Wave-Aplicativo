/**
 * Electron main.js — PlayWave Desktop Player
 *
 * Suporte: Windows (.exe) e Linux (AppImage / .deb / .rpm)
 * Modo: Kiosk fullscreen permanente, sem barra de título, sem menus
 * Uso 24/7: watchdog, auto-restart em crash, keep-awake via powerSaveBlocker
 */

const {
  app,
  BrowserWindow,
  powerSaveBlocker,
  session,
  ipcMain,
} = require("electron");
const path = require("path");
const os = require("os");
const http = require("http");
const fs = require("fs");
const { exec } = require("child_process");
const { extname } = require("path");

const DEV_MODE = process.env.NODE_ENV === "development";
const EXTERNAL_URL = process.env.VITE_PLAYER_URL || null;
const KIOSK = process.env.PLAYER_KIOSK !== "false";

// Backend URL — pode ser sobrescrita por VITE_BACKEND_URL
const BACKEND_URL = process.env.VITE_BACKEND_URL || "http://localhost:8000";
console.log("[electron] BACKEND_URL:", BACKEND_URL);

// Pasta do React build dentro do pacote (ou repo local em dev)
const DIST_DIR = app.isPackaged
  ? path.join(process.resourcesPath, "dist")
  : path.join(__dirname, "../dist");

const MIME = {
  ".html": "text/html",
  ".js": "application/javascript",
  ".css": "text/css",
  ".json": "application/json",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".svg": "image/svg+xml",
  ".woff2": "font/woff2",
  ".ico": "image/x-icon",
};

let localPort = 0;

/**
 * Inicia um servidor HTTP estático servindo DIST_DIR.
 * Retorna uma Promise com a porta usada.
 */
function startLocalServer() {
  return new Promise((resolve, reject) => {
    if (EXTERNAL_URL) return resolve(null); // usa URL externa se definida

    const server = http.createServer((req, res) => {
      // Remove query string e decode URI
      let urlPath = decodeURIComponent(req.url.split("?")[0]);

      // SPA fallback: qualquer rota desconhecida serve index.html
      let filePath = path.join(DIST_DIR, urlPath);
      if (!fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
        filePath = path.join(DIST_DIR, "index.html");
      }

      const ext = extname(filePath).toLowerCase();
      const mime = MIME[ext] || "application/octet-stream";

      fs.readFile(filePath, (err, data) => {
        if (err) {
          res.writeHead(404);
          res.end("Not found");
          return;
        }
        res.writeHead(200, { "Content-Type": mime });
        res.end(data);
      });
    });

    // Porta fixa para CORS funcionar (backend precisa conhecer a origem)
    server.listen(3500, "127.0.0.1", () => {
      localPort = server.address().port;
      console.log(
        `[electron] local server on port ${localPort} serving ${DIST_DIR}`,
      );
      resolve(localPort);
    });
    server.on("error", reject);
  });
}

let mainWindow = null;
let powerSaveId = null;
let crashCount = 0;
let PLAYER_URL = null;
let desktopExposureRestoreTimer = null;
let lastWindowState = null;

function snapshotWindowState() {
  if (!mainWindow) return null;
  return {
    fullscreen: mainWindow.isFullScreen(),
    kiosk: mainWindow.isKiosk(),
    alwaysOnTop: mainWindow.isAlwaysOnTop(),
  };
}

function prepareWindowForDesktopExposure() {
  if (!mainWindow) throw new Error("no_window");
  lastWindowState = snapshotWindowState();
  if (mainWindow.isKiosk()) mainWindow.setKiosk(false);
  if (mainWindow.isFullScreen()) mainWindow.setFullScreen(false);
  if (mainWindow.isAlwaysOnTop()) mainWindow.setAlwaysOnTop(false);
}

function restoreWindowState(state = lastWindowState) {
  if (!mainWindow) throw new Error("no_window");
  mainWindow.restore();
  mainWindow.show();
  mainWindow.focus();
  if (state?.alwaysOnTop) mainWindow.setAlwaysOnTop(true);
  if (state?.fullscreen) mainWindow.setFullScreen(true);
  if (state?.kiosk) mainWindow.setKiosk(true);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1920,
    height: 1080,
    fullscreen: KIOSK,
    kiosk: KIOSK,
    frame: false,
    alwaysOnTop: !DEV_MODE,
    autoHideMenuBar: true,
    backgroundColor: "#000000",
    show: false,
    webPreferences: {
      preload: app.isPackaged
        ? path.join(process.resourcesPath, "app.asar.unpacked", "preload.js")
        : path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true,
      allowRunningInsecureContent: false,
      // Permite autoplay de mídia sem gesto do usuário
      autoplayPolicy: "no-user-gesture-required",
    },
  });

  // Oculta cursor em modo kiosk (display público)
  if (KIOSK) {
    mainWindow.webContents.on("did-finish-load", () => {
      mainWindow.webContents
        .insertCSS("* { cursor: none !important; }")
        .catch(() => {});
    });
  }

  mainWindow.once("ready-to-show", () => {
    mainWindow.show();
    console.log("[electron] window ready — platform:", os.platform());
  });

  const url = PLAYER_URL || `http://127.0.0.1:${localPort}/player`;
  mainWindow.loadURL(url).catch((err) => {
    console.error("[electron] failed to load URL:", url, err);
    setTimeout(() => mainWindow?.loadURL(url).catch(() => {}), 5000);
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });

  // Auto-restart em crash da página
  mainWindow.webContents.on("render-process-gone", (_, details) => {
    console.error("[electron] renderer crashed:", details.reason);
    crashCount++;
    const url = PLAYER_URL || `http://127.0.0.1:${localPort}/player`;
    if (crashCount < 10) {
      setTimeout(
        () => {
          if (mainWindow) {
            console.log("[electron] reloading after crash...");
            mainWindow.loadURL(url).catch(() => {});
          } else {
            createWindow();
          }
        },
        3000 * Math.min(crashCount, 5),
      );
    }
  });

  mainWindow.webContents.on("unresponsive", () => {
    console.warn("[electron] renderer unresponsive — forcing reload");
    mainWindow?.reload();
  });

  // SPEC 003 — `window.__ELECTRON__` agora é exposto pelo preload.js como
  // objeto real (`{ platform, player: { restartApp, ... } }`). Mantemos
  // apenas `window.__PLATFORM__` como dica adicional para debug.
  mainWindow.webContents.on("dom-ready", () => {
    mainWindow.webContents
      .executeJavaScript("window.__PLATFORM__ = '" + os.platform() + "';")
      .catch(() => {});
  });

  if (DEV_MODE) mainWindow.webContents.openDevTools({ mode: "detach" });
}

app.whenReady().then(async () => {
  PLAYER_URL = EXTERNAL_URL;
  if (!PLAYER_URL) await startLocalServer();
  // Bloqueia screensaver / suspensão do sistema (24/7)
  powerSaveId = powerSaveBlocker.start("prevent-display-sleep");
  console.log("[electron] powerSaveBlocker started, id:", powerSaveId);

  // Configura política de permissões de mídia (autoplay liberado)
  session.defaultSession.setPermissionRequestHandler(
    (webContents, permission, callback) => {
      const allowed = [
        "media",
        "microphone",
        "camera",
        "notifications",
        "fullscreen",
      ];
      callback(allowed.includes(permission));
    },
  );

  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  if (powerSaveId !== null) {
    powerSaveBlocker.stop(powerSaveId);
  }
});

// IPC: comandos do renderer para o processo principal

/**
 * Executa um comando shell e devolve uma Promise resolvida com stdout.
 */
function runShell(cmd) {
  return new Promise((resolve, reject) => {
    exec(cmd, (err, stdout, stderr) => {
      if (err) {
        console.error("[electron] shell failed:", cmd, stderr || err.message);
        reject(new Error(`${cmd}: ${(stderr || err.message).trim()}`));
      } else {
        resolve((stdout || "").trim());
      }
    });
  });
}

// Legado — alias de `player:restart_app`. Mantém compatibilidade com bundles
// antigos que ainda enviam `player:restart` via `electronBridge.restart()`.
ipcMain.on("player:restart", () => {
  console.log("[electron] IPC player:restart (legacy) — reloading renderer");
  const url = PLAYER_URL || `http://127.0.0.1:${localPort}/player`;
  mainWindow?.loadURL(url).catch(() => {});
});

ipcMain.on("player:fullscreen-toggle", () => {
  if (mainWindow) {
    mainWindow.setFullScreen(!mainWindow.isFullScreen());
  }
});

// SPEC 003 — Handlers de comando reais.
// Para comandos destrutivos (restart/shutdown), agendamos via setTimeout para
// retornar o ACK ao renderer ANTES do processo morrer.

ipcMain.handle("player:minimize_window", async () => {
  if (!mainWindow) throw new Error("no_window");
  console.log("[electron] IPC player:minimize_window");
  prepareWindowForDesktopExposure();
  mainWindow.minimize();
  return {
    ok: true,
    platform: process.platform,
    minimized_at: new Date().toISOString(),
  };
});

ipcMain.handle("player:restore_window", async () => {
  if (!mainWindow) throw new Error("no_window");
  console.log("[electron] IPC player:restore_window");
  if (desktopExposureRestoreTimer) {
    clearTimeout(desktopExposureRestoreTimer);
    desktopExposureRestoreTimer = null;
  }
  restoreWindowState();
  return {
    ok: true,
    platform: process.platform,
    restored_at: new Date().toISOString(),
  };
});

ipcMain.handle(
  "player:show_desktop",
  async (_, durationSeconds = 10, restoreFullscreen = true) => {
    if (!mainWindow) throw new Error("no_window");
    const duration = Math.max(
      1,
      Math.min(300, Math.round(Number(durationSeconds) || 10)),
    );
    const restoreState = snapshotWindowState();
    console.log("[electron] IPC player:show_desktop", duration, {
      restoreFullscreen,
    });

    if (desktopExposureRestoreTimer) {
      clearTimeout(desktopExposureRestoreTimer);
      desktopExposureRestoreTimer = null;
    }

    prepareWindowForDesktopExposure();
    mainWindow.minimize();

    if (restoreFullscreen) {
      desktopExposureRestoreTimer = setTimeout(() => {
        desktopExposureRestoreTimer = null;
        try {
          restoreWindowState(restoreState);
        } catch (e) {
          console.error("[electron] show_desktop restore failed:", e);
        }
      }, duration * 1000);
    }

    return {
      ok: true,
      platform: process.platform,
      duration_seconds: duration,
      restore_fullscreen: restoreFullscreen,
      minimized_at: new Date().toISOString(),
      restore_scheduled_at: restoreFullscreen
        ? new Date(Date.now() + duration * 1000).toISOString()
        : null,
    };
  },
);

ipcMain.handle("player:restart_app", async () => {
  console.log("[electron] IPC player:restart_app — relaunching");
  setTimeout(() => {
    try {
      app.relaunch();
      app.quit();
    } catch (e) {
      console.error("[electron] relaunch failed:", e);
    }
  }, 500);
  return { ok: true, scheduled_at: new Date().toISOString() };
});

ipcMain.handle("player:restart_device", async () => {
  console.log("[electron] IPC player:restart_device");
  const cmd =
    process.platform === "win32" ? "shutdown /r /t 5" : "shutdown -r +1";
  // Schedula em 500ms para garantir ACK chegou ao backend.
  setTimeout(() => {
    runShell(cmd).catch(() => {});
  }, 500);
  return {
    ok: true,
    platform: process.platform,
    scheduled_at: new Date().toISOString(),
  };
});

ipcMain.handle("player:shutdown_device", async () => {
  console.log("[electron] IPC player:shutdown_device");
  const cmd =
    process.platform === "win32" ? "shutdown /s /t 5" : "shutdown -h +1";
  setTimeout(() => {
    runShell(cmd).catch(() => {});
  }, 500);
  return {
    ok: true,
    platform: process.platform,
    scheduled_at: new Date().toISOString(),
  };
});

ipcMain.handle("player:take_screenshot", async () => {
  if (!mainWindow) throw new Error("no_window");
  const image = await mainWindow.webContents.capturePage();
  return {
    base64: image.toPNG().toString("base64"),
    captured_at: new Date().toISOString(),
  };
});
