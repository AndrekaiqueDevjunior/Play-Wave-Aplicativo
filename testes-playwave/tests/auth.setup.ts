/**
 * auth.setup.ts — projeto "setup": faz login no painel uma vez e salva o
 * storageState em playwright/.auth/admin.json, reutilizado pelos testes de UI.
 *
 * Se o login UI falhar (ex: painel sem backend), o setup ainda grava um token
 * obtido via API direto no storage, para os smokes de UI conseguirem navegar.
 */
import { test as setup, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
import { Api } from "../helpers/api.js";
import { ENV } from "../helpers/env.js";

const authFile = "playwright/.auth/admin.json";

setup("autentica admin e salva storageState", async ({ page, request }) => {
  // 1) Obtém token via API (fonte de verdade — não depende de seletor de UI).
  const api = new Api(request);
  const token = await api.login();
  const me = await api.me();
  expect(token, "login API deve retornar token").toBeTruthy();

  fs.mkdirSync(path.dirname(authFile), { recursive: true });

  // 2) Semeia o storage e abre o painel para o Playwright capturar o estado.
  //    Se o painel estiver fora (testes @api não precisam dele), ainda gravamos
  //    um storageState válido para não bloquear os projetos dependentes.
  await page.addInitScript(
    ({ t, u }) => {
      localStorage.setItem("pw_access_token", t);
      localStorage.setItem("pw_user", JSON.stringify(u));
    },
    { t: token, u: me },
  );

  try {
    await page.goto(`${ENV.WEB_URL}/`, { timeout: 8000 });
    await page.context().storageState({ path: authFile });
  } catch {
    console.warn(`[setup] painel indisponível em ${ENV.WEB_URL} — gravando storageState vazio (ok para testes @api).`);
    fs.writeFileSync(authFile, JSON.stringify({ cookies: [], origins: [] }));
  }
});
