/**
 * Cliente HTTP e contratos de tipo para o módulo de mercado e painel técnico R06.
 */

export interface ReferenciaTemporal {
  inicio: string;
  fim: string;
}

export interface ObservadoSerieItem {
  competencia: string;
  valor: number | null;
}

export interface PrevistoSerieItem {
  competencia_origem: string;
  previsao: number;
  realizado: number;
}

export interface ObservadoSecao {
  natureza: string;
  fonte: string;
  populacao: string;
  unidade: string;
  referencia_temporal: ReferenciaTemporal;
  serie: ObservadoSerieItem[];
}

export interface PrevistoSecao {
  natureza: string;
  fonte: string;
  populacao: string;
  unidade: string;
  referencia_temporal: ReferenciaTemporal;
  modelo_exibido: string;
  status_promocao: string;
  serie: PrevistoSerieItem[];
}

export interface ContextoRegionalSecao {
  natureza: string;
  fonte: string;
  populacao: string;
  unidade: string;
  referencia_temporal: ReferenciaTemporal;
  regiao: string;
  serie: ObservadoSerieItem[];
}

export interface AbstencaoSecao {
  motivo: string;
  media_alvo_treino: number | null;
  limite_minimo: number;
  contexto_regional: ContextoRegionalSecao;
}

export interface ItemAmostraAdzuna {
  territorio: string;
  termo_busca: string;
  contagem_anuncios: number | null;
}

export interface AmostraAdzuna {
  disponivel: boolean;
  natureza: string;
  motivo: string;
  fonte?: string | null;
  atribuicao?: string | null;
  unidade?: string | null;
  populacao?: string | null;
  coletado_em?: string | null;
  itens: ItemAmostraAdzuna[];
}

export interface RespostaMercado {
  destino: string;
  uf: string;
  uf_codigo: string;
  observado: ObservadoSecao;
  previsto: PrevistoSecao | null;
  abstencao: AbstencaoSecao | null;
  amostra_adzuna: AmostraAdzuna;
  avisos: string[];
}

export interface CriterioPromocao {
  criterio: string;
  status: string;
  modelo_exibido: string;
}

export interface MetricasValidacaoGlobal {
  n: number;
  mae: number;
  rmse: number;
  wape: number;
  mase: number;
}

export interface MetricasCvTreino {
  mae_medio: number;
  mae_desvio: number;
  wape_medio?: number | null;
  wape_desvio?: number | null;
  mase_medio?: number | null;
  mase_desvio?: number | null;
}

export interface MetricasSerie {
  n?: number;
  mae: number;
  rmse?: number;
  wape?: number;
  mase?: number;
}

export interface ModelCard {
  _id: string;
  modelo: string;
  versao_artefato: string;
  tipo: string;
  data_treino_utc: string;
  periodo_treino: [string, string];
  periodo_validacao: [string, string];
  populacao: string;
  hiperparametros: Record<string, unknown>;
  seed: number;
  versoes: Record<string, string>;
  sha256_artefatos: Record<string, string>;
  selecao: string;
  limites: string[];
  status_promocao: string;
}

export interface PrevisaoValidacaoItem {
  competencia: string;
  previsao: number;
  alvo: number;
}

export interface ModeloPainelTecnico {
  id: string;
  nome: string;
  tipo: string;
  promovido: boolean;
  exibido_ao_usuario: boolean;
  metricas_validacao_global: MetricasValidacaoGlobal;
  metricas_cv_treino: MetricasCvTreino;
  metricas_serie: MetricasSerie | null;
  previsoes_validacao: PrevisaoValidacaoItem[];
  model_card: ModelCard;
}

export interface RespostaModelos {
  destino: string;
  uf: string;
  uf_codigo: string;
  elegivel: boolean;
  motivo_densidade: string;
  criterio_promocao: CriterioPromocao;
  modelos: ModeloPainelTecnico[];
  avisos: string[];
}

export class ApiError extends Error {
  status: number;
  detalhes?: string;

  constructor(status: number, message: string, detalhes?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detalhes = detalhes;
  }
}

export const DESTINOS_MVP = [
  {
    value: 'analista_dados_bi',
    label: 'Analista de Dados/BI',
  },
  {
    value: 'analista_monitoramento_iot',
    label: 'Analista de Monitoramento/IoT Industrial',
  },
  {
    value: 'analista_processos',
    label: 'Analista de Processos/Melhoria Contínua',
  },
] as const;

export const UFS_BRASIL = [
  'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA',
  'MT', 'MS', 'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN',
  'RS', 'RO', 'RR', 'SC', 'SP', 'SE', 'TO',
] as const;

export function obterApiBase(): string {
  return import.meta.env.VITE_API_URL ?? '/api';
}

export async function buscarMercado(
  destino: string,
  uf: string
): Promise<RespostaMercado> {
  const base = obterApiBase();
  const url = `${base}/mercado/${destino}?uf=${uf}`;
  const resposta = await fetch(url);

  if (!resposta.ok) {
    if (resposta.status === 503) {
      throw new ApiError(503, 'Dados de mercado indisponíveis no momento');
    }
    let detalhes: string | undefined;
    try {
      const corpo = (await resposta.json()) as { erro?: string; detalhes?: string };
      detalhes = corpo.detalhes ?? corpo.erro;
    } catch {
      // Ignora erro de JSON
    }
    throw new ApiError(
      resposta.status,
      detalhes ?? `Erro ${resposta.status} ao consultar mercado`,
      detalhes
    );
  }

  return (await resposta.json()) as RespostaMercado;
}

export async function buscarModelos(
  destino: string,
  uf: string
): Promise<RespostaModelos> {
  const base = obterApiBase();
  const url = `${base}/mercado/${destino}/modelos?uf=${uf}`;
  const resposta = await fetch(url);

  if (!resposta.ok) {
    if (resposta.status === 503) {
      throw new ApiError(503, 'Dados de mercado indisponíveis no momento');
    }
    let detalhes: string | undefined;
    try {
      const corpo = (await resposta.json()) as { erro?: string; detalhes?: string };
      detalhes = corpo.detalhes ?? corpo.erro;
    } catch {
      // Ignora erro de JSON
    }
    throw new ApiError(
      resposta.status,
      detalhes ?? `Erro ${resposta.status} ao consultar modelos`,
      detalhes
    );
  }

  return (await resposta.json()) as RespostaModelos;
}
