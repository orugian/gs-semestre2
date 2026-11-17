import { test, expect } from '@playwright/test';
import { auditarAcessibilidade, gerarUsuarioE2E } from './apoio';

declare const process: { env: Record<string, string | undefined> };

test.describe('Jornada E2E - CitizenTech', () => {
  test('jornada completa de ponta a ponta', async ({ page }, testInfo) => {
    // 2. Capturar console.warn/error e pageerror desde o início (apenas padrões específicos, sem PII)
    const avisosCapturados: string[] = [];
    const filtrarAvisos = (origem: string, texto: string) => {
      const ehReactTelaPlano =
        texto.includes('Cannot update a component') &&
        texto.includes('while rendering') &&
        texto.includes('TelaPlano');
      const ehDialogSemNome =
        texto.includes('Dialog') &&
        (texto.includes('no accessible name') ||
          texto.includes('accessible name') ||
          texto.includes('accessible-name'));
      if (ehReactTelaPlano || ehDialogSemNome) {
        avisosCapturados.push(`[${origem}] ${texto}`);
      }
    };

    page.on('console', (msg) => {
      const tipo = msg.type();
      if (tipo === 'warning' || tipo === 'error') {
        filtrarAvisos(`console.${tipo}`, msg.text());
      }
    });

    page.on('pageerror', (err) => {
      filtrarAvisos('pageerror', err.message || String(err));
    });

    const usuario = gerarUsuarioE2E();

    await test.step('Cadastrar e entrar', async () => {
      await page.goto('/#minha-transicao');
      await expect(page.getByRole('heading', { level: 1, name: /CitizenTech/i })).toBeVisible();

      // Alternar para modo criar conta
      await page.getByRole('button', { name: /Ainda não tem conta\? Criar conta/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Criar conta/i })).toBeVisible();

      // Preencher email e senha
      await page.getByLabel(/E-mail/i).fill(usuario.email);
      await page.getByLabel(/Senha/i).fill(usuario.senha);

      // Submeter formulário
      await page.getByRole('button', { name: /^Criar conta$/i }).click();

      // Verificar login bem-sucedido
      await expect(page.getByText(usuario.email)).toBeVisible();
      await expect(page.getByRole('button', { name: /Sair/i })).toBeVisible();
      await expect(page.getByRole('heading', { level: 2, name: /Autorizações de uso de dados/i })).toBeVisible();
    });

    await test.step('Conceder perfil e curriculo_llm', async () => {
      // Conceder Perfil e currículo
      const headingPerfil = page.getByRole('heading', { level: 3, name: 'Perfil e currículo' });
      const cardPerfil = headingPerfil.locator('xpath=ancestor::div[contains(@class, "p-5")][1]');
      await cardPerfil.getByRole('button', { name: /Conceder/i }).click();
      await expect(cardPerfil.getByText(/Ativo desde/i)).toBeVisible();

      // Conceder Sugestões com inteligência artificial
      const headingLlm = page.getByRole('heading', { level: 3, name: 'Sugestões com inteligência artificial' });
      const cardLlm = headingLlm.locator('xpath=ancestor::div[contains(@class, "p-5")][1]');
      await cardLlm.getByRole('button', { name: /Conceder/i }).click();
      await expect(cardLlm.getByText(/Ativo desde/i)).toBeVisible();

      // Avançar para a intenção
      await page.getByRole('button', { name: /Continuar para a intenção/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Intenção profissional/i })).toBeVisible();
    });

    await test.step('Salvar intenção (UF SP, 6 h) e ver motivo redigido', async () => {
      await page.locator('#seletor-uf-intencao').selectOption('SP');
      await page.locator('#input-horas-semana').fill('6');

      const emailFicticio = 'contato.ficticio@exemplo.test';
      const motivoTexto = `Busco transição para dados. Contato para retorno: ${emailFicticio}.`;
      await page.locator('#input-novo-motivo').fill(motivoTexto);
      await page.getByRole('button', { name: /Adicionar motivo/i }).click();

      // Salvar intenção
      await page.getByRole('button', { name: /Salvar intenção/i }).click();
      await expect(page.getByText(/Intenção registrada/i)).toBeVisible();

      // Conferir que o motivo salvo voltou redigido (sem o e-mail fictício original)
      const listaMotivos = page.locator('ul').filter({ hasText: 'Busco transição' });
      await expect(listaMotivos).not.toContainText(emailFicticio);
      await expect(listaMotivos).toContainText('[EMAIL]');

      // Continuar para o currículo
      await page.getByRole('button', { name: /Continuar para o currículo/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Envio de currículo/i })).toBeVisible();
    });

    await test.step('Colar currículo com e-mail e telefone fictícios e verificar texto redigido', async () => {
      const emailCv = 'candidato.e2e@exemplo.test';
      const telCv = '(11) 98765-4321';
      const textoCv = `Experiência sólida como analista de suporte. Contato direto: ${emailCv} ou telefone ${telCv}.`;

      await page.getByLabel(/Texto das experiências/i).fill(textoCv);
      await page.getByRole('button', { name: /Processar texto/i }).click();

      // Aguardar área de texto com dados protegidos
      await expect(page.getByRole('heading', { level: 3, name: /Texto com dados protegidos/i })).toBeVisible();

      // Verificar que os dados de contato foram redigidos
      const areaRedigida = page.getByLabel(/Texto com dados protegidos/i);
      const valorRedigido = await areaRedigida.inputValue();
      expect(valorRedigido).not.toContain(emailCv);
      expect(valorRedigido).not.toContain(telCv);
      expect(valorRedigido).toContain('[EMAIL]');
      expect(valorRedigido).toContain('[TELEFONE]');

      // 'Sugerir competências' NÃO EXISTE antes de confirmar
      await expect(page.getByRole('button', { name: /Sugerir competências/i })).toHaveCount(0);

      // Confirmar envio do currículo
      await page.getByRole('button', { name: /Confirmar e liberar para sugestões/i }).click();
      await expect(page.getByText(/Texto confirmado em/i)).toBeVisible();

      // Agora o botão 'Sugerir competências' passa a existir
      const botaoSugerir = page.getByRole('button', { name: /Sugerir competências/i });
      await expect(botaoSugerir).toBeVisible();

      // Clicar em sugerir
      await botaoSugerir.click();

      // Mensagem de serviço indisponível (503 real da API sem chave de LLM)
      await expect(
        page.getByText(/O serviço de sugestões está indisponível agora; seu texto continua salvo e você pode tentar mais tarde/i)
      ).toBeVisible();
    });

    await test.step('Comparação de 2 destinos na ordem escolhida', async () => {
      // Navegar para Comparação via stepper
      await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Comparação').click();
      await expect(page.getByRole('heading', { level: 2, name: /Comparação de destinos/i })).toBeVisible();

      // Selecionar 2 destinos na ordem escolhida: analista_monitoramento_iot primeiro, depois analista_dados_bi
      await page.locator('#cb-analista_monitoramento_iot').check();
      await page.locator('#cb-analista_dados_bi').check();

      await page.getByRole('button', { name: /^Comparar$/i }).click();

      // Aviso "Sem nota única"
      await expect(
        page.getByText(/Sem nota única: cada dimensão é apresentada separadamente e a decisão é sua/i)
      ).toBeVisible();

      // Verificar os dois cartões na ordem escolhida
      const cartoes = page.locator('[data-testid="cartao-destino"]');
      await expect(cartoes).toHaveCount(2);

      const primeiroCartao = cartoes.nth(0);
      const segundoCartao = cartoes.nth(1);

      await expect(primeiroCartao.getByRole('heading', { level: 3 })).toContainText(/Analista de Monitoramento/i);
      await expect(segundoCartao.getByRole('heading', { level: 3 })).toContainText(/Analista de Dados/i);

      // Obrigatórios não atendidos visíveis em ambos
      await expect(primeiroCartao.getByRole('heading', { level: 4, name: /Obrigatórios ainda não atendidos/i })).toBeVisible();
      await expect(segundoCartao.getByRole('heading', { level: 4, name: /Obrigatórios ainda não atendidos/i })).toBeVisible();

      // "Novo Caged" no mercado
      await expect(primeiroCartao.getByText(/Fonte:\s*Novo Caged/i)).toBeVisible();
      await expect(segundoCartao.getByText(/Fonte:\s*Novo Caged/i)).toBeVisible();

      // Escolher o primeiro destino
      await primeiroCartao.getByRole('button', { name: /Escolher este destino/i }).click();

      // Avança automaticamente para o Plano
      await expect(page.getByRole('heading', { level: 3, name: /Checkpoints do plano/i })).toBeVisible();
    });

    await test.step('Plano de desenvolvimento e conclusão de checkpoint', async () => {
      // Aviso institucional obrigatório de que concluir não demonstra
      await expect(
        page.getByText(/concluir (um checkpoint|uma etapa) não torna a competência demonstrada/i)
      ).toBeVisible();

      // Concluir um checkpoint manual (não exercício)
      const botaoConcluir = page.getByRole('button', { name: /Concluir/i }).first();
      await expect(botaoConcluir).toBeVisible();
      await botaoConcluir.click();

      // Verificar que o status mudou para Concluído
      await expect(page.getByText('Concluído').first()).toBeVisible();

      // Sair da tela e retornar para verificar persistência do status pela UI
      await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Comparação').click();
      await expect(page.getByRole('heading', { level: 2, name: /Comparação de destinos/i })).toBeVisible();
      await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Plano').click();
      await expect(page.getByRole('heading', { level: 3, name: /Checkpoints do plano/i })).toBeVisible();
      await expect(page.getByText('Concluído').first()).toBeVisible();

      // Clicar em "Fazer o exercício" no checkpoint de exercício
      await page.getByRole('button', { name: /Fazer o exercício/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Exercício diagnóstico/i })).toBeVisible();
    });

    await test.step('Exercício: critérios antes do envio, nenhum gabarito, resposta e resultado parcial', async () => {
      // Critérios visíveis antes do envio
      await expect(page.getByRole('heading', { level: 3, name: /Critérios da resposta aberta/i })).toBeVisible();
      await expect(page.getByText(/Nível 0:/i).first()).toBeVisible();
      await expect(page.getByText(/Nível 1:/i).first()).toBeVisible();
      await expect(page.getByText(/Nível 2:/i).first()).toBeVisible();

      // Nenhum gabarito na tela antes do envio
      await expect(page.getByText(/Gabarito/i)).toHaveCount(0);

      // Responder às questões objetivas
      const questaoCards = page.locator('div', { has: page.locator('span', { hasText: /^Questão #\d+$/i }) });
      const totalCards = await questaoCards.count();
      for (let i = 0; i < totalCards; i++) {
        await questaoCards.nth(i).locator('input[type="radio"]').first().check({ force: true });
      }

      // Preencher resposta aberta (mínimo 20 caracteres)
      const respostaAberta = 'Realizei a análise diagnóstica dos sensores de temperatura e distância na bancada com calma.';
      await page.getByLabel(/Sua resposta aberta/i).fill(respostaAberta);

      // Enviar resposta
      await page.getByRole('button', { name: /Enviar resposta/i }).click();

      // Resultado parcial explicado
      await expect(page.getByText('Parcial').first()).toBeVisible();
      await expect(
        page.getByText(/a avaliação da resposta aberta não estava disponível; a parte objetiva foi registrada/i)
      ).toBeVisible();

      // Sem nota do exercício (exibida apenas quando não for parcial)
      await expect(page.getByText(/Nota do exercício:/i)).toHaveCount(0);

      // Registrar "Discordo"
      await page.getByRole('button', { name: /^Discordo$/i }).click();
      await expect(page.getByRole('heading', { level: 3, name: /Registrar discordância/i })).toBeVisible();

      // 3. Assertiva SOFT de nome acessível do dialog = Registrar discordância
      const dialogDiscordo = page.getByRole('dialog');
      await expect.soft(dialogDiscordo).toHaveAccessibleName(/Registrar discordância/i);

      // 3. Rodar axe com modal aberto e esperar zero serious/critical, incluindo aria-dialog-name
      const relatorioModal = await auditarAcessibilidade(page, 'modal-discordo-jornada', testInfo);
      expect.soft(
        relatorioModal.violacoesCriticasOuSerias,
        `Violações sérias/críticas no modal aberto de discordância: ${JSON.stringify(relatorioModal.violacoesCriticasOuSerias, null, 2)}`
      ).toEqual([]);

      // Continuar registrando contestação para provar que funciona
      await page.getByLabel(/Motivo da discordância/i).fill('Discordo da pontuação de uma das alternativas da avaliação.');
      await page.getByRole('button', { name: /Confirmar discordância/i }).click();

      await expect(page.getByText(/Contestação registrada/i)).toBeVisible();
    });

    await test.step('Sair e voltar para Entrar', async () => {
      await page.getByRole('button', { name: /Sair/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Entrar/i })).toBeVisible();
    });

    // 2. Assertiva SOFT no fim de que não houve warning de renderização nem de acessibilidade
    expect.soft(
      avisosCapturados,
      `Avisos indesejados capturados no console/pageerror: ${JSON.stringify(avisosCapturados, null, 2)}`
    ).toEqual([]);
  });

  test('segurança visível', async ({ page }) => {
    await test.step('Abrir #minha-transicao sem sessão mostra Entrar', async () => {
      await page.goto('/#minha-transicao');
      await expect(page.getByRole('heading', { level: 2, name: /Entrar/i })).toBeVisible();
    });

    await test.step('Senha com 8 caracteres é recusada no cliente', async () => {
      await page.getByLabel(/E-mail/i).fill('seguranca.teste@exemplo.test');
      await page.getByLabel(/Senha/i).fill('12345678');
      await page.getByRole('button', { name: /^Entrar$/i }).click();

      await expect(page.getByText(/A senha deve ter pelo menos 10 caracteres/i)).toBeVisible();
    });

    await test.step('Depois de sair, recarregar a página continua em Entrar', async () => {
      const usuario = gerarUsuarioE2E();
      await page.getByRole('button', { name: /Ainda não tem conta\? Criar conta/i }).click();
      await page.getByLabel(/E-mail/i).fill(usuario.email);
      await page.getByLabel(/Senha/i).fill(usuario.senha);
      await page.getByRole('button', { name: /^Criar conta$/i }).click();

      await expect(page.getByRole('button', { name: /Sair/i })).toBeVisible();

      // Clica em sair
      await page.getByRole('button', { name: /Sair/i }).click();
      await expect(page.getByRole('heading', { level: 2, name: /Entrar/i })).toBeVisible();

      // Recarrega a página
      await page.reload();
      await expect(page.getByRole('heading', { level: 2, name: /Entrar/i })).toBeVisible();
    });
  });
});

// Sem capturas neste arquivo: protege credenciais inclusive se o login falhar.
// O Playwright exige essas opções no nível do arquivo (escopo de worker).
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test.describe('Persona de demonstração', () => {
  test.afterEach(async ({ page }) => {
    // Inclusive em falha: o contexto ARIA automático não pode reter a senha.
    await page.locator('input').evaluateAll((inputs) => {
      for (const input of inputs) {
        input.value = '';
        input.defaultValue = '';
        input.removeAttribute('value');
      }
    });
  });

  test('persona de demonstração', async ({ page }, testInfo) => {
    const email = process.env.E2E_PERSONA_EMAIL;
    const senha = process.env.E2E_PERSONA_SENHA;

    if (!email || !senha) {
      test.skip(true, 'persona não configurada');
      return;
    }

    await page.goto('/#minha-transicao');
    await page.getByLabel(/E-mail/i).fill(email);
    await page.getByLabel(/Senha/i).fill(senha);
    await page.getByRole('button', { name: /^Entrar$/i }).click();

    // Ver o selo "Persona de demonstração"
    await expect(page.getByText(/Persona de demonstração/i)).toBeVisible();

    // Ver o plano ativo
    await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Plano').click();
    await expect(page.getByRole('heading', { level: 2, name: /Analista de Monitoramento\/IoT Industrial/i })).toBeVisible();
    await expect(page.getByRole('heading', { level: 3, name: /Checkpoints do plano/i })).toBeVisible();

    // Capturas só após autenticar: o formulário com senha já foi desmontado.
    await page.screenshot({ path: testInfo.outputPath('persona-plano-desktop.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: testInfo.outputPath('persona-plano-mobile.png') });
    await page.setViewportSize({ width: 1280, height: 720 });

    // Ver o histórico do exercício
    await page.locator('nav[aria-label="Etapas da jornada"]').getByText('Exercício').click();
    await expect(page.getByRole('heading', { level: 2, name: /Exercício diagnóstico/i })).toBeVisible();
    await expect(page.getByRole('heading', { level: 3, name: /Histórico de tentativas/i })).toBeVisible();
  });
});
