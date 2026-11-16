import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';

import App from '../src/App';
import {PainelTecnico} from '../src/mercado/PainelTecnico';
import modelosElegivel from './fixtures/modelos_elegivel.json';

describe('PainelTecnico', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test('exibe os 6 modelos na ordem da API com tipo RNA, Badge no sazonal e Promovido Não', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/mercado/analista_dados_bi/modelos?uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => modelosElegivel,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<PainelTecnico destino="analista_dados_bi" uf="SP" />);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/mercado/analista_dados_bi/modelos?uf=SP');
    });

    // 1. Critério de promoção e status não decidida legível visíveis
    expect(await screen.findByText(modelosElegivel.criterio_promocao.criterio)).toBeTruthy();
    expect(screen.getAllByText('não decidida').length).toBeGreaterThan(0);

    // 2. Avisos visíveis
    for (const aviso of modelosElegivel.avisos) {
      expect(screen.getByText(aviso)).toBeTruthy();
    }

    // 3. Tabela com caption acessível
    expect(
      screen.getByText(/Tabela comparativa dos 6 modelos preditivos/i)
    ).toBeTruthy();

    // 4. Os 6 modelos com nomes legíveis padronizados
    const nomesLegiveis = [
      'Persistência',
      'Sazonal (ano anterior)',
      'Ridge',
      'Random Forest',
      'HistGradientBoosting',
      'MLP (rede neural)',
    ];
    for (const nome of nomesLegiveis) {
      expect(screen.getAllByText(nome).length).toBeGreaterThan(0);
    }

    // 5. 'mlp' com tipo RNA
    const tiposRna = screen.getAllByText('RNA');
    expect(tiposRna.length).toBeGreaterThan(0);

    // 6. Badge "Exibido ao usuário" apenas no sazonal
    const badges = screen.getAllByText('Exibido ao usuário');
    expect(badges.length).toBe(1);

    // 7. Coluna "Promovido" com "Não" para todos os 6 modelos
    const naos = screen.getAllByText('Não');
    expect(naos.length).toBe(6);

    // 8. Model card do mlp mostra hidden_layers
    expect(screen.getByText(/hidden_layers/)).toBeTruthy();

    // 9. Ausência de status cru e id de modelo cru no DOM
    const corpoTexto = document.body.textContent ?? '';
    expect(corpoTexto).not.toContain('nao_decidida');
    expect(corpoTexto).not.toContain('hist_gradient_boosting');

    // 10. Nenhuma ocorrência de termo proibido
    expect(corpoTexto.toLowerCase()).not.toContain('vaga');
    expect(corpoTexto.toLowerCase()).not.toContain('probabilidade de emprego');
    expect(corpoTexto.toLowerCase()).not.toContain('probabilidade de contratação');
    expect(corpoTexto.toLowerCase()).not.toContain('vale a pena');
    expect(corpoTexto.toLowerCase()).not.toContain('garantia');
  });

  test('navegação entre abas no App renderiza painel técnico', async () => {
    const fetchMock = vi.fn().mockImplementation((url: string) => {
      if (url.includes('/api/mercado/analista_dados_bi?uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => ({
            destino: 'analista_dados_bi',
            uf: 'SP',
            uf_codigo: '35',
            observado: {
              natureza: 'observado',
              fonte: 'Novo Caged',
              populacao: 'Superior',
              unidade: 'admissões por mês',
              referencia_temporal: {inicio: '202001', fim: '202509'},
              serie: [],
            },
            previsto: null,
            abstencao: null,
            amostra_adzuna: {disponivel: false, natureza: 'amostra', motivo: 'Snapshot indisponível'},
            avisos: [],
          }),
        } as Response);
      }
      if (url.includes('/api/mercado/analista_dados_bi/modelos?uf=SP')) {
        return Promise.resolve({
          ok: true,
          status: 200,
          json: async () => modelosElegivel,
        } as Response);
      }
      return Promise.reject(new Error(`URL não esperada: ${url}`));
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<App />);

    // Clica na aba "Painel técnico"
    const abaPainel = screen.getByRole('tab', {name: 'Painel técnico'});
    fireEvent.click(abaPainel);

    // Aguarda carregar dados do painel técnico
    expect(
      await screen.findByText('Painel técnico de modelos preditivos (R06)')
    ).toBeTruthy();

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith('/api/mercado/analista_dados_bi/modelos?uf=SP');
    });

    expect(screen.getByText('MLP (rede neural)')).toBeTruthy();
  });

  test('trata erro 503 no painel técnico sem vazar detalhes técnicos', async () => {
    const fetchMock = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 503,
        json: async () => ({
          erro: 'servico_indisponivel',
          detalhes: 'Internal Database Failure at replica-02',
        }),
      } as Response);
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<PainelTecnico destino="analista_dados_bi" uf="SP" />);

    expect(
      await screen.findByText('Dados de mercado indisponíveis no momento')
    ).toBeTruthy();

    const corpoTexto = document.body.textContent ?? '';
    expect(corpoTexto).not.toContain('replica-02');
    expect(corpoTexto).not.toContain('servico_indisponivel');
  });

  test('trata erro 404 no painel técnico exibindo mensagem da API', async () => {
    const fetchMock = vi.fn().mockImplementation(() => {
      return Promise.resolve({
        ok: false,
        status: 404,
        json: async () => ({
          erro: 'nao_encontrado',
          detalhes: 'Destino ou UF inexistente no painel',
        }),
      } as Response);
    });

    vi.stubGlobal('fetch', fetchMock);

    render(<PainelTecnico destino="inexistente" uf="SP" />);

    expect(
      await screen.findByText('Destino ou UF inexistente no painel')
    ).toBeTruthy();
  });
});
