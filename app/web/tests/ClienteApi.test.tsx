import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {ErroApi, requisitar} from '../src/api/cliente';

describe('ClienteApi - HTTP, CSRF e Tratamento de Erros', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-csrf-teste; path=/';
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('GET não envia cabeçalho X-CSRF-Token', async () => {
    let headersEnviados: HeadersInit | undefined;

    const mockFetch = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
      headersEnviados = init?.headers;
      return {
        ok: true,
        status: 200,
        json: async () => ({ok: true}),
      };
    });
    vi.stubGlobal('fetch', mockFetch);

    const resultado = await requisitar<{ok: boolean}>('GET', '/me');
    expect(resultado).toEqual({ok: true});

    const headers = (headersEnviados || {}) as Record<string, string>;
    expect(headers['X-CSRF-Token']).toBeUndefined();
    expect(headers['x-csrf-token']).toBeUndefined();
  });

  test('POST, PUT, PATCH, DELETE enviam cabeçalho X-CSRF-Token lido do cookie', async () => {
    for (const metodo of ['POST', 'PUT', 'PATCH', 'DELETE']) {
      let headersEnviados: Record<string, string> = {};

      const mockFetch = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
        headersEnviados = (init?.headers || {}) as Record<string, string>;
        return {
          ok: true,
          status: 200,
          json: async () => ({sucesso: true}),
        };
      });
      vi.stubGlobal('fetch', mockFetch);

      await requisitar(metodo, '/teste', {dados: 1});
      expect(headersEnviados['X-CSRF-Token'] || headersEnviados['x-csrf-token']).toBe(
        'tok-csrf-teste'
      );
    }
  });

  test('FormData não recebe Content-Type manual para preservar boundary', async () => {
    let headersEnviados: Record<string, string> = {};

    const mockFetch = vi.fn().mockImplementation(async (_url: string, init?: RequestInit) => {
      headersEnviados = (init?.headers || {}) as Record<string, string>;
      return {
        ok: true,
        status: 201,
        json: async () => ({id: '123'}),
      };
    });
    vi.stubGlobal('fetch', mockFetch);

    const formData = new FormData();
    formData.append('arquivo', new Blob(['conteudo']), 'cv.pdf');

    await requisitar('POST', '/me/curriculo', formData);

    expect(headersEnviados['Content-Type']).toBeUndefined();
    expect(headersEnviados['content-type']).toBeUndefined();
  });

  test('status 204 devolve undefined', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      status: 204,
      text: async () => '',
    });
    vi.stubGlobal('fetch', mockFetch);

    const res = await requisitar<void>('POST', '/auth/logout');
    expect(res).toBeUndefined();
  });

  test('erro 400 lança ErroApi com detalhes', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({
        erro: 'validacao',
        detalhes: 'O campo e-mail é obrigatório.',
      }),
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(requisitar('POST', '/auth/registrar', {})).rejects.toThrow(ErroApi);

    try {
      await requisitar('POST', '/auth/registrar', {});
    } catch (err) {
      expect(err).toBeInstanceOf(ErroApi);
      const erroApi = err as ErroApi;
      expect(erroApi.status).toBe(400);
      expect(erroApi.erro).toBe('validacao');
      expect(erroApi.detalhes).toBe('O campo e-mail é obrigatório.');
    }
  });

  test('tolera corpo de erro não-JSON e vazio', async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => {
        throw new Error('Não é JSON');
      },
      text: async () => 'Erro em texto puro',
    });
    vi.stubGlobal('fetch', mockFetch);

    await expect(requisitar('GET', '/me')).rejects.toThrow(ErroApi);
  });
});
