import {useEffect, useRef, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {TextArea} from '@astryxdesign/core/TextArea';
import {ErroApi} from '../api/cliente';
import {
  criarSessaoLaboratorio,
  DetalheSessaoLaboratorio,
  enviarRelatoLaboratorio,
  obterSessaoAtual,
  obterSessaoLaboratorio,
  SessaoLaboratorio,
} from '../api/laboratorio';
import {formatarDataHora, TEXTOS_JORNADA} from './textos';

export interface TelaLaboratorioProps {
  onIrParaConsentimentos?: () => void;
  onVoltarParaPlano?: () => void;
}

export function TelaLaboratorio({
  onIrParaConsentimentos,
  onVoltarParaPlano,
}: TelaLaboratorioProps) {
  const [sessao, setSessao] = useState<DetalheSessaoLaboratorio | SessaoLaboratorio | null>(null);
  const [carregandoInicial, setCarregandoInicial] = useState(true);
  const [abrindoSessao, setAbrindoSessao] = useState(false);
  const [atualizandoLeituras, setAtualizandoLeituras] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [erro403, setErro403] = useState(false);
  const [codigoCopiado, setCodigoCopiado] = useState(false);

  // Relato de observação
  const [textoRelato, setTextoRelato] = useState('');
  const [enviandoRelato, setEnviandoRelato] = useState(false);
  const [relatoRegistrado, setRelatoRegistrado] = useState<{
    texto_redigido: string | null;
    status: string;
  } | null>(null);

  const sessaoIdRef = useRef<string | null>(null);
  sessaoIdRef.current = sessao?.id || null;

  // Carrega sessão atual ao entrar se houver
  useEffect(() => {
    let cancelado = false;
    setCarregandoInicial(true);
    setErro(null);
    setErro403(false);

    obterSessaoAtual()
      .then((detalhes) => {
        if (!cancelado) {
          setSessao(detalhes);
          if (detalhes.relato && detalhes.relato.texto_redigido) {
            setRelatoRegistrado(detalhes.relato);
          }
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          if (err instanceof ErroApi) {
            if (err.status === 403) {
              setErro403(true);
            } else if (err.status === 404) {
              // Sem sessão ativa no momento - normal
              setSessao(null);
            } else {
              setErro(err.detalhes || err.erro);
            }
          }
        }
      })
      .finally(() => {
        if (!cancelado) {
          setCarregandoInicial(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, []);

  // Atualização periódica das leituras a cada 10 s (limpa ao desmontar)
  useEffect(() => {
    if (!sessao?.id) return;

    const intervalId = setInterval(() => {
      const idAtual = sessaoIdRef.current;
      if (!idAtual) return;

      obterSessaoLaboratorio(idAtual)
        .then((detalhes) => {
          setSessao(detalhes);
          if (detalhes.relato && detalhes.relato.texto_redigido) {
            setRelatoRegistrado(detalhes.relato);
          }
        })
        .catch(() => {
          // Erro de polling transitório
        });
    }, 10000);

    return () => {
      clearInterval(intervalId);
    };
  }, [sessao?.id]);

  const handleAbrirSessao = async () => {
    setAbrindoSessao(true);
    setErro(null);

    try {
      const novaSessao = await criarSessaoLaboratorio();
      setSessao(novaSessao);
      // Busca detalhes da sessão criada
      try {
        const detalhes = await obterSessaoLaboratorio(novaSessao.id);
        setSessao(detalhes);
      } catch {
        // Usa objeto criado inicial
      }
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        if (err.status === 403) {
          setErro403(true);
        } else {
          setErro(err.detalhes || err.erro);
        }
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro ao abrir sessão de laboratório.');
      }
    } finally {
      setAbrindoSessao(false);
    }
  };

  const handleAtualizarManual = async () => {
    if (!sessao?.id) return;

    setAtualizandoLeituras(true);
    setErro(null);

    try {
      const detalhes = await obterSessaoLaboratorio(sessao.id);
      setSessao(detalhes);
      if (detalhes.relato && detalhes.relato.texto_redigido) {
        setRelatoRegistrado(detalhes.relato);
      }
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        setErro(err.detalhes || err.erro);
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro ao atualizar leituras.');
      }
    } finally {
      setAtualizandoLeituras(false);
    }
  };

  const handleCopiarCodigo = () => {
    if (!sessao?.codigo) return;
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard) {
        navigator.clipboard.writeText(sessao.codigo);
      }
      setCodigoCopiado(true);
      setTimeout(() => setCodigoCopiado(false), 3000);
    } catch {
      // Ignora erro de clipboard em ambiente restrito
    }
  };

  const handleEnviarRelato = async () => {
    if (!sessao?.id) return;
    const relatoTrim = textoRelato.trim();
    if (relatoTrim.length < 1 || relatoTrim.length > 280) return;

    setEnviandoRelato(true);
    setErro(null);

    try {
      const resp = await enviarRelatoLaboratorio(sessao.id, relatoTrim);
      setRelatoRegistrado(resp);
      setTextoRelato('');
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        if (err.status === 409) {
          setErro(
            'Sessão encerrada/expirada ou relato já enviado anteriormente.'
          );
        } else if (err.status === 403) {
          setErro403(true);
        } else {
          setErro(err.detalhes || err.erro);
        }
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro ao enviar relato.');
      }
    } finally {
      setEnviandoRelato(false);
    }
  };

  if (carregandoInicial) {
    return (
      <div className="flex items-center justify-center p-12" aria-live="polite">
        <Spinner label="Carregando laboratório..." />
      </div>
    );
  }

  if (erro403) {
    return (
      <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
        <Banner
          status="warning"
          title="Autorização necessária"
          description={TEXTOS_JORNADA.laboratorio.bloqueioConsentimento}
        />
        {onIrParaConsentimentos && (
          <div className="flex justify-start">
            <Button
              type="button"
              variant="primary"
              label={TEXTOS_JORNADA.laboratorio.irParaConsentimentos}
              onClick={onIrParaConsentimentos}
            />
          </div>
        )}
      </div>
    );
  }

  const leituras = (sessao as DetalheSessaoLaboratorio)?.leituras || [];
  const indicadores = (sessao as DetalheSessaoLaboratorio)?.indicadores || {};

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      {/* Cabeçalho */}
      <header className="flex flex-col gap-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <Heading level={2} type="display-1">{TEXTOS_JORNADA.laboratorio.titulo}</Heading>
          {onVoltarParaPlano && (
            <Button
              type="button"
              variant="secondary"
              label="Voltar ao plano"
              onClick={onVoltarParaPlano}
            />
          )}
        </div>
        <Text type="supporting">{TEXTOS_JORNADA.laboratorio.descricao}</Text>
      </header>

      {/* Destaque de opcionalidade */}
      <div aria-live="polite">
        <Banner
          status="info"
          title="Etapa opcional"
          description={TEXTOS_JORNADA.laboratorio.opcional}
        />
      </div>

      {erro && (
        <div role="alert" aria-live="polite">
          <Banner status="error" title="Atenção" description={erro} />
        </div>
      )}

      {!sessao ? (
        /* Estado sem sessão ativa */
        <Card width="100%">
          <div className="flex flex-col items-center justify-center text-center p-8 gap-4">
            <Heading level={3}>Nenhuma sessão de laboratório ativa</Heading>
            <Text type="supporting">
              Inicie uma sessão para receber o código de bancada e acompanhar a telemetria em tempo real.
            </Text>
            <Button
              type="button"
              variant="primary"
              label={
                abrindoSessao
                  ? TEXTOS_JORNADA.laboratorio.abrindo
                  : TEXTOS_JORNADA.laboratorio.abrirSessao
              }
              onClick={handleAbrirSessao}
              isDisabled={abrindoSessao}
              isLoading={abrindoSessao}
            />
          </div>
        </Card>
      ) : (
        /* Sessão ativa ou existente */
        <div className="flex flex-col gap-6">
          {/* Card do Código da Sessão e Instruções */}
          <Card width="100%">
            <div className="flex flex-col gap-4 p-5">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b pb-4">
                <div className="flex flex-col gap-1">
                  <span className="text-xs font-semibold uppercase tracking-wider">
                    {TEXTOS_JORNADA.laboratorio.codigoSessao}
                  </span>
                  <div className="flex items-center gap-3">
                    <span className="text-3xl font-mono font-bold tracking-widest text-[var(--ct-azul)]">
                      {sessao.codigo}
                    </span>
                    <Button
                      type="button"
                      variant="secondary"
                      label={
                        codigoCopiado
                          ? TEXTOS_JORNADA.laboratorio.codigoCopiado
                          : TEXTOS_JORNADA.laboratorio.copiarCodigo
                      }
                      onClick={handleCopiarCodigo}
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Badge
                    variant={sessao.status === 'ativa' ? 'green' : 'neutral'}
                    label={
                      TEXTOS_JORNADA.laboratorio.statusSessao[sessao.status] ||
                      sessao.status
                    }
                  />
                  <Button
                    type="button"
                    variant="primary"
                    label={
                      atualizandoLeituras
                        ? TEXTOS_JORNADA.laboratorio.atualizando
                        : TEXTOS_JORNADA.laboratorio.atualizarLeituras
                    }
                    onClick={handleAtualizarManual}
                    isDisabled={atualizandoLeituras}
                    isLoading={atualizandoLeituras}
                  />
                </div>
              </div>

              {sessao.instrucoes && (
                <div className="flex flex-col gap-1">
                  <span className="font-semibold text-sm">
                    {TEXTOS_JORNADA.laboratorio.instrucoesTitulo}:
                  </span>
                  <Text type="body">{sessao.instrucoes}</Text>
                </div>
              )}
            </div>
          </Card>

          {/* Indicadores de telemetria */}
          {Object.keys(indicadores).length > 0 && (
            <section className="flex flex-col gap-3">
              <Heading level={3}>
                {TEXTOS_JORNADA.laboratorio.indicadoresTitulo}
              </Heading>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(indicadores).map(([metrica, ind]) => (
                  <Card key={metrica} width="100%">
                    <div className="flex flex-col gap-3 p-4">
                      <div className="flex items-center justify-between border-b pb-2">
                        <Heading level={4}>{metrica}</Heading>
                        <Badge
                          variant={ind.total_alertas > 0 ? 'purple' : 'neutral'}
                          label={`${ind.total_alertas} ${ind.total_alertas === 1 ? 'alerta' : 'alertas'}`}
                        />
                      </div>
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
                        <div className="p-2 border rounded flex flex-col items-center">
                          <Text type="supporting">Total</Text>
                          <span className="font-bold text-sm">
                            {ind.contagem}
                          </span>
                        </div>
                        <div className="p-2 border rounded flex flex-col items-center">
                          <Text type="supporting">Média</Text>
                          <span className="font-bold text-sm">
                            {ind.media}
                          </span>
                        </div>
                        <div className="p-2 border rounded flex flex-col items-center">
                          <Text type="supporting">Mínimo</Text>
                          <span className="font-bold text-sm">
                            {ind.minimo}
                          </span>
                        </div>
                        <div className="p-2 border rounded flex flex-col items-center">
                          <Text type="supporting">Máximo</Text>
                          <span className="font-bold text-sm">
                            {ind.maximo}
                          </span>
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </section>
          )}

          {/* Tabela de Leituras */}
          <section className="flex flex-col gap-3">
            <Heading level={3}>
              {TEXTOS_JORNADA.laboratorio.leiturasTitulo}
            </Heading>

            {leituras.length === 0 ? (
              <Card width="100%">
                <div className="p-6 text-center">
                  <Text type="supporting">
                    Nenhuma leitura recebida ainda. Conecte sua bancada ou aguarde a próxima medição.
                  </Text>
                </div>
              </Card>
            ) : (
              <div className="overflow-x-auto border rounded">
                <table className="w-full text-left text-sm">
                  <thead className="border-b bg-transparent">
                    <tr>
                      <th className="p-3 font-semibold">
                        {TEXTOS_JORNADA.laboratorio.tabela.horario}
                      </th>
                      <th className="p-3 font-semibold">
                        {TEXTOS_JORNADA.laboratorio.tabela.metrica}
                      </th>
                      <th className="p-3 font-semibold">
                        {TEXTOS_JORNADA.laboratorio.tabela.valor}
                      </th>
                      <th className="p-3 font-semibold">
                        {TEXTOS_JORNADA.laboratorio.tabela.risco}
                      </th>
                      <th className="p-3 font-semibold">
                        {TEXTOS_JORNADA.laboratorio.tabela.estadoNuvem}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {leituras.map((leitura) => {
                      const riscoRotulo =
                        TEXTOS_JORNADA.laboratorio.riscos[leitura.risco] ||
                        leitura.risco;

                      return (
                        <tr
                          key={leitura.evento_id}
                          className="border-b last:border-b-0"
                        >
                          <td className="p-3">
                            {formatarDataHora(leitura.medido_em)}
                          </td>
                          <td className="p-3 font-medium">
                            {leitura.metrica}
                          </td>
                          <td className="p-3">
                            {leitura.valor} {leitura.unidade}
                          </td>
                          <td className="p-3">
                            {/* Rótulo textual explícito de risco além de qualquer cor */}
                            <Badge
                              variant={
                                leitura.risco === 'critico'
                                  ? 'purple'
                                  : leitura.risco === 'atencao'
                                  ? 'blue'
                                  : 'green'
                              }
                              label={riscoRotulo}
                            />
                          </td>
                          <td className="p-3">
                            <Text type="supporting">{({pendente_nuvem: 'aguardando envio', sincronizado: 'enviado à nuvem', erro_permanente: 'não enviado'} as Record<string, string>)[leitura.estado] ?? leitura.estado}</Text>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Formulário de Relato de Observação (≤ 280 caracteres) */}
          <section className="flex flex-col gap-4">
            <Heading level={3}>
              {TEXTOS_JORNADA.laboratorio.relatoTitulo}
            </Heading>

            <Card width="100%">
              <div className="flex flex-col gap-4 p-5">
                {relatoRegistrado && relatoRegistrado.texto_redigido && (
                  <div className="p-4 border rounded flex flex-col gap-2">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-sm">
                        {TEXTOS_JORNADA.laboratorio.textoRedigidoTitulo}
                      </span>
                      <Badge
                        variant="blue"
                        label={
                          TEXTOS_JORNADA.laboratorio.statusRelato[
                            relatoRegistrado.status as 'pendente' | 'enviado'
                          ] || relatoRegistrado.status
                        }
                      />
                    </div>
                    <Text type="body">
                      {relatoRegistrado.texto_redigido}
                    </Text>
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  <TextArea
                    label={TEXTOS_JORNADA.laboratorio.rotuloRelato}
                    value={textoRelato}
                    onChange={(val) => setTextoRelato(val)}
                    placeholder={
                      TEXTOS_JORNADA.laboratorio.placeholderRelato
                    }
                    maxLength={280}
                    rows={3}
                  />

                  <div className="flex justify-between items-center text-xs">
                    <Text type="supporting">
                      {TEXTOS_JORNADA.laboratorio.contadorRelato(
                        textoRelato.length
                      )}
                    </Text>
                  </div>
                </div>

                <div className="flex justify-end pt-2">
                  <Button
                    type="button"
                    variant="primary"
                    label={
                      enviandoRelato
                        ? TEXTOS_JORNADA.laboratorio.enviandoRelato
                        : TEXTOS_JORNADA.laboratorio.enviarRelato
                    }
                    onClick={handleEnviarRelato}
                    isDisabled={
                      textoRelato.trim().length === 0 ||
                      textoRelato.length > 280 ||
                      enviandoRelato ||
                      sessao.status !== 'ativa'
                    }
                    isLoading={enviandoRelato}
                  />
                </div>
              </div>
            </Card>
          </section>
        </div>
      )}
    </div>
  );
}
