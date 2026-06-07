import { defineConfig, devices } from "@playwright/test";
import { config as loadEnv } from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
loadEnv({ path: path.resolve(__dirname, ".env") });

const WEB_URL = process.env.WEB_URL || "http://127.0.0.1:3100";

export default defineConfig({
  testDir: "./tests",
  outputDir: "./reports/artifacts",
  fullyParallel: false, // testes de fila/versão compartilham estado no backend
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1, // serial: evita corrida em schedule_version/cache do mesmo tenant
  timeout: 60_000,
  expect: { timeout: 10_000 },

  reporter: [
    ["list"],
    ["html", { outputFolder: "reports/html", open: "never" }],
    ["json", { outputFile: "reports/results.json" }],
  ],

  use: {
    baseURL: WEB_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    actionTimeout: 15_000,
    navigationTimeout: 20_000,
  },

  projects: [
    // Login uma vez → storageState reutilizado pelos testes de UI.
    { name: "setup", testMatch: /auth\.setup\.ts/ },

    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        storageState: "playwright/.auth/admin.json",
      },
      dependencies: ["setup"],
    },
  ],
});
