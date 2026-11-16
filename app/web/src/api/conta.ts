import {requisitar} from './cliente';

export interface Usuario {
  id: string;
  email: string;
  criado_em: string;
  persona_demo?: 'S' | 'N';
}

export type FinalidadeConsentimento = 'perfil' | 'curriculo_llm' | 'laboratorio_nuvem';

export interface Consentimento {
  id: string;
  finalidade: FinalidadeConsentimento;
  versao_termo: string;
  concedido_em: string;
  revogado_em: string | null;
}

export interface RespostaConsentimentos {
  itens: Consentimento[];
}

export async function registrar(
  email: string,
  senha: string
): Promise<{id: string; email: string; criado_em: string}> {
  return requisitar('POST', '/auth/registrar', {email, senha});
}

export async function entrar(
  email: string,
  senha: string
): Promise<{id: string; email: string}> {
  return requisitar('POST', '/auth/login', {email, senha});
}

export async function sair(): Promise<void> {
  return requisitar('POST', '/auth/logout');
}

export async function obterMe(): Promise<Usuario> {
  return requisitar('GET', '/me');
}

export async function listarConsentimentos(): Promise<RespostaConsentimentos> {
  return requisitar('GET', '/me/consentimentos');
}

export async function concederConsentimento(
  finalidade: FinalidadeConsentimento
): Promise<Consentimento> {
  return requisitar('POST', '/me/consentimentos', {finalidade});
}

export async function revogarConsentimento(id: string): Promise<void> {
  return requisitar('DELETE', `/me/consentimentos/${id}`);
}
