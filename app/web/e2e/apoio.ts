// @ts-ignore
import * as fs from 'node:fs';
// @ts-ignore
import * as path from 'node:path';
import AxeBuilder from '@axe-core/playwright';
import { Page, TestInfo, expect } from '@playwright/test';

export function gerarUsuarioE2E() {
  const sufixo = Math.random().toString(36).substring(2, 8) + Date.now().toString(36);
  const email = `e2e-${sufixo}@exemplo.test`;
  const senha = 'E2ePass!' + Math.random().toString(36).substring(2, 10) + '99#';
  return { email, senha };
}

export interface ResumoNoAxe {
  alvo: string[];
  html: string;
  falha?: string;
}

export interface ResumoViolacaoAxe {
  regra: string;
  impacto: string | null;
  ajuda: string;
  descricao: string;
  nos: ResumoNoAxe[];
}

export interface OpcoesAuditoria {
  withRules?: string[];
}

export async function auditarAcessibilidade(
  page: Page,
  tela: string,
  testInfo: TestInfo,
  opcoes?: OpcoesAuditoria
) {
  // 1. Auditoria com tags WCAG 2.0 e 2.1 A e AA completas
  const resultados = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  // 2. Cobertura de regras específicas via withRules (ex: aria-dialog-name)
  const regrasExtras = opcoes?.withRules ?? ['aria-dialog-name'];
  if (regrasExtras.length > 0) {
    const resultadosExtras = await new AxeBuilder({ page })
      .withRules(regrasExtras)
      .analyze();
    const idsExistentes = new Set(resultados.violations.map((v) => v.id));
    for (const violacao of resultadosExtras.violations) {
      if (!idsExistentes.has(violacao.id)) {
        resultados.violations.push(violacao);
        idsExistentes.add(violacao.id);
      }
    }
  }

  const contagem = {
    critical: 0,
    serious: 0,
    moderate: 0,
    minor: 0,
  };

  const violacoesResumidas: ResumoViolacaoAxe[] = resultados.violations.map((v) => {
    const impacto = v.impact || 'minor';
    if (impacto in contagem) {
      contagem[impacto as keyof typeof contagem] += v.nodes.length;
    }
    return {
      regra: v.id,
      impacto: v.impact ?? null,
      ajuda: v.help,
      descricao: v.description,
      nos: v.nodes.map((n) => ({
        alvo: n.target as string[],
        html: n.html,
        falha: n.failureSummary,
      })),
    };
  });

  const nomeArquivo = `axe-${tela}.json`;
  const caminhoDir = path.resolve('test-results');
  if (!fs.existsSync(caminhoDir)) {
    fs.mkdirSync(caminhoDir, { recursive: true });
  }
  const caminhoArquivo = path.join(caminhoDir, nomeArquivo);
  fs.writeFileSync(caminhoArquivo, JSON.stringify(violacoesResumidas, null, 2), 'utf-8');

  await testInfo.attach(nomeArquivo, {
    path: caminhoArquivo,
    contentType: 'application/json',
  });

  console.log(
    `[A11Y] ${tela}: critical=${contagem.critical}, serious=${contagem.serious}, moderate=${contagem.moderate}, minor=${contagem.minor}`
  );

  const violacoesCriticasOuSerias = resultados.violations.filter(
    (v) => v.impact === 'serious' || v.impact === 'critical'
  );

  return {
    resultados,
    violacoes: resultados.violations,
    violacoesCriticasOuSerias,
    contagem,
  };
}

export async function auditarTela(
  page: Page,
  tela: string,
  testInfo: TestInfo,
  todasViolacoes: { tela: string; violacoes: ResumoViolacaoAxe[] }[],
  opcoes?: OpcoesAuditoria
) {
  const relatorio = await auditarAcessibilidade(page, tela, testInfo, opcoes);
  if (relatorio.violacoesCriticasOuSerias.length > 0) {
    todasViolacoes.push({
      tela,
      violacoes: relatorio.violacoesCriticasOuSerias.map((v) => ({
        regra: v.id,
        impacto: v.impact ?? null,
        ajuda: v.help,
        descricao: v.description,
        nos: v.nodes.map((n) => ({
          alvo: n.target as string[],
          html: n.html,
          falha: n.failureSummary,
        })),
      })),
    });
  }
  expect.soft(
    relatorio.violacoesCriticasOuSerias,
    `Violações sérias/críticas na tela ${tela}: ${JSON.stringify(relatorio.violacoesCriticasOuSerias, null, 2)}`
  ).toEqual([]);
  return relatorio;
}
