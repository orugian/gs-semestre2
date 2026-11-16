import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeAll, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaExercicio} from '../src/jornada/TelaExercicio';
import fixtureTentativa from './fixtures/jornada_tentativa.json';

describe('JornadaExercicio - Exercício Diagnóstico (D03, D06, D21, D23, T07)', () => {
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
    document.cookie = 'csrf_token=tok-teste-exercicio; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED: gabarito só depois do envio, parcial explicado e discordo', async () => {
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

      if (url.includes('/destinos/analista_monitoramento_iot/exercicio')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureTentativa.exercicio,
        };
      }

      if (url.includes('/me/tentativas') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixtureTentativa.tentativa_parcial,
        };
      }

      if (url.includes('/discordo') && init?.method === 'POST') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            tentativa_id: 'tent-parcial-1',
            discordo_em: '2026-11-16T14:35:00Z',
            motivo: 'Critérios objetivos foram atendidos plenamente.',
            status_contestacao: 'registrada',
          }),
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

    render(<TelaExercicio destinoId="analista_monitoramento_iot" />);

    // 1. Carregou o exercício
    await waitFor(() => {
      expect(screen.getByText(/cenário/i)).toBeTruthy();
      expect(
        screen.getByText(/Você é responsável por monitorar a bancada/i)
      ).toBeTruthy();
    });

    // Antes do envio: NENHUM texto "gabarito" ou "justificativa" na tela
    expect(screen.queryByText(/gabarito/i)).toBeNull();
    expect(screen.queryByText(/justificativa/i)).toBeNull();

    // Critérios da aberta e âncoras 0, 1 e 2 visíveis antes do envio (transparência)
    expect(
      screen.getByText(/Metodologia de investigação do problema/i)
    ).toBeTruthy();
    expect(
      screen.getByText(/Não apresenta método ou sugere ações sem relação/i)
    ).toBeTruthy();
    expect(
      screen.getByText(/Apresenta isolamento sistemático/i)
    ).toBeTruthy();

    // Questões objetivas presentes
    expect(
      screen.getByText(/Qual protocolo é mais adequado para telemetria leve/i)
    ).toBeTruthy();

    // Botão Enviar deve estar desabilitado até tudo respondido
    const botaoEnviar = screen.getByRole('button', {name: /enviar resposta/i});
    expect(botaoEnviar.getAttribute('aria-disabled')).toBe('true');

    // Responder objetivas
    const radioQ1 = screen.getByLabelText(/MQTT/i);
    fireEvent.click(radioQ1);

    const radioQ2 = screen.getByLabelText(
      /Acionar procedimento de resfriamento ou parada preventiva/i
    );
    fireEvent.click(radioQ2);

    // Responder aberta com menos de 20 chars: continua desabilitado
    const textareaAberta = screen.getByLabelText(/Sua resposta aberta/i);
    fireEvent.change(textareaAberta, {
      target: {value: 'Resposta curta'},
    });
    expect(botaoEnviar.getAttribute('aria-disabled')).toBe('true');

    // Responder aberta com >= 20 chars
    fireEvent.change(textareaAberta, {
      target: {
        value:
          'Iniciaria pelo isolamento elétrico dos cabos e análise de ruído na linha de telemetria.',
      },
    });

    // Agora o botão Enviar fica habilitado
    await waitFor(() => {
      expect(botaoEnviar.getAttribute('aria-disabled')).toBeNull();
    });

    // Enviar tentativa
    fireEvent.click(botaoEnviar);

    // Verifica chamada POST com CSRF
    await waitFor(() => {
      const chamadaPost = chamadas.find(
        (c) => c.url.includes('/me/tentativas') && c.method === 'POST'
      );
      expect(chamadaPost).toBeTruthy();
      expect(chamadaPost?.headers['X-CSRF-Token']).toBe('tok-teste-exercicio');
      expect(chamadaPost?.body).toEqual({
        destino_id: 'analista_monitoramento_iot',
        exercicio_id: 'ex-iot-1',
        respostas_objetivas: {
          q1: 'A',
          q2: 'B',
        },
        resposta_aberta:
          'Iniciaria pelo isolamento elétrico dos cabos e análise de ruído na linha de telemetria.',
      });
    });

    // Resposta parcial recebida: tela mostra explicação de parcial e NÃO mostra nota final do exercício
    await waitFor(() => {
      expect(
        screen.getByText(
          /a avaliação da resposta aberta não estava disponível; a parte objetiva foi registrada/i
        )
      ).toBeTruthy();
    });

    // Não deve mostrar nota final do exercício quando parcial
    expect(screen.queryByText(/nota final/i)).toBeNull();

    // Agora o gabarito e justificativa da objetiva estão visíveis após o envio
    expect(screen.getAllByText(/gabarito/i).length).toBeGreaterThan(0);
    expect(
      screen.getByText(
        /MQTT é projetado especificamente para telemetria leve e redes com restrição/i
      )
    ).toBeTruthy();

    // Botão "Discordo" presente
    const botaoDiscordo = screen.getByRole('button', {name: /discordo/i});
    fireEvent.click(botaoDiscordo);

    // Abre diálogo de contestação com motivo (10 a 1000 caracteres)
    await waitFor(() => {
      expect(screen.getByText(/registrar discordância/i)).toBeTruthy();
    });

    const textareaMotivo = screen.getByLabelText(/motivo da discordância/i);
    const botaoConfirmarDiscordo = screen.getByRole('button', {
      name: /confirmar discordância/i,
    });
    expect(botaoConfirmarDiscordo.getAttribute('aria-disabled')).toBe('true');

    fireEvent.change(textareaMotivo, {
      target: {value: 'Critérios objetivos foram atendidos plenamente.'},
    });

    expect(botaoConfirmarDiscordo.getAttribute('aria-disabled')).toBeNull();
    fireEvent.click(botaoConfirmarDiscordo);

    // Verifica chamada POST discordo com CSRF
    await waitFor(() => {
      const chamadaDiscordo = chamadas.find(
        (c) => c.url.includes('/discordo') && c.method === 'POST'
      );
      expect(chamadaDiscordo).toBeTruthy();
      expect(chamadaDiscordo?.headers['X-CSRF-Token']).toBe('tok-teste-exercicio');
      expect(chamadaDiscordo?.body).toEqual({
        motivo: 'Critérios objetivos foram atendidos plenamente.',
      });
    });

    // Exibe "Contestação registrada"
    await waitFor(() => {
      expect(screen.getByText(/contestação registrada/i)).toBeTruthy();
    });
  });

  test('resultado demonstrada exibe nota do exercício, critérios com trecho e rastreabilidade', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.includes('/destinos/analista_monitoramento_iot/exercicio')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureTentativa.exercicio,
        };
      }
      if (url.includes('/me/tentativas') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => fixtureTentativa.tentativa_demonstrada,
        };
      }
      if (url.includes('/me/tentativas') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureTentativa.historico,
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<TelaExercicio destinoId="analista_monitoramento_iot" />);

    await waitFor(() => {
      expect(screen.getByRole('button', {name: /enviar resposta/i})).toBeTruthy();
    });

    // Preenche
    fireEvent.click(screen.getByLabelText(/MQTT/i));
    fireEvent.click(
      screen.getByLabelText(/Acionar procedimento de resfriamento ou parada preventiva/i)
    );
    fireEvent.change(screen.getByLabelText(/Sua resposta aberta/i), {
      target: {
        value:
          'Iniciaria pelo isolamento elétrico dos cabos e análise de ruído na linha de telemetria.',
      },
    });

    fireEvent.click(screen.getByRole('button', {name: /enviar resposta/i}));

    // Verifica nota e conceito
    await waitFor(() => {
      expect(screen.getAllByText(/demonstrada/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/95/).length).toBeGreaterThan(0); // nota_final
      expect(
        screen.getByText(
          /O candidato detalhou isolamento por etapas cobrindo fiação, protocolo e ruído/i
        )
      ).toBeTruthy();
      expect(
        screen.getByText(
          /Iniciaria pelo isolamento elétrico dos cabos e análise de ruído na linha de telemetria/i
        )
      ).toBeTruthy();
    });

    // Rastreabilidade: versão do exercício, modelo e data
    expect(screen.getByText(/versão 1.0/i)).toBeTruthy();
    expect(screen.getByText(/modelo-ia-diagnostico-v1/i)).toBeTruthy();

    // Histórico presente com última e melhor marcadas
    expect(screen.getByText(/histórico de tentativas/i)).toBeTruthy();
    expect(screen.getByText(/melhor/i)).toBeTruthy();
    expect(screen.getByText(/última/i)).toBeTruthy();
  });

  test('limite de tentativas (429) exibe mensagem explícita e bloqueia novo envio', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (url.includes('/destinos/analista_monitoramento_iot/exercicio')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            ...fixtureTentativa.exercicio,
            tentativas_restantes_24h: 0,
          }),
        };
      }
      if (url.includes('/me/tentativas') && (!init?.method || init.method === 'GET')) {
        return {
          ok: true,
          status: 200,
          json: async () => fixtureTentativa.historico,
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    render(<TelaExercicio destinoId="analista_monitoramento_iot" />);

    await waitFor(() => {
      expect(
        screen.getByText(
          /Você atingiu o limite de 3 tentativas em 24 horas para este exercício/i
        )
      ).toBeTruthy();
    });

    // Botão enviar fica desabilitado
    expect(
      screen.getByRole('button', {name: /enviar resposta/i}).getAttribute('aria-disabled')
    ).toBe('true');
  });

  test('erro 403 sem consentimento curriculo_llm exibe atalho para consentimentos', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.includes('/destinos/analista_monitoramento_iot/exercicio')) {
        return {
          ok: false,
          status: 403,
          json: async () => ({
            erro: 'consentimento_ausente',
            detalhes: 'Consentimento curriculo_llm necessário.',
          }),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });

    vi.stubGlobal('fetch', mockFetch);

    const onIrParaConsentimentos = vi.fn();
    render(
      <TelaExercicio
        destinoId="analista_monitoramento_iot"
        onIrParaConsentimentos={onIrParaConsentimentos}
      />
    );

    await waitFor(() => {
      expect(
        screen.getByRole('button', {name: /ir para consentimentos/i})
      ).toBeTruthy();
    });

    fireEvent.click(screen.getByRole('button', {name: /ir para consentimentos/i}));
    expect(onIrParaConsentimentos).toHaveBeenCalledTimes(1);
  });
});
