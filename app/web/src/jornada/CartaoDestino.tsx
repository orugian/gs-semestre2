import {Badge} from '@astryxdesign/core/Badge';
import {Button} from '@astryxdesign/core/Button';
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
  onEscolherDestino?: (destinoId: string) => void;
  isEscolhendo?: boolean;
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

export function CartaoDestino({
  destino,
  onEscolherDestino,
  isEscolhendo = false,
}: CartaoDestinoProps) {
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
          <header className="flex flex-col gap-1 border-b border-[#616191]/20 pb-4">
            <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
              {destino.nome}
            </Heading>
          </header>

          {/* (1) Obrigatórios ainda não atendidos (Sempre visível) */}
          <section className="flex flex-col gap-2">
            <Heading level={4} className="!font-['Barlow_Condensed'] font-semibold text-base text-[#000091]">
              {TEXTOS_JORNADA.comparacao.obrigatoriosNaoAtendidos.titulo}
            </Heading>
            {obrigatorios_nao_atendidos.length === 0 ? (
              <div className="p-3 border border-[#616191]/20 rounded bg-[#F2F2F2]">
                <Text type="body">
                  {TEXTOS_JORNADA.comparacao.obrigatoriosNaoAtendidos.todosDemonstrados}
                </Text>
              </div>
            ) : (
              <ul className="flex flex-col gap-2">
                {obrigatorios_nao_atendidos.map((item) => (
                  <li
                    key={item.id_local}
                    className="flex items-center justify-between gap-2 p-2 border border-[#616191]/20 rounded bg-[#FFFFFF]"
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
            <Heading level={4} className="!font-['Barlow_Condensed'] font-semibold text-base text-[#000091]">
              {TEXTOS_JORNADA.comparacao.contagem.titulo}
            </Heading>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              <div className="p-3 border border-[#616191]/20 rounded flex flex-col items-center bg-[#FFFFFF]">
                <Text type="supporting" className="text-xs text-[#616191]">
                  {TEXTOS_JORNADA.comparacao.contagem.demonstrada}
                </Text>
                <span className="text-xl font-bold font-['Barlow_Condensed'] text-[#000091]">
                  {requisitos.contagem.demonstrada}
                </span>
              </div>
              <div className="p-3 border border-[#616191]/20 rounded flex flex-col items-center bg-[#FFFFFF]">
                <Text type="supporting" className="text-xs text-[#616191]">
                  {TEXTOS_JORNADA.comparacao.contagem.declarada}
                </Text>
                <span className="text-xl font-bold font-['Barlow_Condensed'] text-[#000091]">
                  {requisitos.contagem.declarada}
                </span>
              </div>
              <div className="p-3 border border-[#616191]/20 rounded flex flex-col items-center bg-[#FFFFFF]">
                <Text type="supporting" className="text-xs text-[#616191]">
                  {TEXTOS_JORNADA.comparacao.contagem.desconhecida}
                </Text>
                <span className="text-xl font-bold font-['Barlow_Condensed'] text-[#000091]">
                  {requisitos.contagem.desconhecida}
                </span>
              </div>
              <div className="p-3 border border-[#616191]/20 rounded flex flex-col items-center bg-[#FFFFFF]">
                <Text type="supporting" className="text-xs text-[#616191]">
                  {TEXTOS_JORNADA.comparacao.contagem.lacuna}
                </Text>
                <span className="text-xl font-bold font-['Barlow_Condensed'] text-[#000091]">
                  {requisitos.contagem.lacuna}
                </span>
              </div>
            </div>
          </section>

          {/* (3) Lista completa de requisitos agrupada por estado */}
          <section className="flex flex-col gap-3">
            <Heading level={4} className="!font-['Barlow_Condensed'] font-semibold text-base text-[#000091]">
              {TEXTOS_JORNADA.comparacao.requisitos.titulo}
            </Heading>

            <div className="flex flex-col gap-4">
              {ESTADOS_ORDENADOS.map((est) => {
                const itensDoEstado = itensPorEstado[est];
                if (itensDoEstado.length === 0) return null;

                const rotuloEstado = TEXTOS_JORNADA.comparacao.contagem[est];

                return (
                  <div key={est} className="flex flex-col gap-2">
                    <Text type="supporting" className="text-xs font-semibold text-[#616191]">
                      {rotuloEstado}
                    </Text>

                    <ul className="flex flex-col gap-2">
                      {itensDoEstado.map((req) => {
                        const motivoTexto = traduzirMotivo(req.motivo);
                        const temConflito = req.avisos?.includes('entrada_conflitante');

                        return (
                          <li
                            key={req.id_local}
                            className="p-3 border border-[#616191]/20 rounded flex flex-col gap-2 bg-[#FFFFFF]"
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
                              <Text type="supporting" className="text-xs text-[#616191]">{motivoTexto}</Text>
                            )}

                            {req.estado === 'declarada' && req.trecho_origem && (
                              <blockquote className="p-2 border-l-2 border-[#0000F2] bg-[#F2F2F2] rounded-r text-xs">
                                <Text type="supporting">{req.trecho_origem}</Text>
                              </blockquote>
                            )}

                            {temConflito && (
                              <div className="p-2 border border-[#616191]/20 rounded bg-[#F2F2F2]">
                                <Text type="supporting" className="text-xs text-[#616191]">
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
          <section className="flex flex-col gap-2 border-t border-[#616191]/20 pt-4">
            <Heading level={4} className="!font-['Barlow_Condensed'] font-semibold text-base text-[#000091]">
              {TEXTOS_JORNADA.comparacao.mercado.titulo}
            </Heading>

            {mercado.disponivel ? (
              <div className="flex flex-col gap-2 p-3 border border-[#616191]/20 rounded bg-[#FFFFFF]">
                <div className="flex items-center justify-between gap-2">
                  <Text type="body">
                    <span className="font-['IBM_Plex_Mono'] uppercase tracking-wider text-xs font-semibold text-[#000091]">
                      {TEXTOS_JORNADA.comparacao.mercado.natureza}
                    </span>
                  </Text>
                  <a
                    href={`/?destino=${destino.destino_id}&uf=${mercado.uf}`}
                    className="underline text-sm text-[#0000F2] hover:text-[#000091]"
                  >
                    {TEXTOS_JORNADA.comparacao.mercado.verNoMercado}
                  </a>
                </div>

                <Text type="supporting" className="text-xs text-[#616191]">{mercado.resumo}</Text>

                <div className="flex flex-col gap-1 pt-1 text-xs text-[#000091]">
                  <p>
                    <span className="font-medium text-[#616191]">Fonte:</span> {mercado.fonte}
                  </p>
                  <p>
                    <span className="font-medium text-[#616191]">População:</span>{' '}
                    {mercado.populacao}
                  </p>
                  <p>
                    <span className="font-medium text-[#616191]">Unidade:</span>{' '}
                    {mercado.unidade}
                  </p>
                  <p>
                    <span className="font-medium text-[#616191]">Período:</span>{' '}
                    {mercado.referencia_temporal}
                  </p>
                  <p>
                    <span className="font-medium text-[#616191]">UF:</span> {mercado.uf}
                  </p>
                  <p>
                    <span className="font-medium text-[#616191]">
                      {TEXTOS_JORNADA.comparacao.mercado.rotuloValor}:
                    </span>{' '}
                    <span className="font-['IBM_Plex_Mono'] font-semibold">
                      {mercado.ultimo_observado.valor}
                    </span>
                  </p>
                </div>
              </div>
            ) : (
              <div className="p-3 border border-[#616191]/20 rounded bg-[#F2F2F2]">
                <Text type="body">{traduzirMotivoMercado(mercado.motivo)}</Text>
              </div>
            )}
          </section>

          {/* (5) Conflitos e observações com a disponibilidade */}
          <section className="flex flex-col gap-2 border-t border-[#616191]/20 pt-4">
            <Heading level={4} className="!font-['Barlow_Condensed'] font-semibold text-base text-[#000091]">
              {TEXTOS_JORNADA.comparacao.preferencias.titulo}
            </Heading>

            {preferencias.conflitos.length === 0 &&
            preferencias.observacoes.length === 0 ? (
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.comparacao.preferencias.semConflitos}
              </Text>
            ) : (
              <div className="flex flex-col gap-2">
                {preferencias.conflitos.length > 0 && (
                  <ul className="flex flex-col gap-1">
                    {preferencias.conflitos.map((conf, idx) => (
                      <li key={`conf-${idx}`} className="p-2 border border-[#616191]/20 rounded bg-[#FFFFFF]">
                        <Text type="body">{conf}</Text>
                      </li>
                    ))}
                  </ul>
                )}
                {preferencias.observacoes.length > 0 && (
                  <ul className="flex flex-col gap-1">
                    {preferencias.observacoes.map((obs, idx) => (
                      <li key={`obs-${idx}`} className="p-2 border border-[#616191]/20 rounded bg-[#FFFFFF]">
                        <Text type="supporting" className="text-xs text-[#616191]">{obs}</Text>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </section>

          {/* (6) Escolha de Destino */}
          <section className="flex justify-end border-t border-[#616191]/20 pt-4">
            <Button
              type="button"
              variant="primary"
              label={TEXTOS_JORNADA.comparacao.escolherDestino}
              onClick={() => onEscolherDestino?.(destino.destino_id)}
              isDisabled={isEscolhendo}
              isLoading={isEscolhendo}
            />
          </section>
        </div>
      </Card>
    </div>
  );
}
