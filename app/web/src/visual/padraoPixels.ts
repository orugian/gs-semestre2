export interface PosicaoPonteiro {
  x: number;
  y: number;
}

/**
 * Função pura que calcula a intensidade [0..1] de cada pixel da matriz.
 * @param colunas Número de colunas da grade
 * @param linhas Número de linhas da grade
 * @param tempo Timestamp ou tempo acumulado em segundos
 * @param ponteiro Coordenadas do ponteiro (em células da grade ou normalizadas [0..1]), ou null
 * @returns Float32Array com intensidades [0..1] para cada célula (tamanho = colunas * linhas)
 */
export function padraoPixels(
  colunas: number,
  linhas: number,
  tempo: number,
  ponteiro: PosicaoPonteiro | null = null
): Float32Array {
  const total = colunas * linhas;
  const intensidades = new Float32Array(total);

  for (let r = 0; r < linhas; r++) {
    for (let c = 0; c < colunas; c++) {
      const idx = r * colunas + c;

      // Série temporal simulada: oscilação harmônica suave sugerindo tendência e sazonalidade
      const onda1 = Math.sin(c * 0.1 - tempo * 1.4);
      const onda2 = Math.cos(c * 0.22 + tempo * 0.8);
      const alturaNormalizada = 0.5 + 0.3 * onda1 + 0.15 * onda2;
      const linhaAlvo = alturaNormalizada * (linhas - 1);

      // Distância vertical até a linha principal da série
      const distLinha = Math.abs(r - linhaAlvo);
      let valor = 0.04; // Leve presença de fundo na grade

      if (distLinha < 1.0) {
        valor += 0.85 * (1.0 - distLinha);
      } else if (distLinha < 2.5) {
        valor += 0.35 * (1.0 - (distLinha - 1.0) / 1.5);
      }

      // Pulso horizontal viajante (onda de amostragem)
      const pulsoX = ((tempo * 12) % (colunas + 30)) - 15;
      const distPulso = Math.abs(c - pulsoX);
      if (distPulso < 10) {
        const fatorPulso = Math.cos((distPulso / 10) * (Math.PI / 2));
        valor += 0.3 * fatorPulso;
      }

      // Reação ao ponteiro: as células perto do cursor acendem suavemente
      if (ponteiro) {
        const px = ponteiro.x <= 1 && colunas > 1 ? ponteiro.x * colunas : ponteiro.x;
        const py = ponteiro.y <= 1 && linhas > 1 ? ponteiro.y * linhas : ponteiro.y;
        const dx = c - px;
        const dy = r - py;
        const distPonteiro = Math.sqrt(dx * dx + dy * dy);
        const raioInteracao = 6.0;
        if (distPonteiro < raioInteracao) {
          const fatorPonteiro = Math.max(0, 1.0 - distPonteiro / raioInteracao);
          valor += 0.45 * fatorPonteiro;
        }
      }

      // Garante delimitação matemática exata no intervalo [0, 1]
      intensidades[idx] = Math.min(1.0, Math.max(0.0, valor));
    }
  }

  return intensidades;
}
