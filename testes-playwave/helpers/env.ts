/**
 * env.ts — centraliza configuração lida do `.env` (carregado no playwright.config.ts).
 */
export const ENV = {
  WEB_URL: process.env.WEB_URL || "http://127.0.0.1:3100",
  API_URL: process.env.API_URL || "http://127.0.0.1:8000",
  ADMIN_EMAIL: process.env.ADMIN_EMAIL || "admin@playwave.com",
  ADMIN_PASSWORD: process.env.ADMIN_PASSWORD || "",
  TENANT_ID: process.env.TENANT_ID || "",
  TEST_PREFIX: process.env.TEST_PREFIX || "e2e-",
  RUN_PLAYER_API: (process.env.RUN_PLAYER_API ?? "true") === "true",
  QUEUE_WAIT_TIMEOUT: Number(process.env.QUEUE_WAIT_TIMEOUT || 15000),
};

/** Nome único e rastreável para dado de teste (facilita limpeza). */
export function uniqueName(label: string): string {
  const ts = Date.now().toString(36);
  const rnd = Math.random().toString(36).slice(2, 6);
  return `${ENV.TEST_PREFIX}${label}-${ts}${rnd}`;
}
