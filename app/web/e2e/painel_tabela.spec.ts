import { test, expect } from '@playwright/test';

test('Painel técnico: a tabela comparativa mostra todas as linhas, sem cortar a última', async ({ page }) => {
  await page.goto('/#painel-tecnico');
  const tabela = page.getByRole('table', { name: /Tabela comparativa dos 6 modelos preditivos/i });
  await expect(tabela).toBeVisible();

  const medidas = await tabela.evaluate((el) => {
    const regiao = el.closest('[role="region"]') as HTMLElement;
    return { altura: regiao.clientHeight, conteudo: regiao.scrollHeight };
  });
  // A região só pode rolar na horizontal; na vertical todo o conteúdo precisa caber.
  expect(medidas.conteudo).toBeLessThanOrEqual(medidas.altura + 1);
  await expect(tabela.getByRole('row')).toHaveCount(7);
});
