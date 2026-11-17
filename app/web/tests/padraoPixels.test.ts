import { describe, expect, test } from 'vitest';
import { padraoPixels } from '../src/visual/padraoPixels';

describe('padraoPixels (função pura da matriz de pixels)', () => {
  test('tamanho do array corresponde a colunas * linhas', () => {
    const colunas = 96;
    const linhas = 28;
    const intensidades = padraoPixels(colunas, linhas, 1.0, null);
    expect(intensidades.length).toBe(colunas * linhas);
  });

  test('todos os valores retornados estão dentro do intervalo [0, 1]', () => {
    const colunas = 40;
    const linhas = 10;
    const intensidades = padraoPixels(colunas, linhas, 2.5, { x: 20, y: 5 });
    for (let i = 0; i < intensidades.length; i++) {
      expect(intensidades[i]).toBeGreaterThanOrEqual(0);
      expect(intensidades[i]).toBeLessThanOrEqual(1);
    }
  });

  test('determinismo: chamadas com o mesmo tempo e ponteiro produzem os mesmos valores', () => {
    const colunas = 48;
    const linhas = 14;
    const t = 10.5;
    const frame1 = padraoPixels(colunas, linhas, t, { x: 10, y: 7 });
    const frame2 = padraoPixels(colunas, linhas, t, { x: 10, y: 7 });
    expect(frame1).toEqual(frame2);
  });

  test('reduced-motion: com tempo fixo constante, dois quadros sucessivos são estáticos e idênticos', () => {
    const colunas = 48;
    const linhas = 14;
    const tempoFixo = 0.0;
    const frameA = padraoPixels(colunas, linhas, tempoFixo, null);
    const frameB = padraoPixels(colunas, linhas, tempoFixo, null);
    expect(frameA).toEqual(frameB);
  });
});
