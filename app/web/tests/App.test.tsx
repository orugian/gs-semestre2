import {cleanup, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, test, vi} from 'vitest';

import App from '../src/App';
import {formatarUrlNavegacao, lerEstadoUrl} from '../src/mercado/formatacao';

describe('App e Deep-linking', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    window.history.replaceState(null, '', '/');
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  test('renderiza a tela inicial com abas e heading CitizenTech', () => {
    render(<App />);

    expect(screen.getByRole('heading', {name: 'CitizenTech'})).toBeTruthy();
    expect(screen.getByRole('tab', {name: 'Mercado'})).toBeTruthy();
    expect(screen.getByRole('tab', {name: 'Painel técnico'})).toBeTruthy();
  });

  test('item 5: leitura da URL com parâmetros válidos e fallback para valores inválidos', () => {
    // Parâmetros válidos
    const estadoValido = lerEstadoUrl('?destino=analista_processos&uf=MG', '#painel-tecnico');
    expect(estadoValido).toEqual({
      aba: 'painel_tecnico',
      destino: 'analista_processos',
      uf: 'MG',
    });

    // Parâmetros inválidos caem no padrão (não quebram)
    const estadoInvalido = lerEstadoUrl('?destino=inexistente&uf=ZZ', '#desconhecido');
    expect(estadoInvalido).toEqual({
      aba: 'mercado',
      destino: 'analista_dados_bi',
      uf: 'SP',
    });

    // Sem parâmetros cai no padrão
    expect(lerEstadoUrl('', '')).toEqual({
      aba: 'mercado',
      destino: 'analista_dados_bi',
      uf: 'SP',
    });
  });

  test('item 5: escrita da URL formata query e hash corretamente', () => {
    const urlMercado = formatarUrlNavegacao(
      {aba: 'mercado', destino: 'analista_dados_bi', uf: 'SP'},
      '/'
    );
    expect(urlMercado).toBe('/?destino=analista_dados_bi&uf=SP');

    const urlTecnico = formatarUrlNavegacao(
      {aba: 'painel_tecnico', destino: 'analista_processos', uf: 'RJ'},
      '/'
    );
    expect(urlTecnico).toBe('/?destino=analista_processos&uf=RJ#painel-tecnico');
  });

  test('item 5: App inicializa a partir da URL e atualiza history.replaceState ao mudar aba', () => {
    const replaceStateSpy = vi.spyOn(window.history, 'replaceState');

    // Simula abertura de URL com deep-link para painel técnico em MG
    window.history.replaceState(null, '', '/?destino=analista_processos&uf=MG#painel-tecnico');

    render(<App />);

    // Aba técnica deve iniciar selecionada
    const tabTecnica = screen.getByRole('tab', {name: 'Painel técnico'});
    expect(tabTecnica.getAttribute('aria-selected')).toBe('true');

    // Ao mudar para a aba Mercado, atualiza a URL com replaceState
    const tabMercado = screen.getByRole('tab', {name: 'Mercado'});
    fireEvent.click(tabMercado);

    expect(replaceStateSpy).toHaveBeenCalledWith(
      null,
      '',
      '/?destino=analista_processos&uf=MG'
    );
  });
});
