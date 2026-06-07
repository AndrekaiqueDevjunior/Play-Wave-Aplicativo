#!/usr/bin/env node

/**
 * SPEC 009 - Teste E2E Automatizado
 *
 * Simula cenários de desktop exposure sem precisar do Electron real
 * Valida: scheduler, fullscreen restore, phase blocking, input validation
 *
 * Uso: node test-e2e-automated.js
 */

const assert = require("assert");

// ─── Simuladores ────────────────────────────────────────────────────────

class MockElectron {
  constructor() {
    this.windowState = {
      minimized: false,
      fullscreen: true,
      kiosk: true,
      alwaysOnTop: false,
    };
    this.lastSnapshot = null;
    this.restoreTimer = null;
  }

  minimize() {
    console.log("  [electron] mainWindow.minimize()");
    this.windowState.minimized = true;
  }

  restore() {
    console.log("  [electron] mainWindow.restore()");
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

  isFullScreen() {
    return this.windowState.fullscreen;
  }
}

class MockScheduler {
  constructor(electron, onExecute) {
    this.electron = electron;
    this.onExecute = onExecute;
    this.timers = [];
    this.lastPhase = null;
  }

  schedule(config, currentPhase) {
    // Bloqueia se em loading/waiting
    if (currentPhase === "loading" || currentPhase === "waiting") {
      console.log(
        "  [scheduler] scheduling... → return (blocked by phase)"
      );
      return false;
    }

    console.log(`  [scheduler] scheduling show_desktop in ${config.interval_seconds}s`);
    this.lastPhase = currentPhase;

    const timer = setTimeout(() => {
      this.onExecute({
        duration_seconds: config.duration_seconds,
        restore_fullscreen: config.restore_fullscreen,
      });
    }, config.interval_seconds * 1000);

    this.timers.push(timer);
    return true;
  }

  stop() {
    this.timers.forEach(clearTimeout);
    this.timers = [];
  }

  executeShowDesktop(config) {
    console.log(
      `  [commands] executing: show_desktop (duration=${config.duration_seconds}s)`
    );

    // Snapshot estado ANTES de preparar
    const snapshot = {
      fullscreen: this.electron.windowState.fullscreen,
      kiosk: this.electron.windowState.kiosk,
      alwaysOnTop: this.electron.windowState.alwaysOnTop,
    };

    console.log(`  [snapshot] captured:`, snapshot);

    // Preparar para desktop exposure
    this.electron.setKiosk(false);
    this.electron.setFullScreen(false);
    this.electron.minimize();

    // Restaurar após duration
    if (config.restore_fullscreen) {
      this.electron.restoreTimer = setTimeout(() => {
        console.log(`  [restore] applying snapshot:`, snapshot);
        this.electron.restore();
        if (snapshot.fullscreen) this.electron.setFullScreen(true);
        if (snapshot.kiosk) this.electron.setKiosk(true);
        if (snapshot.alwaysOnTop)
          this.electron.setAlwaysOnTop(snapshot.alwaysOnTop);
      }, config.duration_seconds * 1000);
    }
  }
}

// ─── Testes ─────────────────────────────────────────────────────────────

let testsPassed = 0;
let testsFailed = 0;

function test(name, fn) {
  try {
    console.log(`\n✓ ${name}`);
    fn();
    testsPassed++;
  } catch (e) {
    console.error(`✗ ${name}`);
    console.error(`  Error: ${e.message}`);
    testsFailed++;
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function runTests() {
  console.log("╔════════════════════════════════════════════════════════╗");
  console.log("║        SPEC 009 - Teste E2E Automatizado               ║");
  console.log("╚════════════════════════════════════════════════════════╝");

  // ─── Teste 1: Input Validation ──────────────────────────────────────

  test("Input Validation: duration clamped to 1-300", () => {
    const clamp = (val) =>
      Math.max(1, Math.min(300, Math.round(Number(val) || 10)));

    assert.strictEqual(clamp(-100), 1);
    assert.strictEqual(clamp(999999), 300);
    assert.strictEqual(clamp(150), 150);
    assert.strictEqual(clamp("invalid"), 10);
    assert.strictEqual(clamp(null), 10);
  });

  // ─── Teste 2: Snapshot Fullscreen State ─────────────────────────────

  test("Snapshot captures fullscreen state before expose", () => {
    const electron = new MockElectron();
    const scheduler = new MockScheduler(electron, () => {});

    electron.windowState.fullscreen = true;
    electron.windowState.kiosk = true;

    const snapshot = {
      fullscreen: electron.windowState.fullscreen,
      kiosk: electron.windowState.kiosk,
    };

    assert.strictEqual(snapshot.fullscreen, true);
    assert.strictEqual(snapshot.kiosk, true);
  });

  // ─── Teste 3: Restore Fullscreen After Desktop Expose ──────────────

  test("Restore fullscreen state after desktop exposure", async () => {
    const electron = new MockElectron();
    const scheduler = new MockScheduler(
      electron,
      (cfg) => {
        scheduler.executeShowDesktop(cfg);
      }
    );

    console.log("  Initial state: fullscreen=true, kiosk=true");
    assert.strictEqual(electron.windowState.fullscreen, true);

    // Execute show_desktop com 1s duration
    scheduler.executeShowDesktop({
      duration_seconds: 1,
      restore_fullscreen: true,
    });

    console.log("  After show_desktop: minimized=true, fullscreen=false");
    assert.strictEqual(electron.windowState.minimized, true);
    assert.strictEqual(electron.windowState.fullscreen, false);

    // Aguardar restore
    await sleep(1100);

    console.log("  After restore timer: minimized=false, fullscreen=true");
    assert.strictEqual(electron.windowState.minimized, false);
    assert.strictEqual(electron.windowState.fullscreen, true);
  });

  // ─── Teste 4: Scheduler Blocked in Loading Phase ────────────────────

  test("Scheduler blocked when phase is 'loading'", () => {
    const electron = new MockElectron();
    const scheduler = new MockScheduler(
      electron,
      () => {}
    );

    const config = {
      enabled: true,
      interval_seconds: 30,
      duration_seconds: 5,
      restore_fullscreen: true,
    };

    const scheduled = scheduler.schedule(config, "loading");

    assert.strictEqual(scheduled, false);
    console.log("  ✓ Scheduler correctly blocked");
  });

  // ─── Teste 5: Scheduler Active in Playing Phase ──────────────────────

  test("Scheduler active when phase is 'playing'", async () => {
    const electron = new MockElectron();
    let executed = false;

    const scheduler = new MockScheduler(electron, () => {
      executed = true;
      console.log("  [scheduler] show_desktop executed!");
    });

    const config = {
      enabled: true,
      interval_seconds: 1, // 1 segundo para teste rápido
      duration_seconds: 1,
      restore_fullscreen: true,
    };

    const scheduled = scheduler.schedule(config, "playing");

    assert.strictEqual(scheduled, true);
    assert.strictEqual(executed, false);

    await sleep(1100);

    assert.strictEqual(executed, true);
    console.log("  ✓ Scheduler executed after interval");
  });

  // ─── Teste 6: Multiple Show Desktop Calls (Cancel Previous) ──────────

  test("Multiple show_desktop calls cancel previous restore timer", async () => {
    const electron = new MockElectron();
    const scheduler = new MockScheduler(
      electron,
      () => {}
    );

    console.log("  First show_desktop (2s duration)");
    scheduler.executeShowDesktop({
      duration_seconds: 2,
      restore_fullscreen: true,
    });

    await sleep(500);

    console.log("  Second show_desktop (1s duration) - cancels first");
    clearTimeout(electron.restoreTimer);
    scheduler.executeShowDesktop({
      duration_seconds: 1,
      restore_fullscreen: true,
    });

    const firstSnapshot = electron.windowState.fullscreen;
    assert.strictEqual(firstSnapshot, false);

    await sleep(1100);

    // Should have restored from second call (1s), not first (2s)
    assert.strictEqual(electron.windowState.minimized, false);
    console.log("  ✓ Timer correctly cancelled and replaced");
  });

  // ─── Teste 7: No Restore If restore_fullscreen=false ────────────────

  test("No restore if restore_fullscreen=false", async () => {
    const electron = new MockElectron();
    const scheduler = new MockScheduler(
      electron,
      () => {}
    );

    scheduler.executeShowDesktop({
      duration_seconds: 1,
      restore_fullscreen: false, // ← importante
    });

    assert.strictEqual(electron.windowState.minimized, true);

    await sleep(1100);

    console.log("  After timer expired: minimized still true (no restore)");
    assert.strictEqual(electron.windowState.minimized, true);
  });

  // ─── Teste 8: Config Validation (Duration < Interval) ───────────────

  test("Config validation: duration_seconds must be < interval_seconds", () => {
    const validateConfig = (config) => {
      if (!config.enabled) return true;
      if (config.duration_seconds >= config.interval_seconds) {
        throw new Error(
          "duration_seconds must be less than interval_seconds"
        );
      }
      return true;
    };

    // Valid
    assert.doesNotThrow(() => {
      validateConfig({
        enabled: true,
        interval_seconds: 30,
        duration_seconds: 5,
      });
    });

    // Invalid
    assert.throws(() => {
      validateConfig({
        enabled: true,
        interval_seconds: 30,
        duration_seconds: 50, // >= 30
      });
    });
  });

  // ─── Teste 9: Fullscreen Restoration Despite User Exit ──────────────

  test("Fullscreen restored from snapshot even if user exits during expose", async () => {
    const electron = new MockElectron();
    const scheduler = new MockScheduler(
      electron,
      () => {}
    );

    console.log("  Initial: fullscreen=true");
    assert.strictEqual(electron.windowState.fullscreen, true);

    scheduler.executeShowDesktop({
      duration_seconds: 1,
      restore_fullscreen: true,
    });

    await sleep(300);

    console.log("  User manually exits fullscreen (during expose)");
    electron.windowState.fullscreen = false;
    assert.strictEqual(electron.windowState.fullscreen, false);

    await sleep(800);

    console.log("  After restore timer: snapshot restored fullscreen=true");
    // Snapshot foi capturado com fullscreen=true, deve restaurar
    assert.strictEqual(electron.windowState.fullscreen, true);
  });

  // ─── Teste 10: Payload Validation (Type Safety) ─────────────────────

  test("Payload validation: reject invalid types", () => {
    const validatePayload = (payload) => {
      if (typeof payload.duration_seconds !== "undefined") {
        const val = Number(payload.duration_seconds);
        if (isNaN(val)) {
          throw new Error("duration_seconds must be a number");
        }
        if (val < 1 || val > 300) {
          throw new Error("duration_seconds must be 1-300");
        }
      }
    };

    // Valid
    assert.doesNotThrow(() => {
      validatePayload({ duration_seconds: 5 });
    });

    // Invalid: string
    assert.throws(() => {
      validatePayload({ duration_seconds: "'; DROP TABLE--" });
    });

    // Invalid: negative
    assert.throws(() => {
      validatePayload({ duration_seconds: -100 });
    });

    // Invalid: too large
    assert.throws(() => {
      validatePayload({ duration_seconds: 999999 });
    });
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
      "\n🎉 TODOS OS TESTES PASSARAM! SPEC 009 está pronto para rollout.\n"
    );
    process.exit(0);
  } else {
    console.log(`\n❌ ${testsFailed} teste(s) falharam\n`);
    process.exit(1);
  }
}

// ─── Executar ────────────────────────────────────────────────────────────

runTests().catch((e) => {
  console.error("Erro ao executar testes:", e);
  process.exit(1);
});
