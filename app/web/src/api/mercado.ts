/**
 * Cliente HTTP e contratos de tipo para o módulo de mercado e painel técnico R06.
 */
import { requisitar, ErroApi } from './cliente';

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

async function requisitarMercado<T>(caminho: string, contexto: string): Promise<T> {
  try {
    return await requisitar<T>('GET', caminho);
  } catch (err) {
    if (err instanceof ErroApi) {
      if (err.status === 503) {
        throw new ErroApi(
          503,
          'Dados de mercado indisponíveis no momento',
          'Dados de mercado indisponíveis no momento'
        );
      }
      if (!err.detalhes) {
        throw new ErroApi(
          err.status,
          err.erro,
          `Erro ${err.status} ao consultar ${contexto}`
        );
      }
    }
    throw err;
  }
}

export async function buscarMercado(
  destino: string,
  uf: string
): Promise<RespostaMercado> {
  return requisitarMercado<RespostaMercado>(
    `/mercado/${destino}?uf=${uf}`,
    'mercado'
  );
}

export async function buscarModelos(
  destino: string,
  uf: string
): Promise<RespostaModelos> {
  return requisitarMercado<RespostaModelos>(
    `/mercado/${destino}/modelos?uf=${uf}`,
    'modelos'
  );
}
