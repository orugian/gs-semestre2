import {ErroApi, requisitar} from './cliente';

export interface IntencaoEntrada {
  atividades_desejadas: string[];
  motivos: string[];
  horas_semana: number;
  orcamento_mensal_brl: number | null;
  uf: string;
}

export interface IntencaoResposta {
  atividades_desejadas: string[];
  motivos: string[];
  horas_semana: number;
  orcamento_mensal_brl: number | null;
  uf: string;
  atualizado_em: string;
}

export async function obterIntencao(): Promise<IntencaoResposta | null> {
  try {
    return await requisitar<IntencaoResposta>('GET', '/me/intencao');
  } catch (err: unknown) {
    if (err instanceof ErroApi && err.status === 404) {
      return null;
    }
    throw err;
  }
}

export async function salvarIntencao(
  dados: IntencaoEntrada
): Promise<IntencaoResposta> {
  return requisitar<IntencaoResposta>('PUT', '/me/intencao', dados);
}
