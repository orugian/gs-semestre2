import {
  DESTINOS_MVP,
  UFS_BRASIL,
  DESTINO_PADRAO,
  UF_PADRAO,
} from '../dominio/listas';

export interface EstadoNavegacao {
  aba: 'mercado' | 'painel_tecnico' | 'jornada';
  destino: string;
  uf: string;
}

const ESTADO_NAVEGACAO_PADRAO: EstadoNavegacao = {
  aba: 'mercado',
  destino: DESTINO_PADRAO,
  uf: UF_PADRAO,
};

const DESTINOS_VALIDOS = new Set<string>(DESTINOS_MVP.map((d) => d.value));
const UFS_VALIDAS = new Set<string>(UFS_BRASIL);

/**
 * Lê e valida o estado de navegação a partir da URL. Valores inválidos caem no padrão.
 */
export function lerEstadoUrl(search: string, hash: string): EstadoNavegacao {
  const query = search.startsWith('?') ? search.slice(1) : search;
  const params = new URLSearchParams(query);
  const paramDestino = params.get('destino');
  const paramUf = params.get('uf')?.toUpperCase();

  const destino =
    paramDestino && DESTINOS_VALIDOS.has(paramDestino)
      ? paramDestino
      : ESTADO_NAVEGACAO_PADRAO.destino;

  const uf =
    paramUf && UFS_VALIDAS.has(paramUf)
      ? paramUf
      : ESTADO_NAVEGACAO_PADRAO.uf;

  const aba =
    hash === '#painel-tecnico'
      ? 'painel_tecnico'
      : hash === '#minha-transicao'
      ? 'jornada'
      : 'mercado';

  return {aba, destino, uf};
}

/**
 * Formata estado de navegação em URL com query e hash.
 */
export function formatarUrlNavegacao(
  estado: EstadoNavegacao,
  pathname = '/'
): string {
  const params = new URLSearchParams();
  params.set('destino', estado.destino);
  params.set('uf', estado.uf);

  const hash =
    estado.aba === 'painel_tecnico'
      ? '#painel-tecnico'
      : estado.aba === 'jornada'
      ? '#minha-transicao'
      : '';
  const search = `?${params.toString()}`;

  return `${pathname}${search}${hash}`;
}
