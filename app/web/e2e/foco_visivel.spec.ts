import { test, expect, Page } from '@playwright/test';

async function verificarIndicadorFoco(page: Page, nomeControle: string) {
  const resultado = await page.evaluate(() => {
    const el = document.activeElement as HTMLElement | null;
    if (!el || el === document.body) {
      return { valido: false, msg: 'Nenhum elemento interativo focado (activeElement é BODY ou null)' };
    }

    // Elemento focado (ou se houver wrapper com anel externo explícito de foco)
    const cs = window.getComputedStyle(el);
    const outlineStyle = cs.outlineStyle;
    const outlineWidth = parseFloat(cs.outlineWidth) || 0;
    const boxShadow = cs.boxShadow;

    // Indicador visível no elemento focado: outline >= 2px ou box-shadow de foco (não borda interna inset)
    const temOutline = outlineStyle !== 'none' && outlineWidth >= 2;
    const temBoxShadow = Boolean(boxShadow && boxShadow !== 'none' && !boxShadow.includes('inset'));

    if (temOutline || temBoxShadow) {
      return {
        valido: true,
        tag: el.tagName,
        id: el.id,
        outlineStyle,
        outlineWidth,
        boxShadow,
        msg: `Foco visível: outline=${outlineStyle} ${outlineWidth}px, shadow=${boxShadow}`,
      };
    }

    // Se o wrapper imediato aplicar outline de foco (:focus-within)
    if (el.parentElement) {
      const csPai = window.getComputedStyle(el.parentElement);
      const paiOutline = csPai.outlineStyle !== 'none' && parseFloat(csPai.outlineWidth) >= 2;
      const paiShadow = Boolean(csPai.boxShadow && csPai.boxShadow !== 'none' && !csPai.boxShadow.includes('inset'));
      if (paiOutline || paiShadow) {
        return {
          valido: true,
          tag: el.tagName,
          id: el.id,
          outlineStyle: csPai.outlineStyle,
          outlineWidth: parseFloat(csPai.outlineWidth) || 0,
          boxShadow: csPai.boxShadow,
          msg: `Foco visível no wrapper: outline=${csPai.outlineStyle}, shadow=${csPai.boxShadow}`,
        };
      }
    }

    return {
      valido: false,
      tag: el.tagName,
      id: el.id,
      outlineStyle,
      outlineWidth,
      boxShadow,
      msg: `Elemento focado sem indicador visível (outline: ${outlineStyle} ${outlineWidth}px, shadow: ${boxShadow})`,
    };
  });

  expect(resultado.valido, `${nomeControle}: ${resultado.msg}`).toBe(true);
}

test.describe('Foco visível (WCAG 2.4.7)', () => {
  test('tela Mercado: abas, Selector Destino e Selector UF possuem indicador visível ao receber foco por Tab', async ({
    page,
  }) => {
    await page.goto('/?destino=analista_dados_bi&uf=SP');
    await expect(
      page.getByRole('heading', { level: 2, name: /Mercado de admissões formais/i })
    ).toBeVisible();

    // 1. Tab até a primeira aba
    await page.keyboard.press('Tab');
    const abaMercado = page.getByRole('tab', { name: 'Mercado' });
    await expect(abaMercado).toBeFocused();
    await verificarIndicadorFoco(page, 'Aba Mercado');

    // 2. Tab até o Selector Destino
    await page.keyboard.press('Tab');
    const seletorDestino = page.getByRole('combobox', { name: /Destino profissional/i });
    await expect(seletorDestino).toBeFocused();
    await verificarIndicadorFoco(page, 'Selector Destino');

    // 3. Tab até o Selector UF
    await page.keyboard.press('Tab');
    const seletorUf = page.getByRole('combobox', { name: /Unidade Federativa/i });
    await expect(seletorUf).toBeFocused();
    await verificarIndicadorFoco(page, 'Selector UF');
  });

  test('tela Entrar: campos E-mail e Senha possuem anel de foco visível ao receber foco por Tab', async ({
    page,
  }) => {
    await page.goto('/#minha-transicao');
    await expect(
      page.getByRole('heading', { level: 2, name: /Entrar/i })
    ).toBeVisible();

    // Pressiona Tab até o campo E-mail
    const emailInput = page.getByLabel(/E-mail/i);
    // Pressiona Tab até focar no e-mail
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press('Tab');
      const isFocused = await emailInput.evaluate((el) => document.activeElement === el);
      if (isFocused) break;
    }
    await expect(emailInput).toBeFocused();
    await verificarIndicadorFoco(page, 'Campo E-mail');

    // Próximo Tab: campo Senha
    await page.keyboard.press('Tab');
    const senhaInput = page.getByLabel(/Senha/i);
    await expect(senhaInput).toBeFocused();
    await verificarIndicadorFoco(page, 'Campo Senha');
  });
});
