import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaConsentimentos} from '../src/jornada/TelaConsentimentos';
import {TelaCurriculo} from '../src/jornada/TelaCurriculo';

describe('JornadaConsentimentos - LGPD e Finalidades Específicas', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-consentimentos; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('lista as 3 finalidades com status correto', async () => {
    const mockConsentimentos = [
      {
        id: 'cons-1',
        finalidade: 'perfil',
        versao_termo: 'v1.0',
        concedido_em: '2026-11-16T12:00:00Z',
        revogado_em: null,
      },
      {
        id: 'cons-2',
        finalidade: 'curriculo_llm',
        versao_termo: 'v1.0',
        concedido_em: '2026-11-15T10:00:00Z',
        revogado_em: '2026-11-15T18:00:00Z',
      },
    ];

    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/me/consentimentos')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: mockConsentimentos}),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaConsentimentos />);

    await waitFor(() => {
      expect(screen.getByText(/perfil e currículo/i)).toBeTruthy();
      expect(screen.getByText(/inteligência artificial/i)).toBeTruthy();
      expect(screen.getByText(/laboratório na nuvem/i)).toBeTruthy();
    });

    // Perfil está ativo
    expect(screen.getByText(/ativo desde/i)).toBeTruthy();
  });

  test('conceder chama POST somente para a finalidade escolhida', async () => {
    const chamadas: {url: string; method: string; body: any}[] = [];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      const parsedBody =
        typeof init?.body === 'string' ? JSON.parse(init.body) : init?.body;
      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
        body: parsedBody,
      });

      if (url.endsWith('/me/consentimentos') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: []}),
        };
      }

      if (url.endsWith('/me/consentimentos') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            id: 'novo-cons-perfil',
            finalidade: parsedBody.finalidade,
            versao_termo: 'v1.0',
            concedido_em: '2026-11-16T15:00:00Z',
            revogado_em: null,
          }),
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaConsentimentos />);

    await waitFor(() => {
      expect(screen.getByText(/perfil e currículo/i)).toBeTruthy();
    });

    const botoesConceder = screen.getAllByRole('button', {name: /^conceder$/i});
    // Clica no primeiro ("perfil")
    fireEvent.click(botoesConceder[0]);

    await waitFor(() => {
      const chamadaPost = chamadas.find(
        (c) => c.url.endsWith('/me/consentimentos') && c.method === 'POST'
      );
      expect(chamadaPost).toBeDefined();
      expect(chamadaPost?.body).toEqual({finalidade: 'perfil'});
    });
  });

  test('revogar chama DELETE com o id ativo', async () => {
    const chamadas: {url: string; method: string}[] = [];

    const mockConsentimentos = [
      {
        id: 'cons-ativo-99',
        finalidade: 'curriculo_llm',
        versao_termo: 'v1.0',
        concedido_em: '2026-11-16T12:00:00Z',
        revogado_em: null,
      },
    ];

    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      chamadas.push({
        url: String(url),
        method: init?.method || 'GET',
      });

      if (url.endsWith('/me/consentimentos') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: mockConsentimentos}),
        };
      }

      if (url.includes('/me/consentimentos/cons-ativo-99') && init?.method === 'DELETE') {
        return {
          ok: true,
          status: 204,
          text: async () => '',
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaConsentimentos />);

    await waitFor(() => {
      expect(screen.getByRole('button', {name: /^revogar$/i})).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', {name: /^revogar$/i}));

    await waitFor(() => {
      const chamadaDelete = chamadas.find(
        (c) => c.url.endsWith('/me/consentimentos/cons-ativo-99') && c.method === 'DELETE'
      );
      expect(chamadaDelete).toBeDefined();
    });
  });

  test('currículo sem consentimento de perfil mostra bloqueio com atalho', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/me/consentimentos')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({itens: []}), // Nenhum consentimento
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    const onIrParaConsentimentos = vi.fn();
    render(<TelaCurriculo onIrParaConsentimentos={onIrParaConsentimentos} />);

    await waitFor(() => {
      expect(
        screen.getByText(/necessário autorizar o armazenamento do perfil/i)
      ).toBeTruthy();
    });

    const botaoAtalho = screen.getByRole('button', {name: /ir para consentimentos/i});
    fireEvent.click(botaoAtalho);
    expect(onIrParaConsentimentos).toHaveBeenCalled();
  });
});
