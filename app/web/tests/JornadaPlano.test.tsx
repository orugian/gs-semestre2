import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeAll, beforeEach, describe, expect, test, vi} from 'vitest';
import {AreaJornada} from '../src/jornada/AreaJornada';
import {TelaComparacao} from '../src/jornada/TelaComparacao';
import {TelaPlano} from '../src/jornada/TelaPlano';
import {RespostaCaminho} from '../src/api/plano';
import fixtureComparacao from './fixtures/jornada_comparacao.json';
import fixturePlano from './fixtures/jornada_plano.json';

describe('JornadaPlano - Plano de Desenvolvimento e Checkpoints (D03, T07, T08)', () => {
  beforeAll(() => {
    if (typeof HTMLDialogElement !== 'undefined') {
      HTMLDialogElement.prototype.showModal =
        HTMLDialogElement.prototype.showModal ||
        function (this: HTMLDialogElement) {
          this.open = true;
        };
      HTMLDialogElement.prototype.close =
        HTMLDialogElement.prototype.close ||
        function (this: HTMLDialogElement) {
          this.open = false;
        };
    }
  });

  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-plano; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED: concluir checkpoint não demonstra e exercício não tem ação manual', async () => {
    const chamadas: {url: string; method: string; headers: Record<string, string>; body: any}[] = [];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string'
          ? JSON.parse(init.body)
          : init?.body;

      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        headers: (init?.headers as Record<string, string>) || {},
        body: parsedBody,
      });

      if (url.includes('/me/plano/checkpoints/cp-1') && init?.method === 'PATCH') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...fixturePlano.plano.checkpoints[0],
            status: 'concluido',
          }),
        };
      }

      if (url.includes('/me/plano') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixturePlano,
        };
      }

      if (url.includes('/me/tentativas') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            itens: [],
            ultima: null,
            melhor: null,
          }),
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    const onFazerExercicio = vi.fn();
    render(<TelaPlano onFazerExercicio={onFazerExercicio} />);

    // 1. Carregou o plano e exibe o cabeçalho com nome do destino e explicação da regra
    await waitFor(() => {
      expect(
        screen.getByText(/Plano de Transição - Analista de Monitoramento IoT/i)
      ).toBeTruthy();
      expect(
        screen.getByText(
          /Checkpoints ordenados por obrigatoriedade e estado de evidência/i
        )
      ).toBeTruthy();
    });

    // 2. Aviso institucional de que concluir checkpoint NÃO demonstra competência está visível
    const aviso = screen.getByText(
      /Concluir um checkpoint não torna a competência demonstrada/i
    );
    expect(aviso).toBeTruthy();

    // 3. Proibição de linguagem: nenhum texto contém "prazo", "semanas", "score", "vaga"
    const textoCompleto = document.body.textContent || '';
    expect(textoCompleto).not.toMatch(/\bprazo\b/i);
    expect(textoCompleto).not.toMatch(/\bsemanas\b/i);
    expect(textoCompleto).not.toMatch(/\bscore\b/i);
    expect(textoCompleto).not.toMatch(/\bvagas?\b/i);

    // 4. Checkpoint "estudar" (cp-1) tem botão para concluir
    const botaoConcluirEstudar = screen.getByRole('button', {
      name: /concluir checkpoint estudo de telemetria e sensores/i,
    });
    expect(botaoConcluirEstudar).toBeTruthy();

    fireEvent.click(botaoConcluirEstudar);

    // Verifica que enviou PATCH com CSRF
    await waitFor(() => {
      const chamadaPatch = chamadas.find(
        (c) => c.url.includes('/me/plano/checkpoints/cp-1') && c.method === 'PATCH'
      );
      expect(chamadaPatch).toBeTruthy();
      expect(chamadaPatch?.headers['X-CSRF-Token']).toBe('tok-teste-plano');
      expect(chamadaPatch?.body).toEqual({status: 'concluido'});
    });

    // 5. Checkpoint "exercicio" (cp-2) NÃO tem ação manual de concluir, tem "Fazer o exercício"
    expect(
      screen.queryByRole('button', {
        name: /concluir checkpoint exercício diagnóstico de iot/i,
      })
    ).toBeNull();

    const botaoFazerExercicio = screen.getByRole('button', {
      name: /fazer o exercício/i,
    });
    expect(botaoFazerExercicio).toBeTruthy();

    fireEvent.click(botaoFazerExercicio);
    expect(onFazerExercicio).toHaveBeenCalledTimes(1);

    // 6. ja_demonstrados e observações visíveis
    expect(screen.getByText(/já demonstradas anteriormente/i)).toBeTruthy();
    expect(screen.getByText(/req_demonstrado_1/i)).toBeTruthy();
    expect(
      screen.getByText(/Os checkpoints práticos podem ser realizados em paralelo/i)
    ).toBeTruthy();
  });

  test('404 exibe estado vazio com atalho para comparar destinos', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/me/plano')) {
        return {
          ok: false,
          status: 404,
          json: async () => ({
            erro: 'plano_nao_encontrado',
            detalhes: 'Você ainda não escolheu um destino.',
          }),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    const onIrParaComparacao = vi.fn();
    render(<TelaPlano onIrParaComparacao={onIrParaComparacao} />);

    await waitFor(() => {
      expect(screen.getByText(/nenhum plano ativo/i)).toBeTruthy();
      expect(
        screen.getByRole('button', {name: /comparar destinos/i})
      ).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', {name: /comparar destinos/i}));
    expect(onIrParaComparacao).toHaveBeenCalledTimes(1);
  });

  test('escolher destino na comparação chama POST /me/caminho com comparacao_id', async () => {
    const chamadas: {url: string; method: string; headers: Record<string, string>; body: any}[] = [];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string'
          ? JSON.parse(init.body)
          : init?.body;

      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        headers: (init?.headers as Record<string, string>) || {},
        body: parsedBody,
      });

      if (url.includes('/destinos')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            itens: [
              {
                destino_id: 'analista_processos',
                nome: 'Analista de Processos/Melhoria Contínua',
              },
            ],
          }),
        };
      }

      if (url.includes('/me/intencao')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({uf: 'SP'}),
        };
      }

      if (url.includes('/me/comparacoes') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixtureComparacao,
        };
      }

      if (url.includes('/me/caminho') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixturePlano,
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    const onDestinoEscolhido = vi.fn();
    const onIrParaPlano = vi.fn();

    render(
      <TelaComparacao
        onDestinoEscolhido={onDestinoEscolhido}
        onIrParaPlano={onIrParaPlano}
      />
    );

    // Seleciona destino e compara
    await waitFor(() => {
      expect(screen.getByRole('button', {name: /comparar/i})).toBeTruthy();
    });

    const checkbox = screen.getByLabelText(/Analista de Processos/i);
    fireEvent.click(checkbox);

    fireEvent.click(screen.getByRole('button', {name: /comparar/i}));

    // Exibe o cartão do destino comparado com o botão "Escolher este destino"
    await waitFor(() => {
      expect(
        screen.getAllByRole('button', {name: /escolher este destino/i}).length
      ).toBeGreaterThan(0);
    });

    const botoesEscolher = screen.getAllByRole('button', {
      name: /escolher este destino/i,
    });
    fireEvent.click(botoesEscolher[0]);

    // Verifica chamada POST /me/caminho com CSRF e comparacao_id
    await waitFor(() => {
      const chamadaCaminho = chamadas.find(
        (c) => c.url.includes('/me/caminho') && c.method === 'POST'
      );
      expect(chamadaCaminho).toBeTruthy();
      expect(chamadaCaminho?.headers['X-CSRF-Token']).toBe('tok-teste-plano');
      expect(chamadaCaminho?.body).toEqual({
        destino_id: 'analista_processos',
        comparacao_id: 'comp-789',
      });
    });

    expect(onDestinoEscolhido).toHaveBeenCalledTimes(1);
    expect(onIrParaPlano).toHaveBeenCalledTimes(1);
  });

  test('escolher novo destino quando já existe plano abre diálogo de confirmação', async () => {
    const chamadas: {url: string; method: string; headers: Record<string, string>; body: any}[] = [];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string'
          ? JSON.parse(init.body)
          : init?.body;

      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        headers: (init?.headers as Record<string, string>) || {},
        body: parsedBody,
      });

      if (url.includes('/destinos')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            itens: [
              {
                destino_id: 'analista_processos',
                nome: 'Analista de Processos/Melhoria Contínua',
              },
            ],
          }),
        };
      }

      if (url.includes('/me/intencao')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({uf: 'SP'}),
        };
      }

      if (url.includes('/me/comparacoes') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixtureComparacao,
        };
      }

      if (url.includes('/me/caminho') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixturePlano,
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    const onDestinoEscolhido = vi.fn();
    const onIrParaPlano = vi.fn();

    render(
      <TelaComparacao
        planoAtivo={fixturePlano as unknown as RespostaCaminho}
        onDestinoEscolhido={onDestinoEscolhido}
        onIrParaPlano={onIrParaPlano}
      />
    );

    await waitFor(() => {
      expect(screen.getByRole('button', {name: /comparar/i})).toBeTruthy();
    });

    fireEvent.click(screen.getByLabelText(/Analista de Processos/i));
    fireEvent.click(screen.getByRole('button', {name: /comparar/i}));

    await waitFor(() => {
      expect(
        screen.getAllByRole('button', {name: /escolher este destino/i}).length
      ).toBeGreaterThan(0);
    });

    const botoesEscolher = screen.getAllByRole('button', {
      name: /escolher este destino/i,
    });
    fireEvent.click(botoesEscolher[0]);

    // Abre diálogo de substituição
    await waitFor(() => {
      expect(screen.getByText(/substituir plano anterior\?/i)).toBeTruthy();
      expect(screen.queryByRole('dialog', {name: /substituir plano anterior\?/i})).toBeTruthy();
    });

    // Clica no botão de confirmação do diálogo
    const botaoConfirmarSubstituicao = screen.getByRole('button', {
      name: /substituir plano/i,
    });
    fireEvent.click(botaoConfirmarSubstituicao);

    await waitFor(() => {
      const chamadaCaminho = chamadas.find(
        (c) => c.url.includes('/me/caminho') && c.method === 'POST'
      );
      expect(chamadaCaminho).toBeTruthy();
      expect(chamadaCaminho?.body.destino_id).toBe('analista_processos');
    });

    expect(onDestinoEscolhido).toHaveBeenCalledTimes(1);
    expect(onIrParaPlano).toHaveBeenCalledTimes(1);
  });

  test('etapa 8 (Laboratório) no Stepper só aparece para analista_monitoramento_iot', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/auth/me')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'usr-1',
            email: 'usuario@teste.com',
            persona_demo: 'N',
          }),
        };
      }

      if (url.includes('/me/plano')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixturePlano, // destino_id: analista_monitoramento_iot
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<AreaJornada />);

    // Destino do plano ativo é analista_monitoramento_iot -> Etapa Laboratório está presente
    await waitFor(() => {
      expect(screen.getByText(/Laboratório/i)).toBeTruthy();
      expect(screen.getByText(/Plano/i)).toBeTruthy();
      expect(screen.getByText(/Exercício/i)).toBeTruthy();
    });
  });
});
