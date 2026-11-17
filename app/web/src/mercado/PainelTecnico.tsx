import {useCallback, useEffect, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Card} from '@astryxdesign/core/Card';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {Heading} from '@astryxdesign/core/Heading';
import {MetadataList, MetadataListItem} from '@astryxdesign/core/MetadataList';
import {Selector} from '@astryxdesign/core/Selector';
import {Spinner} from '@astryxdesign/core/Spinner';
import {
  Table,
  TableHeader,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
} from '@astryxdesign/core/Table';
import {Text} from '@astryxdesign/core/Text';

import {
  buscarModelos,
  RespostaModelos,
} from '../api/mercado';
import {
  DESTINOS_MVP,
  UFS_BRASIL,
  DESTINO_PADRAO,
  UF_PADRAO,
} from '../dominio/listas';
import { mensagemDeErro } from '../api/cliente';
import {
  formatarIdArtefato,
  formatarMediaDesvio,
  formatarNomeModelo,
  formatarNumero,
  formatarPercentual,
  formatarPeriodo,
  formatarStatusPromocao,
} from './formatacao';

export interface PainelTecnicoProps {
  destino?: string;
  onDestinoChange?: (destino: string) => void;
  uf?: string;
  onUfChange?: (uf: string) => void;
}

function formatarTipoModelo(tipo: string): string {
  if (tipo.toLowerCase() === 'rna') {
    return 'RNA';
  }
  if (tipo.toLowerCase() === 'baseline') {
    return 'Baseline';
  }
  if (tipo.toLowerCase() === 'classico') {
    return 'Clássico';
  }
  return tipo;
}

export function PainelTecnico({
  destino: destinoProp,
  onDestinoChange,
  uf: ufProp,
  onUfChange,
}: PainelTecnicoProps) {
  const destinoAtivo = destinoProp ?? DESTINO_PADRAO;
  const ufAtiva = ufProp ?? UF_PADRAO;

  const handleDestinoChange = useCallback(
    (novoDestino: string) => {
      onDestinoChange?.(novoDestino);
    },
    [onDestinoChange]
  );

  const handleUfChange = useCallback(
    (novaUf: string) => {
      onUfChange?.(novaUf);
    },
    [onUfChange]
  );

  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [dados, setDados] = useState<RespostaModelos | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);

    buscarModelos(destinoAtivo, ufAtiva)
      .then((resp) => {
        if (!cancelado) {
          setDados(resp);
          setCarregando(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          setErro(
            mensagemDeErro(
              err,
              'Erro desconhecido ao carregar modelos preditivos'
            )
          );
          setCarregando(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, [destinoAtivo, ufAtiva]);

  const opcoesDestino = DESTINOS_MVP.map((d) => ({
    value: d.value,
    label: d.label,
  }));

  const opcoesUf = UFS_BRASIL.map((u) => ({
    value: u,
    label: u,
  }));

  return (
    <section id="painel-tecnico" className="flex flex-col gap-6 w-full max-w-full min-w-0">
      <div className="flex flex-col gap-1">
        <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl sm:text-3xl tracking-tight text-[#000091]">
          Painel técnico de modelos preditivos (R06)
        </Heading>
        <Text type="supporting" className="text-sm text-[#616191]">
          Comparação sistemática de modelos preditivos validados no Novo Caged. Nenhum modelo é promovido automaticamente.
        </Text>
      </div>

      {/* Barra de Seletores lado a lado */}
      <div className="flex flex-col sm:flex-row gap-4 p-4 rounded bg-[#FFFFFF] border border-[#616191]/20 shadow-[inset_0_0_0_1px_rgba(0,0,242,0.1)]">
        <div className="flex-1 min-w-0">
          <Selector
            label="Destino profissional"
            options={opcoesDestino}
            value={destinoAtivo}
            onChange={(val) => {
              if (val) handleDestinoChange(val);
            }}
            data-testid="seletor-destino-tecnico"
          />
        </div>
        <div className="flex-1 sm:max-w-xs min-w-0">
          <Selector
            label="Unidade Federativa (UF)"
            options={opcoesUf}
            value={ufAtiva}
            onChange={(val) => {
              if (val) handleUfChange(val);
            }}
            data-testid="seletor-uf-tecnico"
          />
        </div>
      </div>

      {/* Estado de carregamento */}
      {carregando && (
        <div className="flex justify-center p-12">
          <Spinner
            size="lg"
            label="Carregando modelos do painel técnico..."
            aria-label="Carregando modelos do painel técnico"
          />
        </div>
      )}

      {/* Estado de erro */}
      {!carregando && erro && (
        <Banner
          status="error"
          title="Erro ao obter modelos preditivos"
          description={erro}
        />
      )}

      {/* Conteúdo do Painel */}
      {!carregando && dados && (
        <div className="flex flex-col gap-6">
          {/* Critério de Promoção e Status */}
          <Card padding={4}>
            <div className="flex flex-col gap-2">
              <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                Critério de promoção
              </Heading>
              <MetadataList orientation="vertical" columns="multi">
                <MetadataListItem label="Critério">
                  {dados.criterio_promocao.criterio}
                </MetadataListItem>
                <MetadataListItem label="Status de promoção">
                  {formatarStatusPromocao(dados.criterio_promocao.status)}
                </MetadataListItem>
                <MetadataListItem label="Modelo de referência exibido">
                  {formatarNomeModelo(dados.criterio_promocao.modelo_exibido)}
                </MetadataListItem>
              </MetadataList>
            </div>
          </Card>

          {/* Avisos Técnicos da API */}
          {dados.avisos && dados.avisos.length > 0 && (
            <Banner
              status="info"
              title="Avisos de integridade e metodologia"
              collapsible={false}
            >
              <ul className="list-disc pl-5 space-y-1 text-xs sm:text-sm text-[#000091]/90">
                {dados.avisos.map((aviso, idx) => (
                  <li key={`aviso-tecnico-${idx}`}>{aviso}</li>
                ))}
              </ul>
            </Banner>
          )}

          {/* Tabela Comparativa dos 6 Modelos */}
          <Card padding={4}>
            <div className="flex flex-col gap-4">
              <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                Comparativo de modelos preditivos
              </Heading>
              <div
                className="w-full shrink-0 overflow-x-auto overflow-y-hidden pb-4"
                tabIndex={0}
                role="region"
                aria-label="Tabela comparativa dos 6 modelos preditivos"
              >
                <Table aria-label="Tabela comparativa dos 6 modelos preditivos">
                  <caption className="text-left text-sm font-semibold py-2 text-[#000091]">
                    Tabela comparativa dos 6 modelos preditivos na validação global e série selecionada
                  </caption>
                  <TableHeader>
                    <TableRow isHeaderRow>
                      <TableHeaderCell>Modelo</TableHeaderCell>
                      <TableHeaderCell>Tipo</TableHeaderCell>
                      <TableHeaderCell>Promovido</TableHeaderCell>
                      <TableHeaderCell>MAE (validação)</TableHeaderCell>
                      <TableHeaderCell>RMSE (validação)</TableHeaderCell>
                      <TableHeaderCell>WAPE (%)</TableHeaderCell>
                      <TableHeaderCell>MASE (validação)</TableHeaderCell>
                      <TableHeaderCell>MAE da série selecionada</TableHeaderCell>
                      <TableHeaderCell>CV treino (MAE médio ± desvio)</TableHeaderCell>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dados.modelos.map((m) => (
                      <TableRow key={m.id}>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-[#000091]">
                              {formatarNomeModelo(m.id)}
                            </span>
                            {m.exibido_ao_usuario && (
                              <Badge label="Exibido ao usuário" variant="success" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono'] text-xs">
                            {formatarTipoModelo(m.tipo)}
                          </span>
                        </TableCell>
                        <TableCell>{m.promovido ? 'Sim' : 'Não'}</TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono']" style={{fontVariantNumeric: 'tabular-nums'}}>
                            {formatarNumero(m.metricas_validacao_global.mae, 2)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono']" style={{fontVariantNumeric: 'tabular-nums'}}>
                            {formatarNumero(m.metricas_validacao_global.rmse, 2)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono']" style={{fontVariantNumeric: 'tabular-nums'}}>
                            {formatarPercentual(m.metricas_validacao_global.wape, 1)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono']" style={{fontVariantNumeric: 'tabular-nums'}}>
                            {formatarNumero(m.metricas_validacao_global.mase, 2)}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono']" style={{fontVariantNumeric: 'tabular-nums'}}>
                            {m.metricas_serie?.mae !== undefined && m.metricas_serie?.mae !== null
                              ? formatarNumero(m.metricas_serie.mae, 2)
                              : '—'}
                          </span>
                        </TableCell>
                        <TableCell>
                          <span className="font-['IBM_Plex_Mono'] text-xs" style={{fontVariantNumeric: 'tabular-nums'}}>
                            {formatarMediaDesvio(
                              m.metricas_cv_treino.mae_medio,
                              m.metricas_cv_treino.mae_desvio
                            )}
                          </span>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </div>
          </Card>

          {/* Model Cards dos 6 Modelos */}
          <div className="flex flex-col gap-4">
            <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
              Model cards detalhados
            </Heading>
            {dados.modelos.map((m) => (
              <Card key={`card-${m.id}`} padding={4}>
                <Collapsible
                  trigger={`Model Card: ${formatarNomeModelo(m.id)} (${formatarTipoModelo(m.tipo)})`}
                  defaultIsOpen={m.id === 'mlp' || m.exibido_ao_usuario}
                >
                  <div className="mt-3">
                    <MetadataList orientation="vertical" columns="multi">
                      <MetadataListItem label="ID do artefato">
                        <span className="font-['IBM_Plex_Mono'] text-xs">
                          {formatarIdArtefato(m.model_card._id)}
                        </span>
                      </MetadataListItem>
                      <MetadataListItem label="Versão do artefato">
                        <span className="font-['IBM_Plex_Mono'] text-xs">
                          {m.model_card.versao_artefato}
                        </span>
                      </MetadataListItem>
                      <MetadataListItem label="Tipo">
                        <span className="font-['IBM_Plex_Mono'] text-xs">
                          {formatarTipoModelo(m.model_card.tipo)}
                        </span>
                      </MetadataListItem>
                      <MetadataListItem label="Data de treino (UTC)">
                        <span className="font-['IBM_Plex_Mono'] text-xs">
                          {m.model_card.data_treino_utc}
                        </span>
                      </MetadataListItem>
                      <MetadataListItem label="Período de treino">
                        {formatarPeriodo(
                          m.model_card.periodo_treino[0],
                          m.model_card.periodo_treino[1]
                        )}
                      </MetadataListItem>
                      <MetadataListItem label="Período de validação">
                        {formatarPeriodo(
                          m.model_card.periodo_validacao[0],
                          m.model_card.periodo_validacao[1]
                        )}
                      </MetadataListItem>
                      <MetadataListItem label="Seed">
                        <span className="font-['IBM_Plex_Mono'] text-xs">
                          {m.model_card.seed}
                        </span>
                      </MetadataListItem>
                      <MetadataListItem label="População">
                        {m.model_card.populacao}
                      </MetadataListItem>
                      <MetadataListItem label="Estratégia de seleção">
                        {m.model_card.selecao}
                      </MetadataListItem>
                      <MetadataListItem label="Status de promoção">
                        {formatarStatusPromocao(m.model_card.status_promocao)}
                      </MetadataListItem>
                      <MetadataListItem label="Limites conhecidos">
                        {m.model_card.limites && m.model_card.limites.length > 0
                          ? m.model_card.limites.join('; ')
                          : 'Nenhum limite reportado'}
                      </MetadataListItem>
                      <MetadataListItem label="Hiperparâmetros">
                        <pre className="max-h-48 overflow-auto rounded border border-[#616191]/20 p-2 text-xs font-mono whitespace-pre-wrap break-all bg-[#F2F2F2] text-[#000091]">
                          {JSON.stringify(m.model_card.hiperparametros, null, 2)}
                        </pre>
                      </MetadataListItem>
                    </MetadataList>
                  </div>
                </Collapsible>
              </Card>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
