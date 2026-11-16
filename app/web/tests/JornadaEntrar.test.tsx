import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {AreaJornada} from '../src/jornada/AreaJornada';
import {TelaEntrar} from '../src/jornada/TelaEntrar';

describe('JornadaEntrar e AreaJornada - Autenticação e Sessão', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('GET /me com 401 renderiza TelaEntrar', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/me')) {
        return {
          ok: false,
          status: 401,
          json: async () => ({erro: 'nao_autenticado', detalhes: 'Sessão necessária.'}),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<AreaJornada />);

    await waitFor(() => {
      expect(screen.getByRole('heading', {name: /entrar/i})).toBeTruthy();
    });
  });

  test('login com 401 exibe detalhes em role="alert"', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/auth/login')) {
        return {
          ok: false,
          status: 401,
          json: async () => ({
            erro: 'credenciais_invalidas',
            detalhes: 'Credenciais inválidas.',
          }),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    const onLoginSucesso = vi.fn();
    render(<TelaEntrar onLoginSucesso={onLoginSucesso} />);

    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: {value: 'usuario@exemplo.com'},
    });
    fireEvent.change(screen.getByLabelText(/^senha/i), {
      target: {value: 'senha123456'},
    });

    const botaoEntrar = screen.getByRole('button', {name: /^entrar$/i});
    fireEvent.click(botaoEntrar);

    await waitFor(() => {
      const alerta = screen.getByRole('alert');
      expect(alerta.textContent).toMatch(/credenciais inválidas/i);
    });

    expect(onLoginSucesso).not.toHaveBeenCalled();
  });

  test('validação no cliente: senha com menos de 10 caracteres avisa antes de enviar', async () => {
    const mockFetch = vi.fn();
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaEntrar onLoginSucesso={vi.fn()} />);

    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: {value: 'usuario@exemplo.com'},
    });
    fireEvent.change(screen.getByLabelText(/^senha/i), {
      target: {value: 'curta'},
    });

    const botaoEntrar = screen.getByRole('button', {name: /^entrar$/i});
    fireEvent.click(botaoEntrar);

    await waitFor(() => {
      expect(screen.getByRole('alert').textContent).toMatch(
        /pelo menos 10 caracteres/i
      );
    });

    expect(mockFetch).not.toHaveBeenCalled();
  });

  test('criar conta chama registrar e em seguida entrar com mesmas credenciais', async () => {
    const chamadas: {url: string; method: string; body: any}[] = [];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string' ? JSON.parse(init.body) : init?.body;
      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        body: parsedBody,
      });

      if (url.endsWith('/auth/registrar')) {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            id: 'novo-user-1',
            email: 'novo@exemplo.com',
            criado_em: '2026-11-16T10:00:00Z',
          }),
        };
      }

      if (url.endsWith('/auth/login')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({id: 'novo-user-1', email: 'novo@exemplo.com'}),
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    const onLoginSucesso = vi.fn();
    render(<TelaEntrar onLoginSucesso={onLoginSucesso} />);

    // Alterna para "Criar conta"
    const botaoAlternar = screen.getByRole('button', {name: /criar conta/i});
    fireEvent.click(botaoAlternar);

    fireEvent.change(screen.getByLabelText(/e-mail/i), {
      target: {value: 'novo@exemplo.com'},
    });
    fireEvent.change(screen.getByLabelText(/^senha/i), {
      target: {value: 'senhaSegura123'},
    });

    // Submete cadastro
    const botaoCadastrar = screen.getByRole('button', {name: /^criar conta$/i});
    fireEvent.click(botaoCadastrar);

    await waitFor(() => {
      expect(chamadas.some((c) => c.url.endsWith('/auth/registrar'))).toBe(true);
      expect(chamadas.some((c) => c.url.endsWith('/auth/login'))).toBe(true);
      expect(onLoginSucesso).toHaveBeenCalled();
    });
  });

  test('persona demo "S" exibe selo no cabeçalho e logout volta para entrar', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.endsWith('/me') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'usr-demo',
            email: 'demo@exemplo.com',
            criado_em: '2026-11-16T10:00:00Z',
            persona_demo: 'S',
          }),
        };
      }
      if (url.endsWith('/me/consentimentos')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: []}),
        };
      }
      if (url.endsWith('/auth/logout')) {
        return {
          ok: true,
          status: 204,
          text: async () => '',
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<AreaJornada />);

    // Selo de persona de demonstração visível
    await waitFor(() => {
      expect(screen.getByText(/persona de demonstração/i)).toBeTruthy();
      expect(screen.getByText('demo@exemplo.com')).toBeTruthy();
    });

    // Clica em "Sair"
    const botaoSair = screen.getByRole('button', {name: /sair/i});
    fireEvent.click(botaoSair);

    await waitFor(() => {
      expect(screen.getByRole('heading', {name: /entrar/i})).toBeTruthy();
    });
  });
});
