import {useCallback, useEffect, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {EmptyState} from '@astryxdesign/core/EmptyState';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {TextArea} from '@astryxdesign/core/TextArea';
import {ErroApi} from '../api/cliente';
import {
  atualizarCompetencia,
  Competencia,
  listarCompetencias,
  RespostaExtracao,
} from '../api/competencias';
import {TEXTOS_JORNADA} from './textos';

export interface TelaCompetenciasProps {
  extracaoInicial?: RespostaExtracao | null;
}

export function TelaCompetencias({extracaoInicial}: TelaCompetenciasProps) {
  const [competencias, setCompetencias] = useState<Competencia[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [processandoId, setProcessandoId] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  // Controle de edição inline de trecho para confirmação
  const [idEditandoTrecho, setIdEditandoTrecho] = useState<string | null>(null);
  const [trechoEditado, setTrechoEditado] = useState<string>('');

  const carregarCompetencias = useCallback(async () => {
    try {
      setCarregando(true);
      setErro(null);
      const resp = await listarCompetencias();
      setCompetencias(resp.itens || []);
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        setErro(err.detalhes || err.erro);
      } else if (err instanceof Error) {
        setErro(err.message);
      } else {
        setErro('Não foi possível carregar as competências.');
      }
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregarCompetencias();
  }, [carregarCompetencias]);

  const handleAcao = async (
    competencia: Competencia,
    acao: 'confirmar' | 'rejeitar' | 'nao_possuo',
    novoTrecho?: string | null
  ) => {
    setProcessandoId(competencia.id);
    setErro(null);

    try {
      const atualizado = await atualizarCompetencia(
        competencia.id,
        acao,
        novoTrecho !== undefined ? novoTrecho : undefined
      );

      setCompetencias((atuais) =>
        atuais.map((c) => (c.id === atualizado.id ? atualizado : c))
      );
      setIdEditandoTrecho(null);
      setTrechoEditado('');
    } catch (err: unknown) {
      if (err instanceof ErroApi) {
        setErro(err.detalhes || err.erro);
      } else if (err instanceof Error) {
        setErro(err.message);
      }
    } finally {
      setProcessandoId(null);
    }
  };

  const descartadasTotal = extracaoInicial?.descartadas
    ? (extracaoInicial.descartadas.fora_da_lista || 0) +
      (extracaoInicial.descartadas.sem_trecho || 0) +
      (extracaoInicial.descartadas.trecho_nao_encontrado || 0) +
      (extracaoInicial.descartadas.duplicadas || 0)
    : 0;

  const pendentes = competencias.filter((c) => c.revisao === 'pendente');
  const confirmadas = competencias.filter((c) => c.revisao === 'confirmada');
  const naoPossuo = competencias.filter((c) => c.revisao === 'nao_possuo');
  const rejeitadas = competencias.filter((c) => c.revisao === 'rejeitada');

  const renderizarGrupo = (
    titulo: string,
    itens: Competencia[],
    mostrarAcoes = false
  ) => {
    if (itens.length === 0) return null;

    return (
      <section className="flex flex-col gap-3">
        <Heading level={3}>{titulo}</Heading>
        <div className="flex flex-col gap-3">
          {itens.map((comp) => {
            const emProcesso = processandoId === comp.id;
            const editando = idEditandoTrecho === comp.id;

            return (
              <Card key={comp.id} width="100%">
                <div className="flex flex-col gap-3 p-4">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <Heading level={4}>{comp.titulo}</Heading>
                    <div className="flex items-center gap-2">
                      <Badge
                        variant={
                          comp.estado_evidencia === 'demonstrada'
                            ? 'success'
                            : 'neutral'
                        }
                        label={comp.estado_evidencia}
                      />
                      <Badge
                        variant={
                          comp.revisao === 'confirmada'
                            ? 'success'
                            : comp.revisao === 'pendente'
                            ? 'neutral'
                            : 'error'
                        }
                        label={{pendente: 'pendente', confirmada: 'confirmada', rejeitada: 'rejeitada', nao_possuo: 'não possuo'}[comp.revisao] ?? comp.revisao}
                      />
                    </div>
                  </div>

                  {comp.trecho_origem && (
                    <blockquote className="p-3 border-l-2 rounded-r">
                      <Text type="supporting">{comp.trecho_origem}</Text>
                    </blockquote>
                  )}

                  {mostrarAcoes && !editando && (
                    <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
                      <Button
                        label={TEXTOS_JORNADA.competencias.acoes.confirmar}
                        variant="primary"
                        onClick={() => handleAcao(comp, 'confirmar')}
                        isDisabled={emProcesso}
                        isLoading={emProcesso}
                      />

                      <Button
                        label={TEXTOS_JORNADA.competencias.acoes.editarTrecho}
                        variant="ghost"
                        onClick={() => {
                          setIdEditandoTrecho(comp.id);
                          setTrechoEditado(comp.trecho_origem || '');
                        }}
                        isDisabled={emProcesso}
                      />

                      <Button
                        label={TEXTOS_JORNADA.competencias.acoes.naoPossuo}
                        variant="secondary"
                        onClick={() => handleAcao(comp, 'nao_possuo')}
                        isDisabled={emProcesso}
                        isLoading={emProcesso}
                      />

                      <Button
                        label={TEXTOS_JORNADA.competencias.acoes.rejeitar}
                        variant="destructive"
                        onClick={() => handleAcao(comp, 'rejeitar')}
                        isDisabled={emProcesso}
                        isLoading={emProcesso}
                      />
                    </div>
                  )}

                  {mostrarAcoes && editando && (
                    <div className="flex flex-col gap-3 pt-2 border-t">
                      <TextArea
                        label="Editar trecho de origem"
                        value={trechoEditado}
                        onChange={(val) => setTrechoEditado(val)}
                        maxLength={500}
                        rows={3}
                        description="Você pode ajustar o trecho comprobatório do currículo (até 500 caracteres)."
                      />
                      <div className="flex items-center gap-2">
                        <Button
                          label={TEXTOS_JORNADA.competencias.acoes.salvar}
                          variant="primary"
                          onClick={() => {
                            const trechoModificado =
                              trechoEditado !== comp.trecho_origem
                                ? trechoEditado
                                : null;
                            handleAcao(comp, 'confirmar', trechoModificado);
                          }}
                          isDisabled={emProcesso}
                          isLoading={emProcesso}
                        />
                        <Button
                          label={TEXTOS_JORNADA.competencias.acoes.cancelar}
                          variant="ghost"
                          onClick={() => {
                            setIdEditandoTrecho(null);
                            setTrechoEditado('');
                          }}
                          isDisabled={emProcesso}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      </section>
    );
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <header className="flex flex-col gap-2">
        <Heading level={2}>{TEXTOS_JORNADA.competencias.titulo}</Heading>
      </header>

      {/* T07: Aviso honesto sobre competências declaradas vs demonstradas */}
      <Banner
        status="info"
        title="Critério de transparência"
        description={TEXTOS_JORNADA.competencias.avisoHonesto}
      />

      {descartadasTotal > 0 && (
        <Banner
          status="info"
          title="Sugestões filtradas"
          description={TEXTOS_JORNADA.competencias.descartadasNota(
            descartadasTotal
          )}
        />
      )}

      {erro && (
        <div role="alert" aria-live="polite">
          <Banner status="error" title="Atenção" description={erro} />
        </div>
      )}

      {carregando ? (
        <div className="flex items-center justify-center p-8" aria-live="polite">
          <Spinner label="Carregando competências..." />
        </div>
      ) : competencias.length === 0 ? (
        <EmptyState
          title={TEXTOS_JORNADA.competencias.vazioTitulo}
          description={TEXTOS_JORNADA.competencias.vazioDescricao}
          headingLevel={3}
        />
      ) : (
        <div className="flex flex-col gap-6">
          {renderizarGrupo(
            TEXTOS_JORNADA.competencias.grupos.pendentes,
            pendentes,
            true
          )}
          {renderizarGrupo(
            TEXTOS_JORNADA.competencias.grupos.confirmadas,
            confirmadas
          )}
          {renderizarGrupo(
            TEXTOS_JORNADA.competencias.grupos.naoPossuo,
            naoPossuo
          )}
          {renderizarGrupo(
            TEXTOS_JORNADA.competencias.grupos.rejeitadas,
            rejeitadas
          )}
        </div>
      )}
    </div>
  );
}
