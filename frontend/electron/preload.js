/**
 * preload.js — Ponte segura entre renderer e processo principal.
 * contextIsolation: true, nodeIntegration: false
 */

const { contextBridge, ipcRenderer } = require("electron");

// Ler config.json de forma defensiva
let backendUrl = "http://localhost:8000";
let prepairedDeviceId   = null;
let prepairedToken      = null;
let prepairedCode       = null;
let prepairedTokenVersion = null;

try {
  const path = require("path");
  const fs = require("fs");
  const configPath = path.join(__dirname, "config.json");
  if (fs.existsSync(configPath)) {
    const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
    if (config.backend_url)    backendUrl          = config.backend_url;
    if (config.device_id)      prepairedDeviceId   = String(config.device_id);
    if (config.device_token)   prepairedToken      = config.device_token;
    if (config.device_code)    prepairedCode       = config.device_code;
    if (config.token_version != null) prepairedTokenVersion = config.token_version;
  }
} catch (err) {
  // Ignora falhas ao ler config — usa padrão localhost:8000
}

// Expor API principal para o renderer
try {
  contextBridge.exposeInMainWorld("__ELECTRON__", {
    backendUrl,
    // Credenciais pré-pareadas vindas do config.json (opcionais).
    // O Player.jsx lê via window.__ELECTRON__.prepaired e pré-popula o
    // localStorage para pular a tela de pareamento completamente.
    prepaired: (prepairedDeviceId && prepairedToken) ? {
      device_id:     prepairedDeviceId,
      device_token:  prepairedToken,
      device_code:   prepairedCode,
      token_version: prepairedTokenVersion,
    } : null,
    platform: process.platform,
    versions: {
      electron: process.versions.electron,
      node: process.versions.node,
    },
    notifyPaired: () => ipcRenderer.send("player:paired"),
    player: {
      restartApp:      () => ipcRenderer.invoke("player:restart_app"),
      minimizeWindow:  () => ipcRenderer.invoke("player:minimize_window"),
      restoreWindow:   () => ipcRenderer.invoke("player:restore_window"),
      showDesktop:     (durationSeconds, restoreFullscreen = true) =>
        ipcRenderer.invoke("player:show_desktop", durationSeconds, restoreFullscreen),
      restartDevice:   () => ipcRenderer.invoke("player:restart_device"),
      shutdownDevice:  () => ipcRenderer.invoke("player:shutdown_device"),
      takeScreenshot:  () => ipcRenderer.invoke("player:take_screenshot"),
      fullscreenToggle: () => ipcRenderer.send("player:fullscreen-toggle"),
    },
  });
} catch (err) {
  console.error("[preload] contextBridge.__ELECTRON__ falhou:", err);
}

// Bridge legada para compatibilidade com código antigo
try {
  contextBridge.exposeInMainWorld("electronBridge", {
    platform: process.platform,
    restart: () => ipcRenderer.send("player:restart"),
    toggleFullscreen: () => ipcRenderer.send("player:fullscreen-toggle"),
    onCommand: (callback) =>
      ipcRenderer.on("remote:command", (_, cmd) => callback(cmd)),
  });
} catch (err) {
  console.error("[preload] contextBridge.electronBridge falhou:", err);
}
