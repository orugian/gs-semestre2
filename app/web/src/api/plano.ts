import {requisitar} from './cliente';

export type TipoCheckpoint =
  | 'estudar'
  | 'praticar'
  | 'demonstrar'
  | 'laboratorio'
  | 'exercicio';

export type StatusCheckpoint = 'pendente' | 'em_andamento' | 'concluido';

export interface CheckpointPlano {
  id: string;
  ordem: number;
  tipo: TipoCheckpoint;
  titulo: string;
  descricao: string;
  criterio_conclusao: string | null;
  requisito_id_local: string | null;
  estado_origem: string | null;
  motivo_origem: string | null;
  obrigatorio: boolean;
  exercicio_id: string | null;
  status: StatusCheckpoint;
}

export interface Plano {
  plano_id: string;
  gerado_em: string;
  destino_id: string;
  nome: string;
  versao_catalogo: string;
  regra: string;
  explicacao_regra: string;
  ja_demonstrados: string[];
  checkpoints: CheckpointPlano[];
  observacoes: string[];
  aviso: string;
}

export interface RespostaCaminho {
  caminho_id: string;
  destino_id: string;
  comparacao_id: string | null;
  criado_em: string;
  plano: Plano;
}

export async function criarCaminho(dados: {
  destino_id: string;
  comparacao_id: string | null;
}): Promise<RespostaCaminho> {
  return requisitar<RespostaCaminho>('POST', '/me/caminho', dados);
}

export async function obterPlano(): Promise<RespostaCaminho> {
  return requisitar<RespostaCaminho>('GET', '/me/plano');
}

export async function atualizarStatusCheckpoint(
  checkpointId: string,
  status: StatusCheckpoint
): Promise<CheckpointPlano> {
  return requisitar<CheckpointPlano>(
    'PATCH',
    `/me/plano/checkpoints/${checkpointId}`,
    {status}
  );
}
