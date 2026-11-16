import {requisitar} from './cliente';

export type EstadoEvidencia = 'declarada' | 'demonstrada';
export type RevisaoCompetencia = 'pendente' | 'confirmada' | 'rejeitada' | 'nao_possuo';
export type OrigemCompetencia = 'extracao_llm' | 'manual';

export interface Competencia {
  id: string;
  esco_id: string;
  titulo: string;
  trecho_origem: string | null;
  origem: OrigemCompetencia;
  estado_evidencia: EstadoEvidencia;
  revisao: RevisaoCompetencia;
  curriculo_id: string;
  extracao_id: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface Descartadas {
  fora_da_lista: number;
  sem_trecho: number;
  trecho_nao_encontrado: number;
  duplicadas: number;
}

export interface RespostaExtracao {
  extracao_id: string;
  modelo: string;
  candidatas: Competencia[];
  descartadas: Descartadas;
  aviso: string;
}

export interface RespostaListarCompetencias {
  itens: Competencia[];
}

export async function extrairCompetencias(
  curriculoId: string
): Promise<RespostaExtracao> {
  return requisitar<RespostaExtracao>('POST', '/me/competencias/extrair', {
    curriculo_id: curriculoId,
  });
}

export async function listarCompetencias(): Promise<RespostaListarCompetencias> {
  return requisitar<RespostaListarCompetencias>('GET', '/me/competencias');
}

export async function atualizarCompetencia(
  id: string,
  acao: 'confirmar' | 'rejeitar' | 'nao_possuo',
  trechoOrigem?: string | null
): Promise<Competencia> {
  const corpo: {acao: string; trecho_origem?: string | null} = {acao};
  if (trechoOrigem !== undefined) {
    corpo.trecho_origem = trechoOrigem;
  }
  return requisitar<Competencia>('PATCH', `/me/competencias/${id}`, corpo);
}
