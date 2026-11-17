export const MOTIVOS_REQUISITO: Record<string, string> = {
  sem_informacao_suficiente: 'sem informação suficiente',
  ausencia_informada_pelo_usuario: 'você informou que não possui',
  exercicio_abaixo_do_minimo: 'exercício abaixo do mínimo',
  avaliacao_parcial_llm_indisponivel: 'avaliação parcial (IA indisponível)',
};

export function traduzirMotivo(motivo: string | null | undefined): string | null {
  if (!motivo) return null;
  return MOTIVOS_REQUISITO[motivo] || motivo;
}

export function varianteBadgeResultado(resultado: string): 'green' | 'blue' | 'neutral' {
  if (resultado === 'demonstrada') return 'green';
  if (resultado === 'parcial') return 'blue';
  return 'neutral';
}

export const ROTULOS_ESTADO_NUVEM: Record<string, string> = {
  pendente_nuvem: 'aguardando envio',
  sincronizado: 'enviado à nuvem',
  erro_permanente: 'não enviado',
};

export function traduzirEstadoNuvem(estado: string): string {
  return ROTULOS_ESTADO_NUVEM[estado] ?? estado;
}

export const ROTULOS_REVISAO: Record<string, string> = {
  pendente: 'pendente',
  confirmada: 'confirmada',
  rejeitada: 'rejeitada',
  nao_possuo: 'não possuo',
};

export function traduzirRevisao(revisao: string): string {
  return ROTULOS_REVISAO[revisao] ?? revisao;
}
