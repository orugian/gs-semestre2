import {Collapsible} from '@astryxdesign/core/Collapsible';
import {Heading} from '@astryxdesign/core/Heading';
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
  formatarCompetencia,
  formatarNumero,
  formatarValorSerie,
  gerarIndicesTicks,
} from './formatacao';

export interface GraficoPonto {
  competencia: string;
  observado?: number | null;
  previsto?: number | null;
  realizado?: number | null;
}

export interface GraficoSerieProps {
  titulo: string;
  descricaoAcessivel: string;
  pontos: GraficoPonto[];
  unidade: string;
}

export function GraficoSerie({
  titulo,
  descricaoAcessivel,
  pontos,
  unidade,
}: GraficoSerieProps) {
  const temObservado = pontos.some(
    (p) => typeof p.observado === 'number' && !Number.isNaN(p.observado)
  );
  const temPrevisto = pontos.some(
    (p) => typeof p.previsto === 'number' && !Number.isNaN(p.previsto)
  );
  const temRealizado = pontos.some(
    (p) => typeof p.realizado === 'number' && !Number.isNaN(p.realizado)
  );

  // Coleta todos os valores válidos para escala
  const todosValores: number[] = [];
  pontos.forEach((p) => {
    if (typeof p.observado === 'number' && !Number.isNaN(p.observado)) {
      todosValores.push(p.observado);
    }
    if (typeof p.previsto === 'number' && !Number.isNaN(p.previsto)) {
      todosValores.push(p.previsto);
    }
    if (typeof p.realizado === 'number' && !Number.isNaN(p.realizado)) {
      todosValores.push(p.realizado);
    }
  });

  const svgWidth = 640;
  const svgHeight = 240;
  const padding = {top: 24, right: 32, bottom: 48, left: 64};
  const plotWidth = svgWidth - padding.left - padding.right;
  const plotHeight = svgHeight - padding.top - padding.bottom;

  let minVal = todosValores.length > 0 ? Math.min(...todosValores) : 0;
  let maxVal = todosValores.length > 0 ? Math.max(...todosValores) : 100;

  if (minVal === maxVal) {
    minVal = Math.max(0, minVal - 10);
    maxVal = maxVal + 10;
  }
  // Folga de 5% no topo
  maxVal = maxVal * 1.05;
  minVal = Math.max(0, minVal * 0.95);

  const getX = (index: number) => {
    if (pontos.length <= 1) return padding.left + plotWidth / 2;
    return padding.left + (index / (pontos.length - 1)) * plotWidth;
  };

  const getY = (val: number) => {
    const range = maxVal - minVal || 1;
    return padding.top + plotHeight - ((val - minVal) / range) * plotHeight;
  };

  // Segmentos observados
  const segmentosObservado: Array<Array<{x: number; y: number; p: GraficoPonto}>> = [];
  let segObsAtual: Array<{x: number; y: number; p: GraficoPonto}> = [];
  pontos.forEach((p, i) => {
    if (typeof p.observado === 'number' && !Number.isNaN(p.observado)) {
      segObsAtual.push({x: getX(i), y: getY(p.observado), p});
    } else {
      if (segObsAtual.length > 0) {
        segmentosObservado.push(segObsAtual);
        segObsAtual = [];
      }
    }
  });
  if (segObsAtual.length > 0) {
    segmentosObservado.push(segObsAtual);
  }

  // Segmentos realizados
  const segmentosRealizado: Array<Array<{x: number; y: number; p: GraficoPonto}>> = [];
  let segRealAtual: Array<{x: number; y: number; p: GraficoPonto}> = [];
  pontos.forEach((p, i) => {
    if (typeof p.realizado === 'number' && !Number.isNaN(p.realizado)) {
      segRealAtual.push({x: getX(i), y: getY(p.realizado), p});
    } else {
      if (segRealAtual.length > 0) {
        segmentosRealizado.push(segRealAtual);
        segRealAtual = [];
      }
    }
  });
  if (segRealAtual.length > 0) {
    segmentosRealizado.push(segRealAtual);
  }

  // Segmentos previstos
  const segmentosPrevisto: Array<Array<{x: number; y: number; p: GraficoPonto}>> = [];
  let segPrevAtual: Array<{x: number; y: number; p: GraficoPonto}> = [];
  pontos.forEach((p, i) => {
    if (typeof p.previsto === 'number' && !Number.isNaN(p.previsto)) {
      segPrevAtual.push({x: getX(i), y: getY(p.previsto), p});
    } else {
      if (segPrevAtual.length > 0) {
        segmentosPrevisto.push(segPrevAtual);
        segPrevAtual = [];
      }
    }
  });
  if (segPrevAtual.length > 0) {
    segmentosPrevisto.push(segPrevAtual);
  }

  // Linhas de grade no eixo Y
  const gridTicks = [minVal, (minVal + maxVal) / 2, maxVal];

  // Rótulos do eixo X com espaçamento uniforme sem sobreposição
  const indicesTicksX = gerarIndicesTicks(pontos.length, 7);

  return (
    <div className="flex flex-col gap-3 min-w-0 max-w-full">
      <div className="flex items-baseline justify-between flex-wrap gap-2">
        <Heading level={4}>{titulo}</Heading>
        <Text type="supporting">Unidade: {unidade}</Text>
      </div>

      <div className="w-full overflow-x-auto rounded border border-neutral-200 bg-white p-2">
        <svg
          role="img"
          aria-label={descricaoAcessivel}
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          width="100%"
          preserveAspectRatio="xMidYMid meet"
          className="w-full h-auto"
        >
          {/* Linhas de grade horizontais */}
          {gridTicks.map((val, idx) => {
            const y = getY(val);
            return (
              <g key={`grid-${idx}`}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={svgWidth - padding.right}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 8}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="10"
                  fill="#6b7280"
                >
                  {formatarNumero(val)}
                </text>
              </g>
            );
          })}

          {/* Eixo X e Y */}
          <line
            x1={padding.left}
            y1={padding.top + plotHeight}
            x2={svgWidth - padding.right}
            y2={padding.top + plotHeight}
            stroke="#9ca3af"
          />
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left}
            y2={padding.top + plotHeight}
            stroke="#9ca3af"
          />

          {/* Rótulos do Eixo X sem colisão */}
          {indicesTicksX.map((i) => {
            const p = pontos[i];
            if (!p) return null;
            const x = getX(i);
            return (
              <text
                key={`label-x-${p.competencia}-${i}`}
                x={x}
                y={padding.top + plotHeight + 18}
                textAnchor="middle"
                fontSize="10"
                fill="#4b5563"
              >
                {formatarCompetencia(p.competencia)}
              </text>
            );
          })}

          {/* Série Observada (linha azul sólida) */}
          {segmentosObservado.map((seg, sIdx) => {
            const pathData =
              seg.length > 1
                ? `M ${seg[0].x} ${seg[0].y} ` +
                  seg.slice(1).map((pt) => `L ${pt.x} ${pt.y}`).join(' ')
                : `M ${seg[0].x} ${seg[0].y} L ${seg[0].x} ${seg[0].y}`;
            return (
              <g key={`seg-obs-${sIdx}`} data-serie="observado">
                <path
                  data-serie="observado"
                  d={pathData}
                  fill="none"
                  stroke="#2563eb"
                  strokeWidth="2.5"
                />
                {seg.map((pt, ptIdx) => (
                  <circle
                    key={`obs-pt-${sIdx}-${ptIdx}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="3.5"
                    fill="#2563eb"
                    data-serie="observado"
                  >
                    <title>{`${formatarCompetencia(pt.p.competencia)}: ${formatarNumero(pt.p.observado)}`}</title>
                  </circle>
                ))}
              </g>
            );
          })}

          {/* Série Realizado (linha azul escura sólida) */}
          {segmentosRealizado.map((seg, sIdx) => {
            const pathData =
              seg.length > 1
                ? `M ${seg[0].x} ${seg[0].y} ` +
                  seg.slice(1).map((pt) => `L ${pt.x} ${pt.y}`).join(' ')
                : `M ${seg[0].x} ${seg[0].y} L ${seg[0].x} ${seg[0].y}`;
            return (
              <g key={`seg-real-${sIdx}`} data-serie="realizado">
                <path
                  data-serie="realizado"
                  d={pathData}
                  fill="none"
                  stroke="#1d4ed8"
                  strokeWidth="2.5"
                />
                {seg.map((pt, ptIdx) => (
                  <circle
                    key={`real-pt-${sIdx}-${ptIdx}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="3.5"
                    fill="#1d4ed8"
                    data-serie="realizado"
                  >
                    <title>{`Realizado ${formatarCompetencia(pt.p.competencia)}: ${formatarNumero(pt.p.realizado)}`}</title>
                  </circle>
                ))}
              </g>
            );
          })}

          {/* Série Prevista Retrospectiva (linha verde tracejada) */}
          {segmentosPrevisto.map((seg, sIdx) => {
            const pathData =
              seg.length > 1
                ? `M ${seg[0].x} ${seg[0].y} ` +
                  seg.slice(1).map((pt) => `L ${pt.x} ${pt.y}`).join(' ')
                : `M ${seg[0].x} ${seg[0].y} L ${seg[0].x} ${seg[0].y}`;
            return (
              <g key={`seg-prev-${sIdx}`} data-serie="previsto">
                <path
                  data-serie="previsto"
                  d={pathData}
                  fill="none"
                  stroke="#16a34a"
                  strokeWidth="2.5"
                  strokeDasharray="4 4"
                />
                {seg.map((pt, ptIdx) => (
                  <circle
                    key={`prev-pt-${sIdx}-${ptIdx}`}
                    cx={pt.x}
                    cy={pt.y}
                    r="3.5"
                    fill="#16a34a"
                    data-serie="previsto"
                  >
                    <title>{`Estimativa ${formatarCompetencia(pt.p.competencia)}: ${formatarNumero(pt.p.previsto)}`}</title>
                  </circle>
                ))}
              </g>
            );
          })}
        </svg>

        {/* Legenda com distinção clara de séries */}
        <div className="flex flex-wrap items-center justify-center gap-6 pt-2 text-xs text-neutral-700">
          {temObservado && (
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-blue-600" />
              <span>Observado</span>
            </div>
          )}
          {temRealizado && (
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 rounded-full bg-blue-700" />
              <span>Realizado (admissões no trimestre seguinte)</span>
            </div>
          )}
          {temPrevisto && (
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-3 w-3 border-b-2 border-dashed border-green-600 bg-green-600" />
              <span>Estimativa retrospectiva (2025)</span>
            </div>
          )}
        </div>
      </div>

      {/* Tabela de dados alternativa acessível */}
      <Collapsible trigger="Ver tabela de dados da série" defaultIsOpen={false}>
        <div
          className="mt-2 w-full overflow-x-auto"
          tabIndex={0}
          role="region"
          aria-label={`Tabela de dados da série: ${titulo}`}
        >
          <Table aria-label={`Tabela de dados: ${titulo}`}>
            <caption className="text-left text-sm font-semibold py-1">
              Tabela de dados da série temporal ({titulo})
            </caption>
            <TableHeader>
              <TableRow isHeaderRow>
                {temRealizado && temPrevisto ? (
                  <>
                    <TableHeaderCell>Competência de origem</TableHeaderCell>
                    <TableHeaderCell>Estimativa</TableHeaderCell>
                    <TableHeaderCell>Realizado</TableHeaderCell>
                    <TableHeaderCell>Erro absoluto</TableHeaderCell>
                  </>
                ) : (
                  <>
                    <TableHeaderCell>Competência</TableHeaderCell>
                    {temObservado && <TableHeaderCell>Observado</TableHeaderCell>}
                    {temPrevisto && (
                      <TableHeaderCell>Estimativa retrospectiva</TableHeaderCell>
                    )}
                    {temRealizado && <TableHeaderCell>Realizado</TableHeaderCell>}
                  </>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {pontos.map((p, idx) => (
                <TableRow key={`linha-${p.competencia}-${idx}`}>
                  {temRealizado && temPrevisto ? (
                    <>
                      <TableCell>{formatarCompetencia(p.competencia)}</TableCell>
                      <TableCell>{formatarValorSerie(p.previsto)}</TableCell>
                      <TableCell>{formatarValorSerie(p.realizado)}</TableCell>
                      <TableCell>
                        {typeof p.previsto === 'number' &&
                        typeof p.realizado === 'number' &&
                        !Number.isNaN(p.previsto) &&
                        !Number.isNaN(p.realizado)
                          ? formatarNumero(Math.abs(p.realizado - p.previsto))
                          : 'sem dado'}
                      </TableCell>
                    </>
                  ) : (
                    <>
                      <TableCell>{formatarCompetencia(p.competencia)}</TableCell>
                      {temObservado && (
                        <TableCell>{formatarValorSerie(p.observado)}</TableCell>
                      )}
                      {temPrevisto && (
                        <TableCell>{formatarValorSerie(p.previsto)}</TableCell>
                      )}
                      {temRealizado && (
                        <TableCell>{formatarValorSerie(p.realizado)}</TableCell>
                      )}
                    </>
                  )}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </Collapsible>
    </div>
  );
}
