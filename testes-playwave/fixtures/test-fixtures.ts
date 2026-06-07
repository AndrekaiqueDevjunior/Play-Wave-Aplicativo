/**
 * test-fixtures.ts — fixtures reutilizáveis.
 *
 * Expõe:
 *   - api      : Api logado como admin (APIRequestContext do Playwright)
 *   - tracker  : coletor de recursos com cleanup automático no afterEach
 *   - playerEnabled : boolean (ENV.RUN_PLAYER_API) p/ guardas de teste
 *
 * Uso:
 *   import { test, expect } from "../fixtures/test-fixtures";
 *   test("...", async ({ api, tracker }) => { ... });
 */
import { test as base, expect } from "@playwright/test";
import { Api } from "../helpers/api.js";
import { Tracker } from "../helpers/cleanup.js";
import { ENV } from "../helpers/env.js";

type Fixtures = {
  api: Api;
  tracker: Tracker;
  playerEnabled: boolean;
};

export const test = base.extend<Fixtures>({
  api: async ({ request }, use) => {
    const api = new Api(request);
    await api.login();
    await use(api);
  },

  tracker: async ({ api }, use) => {
    const tracker = new Tracker();
    await use(tracker);
    await tracker.cleanup(api);
  },

  playerEnabled: async ({}, use) => {
    await use(ENV.RUN_PLAYER_API);
  },
});

export { expect };
