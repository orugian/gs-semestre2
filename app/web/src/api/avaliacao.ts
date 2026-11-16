import {requisitar} from './cliente';

export interface QuestaoObjetiva {
  id: string;
  enunciado: string;
  alternativas: Record<string, string>;
}

export interface CriterioAberta {
  id: string;
  descricao: string;
  ancoras: Record<'0' | '1' | '2', string>;
}

export interface QuestaoAberta {
  id: string;
  enunciado: string;
  criterios: CriterioAberta[];
}

export interface PoliticaExercicio {
  pesos: {
    objetiva: number;
    llm: number;
  };
  minimo_objetiva: number;
  minimo_llm: number;
  max_tentativas_24h: number;
}

export interface ExercicioDiagnostico {
  destino_id: string;
  exercicio_id: string;
  versao: string;
  cenario: string;
  questoes_objetivas: QuestaoObjetiva[];
  questao_aberta: QuestaoAberta;
  politica: PoliticaExercicio;
  tentativas_restantes_24h: number;
}

export interface QuestaoObjetivaResultado {
  id: string;
  resposta: string;
  correta: boolean;
  gabarito: string;
  justificativa: string;
}

export interface ResultadoObjetiva {
  acertos: number;
  total: number;
  nota: number;
  questoes: QuestaoObjetivaResultado[];
}

export interface CriterioAbertaResultado {
  id: string;
  nivel: number;
  justificativa: string;
  trecho_resposta: string;
}

export interface ResultadoAberta {
  status: 'avaliada' | 'parcial';
  nota: number | null;
  modelo: string | null;
  em_cache: boolean;
  criterios: CriterioAbertaResultado[];
}

export type ResultadoTentativa = 'demonstrada' | 'insuficiente' | 'parcial';

export interface RequisitoAvaliado {
  id_local: string;
  esco_id: string;
}

export interface TentativaExercicio {
  tentativa_id: string;
  destino_id: string;
  exercicio_id: string;
  exercicio_versao: string;
  criado_em: string;
  objetiva: ResultadoObjetiva;
  aberta: ResultadoAberta;
  nota_final: number | null;
  resultado: ResultadoTentativa;
  requisitos_avaliados: RequisitoAvaliado[];
  tentativas_restantes_24h: number;
  aviso: string;
}

export interface ItemHistoricoTentativa {
  tentativa_id: string;
  destino_id: string;
  exercicio_id: string;
  exercicio_versao: string;
  criado_em: string;
  nota_objetiva: number;
  status_aberta: 'avaliada' | 'parcial';
  nota_llm: number | null;
  nota_final: number | null;
  resultado: ResultadoTentativa;
  discordo_em: string | null;
}

export interface HistoricoTentativas {
  itens: ItemHistoricoTentativa[];
  ultima: string | null;
  melhor: string | null;
}

export interface RespostaDiscordo {
  tentativa_id: string;
  discordo_em: string;
  motivo: string;
  status_contestacao: 'registrada';
}

export async function obterExercicio(
  destinoId: string
): Promise<ExercicioDiagnostico> {
  return requisitar<ExercicioDiagnostico>(
    'GET',
    `/destinos/${destinoId}/exercicio`
  );
}

export async function enviarTentativa(dados: {
  destino_id: string;
  exercicio_id: string;
  respostas_objetivas: Record<string, string>;
  resposta_aberta: string;
}): Promise<TentativaExercicio> {
  return requisitar<TentativaExercicio>('POST', '/me/tentativas', dados);
}

export async function registrarDiscordo(
  tentativaId: string,
  motivo: string
): Promise<RespostaDiscordo> {
  return requisitar<RespostaDiscordo>(
    'POST',
    `/me/tentativas/${tentativaId}/discordo`,
    {motivo}
  );
}

export async function listarTentativas(
  destinoId: string
): Promise<HistoricoTentativas> {
  return requisitar<HistoricoTentativas>(
    'GET',
    `/me/tentativas?destino_id=${destinoId}`
  );
}
