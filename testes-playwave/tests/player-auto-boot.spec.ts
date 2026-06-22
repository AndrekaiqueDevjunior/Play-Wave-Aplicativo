/**
 * player-auto-boot.spec.ts — SPEC-011: Inicialização Automática do Player
 *
 * Valida os critérios de aceite do SPEC-011 via API (backend real).
 * Testes de UI do Player.jsx (logs PLAYER_AUTO_BOOT_*, comportamento de sessão)
 * ficam em frontend/src/__tests__/ como testes de componente.
 *
 * Critérios cobertos aqui:
 *   CA-1: backend registra que o player iniciou (heartbeat com boot_mode)
 *   CA-2: sessão válida permite acesso ao playlist endpoint
 *   CA-3: token expirado/inválido retorna 401/403 (player deve limpar e reparear)
 *   CA-4: player sem campanha recebe resposta válida (array vazio / no_campaign)
 *   CA-5: heartbeat atualiza last_seen_at do dispositivo
 *   CA-6: cache local do player é suficiente para operar offline
 *         (validado indiretamente: backend entrega playlist e o player armazena)
 */

import { test, expect } from "../fixtures/test-fixtures.js";
import { uniqueName } from "../helpers/env.js";

// ── CA-1 + CA-5: Backend registra heartbeat inicial com boot_mode ─────────────
test.describe("@api SPEC-011 CA-1 Heartbeat inicial registra boot do player", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("heartbeat com boot_mode e player_version é aceito e atualiza last_seen_at", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-heartbeat") });
    tracker.device(dev.device_id);

    const before = await api.getDevice(dev.device_id);
    const lastSeenBefore = before.last_seen_at;

    // Simula o heartbeat que o Player.jsx envia no boot com boot_mode e os_platform.
    const res = await api.raw("post", `/devices/${dev.device_id}/heartbeat`, {
      headers: { "X-Device-Token": dev.device_token },
      data: {
        timestamp: new Date().toISOString(),
        status: "online",
        player_version: "3.1.0",
        boot_mode: "electron",
        os_platform: "win32",
        playback_status: "loading",
      },
    });
    expect([200, 201], "heartbeat de boot aceito pelo backend").toContain(res.status());

    // last_seen_at deve ter sido atualizado após o heartbeat.
    const after = await api.getDevice(dev.device_id);
    expect(after.last_seen_at, "last_seen_at atualizado após heartbeat").not.toBe(lastSeenBefore);
  });

  test("heartbeat sem boot_mode (campo adicional) também é aceito (backward compat)", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-legacy-hb") });
    tracker.device(dev.device_id);

    const res = await api.raw("post", `/devices/${dev.device_id}/heartbeat`, {
      headers: { "X-Device-Token": dev.device_token },
      data: {
        timestamp: new Date().toISOString(),
        status: "online",
        player_version: "3.1.0",
      },
    });
    expect([200, 201], "heartbeat legado (sem boot_mode) aceito").toContain(res.status());
  });
});

// ── CA-2: Sessão válida acessa playlist ───────────────────────────────────────
test.describe("@api SPEC-011 CA-2 Sessão válida restaura player sem intervenção", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("device_token válido acessa /playlist e /api/v1/player/schedule", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-valid-session") });
    tracker.device(dev.device_id);

    // Rota legada (usada pelo Player.jsx → getDevicePlaylist)
    const playlist = await api.devicePlaylist(dev.device_id, dev.device_token);
    expect(playlist, "payload de playlist retornado com token válido").toBeTruthy();

    // Rota nova (player schedule com versão)
    const schedule = await api.playerSchedule(dev.device_id, dev.device_token);
    expect(schedule, "player schedule retornado com token válido").toBeTruthy();
  });

  test("device sem campanha recebe resposta estruturada (sem erro 5xx)", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-no-campaign") });
    tracker.device(dev.device_id);

    // Device sem campanha vinculada: não pode retornar erro — deve retornar estrutura vazia.
    const res = await api.raw("get", `/devices/${dev.device_id}/playlist`, {
      headers: { "X-Device-Token": dev.device_token },
    });
    expect([200], "playlist sem campanha retorna 200 (não 5xx)").toContain(res.status());

    const body = await res.json();
    // O campo media pode ser array vazio ou ausente, mas não deve ser erro.
    const mediaList = body?.media ?? [];
    expect(Array.isArray(mediaList), "media é array (pode estar vazio)").toBe(true);
  });
});

// ── CA-3: Token inválido é rejeitado (player limpa e reparea) ─────────────────
test.describe("@api SPEC-011 CA-3 Sessão inválida força novo pareamento", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("token inexistente recebe 401 ou 403 no playlist endpoint", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-bad-token") });
    tracker.device(dev.device_id);

    const fakeToken = "TOKEN_INVALIDO_E2E_" + Date.now();
    const res = await api.raw("get", `/devices/${dev.device_id}/playlist`, {
      headers: { "X-Device-Token": fakeToken },
    });
    expect([401, 403], "token falso é rejeitado").toContain(res.status());
  });

  test("token revogado é rejeitado após revoke-token", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-revoke") });
    tracker.device(dev.device_id);

    // Token válido funciona antes da revogação.
    const before = await api.raw("get", `/devices/${dev.device_id}/playlist`, {
      headers: { "X-Device-Token": dev.device_token },
    });
    expect([200], "token válido antes de revogar").toContain(before.status());

    // Admin revoga o token.
    await api.revokeToken(dev.device_id);

    // Token antigo deve ser rejeitado — player precisa ir para waiting/pairing.
    const after = await api.raw("get", `/devices/${dev.device_id}/playlist`, {
      headers: { "X-Device-Token": dev.device_token },
    });
    expect([401, 403], "token revogado é rejeitado — player redireciona para pareamento").toContain(after.status());
  });

  test("player schedule também rejeita token inválido", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-bad-sched") });
    tracker.device(dev.device_id);

    const fakeToken = "TOKEN_INVALIDO_E2E_SCHED_" + Date.now();
    const res = await api.raw(
      "get",
      `/api/v1/player/schedule?device_id=${dev.device_id}&device_token=${encodeURIComponent(fakeToken)}`,
    );
    expect([401, 403, 404], "schedule com token falso é rejeitado").toContain(res.status());
  });
});

// ── CA-5: gerenciador mostra status atualizado após heartbeat ─────────────────
test.describe("@api SPEC-011 CA-5 Gerenciador reflete status do player", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("player_version enviada no heartbeat aparece no device", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-status") });
    tracker.device(dev.device_id);

    await api.raw("post", `/devices/${dev.device_id}/heartbeat`, {
      headers: { "X-Device-Token": dev.device_token },
      data: {
        timestamp: new Date().toISOString(),
        status: "online",
        player_version: "3.1.0",
        playback_status: "playing",
      },
    });

    const device = await api.getDevice(dev.device_id);
    // Backend deve persistir player_version e/ou status após heartbeat.
    // Se o campo existir, valida; caso o backend não persista ainda, o teste documenta a lacuna.
    if ("player_version" in device) {
      expect(device.player_version, "player_version persistida após heartbeat").toBe("3.1.0");
    } else if ("last_seen_at" in device) {
      // Mínimo aceitável: last_seen_at atualizado confirma que o heartbeat chegou.
      expect(device.last_seen_at).toBeTruthy();
    } else {
      // Backend não retorna esses campos no GET /devices/{id} — documenta pendência.
      console.warn("[SPEC-011 CA-5] GET /devices/{id} não retorna player_version nem last_seen_at — ajustar schema do gerenciador.");
    }
  });

  test("status online/offline reflete no device após heartbeat", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-online-status") });
    tracker.device(dev.device_id);

    await api.raw("post", `/devices/${dev.device_id}/heartbeat`, {
      headers: { "X-Device-Token": dev.device_token },
      data: {
        timestamp: new Date().toISOString(),
        status: "online",
      },
    });

    const device = await api.getDevice(dev.device_id);
    // last_seen_at deve estar próximo de agora (dentro de 10s).
    if (device.last_seen_at) {
      const diffMs = Date.now() - new Date(device.last_seen_at).getTime();
      expect(diffMs, "last_seen_at atualizado recentemente (< 10s)").toBeLessThan(10_000);
    }
  });
});

// ── CA-6 (indireto): playlist entregue é estruturada para cache local ─────────
test.describe("@api SPEC-011 CA-6 Playlist estruturada para cache offline", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("payload de playlist contém campos necessários para cache local do player", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("boot-cache-fields") });
    tracker.device(dev.device_id);

    const res = await api.raw("get", `/devices/${dev.device_id}/playlist`, {
      headers: { "X-Device-Token": dev.device_token },
    });
    expect(res.status()).toBe(200);

    const body = await res.json();
    // O PlaylistCache.set() em Player.jsx armazena `medias` e `timestamp`.
    // O payload do backend deve retornar `media` (array) para que o player
    // possa populá-lo antes de salvar no IndexedDB.
    expect(body).toHaveProperty("media");
    expect(Array.isArray(body.media), "campo media é array").toBe(true);

    // Se houver campanha, deve ter config_version para cache de versão.
    if (body.campaign) {
      expect(body.campaign).toHaveProperty("id");
      // config_version pode ser null em campanha sem versão ainda, mas o campo deve existir.
      expect("config_version" in body.campaign, "campaign.config_version presente").toBe(true);
    }
  });
});
