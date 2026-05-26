/**
 * Extensões de tipos para window global
 * Define interfaces para bridges nativos de plataformas
 */

interface PlayWaveNativeBridge {
  shutdownDevice: () => Promise<void>;
  restartDevice: () => Promise<void>;
  restartApp: () => Promise<void>;
  takeScreenshot: () => Promise<string>;
}

interface AndroidPlayerBridge {
  shutdownDevice: () => Promise<void>;
  restartDevice: () => Promise<void>;
  restartApp: () => Promise<void>;
  takeScreenshot: () => Promise<string>;
}

interface ElectronPlayerBridge {
  player?: {
    shutdownDevice: () => Promise<void>;
    restartDevice: () => Promise<void>;
    restartApp: () => Promise<void>;
    takeScreenshot: () => Promise<string>;
  };
}

declare global {
  interface Window {
    PlayWaveNative?: PlayWaveNativeBridge;
    AndroidPlayer?: AndroidPlayerBridge;
    __ELECTRON__?: ElectronPlayerBridge;
  }
}

export {};
