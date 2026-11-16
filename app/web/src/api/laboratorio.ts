import {requisitar} from './cliente';

export type StatusSessao = 'ativa' | 'encerrada' | 'expirada';
export type RiscoLeitura = 'normal' | 'atencao' | 'critico';
export type StatusRelato = 'nenhum' | 'pendente' | 'enviado';

export interface SessaoLaboratorio {
  id: string;
  codigo: string;
  status: StatusSessao;
  criado_em: string;
  expira_em: string;
  instrucoes: string;
}

export interface LeituraLaboratorio {
  evento_id: string;
  metrica: string;
  unidade: string;
  valor: number;
  risco: RiscoLeitura;
  alerta: boolean;
  estado: string;
  medido_em: string;
}

export interface IndicadorMetrica {
  contagem: number;
  total_alertas: number;
  media: number;
  maximo: number;
  minimo: number;
}

export interface RelatoSessao {
  texto_redigido: string | null;
  status: StatusRelato;
}

export interface DetalheSessaoLaboratorio {
  id: string;
  codigo: string;
  status: StatusSessao;
  criado_em: string;
  expira_em: string;
  instrucoes: string;
  relato: RelatoSessao;
  leituras: LeituraLaboratorio[];
  indicadores: Record<string, IndicadorMetrica>;
}

export interface RespostaRelato {
  texto_redigido: string;
  status: 'pendente';
}

export async function criarSessaoLaboratorio(): Promise<SessaoLaboratorio> {
  return requisitar<SessaoLaboratorio>('POST', '/me/laboratorio/sessoes');
}

export async function obterSessaoAtual(): Promise<DetalheSessaoLaboratorio> {
  return requisitar<DetalheSessaoLaboratorio>(
    'GET',
    '/me/laboratorio/sessoes/atual'
  );
}

export async function obterSessaoLaboratorio(
  sessaoId: string
): Promise<DetalheSessaoLaboratorio> {
  return requisitar<DetalheSessaoLaboratorio>(
    'GET',
    `/me/laboratorio/sessoes/${sessaoId}`
  );
}

export async function enviarRelatoLaboratorio(
  sessaoId: string,
  relato: string
): Promise<RespostaRelato> {
  return requisitar<RespostaRelato>(
    'POST',
    `/me/laboratorio/sessoes/${sessaoId}/relato`,
    {relato}
  );
}
