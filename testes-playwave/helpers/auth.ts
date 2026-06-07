/**
 * auth.ts — login no painel (UI) e no backend (API).
 *
 * O painel NÃO tem data-testid (auditado: 0 ocorrências), então o login UI
 * usa seletores por tipo/role. Campos reais (frontend/src/pages/Login.jsx):
 *   - input[type="email"]  (placeholder "seu@email.com")
 *   - input[type="password"]
 *   - button[type="submit"] (texto "Entrar"/"Acessar")
 *
 * Tokens são guardados em localStorage: pw_access_token + pw_user.
 */
import type { Page } from "@playwright/test";
import { ENV } from "./env.js";

export async function loginViaUI(page: Page, email = ENV.ADMIN_EMAIL, password = ENV.ADMIN_PASSWORD): Promise<void> {
  await page.goto(`${ENV.WEB_URL}/login`);
  await page.locator('input[type="email"]').first().fill(email);
  await page.locator('input[type="password"]').first().fill(password);
  await page.locator('button[type="submit"]').first().click();
  // Sucesso: sai de /login (redireciona p/ dashboard) ou grava token.
  await page.waitForFunction(
    () => !!localStorage.getItem("pw_access_token"),
    undefined,
    { timeout: 15_000 },
  );
}

/**
 * Injeta um token já obtido por API direto no storage — atalho para testes de
 * UI que não querem repetir o fluxo visual de login.
 */
export async function seedAuthStorage(page: Page, token: string, user: Record<string, any>): Promise<void> {
  await page.addInitScript(
    ({ t, u }) => {
      localStorage.setItem("pw_access_token", t);
      localStorage.setItem("pw_user", JSON.stringify(u));
    },
    { t: token, u: user },
  );
}
