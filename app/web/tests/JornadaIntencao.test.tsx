import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaIntencao} from '../src/jornada/TelaIntencao';

describe('JornadaIntencao - Registro e Validação de Intenção Profissional', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-intencao; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED 2: salva intenção e exibe motivos redigidos', async () => {
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

      if (url.endsWith('/me/intencao') && (!init?.method || init.method === 'GET')) {
        return {
          ok: false,
          status: 404,
          json: async () => ({
            erro: 'nao_encontrado',
            detalhes: 'Intenção ainda não cadastrada.',
          }),
        };
      }

      if (url.endsWith('/me/intencao') && init?.method === 'PUT') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            atividades_desejadas: parsedBody.atividades_desejadas,
            motivos: ['Quero mudar de área profissional. Contato: [EMAIL].'],
            horas_semana: parsedBody.horas_semana,
            orcamento_mensal_brl: parsedBody.orcamento_mensal_brl,
            uf: parsedBody.uf,
            atualizado_em: '2026-11-16T16:00:00Z',
          }),
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<TelaIntencao />);

    // 1. O formulário carrega e inicia vazio (404 é tratado como estado vazio)
    await waitFor(() => {
      expect(screen.getByRole('heading', {level: 2, name: /intenção/i})).toBeTruthy();
    });

    // 2. Preencher atividade desejada e adicionar à lista
    const inputNovaAtividade = screen.getByLabelText(/nova atividade desejada/i);
    fireEvent.change(inputNovaAtividade, {
      target: {value: 'Automação de processos industriais'},
    });
    fireEvent.click(screen.getByRole('button', {name: /adicionar atividade/i}));

    expect(screen.getByText('Automação de processos industriais')).toBeTruthy();

    // 3. Preencher motivo com dado sensível que a API redigirá
    const inputNovoMotivo = screen.getByLabelText(/novo motivo/i);
    fireEvent.change(inputNovoMotivo, {
      target: {value: 'Quero mudar de área profissional. Contato: dev@exemplo.com.'},
    });
    fireEvent.click(screen.getByRole('button', {name: /adicionar motivo/i}));

    expect(
      screen.getByText('Quero mudar de área profissional. Contato: dev@exemplo.com.')
    ).toBeTruthy();

    // 4. Preencher horas por semana
    const inputHoras = screen.getByLabelText(/horas por semana/i);
    fireEvent.change(inputHoras, {target: {value: '30'}});

    // 5. Preencher orçamento mensal
    const inputOrcamento = screen.getByLabelText(/orçamento mensal/i);
    fireEvent.change(inputOrcamento, {target: {value: '500'}});

    // 6. Selecionar UF
    const selectUf = screen.getByLabelText(/unidade federativa|uf/i);
    fireEvent.change(selectUf, {target: {value: 'SP'}});

    // 7. Clicar em salvar
    const botaoSalvar = screen.getByRole('button', {name: /salvar/i});
    fireEvent.click(botaoSalvar);

    // 8. PUT /api/me/intencao é chamado com corpo esperado e CSRF
    await waitFor(() => {
      const chamadaPut = chamadas.find(
        (c) => c.url.endsWith('/me/intencao') && c.method === 'PUT'
      );
      expect(chamadaPut).toBeDefined();
      expect(chamadaPut?.body).toEqual({
        atividades_desejadas: ['Automação de processos industriais'],
        motivos: ['Quero mudar de área profissional. Contato: dev@exemplo.com.'],
        horas_semana: 30,
        orcamento_mensal_brl: 500,
        uf: 'SP',
      });
      const headers = chamadaPut?.headers as Record<string, string>;
      expect(headers['X-CSRF-Token'] || headers['x-csrf-token']).toBe('tok-teste-intencao');
    });

    // 9. Tela mostra "Salvo em" e os motivos devolvidos REDIGIDOS com [EMAIL]
    await waitFor(() => {
      expect(screen.getByText(/salvo em/i)).toBeTruthy();
      expect(
        screen.getByText('Quero mudar de área profissional. Contato: [EMAIL].')
      ).toBeTruthy();
    });
  });

  test('validações no cliente: horas 0 e 81, 11 atividades, motivo com 301 chars impedem chamada', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/me/intencao')) {
        return {
          ok: false,
          status: 404,
          json: async () => ({erro: 'nao_encontrado'}),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaIntencao />);

    await waitFor(() => {
      expect(screen.getByRole('heading', {level: 2, name: /intenção/i})).toBeTruthy();
    });

    const inputHoras = screen.getByLabelText(/horas por semana/i);
    const selectUf = screen.getByLabelText(/unidade federativa|uf/i);
    const botaoSalvar = screen.getByRole('button', {name: /salvar/i});

    // 1. Horas = 0
    fireEvent.change(inputHoras, {target: {value: '0'}});
    fireEvent.change(selectUf, {target: {value: 'SP'}});
    fireEvent.click(botaoSalvar);

    await waitFor(() => {
      expect(screen.getByText(/horas.*entre 1 e 80/i)).toBeTruthy();
    });

    // 2. Horas = 81
    fireEvent.change(inputHoras, {target: {value: '81'}});
    fireEvent.click(botaoSalvar);

    await waitFor(() => {
      expect(screen.getByText(/horas.*entre 1 e 80/i)).toBeTruthy();
    });

    // 3. Adicionar mais de 10 atividades (ao tentar adicionar a 11ª)
    const inputAtividade = screen.getByLabelText(/nova atividade desejada/i);
    const botaoAddAtividade = screen.getByRole('button', {name: /adicionar atividade/i});

    for (let i = 1; i <= 10; i++) {
      fireEvent.change(inputAtividade, {target: {value: `Atividade ${i}`}});
      fireEvent.click(botaoAddAtividade);
    }

    // Tentativa 11ª atividade
    fireEvent.change(inputAtividade, {target: {value: 'Atividade 11'}});
    fireEvent.click(botaoAddAtividade);

    await waitFor(() => {
      expect(
        screen.getByText(/limite de até 10 atividades desejadas atingido/i)
      ).toBeTruthy();
    });

    // 4. Motivo com 301 caracteres
    const inputMotivo = screen.getByLabelText(/novo motivo/i);
    const botaoAddMotivo = screen.getByRole('button', {name: /adicionar motivo/i});
    const motivoLongo = 'A'.repeat(301);

    fireEvent.change(inputMotivo, {target: {value: motivoLongo}});
    fireEvent.click(botaoAddMotivo);

    await waitFor(() => {
      expect(
        screen.getByText(/cada motivo deve ter até 300 caracteres/i)
      ).toBeTruthy();
    });

    // Nenhuma chamada PUT foi realizada à API
    const chamadasPut = mockFetch.mock.calls.filter(
      ([url, init]) => String(url).endsWith('/me/intencao') && init?.method === 'PUT'
    );
    expect(chamadasPut.length).toBe(0);
  });

  test('erro 403 sem consentimento exibe atalho para consentimentos', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/me/intencao') && (!init?.method || init.method === 'GET')) {
        return {ok: false, status: 404, json: async () => ({})};
      }
      if (url.endsWith('/me/intencao') && init?.method === 'PUT') {
        return {
          ok: false,
          status: 403,
          json: async () => ({
            erro: 'consentimento_ausente',
            detalhes: 'Consentimento de perfil necessário.',
          }),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    const onIrParaConsentimentos = vi.fn();
    render(<TelaIntencao onIrParaConsentimentos={onIrParaConsentimentos} />);

    await waitFor(() => {
      expect(screen.getByRole('heading', {level: 2, name: /intenção/i})).toBeTruthy();
    });

    fireEvent.change(screen.getByLabelText(/horas por semana/i), {target: {value: '40'}});
    fireEvent.change(screen.getByLabelText(/unidade federativa|uf/i), {target: {value: 'SP'}});
    fireEvent.click(screen.getByRole('button', {name: /salvar/i}));

    await waitFor(() => {
      expect(screen.getByText(/consentimento de perfil necessário/i)).toBeTruthy();
      expect(
        screen.getByRole('button', {name: /ir para consentimentos/i})
      ).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', {name: /ir para consentimentos/i}));
    expect(onIrParaConsentimentos).toHaveBeenCalled();
  });
});
