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
  ApiError,
  buscarModelos,
  DESTINOS_MVP,
  RespostaModelos,
  UFS_BRASIL,
} from '../api/mercado';
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
  const [destinoLocal, setDestinoLocal] = useState('analista_dados_bi');
  const [ufLocal, setUfLocal] = useState('SP');

  const destinoAtivo = destinoProp ?? destinoLocal;
  const ufAtiva = ufProp ?? ufLocal;

  const handleDestinoChange = useCallback(
    (novoDestino: string) => {
      if (onDestinoChange) {
        onDestinoChange(novoDestino);
      } else {
        setDestinoLocal(novoDestino);
      }
    },
    [onDestinoChange]
  );

  const handleUfChange = useCallback(
    (novaUf: string) => {
      if (onUfChange) {
        onUfChange(novaUf);
      } else {
        setUfLocal(novaUf);
      }
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
          if (err instanceof ApiError) {
            setErro(err.message);
          } else if (err instanceof Error) {
            setErro(err.message);
          } else {
            setErro('Erro desconhecido ao carregar modelos preditivos');
          }
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
        <Heading level={2}>Painel técnico de modelos preditivos (R06)</Heading>
        <Text type="supporting">
          Comparação sistemática de modelos preditivos validados no Novo Caged. Nenhum modelo é promovido automaticamente.
        </Text>
      </div>

      {/* Seletores */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Selector
          label="Destino profissional"
          options={opcoesDestino}
          value={destinoAtivo}
          onChange={(val) => {
            if (val) handleDestinoChange(val);
          }}
          data-testid="seletor-destino-tecnico"
        />
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
              <Heading level={3}>Critério de promoção</Heading>
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
            <div className="flex flex-col gap-2">
              {dados.avisos.map((aviso, idx) => (
                <Banner
                  key={`aviso-tecnico-${idx}`}
                  status="info"
                  title="Aviso de integridade e metodologia"
                  description={aviso}
                />
              ))}
            </div>
          )}

          {/* Tabela Comparativa dos 6 Modelos */}
          <Card padding={4}>
            <div className="flex flex-col gap-4">
              <Heading level={3}>Comparativo de modelos preditivos</Heading>
              <div
                className="w-full overflow-x-auto"
                tabIndex={0}
                role="region"
                aria-label="Tabela comparativa dos 6 modelos preditivos"
              >
                <Table aria-label="Tabela comparativa dos 6 modelos preditivos">
                  <caption className="text-left text-sm font-semibold py-2">
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
                            <span className="font-medium">
                              {formatarNomeModelo(m.id)}
                            </span>
                            {m.exibido_ao_usuario && (
                              <Badge label="Exibido ao usuário" variant="success" />
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{formatarTipoModelo(m.tipo)}</TableCell>
                        <TableCell>{m.promovido ? 'Sim' : 'Não'}</TableCell>
                        <TableCell>
                          {formatarNumero(m.metricas_validacao_global.mae, 2)}
                        </TableCell>
                        <TableCell>
                          {formatarNumero(m.metricas_validacao_global.rmse, 2)}
                        </TableCell>
                        <TableCell>
                          {formatarPercentual(m.metricas_validacao_global.wape, 1)}
                        </TableCell>
                        <TableCell>
                          {formatarNumero(m.metricas_validacao_global.mase, 2)}
                        </TableCell>
                        <TableCell>
                          {m.metricas_serie?.mae !== undefined && m.metricas_serie?.mae !== null
                            ? formatarNumero(m.metricas_serie.mae, 2)
                            : '—'}
                        </TableCell>
                        <TableCell>
                          {formatarMediaDesvio(
                            m.metricas_cv_treino.mae_medio,
                            m.metricas_cv_treino.mae_desvio
                          )}
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
            <Heading level={3}>Model cards detalhados</Heading>
            {dados.modelos.map((m) => (
              <Card key={`card-${m.id}`} padding={4}>
                <Collapsible
                  trigger={`Model Card: ${formatarNomeModelo(m.id)} (${formatarTipoModelo(m.tipo)})`}
                  defaultIsOpen={m.id === 'mlp' || m.exibido_ao_usuario}
                >
                  <div className="mt-3">
                    <MetadataList orientation="vertical" columns="multi">
                      <MetadataListItem label="ID do artefato">
                        {formatarIdArtefato(m.model_card._id)}
                      </MetadataListItem>
                      <MetadataListItem label="Versão do artefato">
                        {m.model_card.versao_artefato}
                      </MetadataListItem>
                      <MetadataListItem label="Tipo">
                        {formatarTipoModelo(m.model_card.tipo)}
                      </MetadataListItem>
                      <MetadataListItem label="Data de treino (UTC)">
                        {m.model_card.data_treino_utc}
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
                        {m.model_card.seed}
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
                        <pre className="max-h-48 overflow-auto rounded border p-2 text-xs font-mono whitespace-pre-wrap break-all">
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
