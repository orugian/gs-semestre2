import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaComparacao} from '../src/jornada/TelaComparacao';
import fixtureComparacao from './fixtures/jornada_comparacao.json';

const DESTINOS_TESTE = {
  itens: [
    {
      destino_id: 'analista_processos',
      nome: 'Analista de Processos/Melhoria Contínua',
      descricao: 'Otimização e modelagem de processos organizacionais.',
      requisitos: [
        {
          id_local: 'req-proc-1',
          esco_id: 'http://data.europa.eu/esco/skill/gestao-processos',
          titulo: 'Gestão de Processos de Negócio',
          obrigatorio: true,
        },
      ],
    },
    {
      destino_id: 'analista_dados_bi',
      nome: 'Analista de Dados/BI',
      descricao: 'Análise de dados e inteligência de negócios.',
      requisitos: [
        {
          id_local: 'req-dados-1',
          esco_id: 'http://data.europa.eu/esco/skill/sql',
          titulo: 'SQL e Modelagem de Dados',
          obrigatorio: true,
        },
      ],
    },
    {
      destino_id: 'analista_monitoramento_iot',
      nome: 'Analista de Monitoramento/IoT Industrial',
      descricao: 'Sensoriamento e monitoramento industrial.',
      requisitos: [
        {
          id_local: 'req-iot-1',
          esco_id: 'http://data.europa.eu/esco/skill/iot',
          titulo: 'Protocolos IoT',
          obrigatorio: true,
        },
      ],
    },
    {
      destino_id: 'desenvolvedor_software',
      nome: 'Desenvolvedor de Software',
      descricao: 'Construção de aplicações e serviços.',
      requisitos: [
        {
          id_local: 'req-dev-1',
          esco_id: 'http://data.europa.eu/esco/skill/programacao',
          titulo: 'Lógica de Programação',
          obrigatorio: true,
        },
      ],
    },
  ],
};

describe('JornadaComparacao - Comparação de Destinos sem Score (D07, T07, T17)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-comparacao; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED 1: obrigatório não atendido sempre visível, ordem preservada e sem score', async () => {
    const chamadas: {url: string; method: string; headers: HeadersInit; body: any}[] = [];

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

      if (url.endsWith('/destinos')) {
        return {
          ok: true,
          status: 200,
          json: async () => DESTINOS_TESTE,
        };
      }

      if (url.endsWith('/me/intencao') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            atividades_desejadas: ['Processos'],
            motivos: ['Transição'],
            horas_semana: 30,
            orcamento_mensal_brl: 500,
            uf: 'SP',
            atualizado_em: '2026-11-16T10:00:00Z',
          }),
        };
      }

      if (url.endsWith('/me/comparacoes') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixtureComparacao,
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<TelaComparacao />);

    // 1. Aguarda carregamento dos destinos
    await waitFor(() => {
      expect(screen.getByText('Analista de Processos/Melhoria Contínua')).toBeTruthy();
      expect(screen.getByText('Analista de Dados/BI')).toBeTruthy();
      expect(screen.getByText('Analista de Monitoramento/IoT Industrial')).toBeTruthy();
    });

    // 2. A pessoa escolhe analista_processos e depois analista_dados_bi
    const checkboxProcessos = screen.getByLabelText(/analista de processos/i);
    const checkboxDados = screen.getByLabelText(/analista de dados\/bi/i);

    fireEvent.click(checkboxProcessos);
    fireEvent.click(checkboxDados);

    // 3. Clica em "Comparar"
    const botaoComparar = screen.getByRole('button', {name: /^comparar$/i});
    expect(botaoComparar.hasAttribute('disabled')).toBe(false);
    fireEvent.click(botaoComparar);

    // 4. POST /api/me/comparacoes recebe destinos na ordem exata e CSRF
    await waitFor(() => {
      const chamadaPost = chamadas.find(
        (c) => c.url.endsWith('/me/comparacoes') && c.method === 'POST'
      );
      expect(chamadaPost).toBeDefined();
      expect(chamadaPost?.body).toEqual({
        destinos: ['analista_processos', 'analista_dados_bi'],
        uf: 'SP',
      });
      const headers = chamadaPost?.headers as Record<string, string>;
      expect(headers['X-CSRF-Token'] || headers['x-csrf-token']).toBe('tok-teste-comparacao');
    });

    // 5. Com a fixture, os cartões aparecem na ordem escolhida: processos -> dados
    await waitFor(() => {
      const titulosCartoes = screen.getAllByRole('heading', {level: 3});
      const nomesDestinos = titulosCartoes
        .map((h) => h.textContent || '')
        .filter((t) => t.includes('Analista'));

      expect(nomesDestinos[0]).toContain('Analista de Processos/Melhoria Contínua');
      expect(nomesDestinos[1]).toContain('Analista de Dados/BI');
    });

    // 6. Cada obrigatório de obrigatorios_nao_atendidos aparece no seu cartão com o estado
    expect(
      screen.getAllByText('Mapeamento e Modelagem de Processos').length
    ).toBeGreaterThan(0);
    expect(
      screen.getAllByText('SQL e Modelagem de Dados').length
    ).toBeGreaterThan(0);

    // 7. O aviso da API aparece em destaque
    expect(
      screen.getByText(
        'Sem nota única: cada dimensão é apresentada separadamente e a decisão é sua.'
      )
    ).toBeTruthy();

    // 8. O mercado mostra fonte, "observado" e o período
    expect(screen.getAllByText(/Novo Caged \/ MTE/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/observado/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/202001[–-]202509/).length).toBeGreaterThan(0);

    // 9. Nenhum texto nos cartões contém score, nota, ranking, melhor, vaga, probabilidade, %
    const cartoes = screen.getAllByTestId('cartao-destino');
    expect(cartoes.length).toBe(2);
    for (const cartao of cartoes) {
      const texto = cartao.textContent || '';
      expect(texto).not.toMatch(/\bscore\b/i);
      expect(texto).not.toMatch(/\bnota\b/i);
      expect(texto).not.toMatch(/\branking\b/i);
      expect(texto).not.toMatch(/\bmelhor\b/i);
      expect(texto).not.toMatch(/\bvaga(s)?\b/i);
      expect(texto).not.toMatch(/\bprobabilidade\b/i);
      expect(texto).not.toContain('%');
    }
  });

  test('seleção: 4ª escolha é impedida com mensagem; Comparar desabilitado com 0 escolhidos', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/destinos')) {
        return {
          ok: true,
          status: 200,
          json: async () => DESTINOS_TESTE,
        };
      }
      if (url.endsWith('/me/intencao')) {
        return {
          ok: false,
          status: 404,
          json: async () => ({erro: 'nao_encontrado', detalhes: ''}),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaComparacao />);

    await waitFor(() => {
      expect(screen.getByText('Analista de Processos/Melhoria Contínua')).toBeTruthy();
    });

    const botaoComparar = screen.getByRole('button', {name: /^comparar$/i});
    const estaDesabilitado = (el: HTMLElement) =>
      el.getAttribute('aria-disabled') === 'true' || el.hasAttribute('disabled');

    expect(estaDesabilitado(botaoComparar)).toBe(true);

    const cb1 = screen.getByLabelText(/analista de processos/i);
    const cb2 = screen.getByLabelText(/analista de dados\/bi/i);
    const cb3 = screen.getByLabelText(/analista de monitoramento/i);
    const cb4 = screen.getByLabelText(/desenvolvedor de software/i);

    fireEvent.click(cb1);
    expect(estaDesabilitado(botaoComparar)).toBe(false);

    fireEvent.click(cb2);
    fireEvent.click(cb3);

    // Tenta selecionar o 4º
    fireEvent.click(cb4);

    await waitFor(() => {
      expect(screen.getByText(/máximo 3 destinos/i)).toBeTruthy();
    });
    expect((cb4 as HTMLInputElement).checked).toBe(false);
  });

  test('mercado indisponível mostra texto do motivo e nenhum número', async () => {
    const fixtureMercadoIndisponivel = {
      ...fixtureComparacao,
      destinos: [
        {
          ...fixtureComparacao.destinos[0],
          dimensoes: {
            ...fixtureComparacao.destinos[0].dimensoes,
            mercado: {
              disponivel: false,
              natureza: 'indisponivel',
              motivo: 'uf_nao_informada',
            },
          },
        },
      ],
    };

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/destinos')) {
        return {ok: true, status: 200, json: async () => DESTINOS_TESTE};
      }
      if (url.endsWith('/me/intencao')) {
        return {ok: false, status: 404, json: async () => ({})};
      }
      if (url.endsWith('/me/comparacoes') && init?.method === 'POST') {
        return {ok: true, status: 201, json: async () => fixtureMercadoIndisponivel};
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaComparacao />);

    await waitFor(() => {
      expect(screen.getByLabelText(/analista de processos/i)).toBeTruthy();
    });

    fireEvent.click(screen.getByLabelText(/analista de processos/i));
    fireEvent.click(screen.getByRole('button', {name: /^comparar$/i}));

    await waitFor(() => {
      expect(screen.getByText('Informe a UF para ver o mercado observado')).toBeTruthy();
    });

    // Nenhum número ou dado de admissão no cartão
    expect(screen.queryByText(/645/)).toBeNull();
  });

  test('tradução de estados, trecho de origem em declarada e aviso de entrada conflitante', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/destinos')) {
        return {ok: true, status: 200, json: async () => DESTINOS_TESTE};
      }
      if (url.endsWith('/me/intencao')) {
        return {ok: false, status: 404, json: async () => ({})};
      }
      if (url.endsWith('/me/comparacoes') && init?.method === 'POST') {
        return {ok: true, status: 201, json: async () => fixtureComparacao};
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaComparacao />);

    await waitFor(() => {
      expect(screen.getByLabelText(/analista de processos/i)).toBeTruthy();
    });

    fireEvent.click(screen.getByLabelText(/analista de processos/i));
    fireEvent.click(screen.getByRole('button', {name: /^comparar$/i}));

    await waitFor(() => {
      // Trecho de origem em requisito declarada
      expect(
        screen.getByText(/Atuação com metodologia Kanban e Scrum em processos industriais/i)
      ).toBeTruthy();

      // Motivo traduzido de desconhecida
      expect(screen.getByText('sem informação suficiente')).toBeTruthy();

      // Motivo traduzido de lacuna
      expect(screen.getByText('você informou que não possui')).toBeTruthy();

      // Aviso de entrada conflitante
      expect(
        screen.getByText(/informações conflitantes; revise suas competências/i)
      ).toBeTruthy();
    });
  });

  test('caso com todos os obrigatórios demonstrados exibe mensagem positiva', async () => {
    const fixtureTodosDemonstrados = {
      ...fixtureComparacao,
      destinos: [
        {
          ...fixtureComparacao.destinos[0],
          dimensoes: {
            ...fixtureComparacao.destinos[0].dimensoes,
            obrigatorios_nao_atendidos: [],
          },
          situacao_obrigatorios: 'todos_demonstrados',
        },
      ],
    };

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/destinos')) {
        return {ok: true, status: 200, json: async () => DESTINOS_TESTE};
      }
      if (url.endsWith('/me/intencao')) {
        return {ok: false, status: 404, json: async () => ({})};
      }
      if (url.endsWith('/me/comparacoes') && init?.method === 'POST') {
        return {ok: true, status: 201, json: async () => fixtureTodosDemonstrados};
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaComparacao />);

    await waitFor(() => {
      expect(screen.getByLabelText(/analista de processos/i)).toBeTruthy();
    });

    fireEvent.click(screen.getByLabelText(/analista de processos/i));
    fireEvent.click(screen.getByRole('button', {name: /^comparar$/i}));

    await waitFor(() => {
      expect(screen.getByText(/todos os obrigatórios demonstrados/i)).toBeTruthy();
    });
  });

  test('legenda de estados visível e botão Nova Comparação retorna à seleção', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/destinos')) {
        return {ok: true, status: 200, json: async () => DESTINOS_TESTE};
      }
      if (url.endsWith('/me/intencao')) {
        return {ok: false, status: 404, json: async () => ({})};
      }
      if (url.endsWith('/me/comparacoes') && init?.method === 'POST') {
        return {ok: true, status: 201, json: async () => fixtureComparacao};
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaComparacao />);

    await waitFor(() => {
      expect(screen.getByLabelText(/analista de processos/i)).toBeTruthy();
    });

    fireEvent.click(screen.getByLabelText(/analista de processos/i));
    fireEvent.click(screen.getByRole('button', {name: /^comparar$/i}));

    // Verifica legenda
    await waitFor(() => {
      expect(screen.getByText(/evidência revisada por critério explícito/i)).toBeTruthy();
      expect(screen.getByText(/informada pela pessoa, não comprovada/i)).toBeTruthy();
      expect(screen.getByText(/informação insuficiente, não inaptidão/i)).toBeTruthy();
      expect(screen.getByText(/ausência identificada/i)).toBeTruthy();
    });

    // Clica em "Nova comparação"
    const botaoNova = screen.getByRole('button', {name: /nova comparação/i});
    fireEvent.click(botaoNova);

    // Volta para os seletores
    await waitFor(() => {
      expect(screen.getByRole('button', {name: /^comparar$/i})).toBeTruthy();
    });
  });
});
