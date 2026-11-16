import {useCallback, useEffect, useState} from 'react';
import {Banner} from '@astryxdesign/core/Banner';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {MetadataList, MetadataListItem} from '@astryxdesign/core/MetadataList';
import {Selector} from '@astryxdesign/core/Selector';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';

import {
  ApiError,
  buscarMercado,
  DESTINOS_MVP,
  RespostaMercado,
  UFS_BRASIL,
} from '../api/mercado';
import {
  formatarNomeModelo,
  formatarNumero,
  formatarPeriodo,
  formatarStatusPromocao,
} from './formatacao';
import {GraficoSerie} from './GraficoSerie';

export interface TelaMercadoProps {
  destino?: string;
  onDestinoChange?: (destino: string) => void;
  uf?: string;
  onUfChange?: (uf: string) => void;
}

export function TelaMercado({
  destino: destinoProp,
  onDestinoChange,
  uf: ufProp,
  onUfChange,
}: TelaMercadoProps) {
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
  const [dados, setDados] = useState<RespostaMercado | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    setDados(null);

    buscarMercado(destinoAtivo, ufAtiva)
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
            setErro('Erro desconhecido ao carregar dados de mercado');
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
    <section id="painel-mercado" className="flex flex-col gap-6 w-full max-w-full min-w-0">
      <div className="flex flex-col gap-1">
        <Heading level={2}>Mercado de admissões formais</Heading>
        <Text type="supporting">
          Acompanhamento das admissões formais observadas no Novo Caged e estimativas retrospectivas com validação estatística.
        </Text>
      </div>

      {/* Seletores de Destino e UF */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Selector
          label="Destino profissional"
          options={opcoesDestino}
          value={destinoAtivo}
          onChange={(val) => {
            if (val) handleDestinoChange(val);
          }}
          data-testid="seletor-destino"
        />
        <Selector
          label="Unidade Federativa (UF)"
          options={opcoesUf}
          value={ufAtiva}
          onChange={(val) => {
            if (val) handleUfChange(val);
          }}
          data-testid="seletor-uf"
        />
      </div>

      {/* Estado de Carregamento */}
      {carregando && (
        <div className="flex justify-center p-12">
          <Spinner
            size="lg"
            label="Carregando dados de mercado..."
            aria-label="Carregando dados de mercado"
          />
        </div>
      )}

      {/* Estado de Erro */}
      {!carregando && erro && (
        <Banner
          status="error"
          title="Erro ao obter dados de mercado"
          description={erro}
        />
      )}

      {/* Conteúdo Principal */}
      {!carregando && dados && (
        <div className="flex flex-col gap-6">
          {/* Avisos Institucionais da API */}
          {dados.avisos && dados.avisos.length > 0 && (
            <div className="flex flex-col gap-2">
              {dados.avisos.map((aviso, idx) => (
                <Banner
                  key={`aviso-${idx}`}
                  status="info"
                  title="Aviso institucional"
                  description={aviso}
                />
              ))}
            </div>
          )}

          {/* Bloco 1: Série Observada (T17) */}
          <Card padding={4}>
            <div className="flex flex-col gap-4">
              <Heading level={3}>Observado</Heading>

              <MetadataList orientation="vertical" columns="multi">
                <MetadataListItem label="Natureza">Observado</MetadataListItem>
                <MetadataListItem label="Fonte">{dados.observado.fonte}</MetadataListItem>
                <MetadataListItem label="População">
                  {dados.observado.populacao}
                </MetadataListItem>
                <MetadataListItem label="Unidade">
                  {dados.observado.unidade}
                </MetadataListItem>
                <MetadataListItem label="Período">
                  {formatarPeriodo(
                    dados.observado.referencia_temporal.inicio,
                    dados.observado.referencia_temporal.fim
                  )}
                </MetadataListItem>
              </MetadataList>

              <GraficoSerie
                titulo="Admissões formais observadas"
                descricaoAcessivel="Gráfico da série histórica de admissões formais observadas no Novo Caged"
                pontos={dados.observado.serie.map((item) => ({
                  competencia: item.competencia,
                  observado: item.valor,
                }))}
                unidade={dados.observado.unidade}
              />
            </div>
          </Card>

          {/* Bloco 2: Abstenção (T06) ou Previsão Retrospectiva (T17) */}
          {dados.abstencao ? (
            <div className="flex flex-col gap-4">
              <Banner
                status="warning"
                title="Abstenção de estimativa retrospectiva"
                description={`Série insuficiente nesta UF para estimar (média de ${
                  dados.abstencao.media_alvo_treino !== null
                    ? formatarNumero(dados.abstencao.media_alvo_treino, 1)
                    : 'sem dados'
                } admissões por trimestre no treino; mínimo ${formatarNumero(
                  dados.abstencao.limite_minimo
                )})`}
              />

              {/* Contexto Regional Observado */}
              <Card padding={4}>
                <div className="flex flex-col gap-4">
                  <div className="flex items-baseline justify-between">
                    <Heading level={3}>Contexto regional observado</Heading>
                    <Text type="supporting">
                      Região: {dados.abstencao.contexto_regional.regiao}
                    </Text>
                  </div>

                  <MetadataList orientation="vertical" columns="multi">
                    <MetadataListItem label="Natureza">
                      Contexto regional observado
                    </MetadataListItem>
                    <MetadataListItem label="Região">
                      {dados.abstencao.contexto_regional.regiao}
                    </MetadataListItem>
                    <MetadataListItem label="Fonte">
                      {dados.abstencao.contexto_regional.fonte}
                    </MetadataListItem>
                    <MetadataListItem label="População">
                      {dados.abstencao.contexto_regional.populacao}
                    </MetadataListItem>
                    <MetadataListItem label="Unidade">
                      {dados.abstencao.contexto_regional.unidade}
                    </MetadataListItem>
                    <MetadataListItem label="Período">
                      {formatarPeriodo(
                        dados.abstencao.contexto_regional.referencia_temporal.inicio,
                        dados.abstencao.contexto_regional.referencia_temporal.fim
                      )}
                    </MetadataListItem>
                  </MetadataList>

                  <GraficoSerie
                    titulo={`Contexto regional observado — Região ${dados.abstencao.contexto_regional.regiao}`}
                    descricaoAcessivel={`Gráfico da série agregada de admissões formais na macrorregião ${dados.abstencao.contexto_regional.regiao}`}
                    pontos={dados.abstencao.contexto_regional.serie.map((item) => ({
                      competencia: item.competencia,
                      observado: item.valor,
                    }))}
                    unidade={dados.abstencao.contexto_regional.unidade}
                  />
                </div>
              </Card>
            </div>
          ) : dados.previsto ? (
            <Card padding={4}>
              <div className="flex flex-col gap-4">
                <Heading level={3}>Estimativa retrospectiva (2025)</Heading>

                <MetadataList orientation="vertical" columns="multi">
                  <MetadataListItem label="Natureza">
                    Estimativa retrospectiva (2025)
                  </MetadataListItem>
                  <MetadataListItem label="Fonte">{dados.previsto.fonte}</MetadataListItem>
                  <MetadataListItem label="População">
                    {dados.previsto.populacao}
                  </MetadataListItem>
                  <MetadataListItem label="Unidade">
                    {dados.previsto.unidade}
                  </MetadataListItem>
                  <MetadataListItem label="Período">
                    {formatarPeriodo(
                      dados.previsto.referencia_temporal.inicio,
                      dados.previsto.referencia_temporal.fim
                    )}
                  </MetadataListItem>
                  <MetadataListItem label="Modelo de referência exibido">
                    {formatarNomeModelo(dados.previsto.modelo_exibido)}
                  </MetadataListItem>
                  <MetadataListItem label="Status de promoção">
                    {formatarStatusPromocao(dados.previsto.status_promocao)}
                  </MetadataListItem>
                </MetadataList>

                <GraficoSerie
                  titulo="Estimativa retrospectiva vs. Realizado"
                  descricaoAcessivel="Gráfico de estimativa retrospectiva e valores realizados de admissões formais no período avaliado"
                  pontos={dados.previsto.serie.map((item) => ({
                    competencia: item.competencia_origem,
                    previsto: item.previsao,
                    realizado: item.realizado,
                  }))}
                  unidade={dados.previsto.unidade}
                />
              </div>
            </Card>
          ) : null}

          {/* Situação da Amostra Adzuna (D05a) */}
          {!dados.amostra_adzuna.disponivel && (
            <Card variant="muted" padding={4}>
              <div className="flex flex-col gap-1">
                <Heading level={4}>Amostra Adzuna indisponível</Heading>
                <Text type="body">{dados.amostra_adzuna.motivo}</Text>
              </div>
            </Card>
          )}
        </div>
      )}
    </section>
  );
}
