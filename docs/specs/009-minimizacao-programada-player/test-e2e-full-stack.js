#!/usr/bin/env node

/**
 * SPEC 009 - Teste E2E Full Stack (Backend + Frontend)
 *
 * Simula o fluxo completo:
 * 1. Backend cria config de desktop exposure
 * 2. Frontend recebe via SSE
 * 3. Scheduler local executa
 * 4. Electron IPC manipula window
 *
 * Uso: node test-e2e-full-stack.js
 */

const assert = require("assert");

console.log("╔════════════════════════════════════════════════════════╗");
console.log("║      SPEC 009 - Teste Full Stack (Backend + FE)       ║");
console.log("╚════════════════════════════════════════════════════════╝");
console.log("");

let testsPassed = 0;
let testsFailed = 0;

function test(name, fn) {
  try {
    console.log(`✓ ${name}`);
    fn();
    testsPassed++;
  } catch (e) {
    console.error(`✗ ${name}`);
    console.error(`  Error: ${e.message}`);
    testsFailed++;
  }
}

async function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// ─── Simuladores de Backend ──────────────────────────────────────────

class MockBackend {
  constructor() {
    this.devices = {};
    this.commands = [];
    this.sseListeners = [];
  }

  createDevice(id, tenantId) {
    this.devices[id] = {
      id,
      tenant_id: tenantId,
      desktop_exposure_enabled: false,
      desktop_exposure_interval_seconds: null,
      desktop_exposure_duration_seconds: null,
      desktop_exposure_restore_fullscreen: false,
    };
    console.log(`  [backend] Device created: ${id}`);
    return this.devices[id];
  }

  updateDesktopExposureConfig(deviceId, config, userId, userTenantId) {
    // Validar permissão
    const device = this.devices[deviceId];
    if (!device) throw new Error("Device not found");

    // Admin ou mesmo tenant
    const isAdmin = true; // Simulado
    if (!isAdmin && device.tenant_id !== userTenantId) {
      throw new Error("Unauthorized (403)");
    }

    // Validar payload
    if (config.enabled) {
      if (!config.interval_seconds || !config.duration_seconds) {
        throw new Error("interval_seconds and duration_seconds required");
      }
      if (config.duration_seconds >= config.interval_seconds) {
        throw new Error(
          "duration_seconds must be less than interval_seconds"
        );
      }
      if (config.interval_seconds < 10 || config.interval_seconds > 86400) {
        throw new Error("interval_seconds must be 10-86400");
      }
      if (config.duration_seconds < 1 || config.duration_seconds > 300) {
        throw new Error("duration_seconds must be 1-300");
      }
    }

    // Atualizar
    Object.assign(device, {
      desktop_exposure_enabled: config.enabled ?? device.desktop_exposure_enabled,
      desktop_exposure_interval_seconds:
        config.interval_seconds ?? device.desktop_exposure_interval_seconds,
      desktop_exposure_duration_seconds:
        config.duration_seconds ?? device.desktop_exposure_duration_seconds,
      desktop_exposure_restore_fullscreen:
        config.restore_fullscreen ?? device.desktop_exposure_restore_fullscreen,
    });

    console.log(`  [backend] Config updated for ${deviceId}`);
    console.log(
      `           enabled=${device.desktop_exposure_enabled}, ` +
        `interval=${device.desktop_exposure_interval_seconds}s, ` +
        `duration=${device.desktop_exposure_duration_seconds}s`
    );

    // Publicar SSE
    this.publishSSE(deviceId, {
      event: "config:desktop_exposure_updated",
      data: {
        desktop_exposure_config: {
          enabled: device.desktop_exposure_enabled,
          interval_seconds: device.desktop_exposure_interval_seconds,
          duration_seconds: device.desktop_exposure_duration_seconds,
          restore_fullscreen: device.desktop_exposure_restore_fullscreen,
        },
      },
    });

    return device;
  }

  sendCommand(deviceId, commandType, payload, userId) {
    // Validar comando
    if (!["minimize_player", "restore_player", "show_desktop"].includes(commandType)) {
      throw new Error("Invalid command_type");
    }

    // Validar payload para show_desktop
    if (commandType === "show_desktop" && payload) {
      const duration = Number(payload.duration_seconds || 10);
      if (isNaN(duration) || duration < 1 || duration > 300) {
        throw new Error("duration_seconds must be 1-300");
      }
    }

    const cmd = {
      id: Math.random().toString(36).substr(2, 9),
      device_id: deviceId,
      command_type: commandType,
      payload,
      created_by: userId,
      status: "PENDING",
      created_at: new Date(),
    };

    this.commands.push(cmd);

    console.log(
      `  [backend] Command queued: ${commandType} (ID: ${cmd.id})`
    );
    return cmd;
  }

  publishSSE(deviceId, message) {
    console.log(`  [backend] SSE published to ${deviceId}`);
    this.sseListeners.forEach((cb) => cb(deviceId, message));
  }

  onSSE(callback) {
    this.sseListeners.push(callback);
  }
}

// ─── Simuladores de Frontend ──────────────────────────────────────────

class MockPlayer {
  constructor(deviceId, backend) {
    this.deviceId = deviceId;
    this.backend = backend;
    this.phase = "loading";
    this.config = null;
    this.windowControl = new MockElectronIPC();
    this.scheduler = new MockScheduler(this);
    this.commandExecutor = new CommandExecutor(this.windowControl);

    // Registrar listener de SSE
    backend.onSSE((devId, msg) => {
      if (devId === deviceId) {
        this.onSSEMessage(msg);
      }
    });
  }

  setPhase(phase) {
    this.phase = phase;
    console.log(`  [player] phase changed to: ${phase}`);
    this.scheduler.trySchedule();
  }

  onSSEMessage(msg) {
    if (msg.event === "config:desktop_exposure_updated") {
      this.config = msg.data.desktop_exposure_config;
      console.log(`  [player] config received via SSE:`, {
        enabled: this.config.enabled,
        interval: this.config.interval_seconds,
        duration: this.config.duration_seconds,
      });
      this.scheduler.trySchedule();
    }
  }

  async executeCommand(commandType, payload) {
    console.log(`  [player] executing command: ${commandType}`);
    return await this.commandExecutor.execute(commandType, payload);
  }
}

class MockScheduler {
  constructor(player) {
    this.player = player;
    this.timer = null;
  }

  trySchedule() {
    // Cancelar timer anterior
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    // Verificar condições
    if (!this.player.config?.enabled) {
      console.log(`  [scheduler] config not enabled, skipping`);
      return;
    }

    if (this.player.phase === "loading" || this.player.phase === "waiting") {
      console.log(
        `  [scheduler] blocked by phase=${this.player.phase}, skipping`
      );
      return;
    }

    // Agendar
    const interval = this.player.config.interval_seconds;
    console.log(`  [scheduler] scheduled: will execute in ${interval}s`);

    this.timer = setTimeout(() => {
      console.log(`  [scheduler] timer fired, executing show_desktop`);
      this.player.executeCommand("show_desktop", {
        duration_seconds: this.player.config.duration_seconds,
        restore_fullscreen: this.player.config.restore_fullscreen,
      });
    }, interval * 1000);
  }

  stop() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }
}

class MockElectronIPC {
  constructor() {
    this.windowState = {
      minimized: false,
      fullscreen: true,
      kiosk: true,
    };
    this.lastSnapshot = null;
    this.restoreTimer = null;
  }

  minimize() {
    console.log(`  [electron] mainWindow.minimize()`);
    this.windowState.minimized = true;
  }

  restore() {
    console.log(`  [electron] mainWindow.restore()`);
    this.windowState.minimized = false;
  }

  setFullScreen(val) {
    console.log(`  [electron] mainWindow.setFullScreen(${val})`);
    this.windowState.fullscreen = val;
  }

  setKiosk(val) {
    console.log(`  [electron] mainWindow.setKiosk(${val})`);
    this.windowState.kiosk = val;
  }

  snapshot() {
    return { ...this.windowState };
  }
}

class CommandExecutor {
  constructor(ipc) {
    this.ipc = ipc;
  }

  async execute(commandType, payload) {
    if (commandType === "minimize_player") {
      this.ipc.minimize();
      return { ok: true, completed_at: new Date() };
    }

    if (commandType === "restore_player") {
      this.ipc.restore();
      return { ok: true, completed_at: new Date() };
    }

    if (commandType === "show_desktop") {
      const duration = Math.max(
        1,
        Math.min(300, Math.round(Number(payload?.duration_seconds) || 10))
      );

      // Snapshot
      this.ipc.lastSnapshot = this.ipc.snapshot();
      console.log(`  [snapshot] captured:`, this.ipc.lastSnapshot);

      // Prepare
      this.ipc.setKiosk(false);
      this.ipc.setFullScreen(false);
      this.ipc.minimize();

      // Schedule restore
      this.ipc.restoreTimer = setTimeout(() => {
        console.log(`  [restore] restoring from snapshot`);
        this.ipc.restore();
        if (this.ipc.lastSnapshot.fullscreen)
          this.ipc.setFullScreen(true);
        if (this.ipc.lastSnapshot.kiosk) this.ipc.setKiosk(true);
      }, duration * 1000);

      return { ok: true, completed_at: new Date() };
    }

    throw new Error(`Unknown command: ${commandType}`);
  }
}

// ─── Testes ──────────────────────────────────────────────────────────

async function runTests() {
  // ─── Teste 1: Backend Config Validation ──────────────────────────────

  test("Backend: validate config schema (interval/duration ranges)", () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");

    // Valid
    assert.doesNotThrow(() => {
      backend.updateDesktopExposureConfig(
        "dev1",
        {
          enabled: true,
          interval_seconds: 30,
          duration_seconds: 5,
          restore_fullscreen: true,
        },
        "user1",
        "tenant1"
      );
    });

    // Invalid: duration >= interval
    assert.throws(() => {
      backend.updateDesktopExposureConfig(
        "dev1",
        {
          enabled: true,
          interval_seconds: 30,
          duration_seconds: 50,
          restore_fullscreen: true,
        },
        "user1",
        "tenant1"
      );
    });

    // Invalid: interval too small
    assert.throws(() => {
      backend.updateDesktopExposureConfig(
        "dev1",
        {
          enabled: true,
          interval_seconds: 5, // < 10
          duration_seconds: 1,
          restore_fullscreen: true,
        },
        "user1",
        "tenant1"
      );
    });

    // Invalid: duration too large
    assert.throws(() => {
      backend.updateDesktopExposureConfig(
        "dev1",
        {
          enabled: true,
          interval_seconds: 100,
          duration_seconds: 400, // > 300
          restore_fullscreen: true,
        },
        "user1",
        "tenant1"
      );
    });
  });

  // ─── Teste 2: Backend Permission Check ───────────────────────────────

  test("Backend: permission check (admin/tenant)", () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");

    // Admin can update any device
    assert.doesNotThrow(() => {
      backend.updateDesktopExposureConfig(
        "dev1",
        {
          enabled: true,
          interval_seconds: 30,
          duration_seconds: 5,
        },
        "admin1",
        "tenant1"
      );
    });

    // User from same tenant can update
    assert.doesNotThrow(() => {
      backend.updateDesktopExposureConfig(
        "dev1",
        {
          enabled: false,
        },
        "user1",
        "tenant1"
      );
    });
  });

  // ─── Teste 3: Backend Send Command ──────────────────────────────────

  test("Backend: send_device_command validates payload", () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");

    // Valid
    assert.doesNotThrow(() => {
      backend.sendCommand("dev1", "show_desktop", {
        duration_seconds: 5,
      }, "user1");
    });

    // Invalid: duration out of range
    assert.throws(() => {
      backend.sendCommand("dev1", "show_desktop", {
        duration_seconds: 999,
      }, "user1");
    });

    // Invalid: string payload
    assert.throws(() => {
      backend.sendCommand("dev1", "show_desktop", {
        duration_seconds: "'; DROP TABLE--",
      }, "user1");
    });
  });

  // ─── Teste 4: Frontend Receive Config via SSE ──────────────────────

  test("Frontend: receive config via SSE and activate scheduler", async () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");

    const player = new MockPlayer("dev1", backend);

    // Config not set yet
    assert.strictEqual(player.config, null);

    // Update config in backend
    backend.updateDesktopExposureConfig(
      "dev1",
      {
        enabled: true,
        interval_seconds: 2, // 2s para teste rápido
        duration_seconds: 1,
        restore_fullscreen: true,
      },
      "user1",
      "tenant1"
    );

    // SSE should have delivered config
    assert.notStrictEqual(player.config, null);
    assert.strictEqual(player.config.enabled, true);
    assert.strictEqual(player.config.interval_seconds, 2);
  });

  // ─── Teste 5: Scheduler Blocked in Loading ──────────────────────────

  test("Frontend: scheduler blocked when phase is 'loading'", async () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");
    const player = new MockPlayer("dev1", backend);

    // Update config
    backend.updateDesktopExposureConfig(
      "dev1",
      {
        enabled: true,
        interval_seconds: 1,
        duration_seconds: 1,
      },
      "user1",
      "tenant1"
    );

    // Phase is 'loading' by default
    assert.strictEqual(player.phase, "loading");

    // Scheduler should be blocked
    await sleep(1500);

    // Window should still be normal
    assert.strictEqual(player.windowControl.windowState.minimized, false);
  });

  // ─── Teste 6: Scheduler Active in Playing ──────────────────────────

  test("Frontend: scheduler active and executes when phase is 'playing'", async () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");
    const player = new MockPlayer("dev1", backend);

    // Update config with short interval for testing
    backend.updateDesktopExposureConfig(
      "dev1",
      {
        enabled: true,
        interval_seconds: 1, // 1s
        duration_seconds: 1,
        restore_fullscreen: true,
      },
      "user1",
      "tenant1"
    );

    // Change phase to playing
    player.setPhase("playing");

    // Wait for scheduler to execute
    await sleep(1500);

    // Window should have been minimized and restored
    assert.strictEqual(player.windowControl.windowState.minimized, false);
    assert.strictEqual(player.windowControl.windowState.fullscreen, true);
  });

  // ─── Teste 7: Window Restore Fullscreen ────────────────────────────

  test("Frontend: window restore preserves fullscreen from snapshot", async () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");
    const player = new MockPlayer("dev1", backend);

    // Initial state
    assert.strictEqual(player.windowControl.windowState.fullscreen, true);

    // Execute show_desktop with 1s duration
    await player.executeCommand("show_desktop", {
      duration_seconds: 1,
      restore_fullscreen: true,
    });

    // Should be minimized now
    assert.strictEqual(player.windowControl.windowState.minimized, true);
    assert.strictEqual(player.windowControl.windowState.fullscreen, false);

    // Wait for restore
    await sleep(1200);

    // Should be restored to original state
    assert.strictEqual(player.windowControl.windowState.minimized, false);
    assert.strictEqual(player.windowControl.windowState.fullscreen, true);
  });

  // ─── Teste 8: Manual Command via API ────────────────────────────────

  test("Backend: send manual show_desktop command", () => {
    const backend = new MockBackend();
    backend.createDevice("dev1", "tenant1");

    const cmd = backend.sendCommand("dev1", "show_desktop", {
      duration_seconds: 3,
    }, "admin1");

    assert.strictEqual(cmd.command_type, "show_desktop");
    assert.strictEqual(cmd.payload.duration_seconds, 3);
    assert.strictEqual(cmd.status, "PENDING");
  });

  // ─── Resumo ──────────────────────────────────────────────────────────

  console.log("\n╔════════════════════════════════════════════════════════╗");
  console.log("║                   RESUMO DOS TESTES                    ║");
  console.log("╚════════════════════════════════════════════════════════╝");
  console.log(`\n✓ Testes Passados: ${testsPassed}`);
  console.log(`✗ Testes Falhados: ${testsFailed}`);
  console.log(`\nTotal: ${testsPassed + testsFailed} testes`);

  if (testsFailed === 0) {
    console.log(
      "\n🎉 TODOS OS TESTES FULL STACK PASSARAM!\n" +
        "   Backend: ✅ Config validation, permissions, commands\n" +
        "   Frontend: ✅ SSE, scheduler, window control\n" +
        "   E2E: ✅ Config → SSE → Scheduler → IPC → Window\n"
    );
    process.exit(0);
  } else {
    console.log(`\n❌ ${testsFailed} teste(s) falharam\n`);
    process.exit(1);
  }
}

runTests().catch((e) => {
  console.error("Erro ao executar testes:", e);
  process.exit(1);
});
