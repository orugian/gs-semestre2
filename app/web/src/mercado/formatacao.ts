import {DESTINOS_MVP, UFS_BRASIL} from '../api/mercado';

/**
 * Utilitários de formatação em pt-BR para o módulo de mercado.
 */

const formatoNumeroInteiro = new Intl.NumberFormat('pt-BR', {
  maximumFractionDigits: 0,
});

const formatoNumeroDecimal = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

const formatoNumeroDuasCasas = new Intl.NumberFormat('pt-BR', {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/**
 * Converte competência AAAAMM em mm/aaaa.
 * Exemplo: "202509" -> "09/2025".
 */
export function formatarCompetencia(competencia: string | null | undefined): string {
  if (!competencia || competencia.length !== 6) {
    return '—';
  }
  const ano = competencia.slice(0, 4);
  const mes = competencia.slice(4, 6);
  return `${mes}/${ano}`;
}

/**
 * Formata intervalo de competências como mm/aaaa–mm/aaaa.
 */
export function formatarPeriodo(inicio: string, fim: string): string {
  return `${formatarCompetencia(inicio)}–${formatarCompetencia(fim)}`;
}

/**
 * Formata número no padrão pt-BR. Retorna "—" se nulo/indefinido.
 */
export function formatarNumero(
  valor: number | null | undefined,
  casasDecimais = 0
): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return '—';
  }
  if (casasDecimais === 0) {
    return formatoNumeroInteiro.format(valor);
  }
  if (casasDecimais === 1) {
    return formatoNumeroDecimal.format(valor);
  }
  return formatoNumeroDuasCasas.format(valor);
}

/**
 * Formata valor de série: se null, retorna "sem dado".
 */
export function formatarValorSerie(valor: number | null | undefined): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return 'sem dado';
  }
  return formatoNumeroInteiro.format(valor);
}

/**
 * Formata taxa/percentual (ex: 0.1256 -> 12,6%).
 */
export function formatarPercentual(
  valor: number | null | undefined,
  casasDecimais = 1
): string {
  if (valor === null || valor === undefined || Number.isNaN(valor)) {
    return '—';
  }
  const formatter = new Intl.NumberFormat('pt-BR', {
    style: 'percent',
    minimumFractionDigits: casasDecimais,
    maximumFractionDigits: casasDecimais,
  });
  return formatter.format(valor);
}

/**
 * Formata média ± desvio padrão para métricas CV.
 */
export function formatarMediaDesvio(
  medio: number | null | undefined,
  desvio: number | null | undefined
): string {
  if (medio === null || medio === undefined) {
    return '—';
  }
  const medioFormatado = formatarNumero(medio, 1);
  if (desvio === null || desvio === undefined) {
    return medioFormatado;
  }
  const desvioFormatado = formatarNumero(desvio, 1);
  return `${medioFormatado} ± ${desvioFormatado}`;
}

/**
 * Dicionário canônico de nomes legíveis dos modelos do painel técnico.
 */
export const NOMES_LEGIVEIS_MODELOS: Record<string, string> = {
  persistencia: 'Persistência',
  sazonal: 'Sazonal (ano anterior)',
  ridge: 'Ridge',
  random_forest: 'Random Forest',
  hist_gradient_boosting: 'HistGradientBoosting',
  mlp: 'MLP (rede neural)',
};

/**
 * Formata ID ou nome cru de modelo para exibição legível ao usuário.
 */
export function formatarNomeModelo(idOuNome: string | null | undefined): string {
  if (!idOuNome) return '—';
  const chave = idOuNome.toLowerCase().trim();
  if (NOMES_LEGIVEIS_MODELOS[chave]) {
    return NOMES_LEGIVEIS_MODELOS[chave];
  }
  return idOuNome;
}

/**
 * Formata status de promoção cru da API (ex: "nao_decidida" -> "não decidida").
 */
export function formatarStatusPromocao(status: string | null | undefined): string {
  if (!status) return '—';
  if (status === 'nao_decidida') {
    return 'não decidida';
  }
  return status;
}

/**
 * Formata ID de artefato de modelo (ex: "hist_gradient_boosting:..." -> "HistGradientBoosting:...").
 */
export function formatarIdArtefato(id: string | null | undefined): string {
  if (!id) return '—';
  return id.replace(/^([a-z_]+):/, (_, mod) => `${formatarNomeModelo(mod)}:`);
}

/**
 * Gera ticks espaçados de forma uniforme por índice (no máximo maxTicks, ex: 7).
 * Sempre inclui o primeiro (0) e o último (totalPontos - 1).
 * Se o penúltimo tick ficar a menos de um intervalo mínimo do último, omite o penúltimo.
 */
export function gerarIndicesTicks(
  totalPontos: number,
  maxTicks = 7,
  minIntervalo?: number
): number[] {
  if (totalPontos <= 0) return [];
  if (totalPontos === 1) return [0];
  if (totalPontos <= maxTicks) {
    return Array.from({length: totalPontos}, (_, i) => i);
  }

  const passo = Math.max(1, Math.floor((totalPontos - 1) / (maxTicks - 1)));
  const intervaloMin = minIntervalo ?? Math.max(2, Math.floor(passo * 0.5));

  const ticks: number[] = [];
  for (let i = 0; i < totalPontos - 1; i += passo) {
    ticks.push(i);
  }

  const ultimo = totalPontos - 1;
  const penultimo = ticks[ticks.length - 1];

  if (penultimo === ultimo) {
    return ticks;
  }

  if (ultimo - penultimo < intervaloMin || ticks.length >= maxTicks) {
    ticks[ticks.length - 1] = ultimo;
  } else {
    ticks.push(ultimo);
  }

  return ticks;
}

export interface EstadoNavegacao {
  aba: 'mercado' | 'painel_tecnico';
  destino: string;
  uf: string;
}

export const ESTADO_NAVEGACAO_PADRAO: EstadoNavegacao = {
  aba: 'mercado',
  destino: 'analista_dados_bi',
  uf: 'SP',
};

const DESTINOS_VALIDOS = new Set<string>(DESTINOS_MVP.map((d) => d.value));
const UFS_VALIDAS = new Set<string>(UFS_BRASIL);

/**
 * Lê e valida o estado de navegação a partir da URL. Valores inválidos caem no padrão.
 */
export function lerEstadoUrl(search: string, hash: string): EstadoNavegacao {
  const query = search.startsWith('?') ? search.slice(1) : search;
  const params = new URLSearchParams(query);
  const paramDestino = params.get('destino');
  const paramUf = params.get('uf')?.toUpperCase();

  const destino =
    paramDestino && DESTINOS_VALIDOS.has(paramDestino)
      ? paramDestino
      : ESTADO_NAVEGACAO_PADRAO.destino;

  const uf =
    paramUf && UFS_VALIDAS.has(paramUf)
      ? paramUf
      : ESTADO_NAVEGACAO_PADRAO.uf;

  const aba = hash === '#painel-tecnico' ? 'painel_tecnico' : 'mercado';

  return {aba, destino, uf};
}

/**
 * Formata estado de navegação em URL com query e hash.
 */
export function formatarUrlNavegacao(
  estado: EstadoNavegacao,
  pathname = '/'
): string {
  const params = new URLSearchParams();
  params.set('destino', estado.destino);
  params.set('uf', estado.uf);

  const hash = estado.aba === 'painel_tecnico' ? '#painel-tecnico' : '';
  const search = `?${params.toString()}`;

  return `${pathname}${search}${hash}`;
}
