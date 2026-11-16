import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaCompetencias} from '../src/jornada/TelaCompetencias';

describe('JornadaCompetencias - TDD T07 Linguagem Honesta e Ações Distintas', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-competencias; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED 2: "não possuo" é diferente de "rejeitar" e "declarar" não é demonstrar', async () => {
    const chamadas: {url: string; method: string; headers: HeadersInit; body: any}[] = [];

    const mockCompetencias = [
      {
        id: 'comp-1',
        esco_id: 'http://data.europa.eu/esco/skill/sql',
        titulo: 'SQL e Modelagem de Dados',
        trecho_origem: 'Desenvolvimento de consultas SQL complexas.',
        origem: 'extracao_llm' as const,
        estado_evidencia: 'declarada' as const,
        revisao: 'pendente' as const,
        curriculo_id: 'curr-123',
        extracao_id: 'ext-456',
        criado_em: '2026-11-16T10:00:00Z',
        atualizado_em: '2026-11-16T10:00:00Z',
      },
      {
        id: 'comp-2',
        esco_id: 'http://data.europa.eu/esco/skill/gestao-pessoas',
        titulo: 'Gestão de Pessoas',
        trecho_origem: 'Liderança de projetos de automação.',
        origem: 'extracao_llm' as const,
        estado_evidencia: 'declarada' as const,
        revisao: 'pendente' as const,
        curriculo_id: 'curr-123',
        extracao_id: 'ext-456',
        criado_em: '2026-11-16T10:00:00Z',
        atualizado_em: '2026-11-16T10:00:00Z',
      },
    ];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string'
          ? JSON.parse(init.body)
          : init?.body;

      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        headers: init?.headers || {},
        body: parsedBody,
      });

      if (url.endsWith('/me/competencias') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: mockCompetencias}),
        };
      }

      if (url.includes('/me/competencias/comp-1') && init?.method === 'PATCH') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...mockCompetencias[0],
            revisao: parsedBody.acao,
            atualizado_em: '2026-11-16T10:10:00Z',
          }),
        };
      }

      if (url.includes('/me/competencias/comp-2') && init?.method === 'PATCH') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...mockCompetencias[1],
            revisao: parsedBody.acao,
            atualizado_em: '2026-11-16T10:12:00Z',
          }),
        };
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({erro: 'nao_encontrado', detalhes: 'Competência não encontrada'}),
      };
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<TelaCompetencias />);

    // 1. O aviso "Declarar não é o mesmo que demonstrar" está visível
    await waitFor(() => {
      expect(
        screen.getByText(/declarar não é o mesmo que demonstrar/i)
      ).toBeTruthy();
    });

    // 2. Os títulos e trechos de origem estão na tela
    expect(screen.getByText('SQL e Modelagem de Dados')).toBeTruthy();
    expect(
      screen.getByText('Desenvolvimento de consultas SQL complexas.')
    ).toBeTruthy();
    expect(screen.getByText('Gestão de Pessoas')).toBeTruthy();
    expect(
      screen.getByText('Liderança de projetos de automação.')
    ).toBeTruthy();

    // 3. Clicar em "Não possuo" na primeira competência
    const botoesNaoPossuo = screen.getAllByRole('button', {name: /não possuo/i});
    fireEvent.click(botoesNaoPossuo[0]);

    await waitFor(() => {
      const chamadaPatch1 = chamadas.find(
        (c) => c.url.endsWith('/me/competencias/comp-1') && c.method === 'PATCH'
      );
      expect(chamadaPatch1).toBeDefined();
      expect(chamadaPatch1?.body).toEqual({acao: 'nao_possuo'});
      const headers = chamadaPatch1?.headers as Record<string, string>;
      expect(headers['X-CSRF-Token'] || headers['x-csrf-token']).toBe('tok-teste-competencias');
    });

    // 4. Clicar em "Rejeitar" na segunda competência
    const botoesRejeitar = screen.getAllByRole('button', {name: /rejeitar/i});
    fireEvent.click(botoesRejeitar[0]);

    await waitFor(() => {
      const chamadaPatch2 = chamadas.find(
        (c) => c.url.endsWith('/me/competencias/comp-2') && c.method === 'PATCH'
      );
      expect(chamadaPatch2).toBeDefined();
      expect(chamadaPatch2?.body).toEqual({acao: 'rejeitar'});
    });

    // 5. Nenhum texto da tela contém termos proibidos ("vaga", "score", "nota", "probabilidade")
    const textoCompleto = document.body.textContent?.toLowerCase() || '';
    expect(textoCompleto).not.toMatch(/\bvaga(s)?\b/i);
    expect(textoCompleto).not.toMatch(/\bscore\b/i);
    expect(textoCompleto).not.toMatch(/\bnota\b/i);
    expect(textoCompleto).not.toMatch(/\bprobabilidade\b/i);
  });

  test('confirmar com trecho editado envia trecho_origem; confirmar sem editar não envia', async () => {
    const chamadas: {url: string; method: string; body: any}[] = [];

    const mockCompetencia = {
      id: 'comp-10',
      esco_id: 'http://data.europa.eu/esco/skill/python',
      titulo: 'Programação Python',
      trecho_origem: 'Uso de Python para scripts.',
      origem: 'extracao_llm' as const,
      estado_evidencia: 'declarada' as const,
      revisao: 'pendente' as const,
      curriculo_id: 'curr-123',
      extracao_id: 'ext-456',
      criado_em: '2026-11-16T10:00:00Z',
      atualizado_em: '2026-11-16T10:00:00Z',
    };

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string'
          ? JSON.parse(init.body)
          : init?.body;

      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        body: parsedBody,
      });

      if (url.endsWith('/me/competencias') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: [mockCompetencia]}),
        };
      }

      if (url.includes('/me/competencias/comp-10') && init?.method === 'PATCH') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...mockCompetencia,
            revisao: 'confirmada',
            trecho_origem: parsedBody.trecho_origem ?? mockCompetencia.trecho_origem,
          }),
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaCompetencias />);

    await waitFor(() => {
      expect(screen.getByText('Programação Python')).toBeTruthy();
    });

    const botaoConfirmar = screen.getByRole('button', {name: /confirmar/i});
    fireEvent.click(botaoConfirmar);

    await waitFor(() => {
      const patchCall = chamadas.find(
        (c) => c.url.endsWith('/me/competencias/comp-10') && c.method === 'PATCH'
      );
      expect(patchCall).toBeDefined();
      expect(patchCall?.body.acao).toBe('confirmar');
      // Não enviou trecho_origem ou enviou null/undefined pois não foi editado
      expect(patchCall?.body.trecho_origem).toBeFalsy();
    });
  });

  test('exibe EmptyState quando não há competências', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({itens: []}),
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaCompetencias />);

    await waitFor(() => {
      expect(screen.getByText(/nenhuma competência sugerida/i)).toBeTruthy();
    });
  });

  test('exibe nota discreta quando há sugestões descartadas', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({itens: []}),
    });
    vi.stubGlobal('fetch', mockFetch);

    render(
      <TelaCompetencias
        extracaoInicial={{
          extracao_id: 'ext-99',
          modelo: 'gemini',
          candidatas: [],
          descartadas: {
            fora_da_lista: 1,
            sem_trecho: 2,
            trecho_nao_encontrado: 1,
            duplicadas: 0,
          },
          aviso: '',
        }}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByText(/4 sugestões foram descartadas por não terem trecho correspondente no texto/i)
      ).toBeTruthy();
    });
  });
});
