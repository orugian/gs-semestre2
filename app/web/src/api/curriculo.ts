import {requisitar} from './cliente';

export interface Redacoes {
  nome: number;
  email: number;
  telefone: number;
  cpf: number;
  cep: number;
  endereco: number;
  url: number;
}

export type OrigemCurriculo = 'texto' | 'pdf' | 'docx';
export type StatusCurriculo = 'aguardando_confirmacao' | 'confirmado';

export interface Curriculo {
  id: string;
  origem: OrigemCurriculo;
  status: StatusCurriculo;
  texto_redigido: string;
  sha256_texto_redigido: string;
  redacoes: Redacoes;
  aviso_redacao: string;
  criado_em: string;
  confirmado_em: string | null;
}

export async function enviarExperiencias(texto: string): Promise<Curriculo> {
  return requisitar<Curriculo>('POST', '/me/experiencias', {texto});
}

export async function enviarArquivoCurriculo(arquivo: File): Promise<Curriculo> {
  const formData = new FormData();
  formData.append('arquivo', arquivo);
  return requisitar<Curriculo>('POST', '/me/curriculo', formData);
}

export async function obterCurriculo(id: string): Promise<Curriculo> {
  return requisitar<Curriculo>('GET', `/me/curriculo/${id}`);
}

export async function confirmarEnvioCurriculo(
  curriculoId: string,
  textoRevisado: string | null
): Promise<Curriculo> {
  return requisitar<Curriculo>('POST', '/me/curriculo/confirmar-envio', {
    curriculo_id: curriculoId,
    texto_revisado: textoRevisado,
  });
}
