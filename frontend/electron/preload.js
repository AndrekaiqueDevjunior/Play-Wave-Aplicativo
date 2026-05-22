/**
 * preload.js — Ponte segura entre renderer e processo principal.
 * contextIsolation: true, nodeIntegration: false
 *
 * SPEC 003 — expõe `window.__ELECTRON__.player` como objeto real com métodos
 * para o motor de comandos (`player-core/commands.js`) conseguir invocar
 * restart/shutdown/screenshot nativos via IPC.
 *
 * Antes desta SPEC, o main.js injetava `window.__ELECTRON__ = true` (boolean),
 * o que fazia `__ELECTRON__?.player?.shutdownDevice` ser undefined → todo
 * comando de energia falhava silenciosamente em "platform_unsupported".
 */

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("__ELECTRON__", {
  platform: process.platform,
  versions: {
    electron: process.versions.electron,
    node:     process.versions.node,
  },

  player: {
    restartApp:       () => ipcRenderer.invoke("player:restart_app"),
    restartDevice:    () => ipcRenderer.invoke("player:restart_device"),
    shutdownDevice:   () => ipcRenderer.invoke("player:shutdown_device"),
    takeScreenshot:   () => ipcRenderer.invoke("player:take_screenshot"),
    fullscreenToggle: () => ipcRenderer.send("player:fullscreen-toggle"),
  },
});

// Compat — bridge legada usada por código antigo que possa existir.
contextBridge.exposeInMainWorld("electronBridge", {
  platform: process.platform,
  restart:          () => ipcRenderer.send("player:restart"),
  toggleFullscreen: () => ipcRenderer.send("player:fullscreen-toggle"),
  onCommand:        (callback) =>
    ipcRenderer.on("remote:command", (_, cmd) => callback(cmd)),
});
