import {cleanup, fireEvent, render, screen, waitFor} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';
import {TelaCurriculo} from '../src/jornada/TelaCurriculo';

describe('JornadaCurriculo - TDD D22 e Proteção de Dados', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    document.cookie = 'csrf_token=tok-teste-curriculo; path=/';
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    document.cookie = 'csrf_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
  });

  test('prioritário RED 1: não envia nada à IA antes da confirmação do usuário', async () => {
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

      // 1. Envio de experiências (texto)
      if (url.endsWith('/me/experiencias') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            id: 'curr-123',
            origem: 'texto',
            status: 'aguardando_confirmacao',
            texto_redigido: 'Experiência em SQL e Python. Contato: [EMAIL].',
            sha256_texto_redigido: 'sha-abc',
            redacoes: {
              nome: 0,
              email: 1,
              telefone: 0,
              cpf: 0,
              cep: 0,
              endereco: 0,
              url: 0,
            },
            aviso_redacao: '1 e-mail ocultado antes de prosseguir.',
            criado_em: '2026-11-16T10:00:00Z',
            confirmado_em: null,
          }),
        };
      }

      // 2. Confirmar envio
      if (url.endsWith('/me/curriculo/confirmar-envio') && init?.method === 'POST') {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            id: 'curr-123',
            origem: 'texto',
            status: 'confirmado',
            texto_redigido: 'Experiência em SQL e Python e BI. Contato: [EMAIL].',
            sha256_texto_redigido: 'sha-def',
            redacoes: {
              nome: 0,
              email: 1,
              telefone: 0,
              cpf: 0,
              cep: 0,
              endereco: 0,
              url: 0,
            },
            aviso_redacao: '1 e-mail ocultado antes de prosseguir.',
            criado_em: '2026-11-16T10:00:00Z',
            confirmado_em: '2026-11-16T10:05:00Z',
          }),
        };
      }

      // 3. Extração com LLM
      if (url.endsWith('/me/competencias/extrair') && init?.method === 'POST') {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            extracao_id: 'ext-456',
            modelo: 'gemini-1.5-flash',
            candidatas: [
              {
                id: 'comp-1',
                esco_id: 'http://data.europa.eu/esco/skill/sql',
                titulo: 'SQL',
                trecho_origem: 'Experiência em SQL',
                origem: 'extracao_llm',
                estado_evidencia: 'declarada',
                revisao: 'pendente',
                curriculo_id: 'curr-123',
                extracao_id: 'ext-456',
                criado_em: '2026-11-16T10:06:00Z',
                atualizado_em: '2026-11-16T10:06:00Z',
              },
            ],
            descartadas: {
              fora_da_lista: 0,
              sem_trecho: 0,
              trecho_nao_encontrado: 0,
              duplicadas: 0,
            },
            aviso: 'Sugestões geradas com base no texto revisado.',
          }),
        };
      }

      return {
        ok: false,
        status: 404,
        json: async () => ({erro: 'nao_encontrado', detalhes: 'Rota não encontrada'}),
      };
    });

    vi.stubGlobal('fetch', mockFetch);

    const onSugerirSucesso = vi.fn();
    render(<TelaCurriculo onSugerirSucesso={onSugerirSucesso} />);

    // 1. Usuário digita texto inicial no textarea
    const inputTexto = screen.getByLabelText(/texto/i);
    fireEvent.change(inputTexto, {
      target: {value: 'Experiência em SQL e Python. Contato: dev@exemplo.com'},
    });

    // 2. Clica para processar o texto
    const botaoEnviar = screen.getByRole('button', {name: /processar texto/i});
    fireEvent.click(botaoEnviar);

    // 3. Espera tela atualizar com texto redigido e aviso
    await waitFor(() => {
      expect(screen.getByText(/1 e-mail ocultado antes de prosseguir/i)).toBeTruthy();
    });

    // Verifica que o texto redigido está no textarea editável
    const areaRedigida = screen.getByDisplayValue(
      'Experiência em SQL e Python. Contato: [EMAIL].'
    );
    expect(areaRedigida).toBeTruthy();

    // D22: Botão de sugerir competências NÃO DEVE existir ou estar habilitado antes da confirmação!
    const botaoSugerirAntes = screen.queryByRole('button', {name: /sugerir competências/i});
    if (botaoSugerirAntes) {
      expect(botaoSugerirAntes.hasAttribute('disabled')).toBe(true);
    }
    // Nenhuma chamada a extrair foi feita!
    expect(chamadas.some((c) => c.url.endsWith('/me/competencias/extrair'))).toBe(false);

    // 4. Usuário edita o texto redigido
    fireEvent.change(areaRedigida, {
      target: {value: 'Experiência em SQL e Python e BI. Contato: [EMAIL].'},
    });

    // 5. Clica em "Confirmar e liberar para sugestões"
    const botaoConfirmar = screen.getByRole('button', {
      name: /confirmar e liberar para sugestões/i,
    });
    fireEvent.click(botaoConfirmar);

    // 6. Verifica chamada de confirmação com X-CSRF-Token e texto revisado
    await waitFor(() => {
      const chamadaConfirmar = chamadas.find((c) =>
        c.url.endsWith('/me/curriculo/confirmar-envio')
      );
      expect(chamadaConfirmar).toBeDefined();
      expect(chamadaConfirmar?.body).toEqual({
        curriculo_id: 'curr-123',
        texto_revisado: 'Experiência em SQL e Python e BI. Contato: [EMAIL].',
      });
      const headers = chamadaConfirmar?.headers as Record<string, string>;
      expect(headers['X-CSRF-Token'] || headers['x-csrf-token']).toBe('tok-teste-curriculo');
    });

    // 7. Agora "Sugerir competências" deve estar visível e habilitado
    const botaoSugerirConfirmado = await screen.findByRole('button', {name: /sugerir competências/i});
    expect(botaoSugerirConfirmado.hasAttribute('disabled')).toBe(false);

    // 7b. Editar depois de confirmar exige nova confirmação antes de sugerir
    const areaConfirmada = screen.getByDisplayValue(
      'Experiência em SQL e Python e BI. Contato: [EMAIL].'
    );
    fireEvent.change(areaConfirmada, {target: {value: 'Texto alterado sem confirmar.'}});
    expect(screen.queryByRole('button', {name: /sugerir competências/i})).toBeNull();
    fireEvent.change(areaConfirmada, {
      target: {value: 'Experiência em SQL e Python e BI. Contato: [EMAIL].'},
    });
    const botaoSugerir = await screen.findByRole('button', {name: /sugerir competências/i});

    // 8. Clica em "Sugerir competências"
    fireEvent.click(botaoSugerir);

    await waitFor(() => {
      const chamadaExtrair = chamadas.find((c) =>
        c.url.endsWith('/me/competencias/extrair')
      );
      expect(chamadaExtrair).toBeDefined();
      expect(chamadaExtrair?.body).toEqual({curriculo_id: 'curr-123'});
      expect(onSugerirSucesso).toHaveBeenCalled();
    });
  });

  test('recusa arquivo maior que 2 MB no cliente sem chamada à API', async () => {
    const mockFetch = vi.fn();
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaCurriculo />);

    // Alterna para envio de arquivo se houver abas
    const abaArquivo = screen.queryByRole('tab', {name: /enviar arquivo/i});
    if (abaArquivo) {
      fireEvent.click(abaArquivo);
    }

    const inputArquivo = document.querySelector('input[type="file"]') as HTMLInputElement;

    // Cria arquivo simulado de 2.5 MB
    const arquivoGrande = new File([new ArrayBuffer(2.5 * 1024 * 1024)], 'curriculo.pdf', {
      type: 'application/pdf',
    });

    fireEvent.change(inputArquivo, {target: {files: [arquivoGrande]}});

    const botaoEnviarArquivo = screen.getByRole('button', {name: /processar arquivo/i});
    fireEvent.click(botaoEnviarArquivo);

    await waitFor(() => {
      expect(screen.getByText(/maior que 2 MB/i)).toBeTruthy();
    });

    // Nenhuma requisição de upload foi feita à API
    const chamadaUpload = mockFetch.mock.calls.find(([url]) =>
      String(url).endsWith('/me/curriculo')
    );
    expect(chamadaUpload).toBeUndefined();
  });

  test('trata erros 429 e 503 na extração com mensagens específicas', async () => {
    const mockFetch = vi.fn().mockImplementation(async (url: string) => {
      if (url.endsWith('/me/consentimentos')) {
        return {
          ok: true,
          status: 200,
          json: async () => ({
            itens: [
              {
                id: 'c-perfil',
                finalidade: 'perfil',
                versao_termo: 'v1.0',
                concedido_em: '2026-11-16T10:00:00Z',
                revogado_em: null,
              },
            ],
          }),
        };
      }
      if (url.endsWith('/me/experiencias')) {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            id: 'curr-429',
            origem: 'texto',
            status: 'confirmado',
            texto_redigido: 'Texto já confirmado',
            sha256_texto_redigido: 'sha-x',
            redacoes: {nome: 0, email: 0, telefone: 0, cpf: 0, cep: 0, endereco: 0, url: 0},
            aviso_redacao: '',
            criado_em: '2026-11-16T10:00:00Z',
            confirmado_em: '2026-11-16T10:00:00Z',
          }),
        };
      }
      if (url.endsWith('/me/competencias/extrair')) {
        return {
          ok: false,
          status: 429,
          json: async () => ({
            erro: 'limite_atingido',
            detalhes: 'Limite de 5 sugestões em 24 horas atingido.',
          }),
        };
      }
      return {ok: true, status: 200, json: async () => ({})};
    });
    vi.stubGlobal('fetch', mockFetch);

    render(<TelaCurriculo />);

    const inputTexto = screen.getByLabelText(/texto/i);
    fireEvent.change(inputTexto, {target: {value: 'Texto de teste'}});
    fireEvent.click(screen.getByRole('button', {name: /processar texto/i}));

    const botaoSugerir = await screen.findByRole('button', {name: /sugerir competências/i});
    fireEvent.click(botaoSugerir);

    await waitFor(() => {
      expect(screen.getByText(/limite de 5 sugestões em 24 horas/i)).toBeTruthy();
    });
  });
});
