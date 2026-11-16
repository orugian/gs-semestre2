import {requisitar} from './cliente';

export type EstadoRequisito = 'demonstrada' | 'declarada' | 'desconhecida' | 'lacuna';

export interface RequisitoDestino {
  id_local: string;
  esco_id: string;
  titulo: string;
  obrigatorio: boolean;
}

export interface DestinoResumo {
  destino_id: string;
  nome: string;
  descricao: string | null;
  requisitos: RequisitoDestino[];
}

export interface RespostaListarDestinos {
  itens: DestinoResumo[];
}

export interface RequisitoComparacaoItem {
  id_local: string;
  esco_id: string;
  titulo: string;
  obrigatorio: boolean;
  estado: EstadoRequisito;
  motivo: string | null;
  origem: string | null;
  trecho_origem: string | null;
  avisos: string[];
}

export interface ContagemEstados {
  demonstrada: number;
  declarada: number;
  desconhecida: number;
  lacuna: number;
}

export interface ObrigatorioNaoAtendido {
  id_local: string;
  titulo: string;
  estado: EstadoRequisito;
}

export interface MercadoDisponivel {
  disponivel: true;
  natureza: 'observado';
  fonte: string;
  populacao: string;
  unidade: string;
  uf: string;
  referencia_temporal: string;
  ultimo_observado: {
    competencia: string;
    valor: number;
  };
  elegivel_previsao: boolean;
  resumo: string;
  detalhe_url: string;
}

export interface MercadoIndisponivel {
  disponivel: false;
  natureza: 'indisponivel';
  motivo: 'uf_nao_informada' | 'snapshot_indisponivel' | 'sem_serie_para_uf' | string;
  uf?: string;
}

export type MercadoComparacao = MercadoDisponivel | MercadoIndisponivel;

export interface PreferenciasComparacao {
  conflitos: string[];
  observacoes: string[];
}

export interface AproveitamentoExperiencia {
  declarados: string[];
  demonstrados: string[];
}

export interface DimensoesComparacao {
  requisitos: {
    itens: RequisitoComparacaoItem[];
    contagem: ContagemEstados;
  };
  obrigatorios_nao_atendidos: ObrigatorioNaoAtendido[];
  aproveitamento_experiencia: AproveitamentoExperiencia;
  mercado: MercadoComparacao;
  preferencias: PreferenciasComparacao;
}

export interface DestinoComparado {
  destino_id: string;
  nome: string;
  dimensoes: DimensoesComparacao;
  situacao_obrigatorios: 'todos_demonstrados' | 'ha_obrigatorios_nao_demonstrados';
}

export interface RespostaComparacao {
  comparacao_id: string;
  criado_em: string;
  uf: string | null;
  destinos: DestinoComparado[];
  aviso: string;
}

export interface CriarComparacaoEntrada {
  destinos: string[];
  uf: string | null;
}

export async function listarDestinos(): Promise<RespostaListarDestinos> {
  return requisitar<RespostaListarDestinos>('GET', '/destinos');
}

export async function criarComparacao(
  entrada: CriarComparacaoEntrada
): Promise<RespostaComparacao> {
  return requisitar<RespostaComparacao>('POST', '/me/comparacoes', entrada);
}

export async function obterComparacao(id: string): Promise<RespostaComparacao> {
  return requisitar<RespostaComparacao>('GET', `/me/comparacoes/${id}`);
}
