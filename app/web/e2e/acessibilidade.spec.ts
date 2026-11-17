import { test, expect } from '@playwright/test';
import { auditarTela, gerarUsuarioE2E, ResumoViolacaoAxe } from './apoio';

test.describe('Acessibilidade - Auditoria WCAG 2.1 AA (axe-core)', () => {
  test('auditoria de acessibilidade nas 11 telas e estado modal', async ({ page }, testInfo) => {
    const todasViolacoes: { tela: string; violacoes: ResumoViolacaoAxe[] }[] = [];

    // 1. aba Mercado
    await test.step('Auditoria: aba Mercado', async () => {
      await page.goto('/?destino=analista_dados_bi&uf=SP');
      await expect(page.getByRole('heading', { level: 2, name: /Mercado de admissões formais/i })).toBeVisible();
      await expect(page.getByRole('heading', { level: 3, name: /Observado/i })).toBeVisible();

      await auditarTela(page, 'mercado', testInfo, todasViolacoes);
    });

    // 2. Painel técnico
    await test.step('Auditoria: Painel técnico', async () => {
      await page.goto('/#painel-tecnico');
      await expect(page.getByRole('heading', { level: 2, name: /Painel técnico de modelos preditivos/i })).toBeVisible();
      await expect(page.getByRole('heading', { level: 3, name: /Comparativo de modelos preditivos/i })).toBeVisible();

      await auditarTela(page, 'painel-tecnico', testInfo, todasViolacoes);
    });

    // 3. Entrar
    await test.step('Auditoria: Entrar', async () => {
      await page.goto('/#minha-transicao');
      await expect(page.getByRole('heading', { level: 2, name: /Entrar/i })).toBeVisible();

      await auditarTela(page, 'entrar', testInfo, todasViolacoes);
    });

    // Autenticar para acessar as telas da jornada
    const usuario = gerarUsuarioE2E();
    await page.getByRole('button', { name: /Ainda não tem conta\? Criar conta/i }).click();
    await page.getByLabel(/E-mail/i).fill(usuario.email);
    await page.getByLabel(/Senha/i).fill(usuario.senha);
    await page.getByRole('button', { name: /^Criar conta$/i }).click();
    await expect(page.getByRole('heading', { level: 2, name: /Autorizações de uso de dados/i })).toBeVisible();

    // 4. Consentimentos
    await test.step('Auditoria: Consentimentos', async () => {
      await auditarTela(page, 'consentimentos', testInfo, todasViolacoes);
    });

    // Conceder autorizações e avançar
    const headingPerfil = page.getByRole('heading', { level: 3, name: 'Perfil e currículo' });
    const cardPerfil = headingPerfil.locator('xpath=ancestor::div[contains(@class, "p-5")][1]');
    await cardPerfil.getByRole('button', { name: /Conceder/i }).click();
    await expect(cardPerfil.getByText(/Ativo desde/i)).toBeVisible();

    const headingLlm = page.getByRole('heading', { level: 3, name: 'Sugestões com inteligência artificial' });
    const cardLlm = headingLlm.locator('xpath=ancestor::div[contains(@class, "p-5")][1]');
    await cardLlm.getByRole('button', { name: /Conceder/i }).click();
    await expect(cardLlm.getByText(/Ativo desde/i)).toBeVisible();

    await page.getByRole('button', { name: /Continuar para a intenção/i }).click();
    await expect(page.getByRole('heading', { level: 2, name: /Intenção profissional/i })).toBeVisible();

    // 5. Intenção
    await test.step('Auditoria: Intenção', async () => {
      await auditarTela(page, 'intencao', testInfo, todasViolacoes);
    });

    // Preencher intenção e avançar
    await page.locator('#seletor-uf-intencao').selectOption('SP');
    await page.locator('#input-horas-semana').fill('6');
    await page.locator('#input-novo-motivo').fill('Busco transição para dados e tecnologia.');
    await page.getByRole('button', { name: /Adicionar motivo/i }).click();
    await page.getByRole('button', { name: /Salvar intenção/i }).click();
    await expect(page.getByText(/Intenção registrada/i)).toBeVisible();

    await page.getByRole('button', { name: /Continuar para o currículo/i }).click();
    await expect(page.getByRole('heading', { level: 2, name: /Envio de currículo/i })).toBeVisible();

    // Colar currículo e processar texto para exibir tela com texto redigido
    await page.getByLabel(/Texto das experiências/i).fill('Experiência em suporte e análise de sistemas. Contato dev@exemplo.test.');
    await page.getByRole('button', { name: /Processar texto/i }).click();
    await expect(page.getByRole('heading', { level: 3, name: /Texto com dados protegidos/i })).toBeVisible();

    // 6. Currículo (com texto redigido)
    await test.step('Auditoria: Currículo (com texto redigido)', async () => {
      await auditarTela(page, 'curriculo', testInfo, todasViolacoes);
    });

    // Confirmar currículo
    await page.getByRole('button', { name: /Confirmar e liberar para sugestões/i }).click();
    await expect(page.getByText(/Texto confirmado em/i)).toBeVisible();

    // 7. Competências (estado vazio real da API sem LLM)
    await test.step('Auditoria: Competências (estado vazio)', async () => {
      await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Competências').click();
      await expect(page.getByRole('heading', { level: 2, name: /Revisão de competências/i })).toBeVisible();
      await expect(page.getByRole('heading', { level: 3, name: /Nenhuma competência sugerida/i })).toBeVisible();

      await auditarTela(page, 'competencias', testInfo, todasViolacoes);
    });

    // 8. Comparação (com resultado)
    await test.step('Auditoria: Comparação (com resultado)', async () => {
      await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Comparação').click();
      await expect(page.getByRole('heading', { level: 2, name: /Comparação de destinos/i })).toBeVisible();

      // Selecionar destinos e comparar
      await page.locator('#cb-analista_monitoramento_iot').check();
      await page.locator('#cb-analista_dados_bi').check();
      await page.getByRole('button', { name: /^Comparar$/i }).click();
      await expect(page.getByText(/Sem nota única/i)).toBeVisible();

      await auditarTela(page, 'comparacao', testInfo, todasViolacoes);
    });

    // 9. Plano
    await test.step('Auditoria: Plano', async () => {
      const primeiroCartao = page.locator('[data-testid="cartao-destino"]').first();
      await primeiroCartao.getByRole('button', { name: /Escolher este destino/i }).click();
      await expect(page.getByRole('heading', { level: 3, name: /Checkpoints do plano/i })).toBeVisible();

      await auditarTela(page, 'plano', testInfo, todasViolacoes);
    });

    // 10. Exercício
    await test.step('Auditoria: Exercício', async () => {
      await page.getByRole('button', { name: /Fazer o exercício/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Exercício diagnóstico/i })).toBeVisible({ timeout: 15_000 });

      await auditarTela(page, 'exercicio', testInfo, todasViolacoes);
    });

    // Diálogo Discordo (estado modal)
    await test.step('Auditoria: Diálogo Discordo (estado modal)', async () => {
      const questaoCards = page.locator('div', { has: page.locator('span', { hasText: /^Questão #\d+$/i }) });
      const totalCards = await questaoCards.count();
      for (let i = 0; i < totalCards; i++) {
        await questaoCards.nth(i).locator('input[type="radio"]').first().check({ force: true });
      }

      const respostaAberta = 'Realizei a análise diagnóstica dos sensores de temperatura e distância na bancada com calma.';
      await page.getByLabel(/Sua resposta aberta/i).fill(respostaAberta);
      await page.getByRole('button', { name: /Enviar resposta/i }).click();
      await expect(page.getByText('Parcial').first()).toBeVisible();

      // Abrir modal "Discordo"
      await page.getByRole('button', { name: /^Discordo$/i }).click();
      await expect(page.getByRole('heading', { level: 3, name: /Registrar discordância/i })).toBeVisible();

      await auditarTela(page, 'dialog-discordo', testInfo, todasViolacoes);

      // Cancelar para fechar o diálogo
      await page.getByRole('button', { name: /Cancelar/i }).click();
      await expect(page.getByRole('heading', { level: 3, name: /Registrar discordância/i })).toHaveCount(0);
    });

    // 11. Laboratório (plano IoT ativo)
    await test.step('Auditoria: Laboratório (plano IoT ativo)', async () => {
      await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Laboratório').click();
      await expect(page.getByRole('heading', { level: 2, name: /Laboratório na nuvem/i })).toBeVisible();
      await expect(page.getByRole('heading', { level: 3, name: /Nenhuma sessão de laboratório ativa/i })).toBeVisible();

      await auditarTela(page, 'laboratorio', testInfo, todasViolacoes);
    });

    // Se houve qualquer violação séria ou crítica em qualquer tela, falha o teste com a lista exata
    expect(
      todasViolacoes,
      `Violações sérias ou críticas de acessibilidade encontradas nas telas: ${JSON.stringify(todasViolacoes, null, 2)}`
    ).toEqual([]);
  });
});
