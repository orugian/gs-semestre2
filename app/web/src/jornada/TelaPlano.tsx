import {useEffect, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {listarTentativas} from '../api/avaliacao';
import {ErroApi} from '../api/cliente';
import {
  atualizarStatusCheckpoint,
  CheckpointPlano,
  obterPlano,
  RespostaCaminho,
  StatusCheckpoint,
} from '../api/plano';
import {TEXTOS_JORNADA} from './textos';

export interface TelaPlanoProps {
  planoInicial?: RespostaCaminho | null;
  onPlanoAtualizado?: (caminho: RespostaCaminho) => void;
  onIrParaComparacao?: () => void;
  onFazerExercicio?: () => void;
  onIrParaLaboratorio?: () => void;
}

function traduzirMotivo(motivo: string | null | undefined): string | null {
  if (!motivo) return null;
  const dicionario: Record<string, string> =
    TEXTOS_JORNADA.comparacao.requisitos.motivos;
  return dicionario[motivo] || motivo;
}

export function TelaPlano({
  planoInicial,
  onPlanoAtualizado,
  onIrParaComparacao,
  onFazerExercicio,
  onIrParaLaboratorio,
}: TelaPlanoProps) {
  const [caminho, setCaminho] = useState<RespostaCaminho | null>(
    planoInicial || null
  );
  const [carregando, setCarregando] = useState(!planoInicial);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizandoCpId, setAtualizandoCpId] = useState<string | null>(null);
  const [ultimaTentativa, setUltimaTentativa] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;

    if (!planoInicial) {
      setCarregando(true);
      setErro(null);

      obterPlano()
        .then((resp) => {
          if (!cancelado) {
            setCaminho(resp);
          }
        })
        .catch((err: unknown) => {
          if (!cancelado) {
            if (err instanceof ErroApi && err.status === 404) {
              setCaminho(null);
            } else if (err instanceof ErroApi) {
              setErro(err.detalhes || err.erro);
            } else if (err instanceof Error) {
              setErro(err.message);
            } else {
              setErro('Não foi possível carregar o plano.');
            }
          }
        })
        .finally(() => {
          if (!cancelado) {
            setCarregando(false);
          }
        });
    } else {
      setCaminho(planoInicial);
      setCarregando(false);
    }

    return () => {
      cancelado = true;
    };
  }, [planoInicial, onPlanoAtualizado]);

  // Notifica o pai após o commit do React, nunca dentro do atualizador de estado.
  useEffect(() => {
    if (caminho) onPlanoAtualizado?.(caminho);
  }, [caminho, onPlanoAtualizado]);

  // Carrega histórico para exibir última tentativa do exercício diagnóstico
  useEffect(() => {
    let cancelado = false;
    const destinoId = caminho?.destino_id;
    if (!destinoId) return;

    listarTentativas(destinoId)
      .then((hist) => {
        if (!cancelado && hist?.itens?.length > 0) {
          const ult = hist.itens.find((i) => i.tentativa_id === hist.ultima) || hist.itens[0];
          if (ult) {
            setUltimaTentativa(ult.resultado);
          }
        }
      })
      .catch(() => {
        // Ignora erro no histórico secundário
      });

    return () => {
      cancelado = true;
    };
  }, [caminho?.destino_id]);

  const handleAtualizarStatus = async (
    cp: CheckpointPlano,
    novoStatus: StatusCheckpoint
  ) => {
    if (cp.tipo === 'exercicio') return; // Tipo exercício não tem ação manual

    setAtualizandoCpId(cp.id);
    setErro(null);

    try {
      const cpAtualizado = await atualizarStatusCheckpoint(cp.id, novoStatus);

      setCaminho((anterior) => {
        if (!anterior) return null;
        const novosCheckpoints = anterior.plano.checkpoints.map((item) =>
          item.id === cp.id ? cpAtualizado : item
        );
        const atualizado: RespostaCaminho = {
          ...anterior,
          plano: {
            ...anterior.plano,
            checkpoints: novosCheckpoints,
          },
        };
        return atualizado;
      });
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        setErro(err.detalhes || err.erro);
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro ao atualizar checkpoint.');
      }
    } finally {
      setAtualizandoCpId(null);
    }
  };

  if (carregando) {
    return (
      <div className="flex items-center justify-center p-12" aria-live="polite">
        <Spinner label={TEXTOS_JORNADA.plano.carregando} />
      </div>
    );
  }

  if (!caminho || !caminho.plano) {
    return (
      <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
        <header className="flex flex-col gap-2">
          <Heading level={2}>{TEXTOS_JORNADA.plano.titulo}</Heading>
        </header>

        <Card width="100%">
          <div className="flex flex-col items-center justify-center text-center p-8 gap-4">
            <Heading level={3}>{TEXTOS_JORNADA.plano.vazioTitulo}</Heading>
            <Text type="supporting">
              {TEXTOS_JORNADA.plano.vazioDescricao}
            </Text>
            {onIrParaComparacao && (
              <Button
                type="button"
                variant="primary"
                label={TEXTOS_JORNADA.plano.irParaComparacao}
                onClick={onIrParaComparacao}
              />
            )}
          </div>
        </Card>
      </div>
    );
  }

  const {plano} = caminho;
  const checkpointsOrdenados = [...plano.checkpoints].sort(
    (a, b) => a.ordem - b.ordem
  );

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      {/* Cabeçalho */}
      <header className="flex flex-col gap-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <Heading level={2}>{plano.nome || TEXTOS_JORNADA.plano.titulo}</Heading>
          {onIrParaComparacao && (
            <Button
              type="button"
              variant="secondary"
              label={TEXTOS_JORNADA.plano.irParaComparacao}
              onClick={onIrParaComparacao}
            />
          )}
        </div>
        {plano.explicacao_regra && (
          <Text type="supporting">{plano.explicacao_regra}</Text>
        )}
      </header>

      {/* Erro global */}
      {erro && (
        <div role="alert" aria-live="polite">
          <Banner status="error" title="Atenção" description={erro} />
        </div>
      )}

      {/* Aviso institucional obrigatório em destaque (T07/T08) */}
      <div aria-live="polite">
        <Banner
          status="info"
          title="Aviso sobre o plano"
          description={plano.aviso || TEXTOS_JORNADA.plano.avisoFixo}
        />
      </div>

      {/* Lista ordenada de Checkpoints */}
      <section className="flex flex-col gap-4">
        <Heading level={3}>{TEXTOS_JORNADA.plano.secaoCheckpoints}</Heading>

        <div className="flex flex-col gap-4">
          {checkpointsOrdenados.map((cp) => {
            const isAtualizando = atualizandoCpId === cp.id;
            const estadoTraduzido = cp.estado_origem
              ? (TEXTOS_JORNADA.comparacao.contagem as Record<string, string>)[
                  cp.estado_origem
                ] || cp.estado_origem
              : null;
            const motivoTraduzido = traduzirMotivo(cp.motivo_origem);
            const tipoRotulo =
              TEXTOS_JORNADA.plano.tipos[cp.tipo] || cp.tipo;
            const statusRotulo =
              TEXTOS_JORNADA.plano.status[cp.status] || cp.status;

            return (
              <Card key={cp.id} width="100%">
                <div className="flex flex-col gap-4 p-5">
                  {/* Cabeçalho do Checkpoint */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b pb-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-sm">
                        #{cp.ordem}
                      </span>
                      <Heading level={4}>{cp.titulo}</Heading>
                      <Badge variant="purple" label={tipoRotulo} />
                      {cp.obrigatorio ? (
                        <Badge
                          variant="neutral"
                          label={TEXTOS_JORNADA.plano.obrigatorio}
                        />
                      ) : (
                        <Badge
                          variant="neutral"
                          label={TEXTOS_JORNADA.plano.opcional}
                        />
                      )}
                    </div>
                    <Badge
                      variant={
                        cp.status === 'concluido'
                          ? 'green'
                          : cp.status === 'em_andamento'
                          ? 'blue'
                          : 'neutral'
                      }
                      label={statusRotulo}
                    />
                  </div>

                  {/* Descrição e Critério de Conclusão */}
                  <div className="flex flex-col gap-2">
                    <Text type="body">{cp.descricao}</Text>

                    {cp.criterio_conclusao && (
                      <div className="p-3 border rounded">
                        <span className="text-xs font-semibold uppercase tracking-wider block mb-1">
                          {TEXTOS_JORNADA.plano.criterioConclusao}
                        </span>
                        <Text type="supporting">{cp.criterio_conclusao}</Text>
                      </div>
                    )}
                  </div>

                  {/* Estado e Motivo de Origem */}
                  {(estadoTraduzido || motivoTraduzido) && (
                    <div className="flex items-center gap-2 flex-wrap text-xs">
                      {estadoTraduzido && (
                        <span>
                          <span className="font-medium">Origem:</span>{' '}
                          {estadoTraduzido}
                        </span>
                      )}
                      {motivoTraduzido && (
                        <span>({motivoTraduzido})</span>
                      )}
                    </div>
                  )}

                  {/* Ações do Checkpoint */}
                  <div className="flex items-center justify-between gap-3 pt-3 border-t flex-wrap">
                    <div className="flex items-center gap-2">
                      {cp.tipo === 'exercicio' && ultimaTentativa && (
                        <span className="text-xs">
                          {TEXTOS_JORNADA.plano.resultadoExercicio.titulo}:{' '}
                          <span className="font-semibold">
                            {ultimaTentativa}
                          </span>
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Checkpoint tipo exercicio: NUNCA tem ação manual; tem "Fazer o exercício" */}
                      {cp.tipo === 'exercicio' ? (
                        onFazerExercicio && (
                          <Button
                            type="button"
                            variant="primary"
                            label={TEXTOS_JORNADA.plano.acoes.fazerExercicio}
                            onClick={onFazerExercicio}
                          />
                        )
                      ) : (
                        <>
                          {cp.tipo === 'laboratorio' && onIrParaLaboratorio && (
                            <Button
                              type="button"
                              variant="secondary"
                              label={TEXTOS_JORNADA.plano.acoes.irParaLaboratorio}
                              onClick={onIrParaLaboratorio}
                            />
                          )}

                          {cp.status === 'pendente' && (
                            <Button
                              type="button"
                              variant="secondary"
                              label={TEXTOS_JORNADA.plano.acoes.comecar}
                              aria-label={TEXTOS_JORNADA.plano.acoes.comecarAria(
                                cp.titulo
                              )}
                              onClick={() =>
                                handleAtualizarStatus(cp, 'em_andamento')
                              }
                              isDisabled={isAtualizando}
                              isLoading={isAtualizando}
                            />
                          )}

                          {cp.status !== 'concluido' && (
                            <Button
                              type="button"
                              variant="primary"
                              label={TEXTOS_JORNADA.plano.acoes.concluir}
                              aria-label={TEXTOS_JORNADA.plano.acoes.concluirAria(
                                cp.titulo
                              )}
                              onClick={() =>
                                handleAtualizarStatus(cp, 'concluido')
                              }
                              isDisabled={isAtualizando}
                              isLoading={isAtualizando}
                            />
                          )}
                        </>
                      )}
                    </div>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Competências já demonstradas */}
      {plano.ja_demonstrados && plano.ja_demonstrados.length > 0 && (
        <section className="flex flex-col gap-2">
          <Heading level={3}>{TEXTOS_JORNADA.plano.secaoJaDemonstrados}</Heading>
          <Card width="100%">
            <ul className="flex flex-col gap-2 p-4">
              {plano.ja_demonstrados.map((item, idx) => (
                <li key={`ja-demo-${idx}`} className="flex items-center gap-2">
                  <Badge variant="green" label="Demonstrada" />
                  <Text type="body">{item}</Text>
                </li>
              ))}
            </ul>
          </Card>
        </section>
      )}

      {/* Observações do plano */}
      {plano.observacoes && plano.observacoes.length > 0 && (
        <section className="flex flex-col gap-2">
          <Heading level={3}>{TEXTOS_JORNADA.plano.secaoObservacoes}</Heading>
          <Card width="100%">
            <ul className="flex flex-col gap-2 p-4">
              {plano.observacoes.map((obs, idx) => (
                <li key={`obs-${idx}`} className="p-2 border rounded">
                  <Text type="supporting">{obs}</Text>
                </li>
              ))}
            </ul>
          </Card>
        </section>
      )}
    </div>
  );
}
