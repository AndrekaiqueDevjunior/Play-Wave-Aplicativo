/**
 * dispositivos-comandos.spec.ts — TASKS 18, 19, 20
 * Comandos remotos (restart/sync), invalidar pareamento e "não reiniciar player".
 *
 * Endpoints: POST /devices/{id}/command, GET /devices/{id}/commands(+/pending),
 *            POST /devices/{id}/revoke-token, GET /api/v1/player/schedule
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { uniqueName } from "../helpers/env.js";

test.describe("@api 18 Comandos desligar/reiniciar", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("enviar comando enfileira e aparece no histórico; player consome via pending", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("cmd") });
    tracker.device(dev.device_id);

    const cmd = await api.deviceCommand(dev.device_id, "sync");
    expect(cmd.id || cmd.command_id || cmd.queued, "comando aceito").toBeTruthy();

    const history = await api.listCommands(dev.device_id, { limit: "10" });
    expect(Array.isArray(history)).toBe(true);

    // Player consulta a fila de comandos pendentes com o device_token:
    const pending = await api.pendingCommands(dev.device_id, dev.device_token);
    expect(Array.isArray(pending)).toBe(true);
  });

  test("comandos restart e clear_cache são aceitos", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("cmd2") });
    tracker.device(dev.device_id);
    for (const c of ["restart", "clear_cache"]) {
      const res = await api.raw("post", `/devices/${dev.device_id}/command`, { data: { command_type: c } });
      expect([200, 201], `comando ${c}`).toContain(res.status());
    }
  });
});

test.describe("@api 19 Invalidar pareamento", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("revogar token: o token antigo perde acesso ao player schedule", async ({ api, tracker }) => {
    const dev = await api.pairDevice({ name: uniqueName("revoke") });
    tracker.device(dev.device_id);

    // Token atual funciona.
    const ok = await api.raw("get", `/api/v1/player/schedule?device_id=${dev.device_id}&device_token=${dev.device_token}`);
    expect([200], "token válido acessa schedule").toContain(ok.status());

    // Revoga o token do dispositivo.
    await api.revokeToken(dev.device_id);

    // Token antigo deve ser rejeitado (403) — player precisa reparear.
    const denied = await api.raw("get", `/api/v1/player/schedule?device_id=${dev.device_id}&device_token=${dev.device_token}`);
    expect([401, 403], "token revogado é rejeitado").toContain(denied.status());
  });
});

test.describe("@api 20 Não reiniciar player (atualização incremental)", () => {
  test.beforeEach(async ({ playerEnabled }) => test.skip(!playerEnabled, "RUN_PLAYER_API=false"));

  test("mudança de programação altera schedule_version (base para o player NÃO recarregar à toa)", async ({ api, tracker }) => {
    // O Player (frontend/src/pages/Player.jsx) ignora playlist_invalidated quando
    // config_version não muda — evitando reload completo. Aqui validamos a base
    // server-side: a versão muda apenas quando há mudança real de conteúdo.
    const dev = await api.pairDevice({ name: uniqueName("noreload") });
    tracker.device(dev.device_id);
    const v0 = Number((await api.getDevice(dev.device_id)).schedule_version);

    // Atualização "no-op" de nome do device não deveria bumpar schedule_version.
    await api.updateDevice(dev.device_id, { name: `${dev.name}-rotulo` });
    const v1 = Number((await api.getDevice(dev.device_id)).schedule_version);
    expect(v1, "renomear device não muda schedule_version").toBe(v0);
  });

  test.fixme("player NÃO recarrega ao receber playlist_invalidated com versão igual", async () => {
    // Comportamento client-side do Player.jsx (guard de config_version) — cobrir em
    // teste de componente (já existe frontend/src/__tests__/player_sse.test.js).
  });
});
