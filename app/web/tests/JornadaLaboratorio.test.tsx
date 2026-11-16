import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaLaboratorio} from '../src/jornada/TelaLaboratorio';
import fixtureLab from './fixtures/jornada_laboratorio.json';

describe('JornadaLaboratorio - Bancada de Monitoramento e Telemetria', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-lab; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED: abrir sessão, atualizar leituras, relato e opcionalidade explícita', async () => {
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

      if (url.includes('/me/laboratorio/sessoes/atual')) {
        return {
          ok: false,
          status: 404,
          json: async () => ({
            erro: 'sessao_nao_encontrada',
            detalhes: 'Nenhuma sessão ativa.',
          }),
        };
      }

      if (url.includes('/relato') && init?.method === 'POST') {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureLab.relato_resposta,
        };
      }

      if (url.endsWith('/laboratorio/sessoes') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixtureLab.sessao_criada,
        };
      }

      if (url.includes('/me/laboratorio/sessoes/sess-lab-1') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureLab.sessao_detalhe,
        };
      }

      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<TelaLaboratorio />);

    // 1. Mensagem de opcionalidade presente
    await waitFor(() => {
      expect(
        screen.getByText(/esta etapa é opcional/i)
      ).toBeTruthy();
    });

    // 2. Botão "Abrir sessão"
    const botaoAbrir = screen.getByRole('button', {name: /abrir sessão/i});
    fireEvent.click(botaoAbrir);

    // 3. Exibe o código grande copiável e as instruções
    await waitFor(() => {
      expect(screen.getByText('LAB-123456')).toBeTruthy();
      expect(
        screen.getByText(/Conecte sua bancada utilizando o código/i)
      ).toBeTruthy();
    });

    // 4. Botão "Atualizar leituras" busca detalhes
    const botaoAtualizar = screen.getByRole('button', {name: /atualizar leituras/i});
    fireEvent.click(botaoAtualizar);

    // Tabela de leituras com risco textual além de cor e hora em America/Sao_Paulo
    await waitFor(() => {
      expect(screen.getAllByText(/temperatura_c/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/24.5/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/distancia_cm/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/12/).length).toBeGreaterThan(0);
      expect(screen.getByText(/normal/i)).toBeTruthy();
      expect(screen.getByText(/atenção/i)).toBeTruthy();
    });

    // Indicadores por métrica visíveis
    expect(screen.getByText(/indicadores de telemetria/i)).toBeTruthy();

    // 5. Formulário de relato (<= 280 caracteres)
    const textareaRelato = screen.getByLabelText(/relato de observação da bancada/i);
    const botaoEnviarRelato = screen.getByRole('button', {name: /enviar relato/i});

    // 281 caracteres bloqueado
    const texto281 = 'A'.repeat(281);
    fireEvent.change(textareaRelato, {target: {value: texto281}});
    expect(botaoEnviarRelato.getAttribute('aria-disabled')).toBe('true');

    // 60 caracteres válido
    const textoValido = 'Observada oscilação na leitura de distância no minuto 6.';
    fireEvent.change(textareaRelato, {target: {value: textoValido}});
    expect(botaoEnviarRelato.getAttribute('aria-disabled')).toBeNull();

    fireEvent.click(botaoEnviarRelato);

    // Verifica chamada POST com CSRF e texto redigido devolvido pelo servidor
    await waitFor(() => {
      const chamadaRelato = chamadas.find(
        (c) => c.url.includes('/relato') && c.method === 'POST'
      );
      expect(chamadaRelato).toBeTruthy();
      expect(chamadaRelato?.headers['X-CSRF-Token']).toBe('tok-teste-lab');
      expect(chamadaRelato?.body).toEqual({
        relato: textoValido,
      });
    });

    // Exibe texto redigido devolvido pelo servidor e status
    await waitFor(() => {
      expect(
        screen.getByText(/será enviado com a próxima leitura/i)
      ).toBeTruthy();
      expect(
        screen.getByText(
          /Observada oscilação na leitura de distância no minuto 6/i
        )
      ).toBeTruthy();
    });
  });

  test('limpa intervalo de atualização automática (10s) ao desmontar', async () => {
    vi.useFakeTimers();

    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/me/laboratorio/sessoes/atual')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureLab.sessao_detalhe,
        };
      }
      if (url.includes('/me/laboratorio/sessoes/sess-lab-1')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureLab.sessao_detalhe,
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    const {unmount} = render(<TelaLaboratorio />);

    // Avança 10s no timer
    await vi.advanceTimersByTimeAsync(10000);
    const chamadasAntes = mockFetch.mock.calls.length;

    // Desmonta componente
    unmount();

    // Avança mais 20s
    await vi.advanceTimersByTimeAsync(20000);
    const chamadasDepois = mockFetch.mock.calls.length;

    // Nenhuma nova chamada após desmontar
    expect(chamadasDepois).toBe(chamadasAntes);

    vi.useRealTimers();
  });

  test('403 sem consentimento laboratorio_nuvem exibe atalho para consentimentos', async () => {
    const mockFetch = vi.fn().mockImplementation(async () => {
      return {
        ok: false,
        status: 403,
        json: async () => ({
          erro: 'consentimento_ausente',
          detalhes: 'Consentimento laboratorio_nuvem necessário.',
        }),
      };
    });

    vi.stubGlobal('fetch', mockFetch);

    const onIrParaConsentimentos = vi.fn();
    render(<TelaLaboratorio onIrParaConsentimentos={onIrParaConsentimentos} />);

    await waitFor(() => {
      expect(
        screen.getByRole('button', {name: /ir para consentimentos/i})
      ).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', {name: /ir para consentimentos/i}));
    expect(onIrParaConsentimentos).toHaveBeenCalledTimes(1);
  });
});
