import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';

import App from '../src/App';
import {TelaMercado} from '../src/mercado/TelaMercado';
import {
  formatarCompetencia,
  formatarNumero,
  gerarIndicesTicks,
} from '../src/mercado/formatacao';
import mercadoAbstencao from './fixtures/mercado_abstencao.json';
import mercadoElegivel from './fixtures/mercado_elegivel.json';

describe('TelaMercado', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test('formatação de competência e número pt-BR', () => {
    expect(formatarCompetencia('202509')).toBe('09/2025');
    expect(formatarCompetencia('202001')).toBe('01/2020');
    expect(formatarCompetencia(null)).toBe('—');
    expect(formatarNumero(1234.56, 1)).toBe('1.234,6');
    expect(formatarNumero(1.77777, 1)).toBe('1,8');
  });

  test('exibe observado e estimativa retrospectiva com metadados T17', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/mercado/analista_dados_bi?uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mercadoElegivel,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<App />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/mercado/analista_dados_bi?uf=SP');
    });

    // Rótulos de natureza visíveis em palavras
    const observados = await screen.findAllByText('Observado');
    expect(observados.length).toBeGreaterThan(0);

    const previstos = await screen.findAllByText(/Estimativa retrospectiva/i);
    expect(previstos.length).toBeGreaterThan(0);

    // Metadados T17 do bloco observado
    expect(screen.getByText(mercadoElegivel.observado.fonte)).toBeTruthy();
    expect(screen.getAllByText(mercadoElegivel.observado.populacao).length).toBeGreaterThan(0);
    expect(screen.getAllByText(mercadoElegivel.observado.unidade).length).toBeGreaterThan(0);
    expect(screen.getByText(/01\/2020[–-]09\/2025/)).toBeTruthy();

    // Metadados T17 do bloco previsto
    expect(screen.getByText(mercadoElegivel.previsto.fonte)).toBeTruthy();
    expect(screen.getAllByText(mercadoElegivel.previsto.unidade).length).toBeGreaterThan(0);
    expect(screen.getByText(/01\/2025[–-]09\/2025/)).toBeTruthy();

    // Avisos presentes
    for (const aviso of mercadoElegivel.avisos) {
      expect(screen.getByText(aviso)).toBeTruthy();
    }

    // Amostra Adzuna
    expect(screen.getByText('Amostra Adzuna indisponível')).toBeTruthy();
    expect(screen.getByText(mercadoElegivel.amostra_adzuna.motivo)).toBeTruthy();

    // Nenhuma ocorrência de termo proibido (ex: "vaga")
    const corpoTexto = document.body.textContent ?? '';
    expect(corpoTexto.toLowerCase()).not.toContain('vaga');
    expect(corpoTexto.toLowerCase()).not.toContain('probabilidade de emprego');
    expect(corpoTexto.toLowerCase()).not.toContain('probabilidade de contratação');
    expect(corpoTexto.toLowerCase()).not.toContain('vale a pena');
    expect(corpoTexto.toLowerCase()).not.toContain('garantia');
  });

  test('trocar UF para AC faz nova chamada com uf=AC e exibe abstenção com média 1,8 e contexto regional Norte', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mercadoElegivel,
        } as Response);
      }
      if (url.includes('uf=AC')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mercadoAbstencao,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    let ufAtual = 'SP';
    const {rerender} = render(
      <TelaMercado
        destino="analista_dados_bi"
        uf={ufAtual}
        onUfChange={(novaUf) => {
          ufAtual = novaUf;
        }}
      />
    );

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/mercado/analista_dados_bi?uf=SP');
    });

    // Troca de UF para AC
    ufAtual = 'AC';
    rerender(
      <TelaMercado
        destino="analista_dados_bi"
        uf={ufAtual}
        onUfChange={(novaUf) => {
          ufAtual = novaUf;
        }}
      />
    );

    // Aguarda mensagem de abstenção com '1,8' e 'mínimo 10'
    expect(
      await screen.findByText(/Série insuficiente nesta UF para estimar \(média de 1,8 admissões por trimestre no treino; mínimo 10\)/)
    ).toBeTruthy();

    expect(fetchMock).toHaveBeenCalledWith('/api/mercado/analista_dados_bi?uf=AC');

    // Não deve exibir bloco de estimativa retrospectiva com número previsto
    expect(screen.queryAllByText('Estimativa retrospectiva (2025)').length).toBe(0);

    // Exibe contexto regional com 'Norte'
    expect(screen.getByText(/Região: Norte/)).toBeTruthy();
    const contextRegional = screen.getAllByText('Contexto regional observado');
    expect(contextRegional.length).toBeGreaterThan(0);
    expect(screen.getByText(mercadoAbstencao.abstencao.contexto_regional.populacao)).toBeTruthy();

    // Verificação de ausência de termos proibidos
    const corpoTexto = document.body.textContent ?? '';
    expect(corpoTexto.toLowerCase()).not.toContain('vaga');
  });

  test('valor null em série gera "sem dado" na tabela alternativa e nunca 0', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('uf=AC')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mercadoAbstencao,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<TelaMercado destino="analista_dados_bi" uf="AC" />);

    // Aguarda o carregamento dos dados
    const gatilhos = await screen.findAllByRole('button', {name: /Ver tabela de dados da série/i});
    expect(gatilhos.length).toBeGreaterThan(0);
    fireEvent.click(gatilhos[0]);

    // Na competência 202508 do observado em AC o valor é null -> deve exibir "sem dado"
    const semDados = await screen.findAllByText('sem dado');
    expect(semDados.length).toBeGreaterThan(0);
  });

  test('erro 503 exibe "Dados de mercado indisponíveis no momento" sem expor detalhes técnicos', async () => {
    const fetchMock = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 503,
        json: async () => ({
          erro: 'servico_indisponivel',
          detalhes: 'Internal Database Crash at postgres://secret@10.0.0.1:5432/db',
        }),
      } as Response);
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<TelaMercado destino="analista_dados_bi" uf="SP" />);

    expect(
      await screen.findByText('Dados de mercado indisponíveis no momento')
    ).toBeTruthy();

    const corpoTexto = document.body.textContent ?? '';
    expect(corpoTexto).not.toContain('Internal Database Crash');
    expect(corpoTexto).not.toContain('postgres://');
    expect(corpoTexto).not.toContain('servico_indisponivel');
  });

  test('erro 404 exibe mensagem de detalhes da API', async () => {
    const fetchMock = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 404,
        json: async () => ({
          erro: 'nao_encontrado',
          detalhes: 'Destino não encontrado na base de dados',
        }),
      } as Response);
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<TelaMercado destino="invalido" uf="SP" />);

    expect(
      await screen.findByText('Destino não encontrado na base de dados')
    ).toBeTruthy();
  });

  test('item 1: gráfico de estimativa retrospectiva vs realizado renderiza 2 séries no SVG, legenda com Realizado e tabela com erro absoluto', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/mercado/analista_dados_bi?uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mercadoElegivel,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<TelaMercado destino="analista_dados_bi" uf="SP" />);

    // Aguarda o card de Estimativa Retrospectiva carregar
    expect(
      await screen.findByRole('heading', {name: 'Estimativa retrospectiva (2025)'})
    ).toBeTruthy();

    const svgEstimativa = screen.getByRole('img', {
      name: /Gráfico de estimativa retrospectiva e valores realizados/i,
    });

    // SVG deve ter 2 séries com data-serie distintos (ex: path e círculos)
    const seriesRealizado = svgEstimativa.querySelectorAll('[data-serie="realizado"]');
    const seriesPrevisto = svgEstimativa.querySelectorAll('[data-serie="previsto"]');
    expect(seriesRealizado.length).toBeGreaterThan(0);
    expect(seriesPrevisto.length).toBeGreaterThan(0);

    // Legenda do bloco de estimativa deve conter "Realizado" e NÃO conter "Observado"
    const containerEstimativa = svgEstimativa.closest('div');
    expect(containerEstimativa).toBeTruthy();
    expect(containerEstimativa?.textContent).toContain('Realizado (admissões no trimestre seguinte)');
    expect(containerEstimativa?.textContent).toContain('Estimativa retrospectiva (2025)');
    expect(containerEstimativa?.textContent).not.toContain('Observado');

    // Tabela alternativa mostra colunas de competência de origem, estimativa, realizado e erro absoluto
    const botoesTabela = screen.getAllByRole('button', {name: /Ver tabela de dados da série/i});
    fireEvent.click(botoesTabela[1]);

    expect(screen.getByText('Competência de origem')).toBeTruthy();
    expect(screen.getByText('Estimativa')).toBeTruthy();
    expect(screen.getByText('Realizado')).toBeTruthy();
    expect(screen.getByText('Erro absoluto')).toBeTruthy();
    // 5459 - 5112 = 347
    expect(screen.getByText('347')).toBeTruthy();
  });

  test('item 2: função gerarIndicesTicks gera no máximo 7 ticks uniformes incluindo extremos e omitindo penúltimo em colisão', () => {
    // Caso com 69 pontos (01/2020 a 09/2025: sobreposição de 07/2025 sobre 09/2025)
    const ticks69 = gerarIndicesTicks(69, 7);
    expect(ticks69.length).toBeLessThanOrEqual(7);
    expect(ticks69[0]).toBe(0);
    expect(ticks69[ticks69.length - 1]).toBe(68);
    // Índice 66 (07/2025) deve ser omitido para não colidir com 68 (09/2025)
    expect(ticks69).not.toContain(66);
    expect(ticks69).toContain(55);

    // Limites de intervalo
    expect(gerarIndicesTicks(0, 7)).toEqual([]);
    expect(gerarIndicesTicks(1, 7)).toEqual([0]);
    expect(gerarIndicesTicks(3, 7)).toEqual([0, 1, 2]);
  });

  test('item 4: SVG do gráfico não tem width numérico fixo, tem viewBox e preserveAspectRatio, e tabelas têm container acessível', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/mercado/analista_dados_bi?uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => mercadoElegivel,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<TelaMercado destino="analista_dados_bi" uf="SP" />);

    expect(
      await screen.findByRole('heading', {name: 'Estimativa retrospectiva (2025)'})
    ).toBeTruthy();

    const svgs = document.querySelectorAll('svg[role="img"]');
    expect(svgs.length).toBeGreaterThan(0);
    svgs.forEach((svg) => {
      expect(svg.getAttribute('viewBox')).toBeTruthy();
      const width = svg.getAttribute('width');
      // Não pode ter width numérico fixo (ex: "640" ou "640px"); aceita-se "100%" ou omitido com class/style
      expect(width === '100%' || width === null).toBe(true);
      expect(svg.getAttribute('preserveAspectRatio')).toBe('xMidYMid meet');
    });

    // Containers de tabelas largas devem ter overflow-x e rótulo acessível
    const regioes = screen.getAllByRole('region');
    expect(regioes.length).toBeGreaterThan(0);
    regioes.forEach((r) => {
      expect(r.getAttribute('aria-label')).toBeTruthy();
      expect(r.className).toContain('overflow-x-auto');
    });
  });
  test('amostra Adzuna disponível mostra contagens, atribuição e data, separada do Caged (D05a)', async () => {
    const comAmostra = {
      ...mercadoElegivel,
      amostra_adzuna: {
        disponivel: true,
        natureza: 'amostra_pontual',
        motivo: 'Amostra pontual Adzuna de 16/11/2026: contagem de anúncios indexados no dia da coleta.',
        fonte: 'Adzuna API (anúncios agregados de terceiros)',
        atribuicao: 'Jobs by Adzuna (https://www.adzuna.com.br)',
        unidade: 'anúncios publicados que correspondem ao termo de busca',
        populacao: 'Anúncios indexados pela Adzuna no Brasil no dia da coleta.',
        coletado_em: '2026-11-16T13:30:00Z',
        itens: [
          {territorio: 'SP', termo_busca: 'analista de dados', contagem_anuncios: 274},
          {territorio: 'BR', termo_busca: 'analista de dados', contagem_anuncios: 1036},
          {territorio: 'RJ', termo_busca: 'analista de dados', contagem_anuncios: null},
        ],
      },
    };
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ok: true, status: 200, json: async () => comAmostra} as Response)
    );

    render(<TelaMercado destino="analista_dados_bi" uf="SP" onUfChange={() => {}} />);

    expect(await screen.findByText('Amostra pontual Adzuna')).toBeTruthy();
    expect(screen.getByText('Jobs by Adzuna (https://www.adzuna.com.br)')).toBeTruthy();
    expect(screen.getByText(comAmostra.amostra_adzuna.motivo)).toBeTruthy();
    expect(screen.getByText('1.036')).toBeTruthy();
    expect(screen.getByText('274')).toBeTruthy();
    expect(screen.getByText('não disponível')).toBeTruthy();
    expect(screen.queryByText('Amostra Adzuna indisponível')).toBeNull();
    expect((document.body.textContent ?? '').toLowerCase()).not.toContain('vaga');
  });});
