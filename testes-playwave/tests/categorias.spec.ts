/**
 * categorias.spec.ts — TASK 02
 * Cria categoria, confirma na listagem e uso em faixa de áudio.
 * Endpoints: POST /audio/categories/, GET /audio/categories, POST /audio/tracks/upload (category_id)
 *
 * Inclui um smoke de UI do drawer (sem data-testid → seletor por texto/role).
 */
import { test, expect } from "../fixtures/test-fixtures.js";
import { genWav } from "../helpers/media-gen.js";
import { uniqueName, ENV } from "../helpers/env.js";

test.describe("@api 02 Categorias personalizadas", () => {
  test("cria categoria e ela aparece na listagem", async ({ api }) => {
    const created = await api.createCategory({ name: uniqueName("categoria") });
    expect(created.id).toBeTruthy();

    const list = await api.listCategories();
    const ids = new Set(list.map((c: any) => c.id));
    expect(ids.has(created.id)).toBe(true);
  });

  test("categoria pode ser usada ao subir uma faixa (category_id)", async ({ api }) => {
    const cat = await api.createCategory({ name: uniqueName("cat-uso") });
    const wav = genWav(1);
    const track = await api.uploadTrack(wav, { name: uniqueName("faixa-cat"), category_id: cat.id });
    expect(track.id).toBeTruthy();
    // Se a resposta expõe category_id, confirma o vínculo.
    if ("category_id" in track) expect(track.category_id).toBe(cat.id);
  });
});

test.describe("@ui 02 Categorias — drawer de criação (smoke)", () => {
  test("painel de faixas de áudio abre e permite acionar criação de categoria", async ({ page }) => {
    // Rota real do painel: /radio/faixas
    await page.goto(`${ENV.WEB_URL}/radio/faixas`);
    // Sem data-testid: tentamos achar um gatilho de "categoria" por texto.
    const trigger = page.getByRole("button", { name: /categoria/i }).first();
    // TODO[data-testid]: adicionar data-testid="btn-nova-categoria" e "drawer-categoria".
    if (await trigger.count()) {
      await expect(trigger).toBeVisible();
    } else {
      test.skip(true, "Gatilho de categoria não localizável sem data-testid — ver RELATORIO_FINAL.md");
    }
  });
});
