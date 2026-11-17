export class ErroApi extends Error {
  status: number;
  erro: string;
  detalhes: string;

  constructor(status: number, erro: string, detalhes: string) {
    super(detalhes || erro || `Erro ${status}`);
    this.name = 'ErroApi';
    this.status = status;
    this.erro = erro;
    this.detalhes = detalhes;
  }
}

export function obterCookieCsrf(): string | null {
  if (typeof document === 'undefined') return null;
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : null;
}

export async function requisitar<T>(
  metodo: string,
  caminho: string,
  corpo?: unknown
): Promise<T> {
  const url = caminho.startsWith('/api')
    ? caminho
    : `/api${caminho.startsWith('/') ? caminho : `/${caminho}`}`;

  const metodoUpper = metodo.toUpperCase();
  const headers: Record<string, string> = {};

  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(metodoUpper)) {
    const csrfToken = obterCookieCsrf();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }

  let body: BodyInit | undefined;
  if (corpo !== undefined) {
    if (typeof FormData !== 'undefined' && corpo instanceof FormData) {
      body = corpo;
      // Não define Content-Type manual para preservar boundary do multipart
    } else {
      headers['Content-Type'] = 'application/json';
      body = JSON.stringify(corpo);
    }
  }

  const resposta =
    metodoUpper === 'GET' && Object.keys(headers).length === 0
      ? await fetch(url)
      : await fetch(url, {
          method: metodoUpper,
          credentials: 'same-origin',
          headers,
          body,
        });

  if (!resposta.ok) {
    let erro = resposta.statusText || `Erro ${resposta.status}`;
    let detalhes = '';

    try {
      const dados = await resposta.json();
      if (dados && typeof dados === 'object') {
        if (typeof dados.erro === 'string') erro = dados.erro;
        if (typeof dados.detalhes === 'string') detalhes = dados.detalhes;
      }
    } catch {
      try {
        const texto = await resposta.text();
        if (texto) detalhes = texto;
      } catch {
        // corpo vazio
      }
    }

    throw new ErroApi(resposta.status, erro, detalhes);
  }

  if (resposta.status === 204) {
    return undefined as T;
  }

  return (await resposta.json()) as T;
}

export function mensagemDeErro(err: unknown, fallback: string): string {
  if (err instanceof ErroApi) {
    return err.detalhes || err.erro || fallback;
  }
  if (err instanceof Error) {
    return err.message || fallback;
  }
  return fallback;
}
