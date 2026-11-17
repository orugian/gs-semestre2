import {useEffect, useState} from 'react';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Dialog} from '@astryxdesign/core/Dialog';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {ErroApi} from '../api/cliente';
import {
  criarComparacao,
  DestinoResumo,
  listarDestinos,
  RespostaComparacao,
} from '../api/comparacao';
import {obterIntencao} from '../api/intencao';
import {UFS_BRASIL} from '../api/mercado';
import {criarCaminho, RespostaCaminho} from '../api/plano';
import {CartaoDestino} from './CartaoDestino';
import {TEXTOS_JORNADA} from './textos';

export interface TelaComparacaoProps {
  onNovaComparacao?: () => void;
  planoAtivo?: RespostaCaminho | null;
  onDestinoEscolhido?: (caminho: RespostaCaminho) => void;
  onIrParaPlano?: () => void;
}

export function TelaComparacao({
  onNovaComparacao,
  planoAtivo,
  onDestinoEscolhido,
  onIrParaPlano,
}: TelaComparacaoProps) {
  const [destinosDisponiveis, setDestinosDisponiveis] = useState<DestinoResumo[]>([]);
  const [destinosSelecionados, setDestinosSelecionados] = useState<string[]>([]);
  const [uf, setUf] = useState<string>('');

  const [carregandoInicial, setCarregandoInicial] = useState(true);
  const [comparando, setComparando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [avisoSelecao, setAvisoSelecao] = useState<string | null>(null);

  const [resultado, setResultado] = useState<RespostaComparacao | null>(null);
  const [destinoParaConfirmar, setDestinoParaConfirmar] = useState<string | null>(null);
  const [escolhendoDestinoId, setEscolhendoDestinoId] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregandoInicial(true);
    setErro(null);

    Promise.all([
      listarDestinos().catch((err) => {
        throw err;
      }),
      obterIntencao().catch(() => null),
    ])
      .then(([respDestinos, respIntencao]) => {
        if (!cancelado) {
          setDestinosDisponiveis(respDestinos.itens || []);
          if (respIntencao?.uf) {
            setUf(respIntencao.uf);
          }
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          if (err instanceof ErroApi) {
            setErro(err.detalhes || err.erro);
          } else if (err instanceof Error) {
            setErro(err.message);
          } else {
            setErro('Não foi possível carregar os destinos.');
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

  const handleToggleDestino = (destinoId: string) => {
    setAvisoSelecao(null);
    if (destinosSelecionados.includes(destinoId)) {
      setDestinosSelecionados((atuais) => atuais.filter((id) => id !== destinoId));
    } else {
      if (destinosSelecionados.length >= 3) {
        setAvisoSelecao(TEXTOS_JORNADA.comparacao.selecao.limiteMaximo);
        return;
      }
      // Preserva a ordem de seleção exata escolhida pela pessoa
      setDestinosSelecionados((atuais) => [...atuais, destinoId]);
    }
  };

  const handleComparar = async () => {
    if (destinosSelecionados.length === 0) {
      setAvisoSelecao(TEXTOS_JORNADA.comparacao.selecao.nenhumSelecionado);
      return;
    }

    setComparando(true);
    setErro(null);
    setAvisoSelecao(null);
    try {
      const resp = await criarComparacao({
        destinos: destinosSelecionados,
        uf: uf.trim() || null,
      });
      setResultado(resp);
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        setErro(err.detalhes || err.erro || 'Erro ao comparar destinos.');
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro inesperado ao comparar destinos.');
      }
    } finally {
      setComparando(false);
    }
  };

  const handleSolicitarEscolha = (destinoId: string) => {
    if (planoAtivo) {
      setDestinoParaConfirmar(destinoId);
    } else {
      executarEscolhaDestino(destinoId);
    }
  };

  const executarEscolhaDestino = async (destinoId: string) => {
    setEscolhendoDestinoId(destinoId);
    setErro(null);

    try {
      const resp = await criarCaminho({
        destino_id: destinoId,
        comparacao_id: resultado?.comparacao_id || null,
      });
      onDestinoEscolhido?.(resp);
      onIrParaPlano?.();
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        setErro(err.detalhes || err.erro);
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Erro ao escolher destino.');
      }
    } finally {
      setEscolhendoDestinoId(null);
      setDestinoParaConfirmar(null);
    }
  };

  const handleLimparComparacao = () => {
    setResultado(null);
    setAvisoSelecao(null);
    setErro(null);
    onNovaComparacao?.();
  };

  if (carregandoInicial) {
    return (
      <div className="flex items-center justify-center p-12" aria-live="polite">
        <Spinner label="Carregando destinos disponíveis..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex flex-col gap-1">
          <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl sm:text-3xl tracking-tight text-[#000091]">
            {TEXTOS_JORNADA.comparacao.titulo}
          </Heading>
          <Text type="supporting" className="text-sm text-[#616191]">
            {TEXTOS_JORNADA.comparacao.descricao}
          </Text>
        </div>

        {resultado && (
          <div className="flex items-center gap-2">
            <Button
              type="button"
              variant="secondary"
              label={TEXTOS_JORNADA.comparacao.novaComparacao}
              onClick={handleLimparComparacao}
            />
          </div>
        )}
      </header>

      {erro && (
        <div role="alert" aria-live="polite">
          <Banner status="error" title="Atenção" description={erro} />
        </div>
      )}

      {avisoSelecao && (
        <div role="alert" aria-live="polite">
          <Banner status="warning" title="Seleção de destinos" description={avisoSelecao} />
        </div>
      )}

      {!resultado ? (
        /* Etapa 1: Seleção de Destinos e UF */
        <Card width="100%">
          <div className="flex flex-col gap-6 p-5">
            <header className="flex flex-col gap-1">
              <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                {TEXTOS_JORNADA.comparacao.selecao.titulo}
              </Heading>
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.comparacao.selecao.descricao}
              </Text>
            </header>

            {/* Lista de Destinos para Escolha */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {destinosDisponiveis.map((dest) => {
                const marcado = destinosSelecionados.includes(dest.destino_id);
                return (
                  <div
                    key={dest.destino_id}
                    className="flex items-start gap-3 p-3 border border-[#616191]/20 rounded select-none bg-[#FFFFFF]"
                  >
                    <input
                      id={`cb-${dest.destino_id}`}
                      type="checkbox"
                      checked={marcado}
                      onChange={() => handleToggleDestino(dest.destino_id)}
                      disabled={comparando}
                      className="mt-1 h-4 w-4 rounded border cursor-pointer"
                    />
                    <label
                      htmlFor={`cb-${dest.destino_id}`}
                      className="flex flex-col gap-1 flex-1 cursor-pointer"
                    >
                      <span className="font-semibold text-sm text-[#000091]">{dest.nome}</span>
                      {dest.descricao && (
                        <Text type="supporting" className="text-xs text-[#616191]">{dest.descricao}</Text>
                      )}
                    </label>
                  </div>
                );
              })}
            </div>

            {/* Seletor de UF */}
            <div className="flex flex-col gap-1 max-w-xs">
              <label htmlFor="seletor-uf-comparacao" className="text-sm font-medium text-[#000091]">
                {TEXTOS_JORNADA.comparacao.selecao.ufRotulo}
              </label>
              <select
                id="seletor-uf-comparacao"
                value={uf}
                onChange={(e) => setUf(e.target.value)}
                disabled={comparando}
                className="border border-[#616191]/30 rounded p-2 text-sm bg-[#FFFFFF] outline-none w-full"
              >
                <option value="">Brasil (sem filtro estadual)</option>
                {UFS_BRASIL.map((sigla) => (
                  <option key={sigla} value={sigla}>
                    {sigla}
                  </option>
                ))}
              </select>
            </div>

            {/* Botão Comparar */}
            <div className="flex justify-end pt-3 border-t border-[#616191]/20">
              <Button
                type="button"
                variant="primary"
                label={
                  comparando
                    ? TEXTOS_JORNADA.comparacao.selecao.comparando
                    : TEXTOS_JORNADA.comparacao.selecao.comparar
                }
                onClick={handleComparar}
                isDisabled={destinosSelecionados.length === 0 || comparando}
                isLoading={comparando}
              />
            </div>
          </div>
        </Card>
      ) : (
        /* Etapa 2: Resultado da Comparação */
        <div className="flex flex-col gap-6">
          {/* Aviso Institucional em Destaque */}
          <div aria-live="polite">
            <Banner
              status="info"
              title="Aviso sobre a comparação"
              description={resultado.aviso || TEXTOS_JORNADA.comparacao.avisoSemNota}
            />
          </div>

          {/* Legenda dos 4 Estados de Evidência */}
          <Card width="100%">
            <div className="flex flex-col gap-3 p-4">
              <Heading level={4} className="!font-['Barlow_Condensed'] font-semibold text-base text-[#000091]">
                {TEXTOS_JORNADA.comparacao.legenda.titulo}
              </Heading>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-[#000091]">
                <p>{TEXTOS_JORNADA.comparacao.legenda.demonstrada}</p>
                <p>{TEXTOS_JORNADA.comparacao.legenda.declarada}</p>
                <p>{TEXTOS_JORNADA.comparacao.legenda.desconhecida}</p>
                <p>{TEXTOS_JORNADA.comparacao.legenda.lacuna}</p>
              </div>
            </div>
          </Card>

          {/* Cartões de Destino na Ordem Escolhida */}
          <div
            className={`grid gap-6 ${
              resultado.destinos.length === 1
                ? 'grid-cols-1 max-w-xl mx-auto w-full'
                : resultado.destinos.length === 2
                ? 'grid-cols-1 md:grid-cols-2'
                : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
            }`}
          >
            {resultado.destinos.map((dest) => (
              <CartaoDestino
                key={dest.destino_id}
                destino={dest}
                onEscolherDestino={handleSolicitarEscolha}
                isEscolhendo={escolhendoDestinoId === dest.destino_id}
              />
            ))}
          </div>
        </div>
      )}

      {/* Confirmação de substituição de plano existente */}
      <Dialog
        isOpen={destinoParaConfirmar !== null}
        aria-label={TEXTOS_JORNADA.comparacao.dialogSubstituir.titulo}
        onOpenChange={(aberto) => {
          if (!aberto) setDestinoParaConfirmar(null);
        }}
        width={480}
      >
        <div className="flex flex-col gap-4 p-5">
          <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
            {TEXTOS_JORNADA.comparacao.dialogSubstituir.titulo}
          </Heading>
          <Text type="body">
            {TEXTOS_JORNADA.comparacao.dialogSubstituir.descricao}
          </Text>
          <div className="flex justify-end gap-3 pt-3 border-t border-[#616191]/20">
            <Button
              type="button"
              variant="secondary"
              label={TEXTOS_JORNADA.comparacao.dialogSubstituir.cancelar}
              onClick={() => setDestinoParaConfirmar(null)}
              isDisabled={escolhendoDestinoId !== null}
            />
            <Button
              type="button"
              variant="primary"
              label={TEXTOS_JORNADA.comparacao.dialogSubstituir.confirmar}
              onClick={() => {
                if (destinoParaConfirmar) {
                  executarEscolhaDestino(destinoParaConfirmar);
                }
              }}
              isLoading={escolhendoDestinoId !== null}
              isDisabled={escolhendoDestinoId !== null}
            />
          </div>
        </div>
      </Dialog>
    </div>
  );
}
