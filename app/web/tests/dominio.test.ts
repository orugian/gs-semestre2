import {describe, expect, test} from 'vitest';
import {traduzirMotivo} from '../src/dominio/rotulos';

describe('dominio/rotulos - traduzirMotivo', () => {
  test('traduz cada motivo conhecido', () => {
    expect(traduzirMotivo('sem_informacao_suficiente')).toBe('sem informação suficiente');
    expect(traduzirMotivo('ausencia_informada_pelo_usuario')).toBe('você informou que não possui');
    expect(traduzirMotivo('exercicio_abaixo_do_minimo')).toBe('exercício abaixo do mínimo');
    expect(traduzirMotivo('avaliacao_parcial_llm_indisponivel')).toBe('avaliação parcial (IA indisponível)');
  });

  test('retorna o próprio código para motivo desconhecido', () => {
    expect(traduzirMotivo('motivo_desconhecido')).toBe('motivo_desconhecido');
  });

  test('retorna null para nulo, indefinido ou vazio', () => {
    expect(traduzirMotivo(null)).toBeNull();
    expect(traduzirMotivo(undefined)).toBeNull();
    expect(traduzirMotivo('')).toBeNull();
  });
});
