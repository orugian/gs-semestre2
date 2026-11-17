import {useEffect, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Dialog} from '@astryxdesign/core/Dialog';
import {Heading} from '@astryxdesign/core/Heading';
import {RadioList, RadioListItem} from '@astryxdesign/core/RadioList';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {TextArea} from '@astryxdesign/core/TextArea';
import {
  enviarTentativa,
  ExercicioDiagnostico,
  HistoricoTentativas,
  listarTentativas,
  obterExercicio,
  registrarDiscordo,
  TentativaExercicio,
} from '../api/avaliacao';
import {ErroApi} from '../api/cliente';
import {formatarDataHora, TEXTOS_JORNADA} from './textos';

export interface TelaExercicioProps {
  destinoId: string;
  onIrParaConsentimentos?: () => void;
  onVoltarParaPlano?: () => void;
}

export function TelaExercicio({
  destinoId,
  onIrParaConsentimentos,
  onVoltarParaPlano,
}: TelaExercicioProps) {
  const [exercicio, setExercicio] = useState<ExercicioDiagnostico | null>(null);
  const [historico, setHistorico] = useState<HistoricoTentativas | null>(null);
  const [tentativaAtual, setTentativaAtual] = useState<TentativaExercicio | null>(null);

  const [respostasObjetivas, setRespostasObjetivas] = useState<Record<string, string>>({});
  const [respostaAberta, setRespostaAberta] = useState('');

  const [carregando, setCarregando] = useState(true);
  const [enviando, setEnviando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [erro403, setErro403] = useState(false);
  const [erro429, setErro429] = useState(false);

  // Estado do diálogo de contestação ("Discordo")
  const [dialogDiscordoAberto, setDialogDiscordoAberto] = useState(false);
  const [motivoDiscordo, setMotivoDiscordo] = useState('');
  const [enviandoDiscordo, setEnviandoDiscordo] = useState(false);
  const [erroDiscordo, setErroDiscordo] = useState<string | null>(null);
  const [mensagemDiscordo, setMensagemDiscordo] = useState<string | null>(null);

  const carregarDados = () => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    setErro403(false);
    setErro429(false);

    Promise.all([
      obterExercicio(destinoId),
      listarTentativas(destinoId).catch(() => null),
    ])
      .then(([dadosExercicio, dadosHistorico]) => {
        if (!cancelado) {
          setExercicio(dadosExercicio);
          if (dadosHistorico) {
            setHistorico(dadosHistorico);
          }
          if (dadosExercicio.tentativas_restantes_24h <= 0) {
            setErro429(true);
          }
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          if (err instanceof ErroApi) {
            if (err.status === 403) {
              setErro403(true);
            } else if (err.status === 429) {
              setErro429(true);
            } else {
              setErro(err.detalhes || err.erro);
            }
          } else if (err instanceof Error) {
            setErro(err.message);
          } else {
            setErro('Erro ao carregar o exercício.');
          }
        }
      })
      .finally(() => {
        if (!cancelado) {
          setCarregando(false);
        }
      });

    return () => {
      cancelado = true;
    };
  };

  useEffect(() => {
    const cancelar = carregarDados();
    return () => {
      cancelar?.();
    };
  }, [destinoId]);

  const handleRefazer = () => {
    setTentativaAtual(null);
    setRespostasObjetivas({});
    setRespostaAberta('');
    setMensagemDiscordo(null);
    setErroDiscordo(null);
    setErro(null);
  };

  const handleEnviar = async () => {
    if (!exercicio) return;

    setEnviando(true);
    setErro(null);

    try {
      const resp = await enviarTentativa({
        destino_id: destinoId,
        exercicio_id: exercicio.exercicio_id,
        respostas_objetivas: respostasObjetivas,
        resposta_aberta: respostaAberta.trim(),
      });

      setTentativaAtual(resp);

      // Atualiza histórico
      listarTentativas(destinoId)
        .then((hist) => setHistorico(hist))
        .catch(() => {});
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        if (err.status === 403) {
          setErro403(true);
        } else if (err.status === 429) {
          setErro429(true);
        } else {
          setErro(err.detalhes || err.erro);
        }
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro ao enviar a tentativa.');
      }
    } finally {
      setEnviando(false);
    }
  };

  const handleConfirmarDiscordo = async () => {
    if (!tentativaAtual) return;
    const motivoTrim = motivoDiscordo.trim();
    if (motivoTrim.length < 10) return;

    setEnviandoDiscordo(true);
    setErroDiscordo(null);

    try {
      const resp = await registrarDiscordo(
        tentativaAtual.tentativa_id,
        motivoTrim
      );
      setMensagemDiscordo(
        TEXTOS_JORNADA.exercicio.contestacao.registrada(
          formatarDataHora(resp.discordo_em)
        )
      );
      setDialogDiscordoAberto(false);
      setMotivoDiscordo('');
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        if (err.status === 409) {
          setErroDiscordo(TEXTOS_JORNADA.exercicio.contestacao.jaRegistrada);
        } else {
          setErroDiscordo(err.detalhes || err.erro);
        }
      } else if (err instanceof Error) {
        setErroDiscordo(err.message);
      } else {
        setErroDiscordo('Erro ao registrar contestação.');
      }
    } finally {
      setEnviandoDiscordo(false);
    }
  };

  if (carregando) {
    return (
      <div className="flex items-center justify-center p-12" aria-live="polite">
        <Spinner label={TEXTOS_JORNADA.exercicio.carregando} />
      </div>
    );
  }

  if (erro403) {
    return (
      <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
        <Banner
          status="warning"
          title="Autorização necessária"
          description={TEXTOS_JORNADA.exercicio.bloqueioConsentimentoLlm}
        />
        {onIrParaConsentimentos && (
          <div className="flex justify-start">
            <Button
              type="button"
              variant="primary"
              label={TEXTOS_JORNADA.exercicio.irParaConsentimentos}
              onClick={onIrParaConsentimentos}
            />
          </div>
        )}
      </div>
    );
  }

  if (!exercicio) {
    return (
      <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
        {erro && <Banner status="error" title="Atenção" description={erro} />}
      </div>
    );
  }

  // Verifica se tudo foi respondido
  const totalObjetivas = exercicio.questoes_objetivas.length;
  const totalRespondidas = Object.keys(respostasObjetivas).length;
  const respostaAbertaValida =
    respostaAberta.trim().length >= 20 && respostaAberta.trim().length <= 4000;
  const tentativasRestantes = tentativaAtual
    ? tentativaAtual.tentativas_restantes_24h
    : exercicio.tentativas_restantes_24h;
  const podeEnviar =
    totalRespondidas === totalObjetivas &&
    respostaAbertaValida &&
    tentativasRestantes > 0 &&
    !enviando;

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      {/* Cabeçalho */}
      <header className="flex flex-col gap-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <Heading level={2}>{TEXTOS_JORNADA.exercicio.titulo}</Heading>
          <div className="flex items-center gap-2">
            <Badge
              variant="neutral"
              label={TEXTOS_JORNADA.exercicio.tentativasRestantes(
                tentativasRestantes
              )}
            />
            {onVoltarParaPlano && (
              <Button
                type="button"
                variant="secondary"
                label="Voltar ao plano"
                onClick={onVoltarParaPlano}
              />
            )}
          </div>
        </div>
      </header>

      {/* Erro global */}
      {erro && (
        <div role="alert" aria-live="polite">
          <Banner status="error" title="Atenção" description={erro} />
        </div>
      )}

      {/* Limite de 429 atingido */}
      {(erro429 || tentativasRestantes <= 0) && (
        <div role="alert" aria-live="polite">
          <Banner
            status="warning"
            title="Limite de tentativas"
            description={TEXTOS_JORNADA.exercicio.limiteAtingido}
          />
        </div>
      )}

      {/* Cenário do Exercício */}
      <Card width="100%">
        <div className="flex flex-col gap-3 p-5">
          <Heading level={3}>{TEXTOS_JORNADA.exercicio.cenarioTitulo}</Heading>
          <Text type="body">{exercicio.cenario}</Text>
        </div>
      </Card>

      {/* Critérios da resposta aberta com âncoras (0, 1 e 2) - transparência antes do envio */}
      <Card width="100%">
        <div className="flex flex-col gap-4 p-5">
          <div className="flex flex-col gap-1">
            <Heading level={3}>
              {TEXTOS_JORNADA.exercicio.criteriosTitulo}
            </Heading>
            <Text type="supporting">
              {TEXTOS_JORNADA.exercicio.criteriosDescricao}
            </Text>
          </div>

          <div className="flex flex-col gap-4">
            {exercicio.questao_aberta.criterios.map((crit) => (
              <div
                key={crit.id}
                className="flex flex-col gap-2 p-3 border rounded"
              >
                <Heading level={4}>{crit.descricao}</Heading>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-2 text-xs pt-1">
                  <div className="p-2 border rounded flex flex-col gap-1">
                    <span className="font-semibold">Nível 0:</span>
                    <Text type="supporting">{crit.ancoras['0']}</Text>
                  </div>
                  <div className="p-2 border rounded flex flex-col gap-1">
                    <span className="font-semibold">Nível 1:</span>
                    <Text type="supporting">{crit.ancoras['1']}</Text>
                  </div>
                  <div className="p-2 border rounded flex flex-col gap-1">
                    <span className="font-semibold">Nível 2:</span>
                    <Text type="supporting">{crit.ancoras['2']}</Text>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>

      {!tentativaAtual ? (
        /* Formulário de Respostas (antes do envio) */
        <div className="flex flex-col gap-6">
          {/* Questões Objetivas */}
          <section className="flex flex-col gap-4">
            <Heading level={3}>
              {TEXTOS_JORNADA.exercicio.questoesObjetivasTitulo}
            </Heading>

            {exercicio.questoes_objetivas.map((q, idx) => (
              <Card key={q.id} width="100%">
                <div className="flex flex-col gap-4 p-5">
                  <span className="font-semibold text-sm">
                    Questão #{idx + 1}
                  </span>
                  <Text type="body">{q.enunciado}</Text>

                  <RadioList
                    label={`Opções para a questão ${idx + 1}`}
                    isLabelHidden
                    value={respostasObjetivas[q.id] || ''}
                    onChange={(val) =>
                      setRespostasObjetivas((prev) => ({
                        ...prev,
                        [q.id]: val,
                      }))
                    }
                  >
                    {Object.entries(q.alternativas).map(([letra, texto]) => (
                      <RadioListItem
                        key={letra}
                        value={letra}
                        label={`${letra}) ${texto}`}
                      />
                    ))}
                  </RadioList>
                </div>
              </Card>
            ))}
          </section>

          {/* Questão Aberta */}
          <section className="flex flex-col gap-4">
            <Heading level={3}>
              {TEXTOS_JORNADA.exercicio.questaoAbertaTitulo}
            </Heading>

            <Card width="100%">
              <div className="flex flex-col gap-4 p-5">
                <Text type="body">{exercicio.questao_aberta.enunciado}</Text>

                <TextArea
                  label={TEXTOS_JORNADA.exercicio.rotuloRespostaAberta}
                  value={respostaAberta}
                  onChange={(val) => setRespostaAberta(val)}
                  maxLength={4000}
                  rows={6}
                />

                <div className="flex justify-between items-center text-xs">
                  <Text type="supporting">
                    {TEXTOS_JORNADA.exercicio.contadorCaracteres(
                      respostaAberta.length
                    )}
                  </Text>
                </div>
              </div>
            </Card>
          </section>

          {/* Botão Enviar */}
          <div className="flex justify-end pt-2">
            <Button
              type="button"
              variant="primary"
              label={
                enviando
                  ? TEXTOS_JORNADA.exercicio.enviando
                  : TEXTOS_JORNADA.exercicio.enviar
              }
              onClick={handleEnviar}
              isDisabled={!podeEnviar}
              isLoading={enviando}
            />
          </div>
        </div>
      ) : (
        /* Resultado da Tentativa (após o envio) */
        <div className="flex flex-col gap-6">
          {/* Aviso institucional da tentativa */}
          {tentativaAtual.aviso && (
            <div aria-live="polite">
              <Banner
                status="info"
                title="Aviso da avaliação"
                description={tentativaAtual.aviso}
              />
            </div>
          )}

          {/* Contestação registrada ou erro */}
          {mensagemDiscordo && (
            <div aria-live="polite">
              <Banner
                status="success"
                title="Contestação"
                description={mensagemDiscordo}
              />
            </div>
          )}

          {/* Cabeçalho do Resultado */}
          <Card width="100%">
            <div className="flex flex-col gap-4 p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b pb-4">
                <div className="flex flex-col gap-1">
                  <Heading level={3}>
                    {TEXTOS_JORNADA.exercicio.resultadoTitulo}
                  </Heading>
                  <Text type="supporting">
                    {TEXTOS_JORNADA.exercicio.rastreabilidade.versao(
                      tentativaAtual.exercicio_versao
                    )}{' '}
                    •{' '}
                    {tentativaAtual.aberta.modelo
                      ? TEXTOS_JORNADA.exercicio.rastreabilidade.modelo(
                          tentativaAtual.aberta.modelo
                        )
                      : 'IA não disponível'}{' '}
                    •{' '}
                    {TEXTOS_JORNADA.exercicio.rastreabilidade.data(
                      formatarDataHora(tentativaAtual.criado_em)
                    )}
                  </Text>
                </div>

                <div className="flex items-center gap-3">
                  <Badge
                    variant={
                      tentativaAtual.resultado === 'demonstrada'
                        ? 'green'
                        : tentativaAtual.resultado === 'parcial'
                        ? 'blue'
                        : 'neutral'
                    }
                    label={
                      TEXTOS_JORNADA.exercicio.conceito[
                        tentativaAtual.resultado
                      ] || tentativaAtual.resultado
                    }
                  />

                  {/* Mostra nota do exercício APENAS se não for parcial */}
                  {tentativaAtual.resultado !== 'parcial' &&
                    tentativaAtual.nota_final !== null && (
                      <span className="text-xl font-bold">
                        {TEXTOS_JORNADA.exercicio.notaExercicio(
                          tentativaAtual.nota_final
                        )}
                      </span>
                    )}
                </div>
              </div>

              {/* Explicação de avaliação parcial */}
              {tentativaAtual.resultado === 'parcial' && (
                <div className="p-3 border rounded" role="alert">
                  <Text type="body">
                    {TEXTOS_JORNADA.exercicio.explicacaoParcial}
                  </Text>
                </div>
              )}

              {/* Botões de Ação: Refazer e Discordo */}
              <div className="flex items-center justify-between gap-3 pt-2 flex-wrap">
                <Button
                  type="button"
                  variant="secondary"
                  label={TEXTOS_JORNADA.exercicio.acoes.discordo}
                  onClick={() => setDialogDiscordoAberto(true)}
                />

                <Button
                  type="button"
                  variant="primary"
                  label={TEXTOS_JORNADA.exercicio.acoes.refazer}
                  onClick={handleRefazer}
                  isDisabled={tentativaAtual.tentativas_restantes_24h <= 0}
                />
              </div>
            </div>
          </Card>

          {/* Correção das Questões Objetivas (gabarito e justificativa SÓ agora) */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <Heading level={3}>
                {TEXTOS_JORNADA.exercicio.questoesObjetivasTitulo}
              </Heading>
              <Text type="supporting">
                {TEXTOS_JORNADA.exercicio.resultadoObjetiva(
                  tentativaAtual.objetiva.acertos,
                  tentativaAtual.objetiva.total
                )}
              </Text>
            </div>

            {tentativaAtual.objetiva.questoes.map((q, idx) => (
              <Card key={q.id} width="100%">
                <div className="flex flex-col gap-3 p-5">
                  <div className="flex items-center justify-between gap-2 border-b pb-2">
                    <span className="font-semibold text-sm">
                      Questão #{idx + 1}
                    </span>
                    <Badge
                      variant={q.correta ? 'green' : 'neutral'}
                      label={
                        q.correta
                          ? TEXTOS_JORNADA.exercicio.respostaCorreta
                          : TEXTOS_JORNADA.exercicio.respostaIncorreta
                      }
                    />
                  </div>

                  <div className="flex flex-col gap-1 text-sm">
                    <p>
                      <span className="font-medium">Sua resposta:</span>{' '}
                      {q.resposta}
                    </p>
                    <p>
                      <span className="font-medium">
                        {TEXTOS_JORNADA.exercicio.gabaritoRotulo}:
                      </span>{' '}
                      {q.gabarito}
                    </p>
                    <p>
                      <span className="font-medium">
                        {TEXTOS_JORNADA.exercicio.justificativaRotulo}:
                      </span>{' '}
                      {q.justificativa}
                    </p>
                  </div>
                </div>
              </Card>
            ))}
          </section>

          {/* Avaliação da Resposta Aberta por Critério */}
          {tentativaAtual.aberta.status === 'avaliada' &&
            tentativaAtual.aberta.criterios.length > 0 && (
              <section className="flex flex-col gap-4">
                <div className="flex items-center justify-between">
                  <Heading level={3}>
                    {TEXTOS_JORNADA.exercicio.questaoAbertaTitulo}
                  </Heading>
                  {tentativaAtual.aberta.nota !== null && (
                    <Text type="supporting">
                      {TEXTOS_JORNADA.exercicio.notaLlmRotulo(
                        tentativaAtual.aberta.nota
                      )}
                    </Text>
                  )}
                </div>

                {tentativaAtual.aberta.criterios.map((crit) => (
                  <Card key={crit.id} width="100%">
                    <div className="flex flex-col gap-3 p-5">
                      <div className="flex items-center justify-between gap-2 border-b pb-2">
                        <Heading level={4}>Critério {crit.id}</Heading>
                        <Badge
                          variant="blue"
                          label={`Nível ${crit.nivel}`}
                        />
                      </div>

                      <div className="flex flex-col gap-2 text-sm">
                        <p>
                          <span className="font-medium">
                            {TEXTOS_JORNADA.exercicio.justificativaRotulo}:
                          </span>{' '}
                          {crit.justificativa}
                        </p>

                        {crit.trecho_resposta && (
                          <div className="p-3 border rounded italic">
                            <span className="font-medium not-italic block mb-1">
                              {TEXTOS_JORNADA.exercicio.trechoCitacao}
                            </span>
                            "{crit.trecho_resposta}"
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                ))}
              </section>
            )}
        </div>
      )}

      {/* Histórico de Tentativas */}
      {historico && historico.itens.length > 0 && (
        <section className="flex flex-col gap-3 border-t pt-4">
          <Heading level={3}>{TEXTOS_JORNADA.exercicio.historico.titulo}</Heading>
          <div className="flex flex-col gap-2">
            {historico.itens.map((item) => {
              const isUltima = item.tentativa_id === historico.ultima;
              const isMelhor = item.tentativa_id === historico.melhor;

              return (
                <div
                  key={item.tentativa_id}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 p-3 border rounded text-sm"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <Badge
                      variant="neutral"
                      label={formatarDataHora(item.criado_em)}
                    />
                    <Badge
                      variant={
                        item.resultado === 'demonstrada'
                          ? 'green'
                          : item.resultado === 'parcial'
                          ? 'blue'
                          : 'neutral'
                      }
                      label={
                        TEXTOS_JORNADA.exercicio.conceito[item.resultado] ||
                        item.resultado
                      }
                    />
                    {item.nota_final !== null && (
                      <span className="font-semibold">
                        Nota: {item.nota_final}
                      </span>
                    )}
                    {isMelhor && (
                      <Badge
                        variant="purple"
                        label={TEXTOS_JORNADA.exercicio.historico.melhor}
                      />
                    )}
                    {isUltima && (
                      <Badge
                        variant="blue"
                        label={TEXTOS_JORNADA.exercicio.historico.ultima}
                      />
                    )}
                  </div>

                  {item.discordo_em && (
                    <Text type="supporting">
                      {TEXTOS_JORNADA.exercicio.contestacao.registrada(
                        formatarDataHora(item.discordo_em)
                      )}
                    </Text>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Diálogo de Contestação ("Discordo") */}
      <Dialog
        isOpen={dialogDiscordoAberto}
        aria-label={TEXTOS_JORNADA.exercicio.contestacao.titulo}
        onOpenChange={(aberto) => {
          if (!aberto) setDialogDiscordoAberto(false);
        }}
        width={500}
      >
        <div className="flex flex-col gap-4 p-5">
          <Heading level={3}>
            {TEXTOS_JORNADA.exercicio.contestacao.titulo}
          </Heading>
          <Text type="supporting">
            {TEXTOS_JORNADA.exercicio.contestacao.descricao}
          </Text>

          {erroDiscordo && (
            <div role="alert" aria-live="polite">
              <Banner status="error" title="Atenção" description={erroDiscordo} />
            </div>
          )}

          <TextArea
            label={TEXTOS_JORNADA.exercicio.contestacao.rotuloMotivo}
            value={motivoDiscordo}
            onChange={(val) => setMotivoDiscordo(val)}
            placeholder={
              TEXTOS_JORNADA.exercicio.contestacao.placeholderMotivo
            }
            maxLength={1000}
            rows={4}
          />

          <div className="flex justify-between items-center text-xs">
            <Text type="supporting">
              {TEXTOS_JORNADA.exercicio.contestacao.contador(
                motivoDiscordo.length
              )}
            </Text>
          </div>

          <div className="flex justify-end gap-3 pt-3 border-t">
            <Button
              type="button"
              variant="secondary"
              label={TEXTOS_JORNADA.exercicio.contestacao.cancelar}
              onClick={() => {
                setDialogDiscordoAberto(false);
                setMotivoDiscordo('');
                setErroDiscordo(null);
              }}
              isDisabled={enviandoDiscordo}
            />
            <Button
              type="button"
              variant="primary"
              label={TEXTOS_JORNADA.exercicio.contestacao.confirmar}
              onClick={handleConfirmarDiscordo}
              isDisabled={motivoDiscordo.trim().length < 10 || enviandoDiscordo}
              isLoading={enviandoDiscordo}
            />
          </div>
        </div>
      </Dialog>
    </div>
  );
}
