import {Badge} from '@astryxdesign/core/Badge';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {Text} from '@astryxdesign/core/Text';
import {
  DestinoComparado,
  EstadoRequisito,
  RequisitoComparacaoItem,
} from '../api/comparacao';
import {TEXTOS_JORNADA} from './textos';

export interface CartaoDestinoProps {
  destino: DestinoComparado;
}

function traduzirMotivo(motivo: string | null | undefined): string | null {
  if (!motivo) return null;
  const dicionario: Record<string, string> =
    TEXTOS_JORNADA.comparacao.requisitos.motivos;
  return dicionario[motivo] || motivo;
}

function traduzirMotivoMercado(motivo: string | null | undefined): string {
  if (!motivo) return 'Mercado indisponível';
  const dicionario: Record<string, string> =
    TEXTOS_JORNADA.comparacao.mercado.motivosIndisponivel;
  return dicionario[motivo] || motivo;
}

const ESTADOS_ORDENADOS: EstadoRequisito[] = [
  'demonstrada',
  'declarada',
  'desconhecida',
  'lacuna',
];

export function CartaoDestino({destino}: CartaoDestinoProps) {
  const {dimensoes} = destino;
  const {requisitos, obrigatorios_nao_atendidos, mercado, preferencias} = dimensoes;

  // Agrupamento de requisitos por estado
  const itensPorEstado: Record<EstadoRequisito, RequisitoComparacaoItem[]> = {
    demonstrada: [],
    declarada: [],
    desconhecida: [],
    lacuna: [],
  };

  for (const item of requisitos.itens || []) {
    if (itensPorEstado[item.estado]) {
      itensPorEstado[item.estado].push(item);
    }
  }

  return (
    <div data-testid="cartao-destino" className="flex flex-col h-full">
      <Card width="100%">
        <div className="flex flex-col gap-6 p-5">
          {/* Cabeçalho do Cartão */}
          <header className="flex flex-col gap-1 border-b pb-4">
            <Heading level={3}>{destino.nome}</Heading>
          </header>

          {/* (1) Obrigatórios ainda não atendidos (Sempre visível) */}
          <section className="flex flex-col gap-2">
            <Heading level={4}>
              {TEXTOS_JORNADA.comparacao.obrigatoriosNaoAtendidos.titulo}
            </Heading>
            {obrigatorios_nao_atendidos.length === 0 ? (
              <div className="p-3 border rounded">
                <Text type="body">
                  {TEXTOS_JORNADA.comparacao.obrigatoriosNaoAtendidos.todosDemonstrados}
                </Text>
              </div>
            ) : (
              <ul className="flex flex-col gap-2">
                {obrigatorios_nao_atendidos.map((item) => (
                  <li
                    key={item.id_local}
                    className="flex items-center justify-between gap-2 p-2 border rounded"
                  >
                    <Text type="body">{item.titulo}</Text>
                    <Badge variant="neutral" label={item.estado} />
                  </li>
                ))}
              </ul>
            )}
          </section>

          {/* (2) Contagem por estado (sem barra de progresso e sem percentual) */}
          <section className="flex flex-col gap-2">
            <Heading level={4}>
              {TEXTOS_JORNADA.comparacao.contagem.titulo}
            </Heading>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-3 border rounded flex flex-col items-center">
                <Text type="supporting">
                  {TEXTOS_JORNADA.comparacao.contagem.demonstrada}
                </Text>
                <span className="text-xl font-bold">
                  {requisitos.contagem.demonstrada}
                </span>
              </div>
              <div className="p-3 border rounded flex flex-col items-center">
                <Text type="supporting">
                  {TEXTOS_JORNADA.comparacao.contagem.declarada}
                </Text>
                <span className="text-xl font-bold">
                  {requisitos.contagem.declarada}
                </span>
              </div>
              <div className="p-3 border rounded flex flex-col items-center">
                <Text type="supporting">
                  {TEXTOS_JORNADA.comparacao.contagem.desconhecida}
                </Text>
                <span className="text-xl font-bold">
                  {requisitos.contagem.desconhecida}
                </span>
              </div>
              <div className="p-3 border rounded flex flex-col items-center">
                <Text type="supporting">
                  {TEXTOS_JORNADA.comparacao.contagem.lacuna}
                </Text>
                <span className="text-xl font-bold">
                  {requisitos.contagem.lacuna}
                </span>
              </div>
            </div>
          </section>

          {/* (3) Lista completa de requisitos agrupada por estado */}
          <section className="flex flex-col gap-3">
            <Heading level={4}>
              {TEXTOS_JORNADA.comparacao.requisitos.titulo}
            </Heading>

            <div className="flex flex-col gap-4">
              {ESTADOS_ORDENADOS.map((est) => {
                const itensDoEstado = itensPorEstado[est];
                if (itensDoEstado.length === 0) return null;

                const rotuloEstado = TEXTOS_JORNADA.comparacao.contagem[est];

                return (
                  <div key={est} className="flex flex-col gap-2">
                    <Text type="supporting">
                      <span className="font-semibold">{rotuloEstado}</span>
                    </Text>

                    <ul className="flex flex-col gap-2">
                      {itensDoEstado.map((req) => {
                        const motivoTexto = traduzirMotivo(req.motivo);
                        const temConflito = req.avisos?.includes('entrada_conflitante');

                        return (
                          <li
                            key={req.id_local}
                            className="p-3 border rounded flex flex-col gap-2"
                          >
                            <div className="flex items-center justify-between gap-2 flex-wrap">
                              <Text type="body">{req.titulo}</Text>
                              {req.obrigatorio && (
                                <Badge
                                  variant="purple"
                                  label={TEXTOS_JORNADA.comparacao.requisitos.obrigatorio}
                                />
                              )}
                            </div>

                            {motivoTexto && (
                              <Text type="supporting">{motivoTexto}</Text>
                            )}

                            {req.estado === 'declarada' && req.trecho_origem && (
                              <blockquote className="p-2 border-l-2 rounded-r">
                                <Text type="supporting">{req.trecho_origem}</Text>
                              </blockquote>
                            )}

                            {temConflito && (
                              <div className="p-2 border rounded">
                                <Text type="supporting">
                                  {TEXTOS_JORNADA.comparacao.requisitos.avisoConflito}
                                </Text>
                              </div>
                            )}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                );
              })}
            </div>
          </section>

          {/* (4) Mercado formal observado */}
          <section className="flex flex-col gap-2 border-t pt-4">
            <Heading level={4}>
              {TEXTOS_JORNADA.comparacao.mercado.titulo}
            </Heading>

            {mercado.disponivel ? (
              <div className="flex flex-col gap-2 p-3 border rounded">
                <div className="flex items-center justify-between gap-2">
                  <Text type="body">
                    <span className="font-semibold">
                      {TEXTOS_JORNADA.comparacao.mercado.natureza}
                    </span>
                  </Text>
                  <a
                    href={`/?destino=${destino.destino_id}&uf=${mercado.uf}`}
                    className="underline text-sm"
                  >
                    {TEXTOS_JORNADA.comparacao.mercado.verNoMercado}
                  </a>
                </div>

                <Text type="supporting">{mercado.resumo}</Text>

                <div className="flex flex-col gap-1 pt-1 text-xs">
                  <p>
                    <span className="font-medium">Fonte:</span> {mercado.fonte}
                  </p>
                  <p>
                    <span className="font-medium">População:</span>{' '}
                    {mercado.populacao}
                  </p>
                  <p>
                    <span className="font-medium">Unidade:</span>{' '}
                    {mercado.unidade}
                  </p>
                  <p>
                    <span className="font-medium">Período:</span>{' '}
                    {mercado.referencia_temporal}
                  </p>
                  <p>
                    <span className="font-medium">UF:</span> {mercado.uf}
                  </p>
                  <p>
                    <span className="font-medium">
                      {TEXTOS_JORNADA.comparacao.mercado.rotuloValor}:
                    </span>{' '}
                    {mercado.ultimo_observado.valor}
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-3 border rounded">
                <Text type="body">{traduzirMotivoMercado(mercado.motivo)}</Text>
              </div>
            )}
          </section>

          {/* (5) Conflitos e observações com a disponibilidade */}
          <section className="flex flex-col gap-2 border-t pt-4">
            <Heading level={4}>
              {TEXTOS_JORNADA.comparacao.preferencias.titulo}
            </Heading>

            {preferencias.conflitos.length === 0 &&
            preferencias.observacoes.length === 0 ? (
              <Text type="supporting">
                {TEXTOS_JORNADA.comparacao.preferencias.semConflitos}
              </Text>
            ) : (
              <div className="flex flex-col gap-2">
                {preferencias.conflitos.length > 0 && (
                  <ul className="flex flex-col gap-1">
                    {preferencias.conflitos.map((conf, idx) => (
                      <li key={`conf-${idx}`} className="p-2 border rounded">
                        <Text type="body">{conf}</Text>
                      </li>
                    ))}
                  </ul>
                )}
                {preferencias.observacoes.length > 0 && (
                  <ul className="flex flex-col gap-1">
                    {preferencias.observacoes.map((obs, idx) => (
                      <li key={`obs-${idx}`} className="p-2 border rounded">
                        <Text type="supporting">{obs}</Text>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </section>
        </div>
      </Card>
    </div>
  );
}
