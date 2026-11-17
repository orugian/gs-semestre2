import {FormEvent, useEffect, useState} from 'react';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {ErroApi, mensagemDeErro} from '../api/cliente';
import {IntencaoResposta, obterIntencao, salvarIntencao} from '../api/intencao';
import {UFS_BRASIL} from '../dominio/listas';
import {formatarDataHora, TEXTOS_JORNADA} from './textos';
import {BloqueioConsentimento} from './BloqueioConsentimento';

export interface TelaIntencaoProps {
  onAvancar?: () => void;
  onIrParaConsentimentos?: () => void;
}

export function TelaIntencao({
  onAvancar,
  onIrParaConsentimentos,
}: TelaIntencaoProps) {
  const [carregando, setCarregando] = useState(true);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [erroConsentimento, setErroConsentimento] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  // Campos do formulário
  const [atividades, setAtividades] = useState<string[]>([]);
  const [novaAtividade, setNovaAtividade] = useState('');
  const [erroAtividade, setErroAtividade] = useState<string | null>(null);

  const [motivos, setMotivos] = useState<string[]>([]);
  const [novoMotivo, setNovoMotivo] = useState('');
  const [erroMotivo, setErroMotivo] = useState<string | null>(null);

  const [horasSemana, setHorasSemana] = useState<string>('');
  const [erroHoras, setErroHoras] = useState<string | null>(null);

  const [orcamento, setOrcamento] = useState<string>('');
  const [erroOrcamento, setErroOrcamento] = useState<string | null>(null);

  const [uf, setUf] = useState<string>('');
  const [erroUf, setErroUf] = useState<string | null>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);

    obterIntencao()
      .then((dados: IntencaoResposta | null) => {
        if (!cancelado && dados) {
          setAtividades(dados.atividades_desejadas || []);
          setMotivos(dados.motivos || []);
          setHorasSemana(
            dados.horas_semana !== null && dados.horas_semana !== undefined
              ? String(dados.horas_semana)
              : ''
          );
          setOrcamento(
            dados.orcamento_mensal_brl !== null && dados.orcamento_mensal_brl !== undefined
              ? String(dados.orcamento_mensal_brl)
              : ''
          );
          setUf(dados.uf || '');
          if (dados.atualizado_em) {
            setMensagemSucesso(
              TEXTOS_JORNADA.intencao.salvoEm(formatarDataHora(dados.atualizado_em))
            );
          }
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          if (err instanceof ErroApi && err.status === 403) {
            setErroConsentimento(true);
            setErro(err.detalhes || TEXTOS_JORNADA.intencao.bloqueioPerfil);
          } else if (err instanceof ErroApi && err.status === 404) {
            // Não registrado ainda: estado vazio esperado
          } else if (err instanceof Error) {
            setErro(err.message);
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
  }, []);

  const handleAdicionarAtividade = () => {
    setErroAtividade(null);
    const texto = novaAtividade.trim();
    if (!texto) {
      setErroAtividade('Digite o nome da atividade.');
      return;
    }
    if (texto.length > 120) {
      setErroAtividade(TEXTOS_JORNADA.intencao.atividades.tamanhoInvalido);
      return;
    }
    if (atividades.length >= 10) {
      setErroAtividade(TEXTOS_JORNADA.intencao.atividades.limite);
      return;
    }
    setAtividades((antigas) => [...antigas, texto]);
    setNovaAtividade('');
  };

  const handleRemoverAtividade = (indice: number) => {
    setAtividades((antigas) => antigas.filter((_, idx) => idx !== indice));
    setErroAtividade(null);
  };

  const handleAdicionarMotivo = () => {
    setErroMotivo(null);
    const texto = novoMotivo.trim();
    if (!texto) {
      setErroMotivo('Digite o motivo.');
      return;
    }
    if (texto.length > 300) {
      setErroMotivo(TEXTOS_JORNADA.intencao.motivos.tamanhoInvalido);
      return;
    }
    if (motivos.length >= 5) {
      setErroMotivo(TEXTOS_JORNADA.intencao.motivos.limite);
      return;
    }
    setMotivos((antigos) => [...antigos, texto]);
    setNovoMotivo('');
  };

  const handleRemoverMotivo = (indice: number) => {
    setMotivos((antigos) => antigos.filter((_, idx) => idx !== indice));
    setErroMotivo(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setErro(null);
    setErroConsentimento(false);
    setErroHoras(null);
    setErroOrcamento(null);
    setErroUf(null);
    setErroAtividade(null);
    setErroMotivo(null);

    let temErro = false;

    // Validação de horas_semana: 1..80
    const horasNum = Number(horasSemana);
    if (!horasSemana.trim() || Number.isNaN(horasNum) || !Number.isInteger(horasNum) || horasNum < 1 || horasNum > 80) {
      setErroHoras(TEXTOS_JORNADA.intencao.horas.erro);
      temErro = true;
    }

    // Validação de atividades: 0..10, cada 1..120
    if (atividades.length > 10) {
      setErroAtividade(TEXTOS_JORNADA.intencao.atividades.limite);
      temErro = true;
    }
    for (const ativ of atividades) {
      if (ativ.length < 1 || ativ.length > 120) {
        setErroAtividade(TEXTOS_JORNADA.intencao.atividades.tamanhoInvalido);
        temErro = true;
        break;
      }
    }

    // Validação de motivos: 0..5, cada 1..300
    if (motivos.length > 5) {
      setErroMotivo(TEXTOS_JORNADA.intencao.motivos.limite);
      temErro = true;
    }
    for (const mot of motivos) {
      if (mot.length < 1 || mot.length > 300) {
        setErroMotivo(TEXTOS_JORNADA.intencao.motivos.tamanhoInvalido);
        temErro = true;
        break;
      }
    }

    // Validação de orçamento: >= 0 e <= 100000 | null
    let orcamentoNum: number | null = null;
    if (orcamento.trim()) {
      orcamentoNum = Number(orcamento);
      if (Number.isNaN(orcamentoNum) || orcamentoNum < 0 || orcamentoNum > 100000) {
        setErroOrcamento(TEXTOS_JORNADA.intencao.orcamento.erro);
        temErro = true;
      }
    }

    // Validação de UF: sigla de 2 letras
    const ufLimpa = uf.trim().toUpperCase();
    if (!ufLimpa || !UFS_BRASIL.includes(ufLimpa as (typeof UFS_BRASIL)[number])) {
      setErroUf(TEXTOS_JORNADA.intencao.uf.erro);
      temErro = true;
    }

    if (temErro) {
      return;
    }

    setSalvando(true);
    try {
      const resp = await salvarIntencao({
        atividades_desejadas: atividades,
        motivos,
        horas_semana: horasNum,
        orcamento_mensal_brl: orcamentoNum,
        uf: ufLimpa,
      });

      // Exibe os motivos redigidos devolvidos pelo servidor
      setMotivos(resp.motivos || []);
      setAtividades(resp.atividades_desejadas || []);
      setUf(resp.uf);
      setMensagemSucesso(
        TEXTOS_JORNADA.intencao.salvoEm(formatarDataHora(resp.atualizado_em))
      );
    } catch (err: unknown) {
      if (err instanceof ErroApi && err.status === 403) {
        setErroConsentimento(true);
        setErro(err.detalhes || TEXTOS_JORNADA.intencao.bloqueioPerfil);
      } else {
        setErro(mensagemDeErro(err, 'Erro ao salvar intenção.'));
      }
    } finally {
      setSalvando(false);
    }
  };

  if (carregando) {
    return (
      <div className="flex items-center justify-center p-12" aria-live="polite">
        <Spinner label="Carregando intenção profissional..." />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <header className="flex flex-col gap-2">
        <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl sm:text-3xl tracking-tight text-[#000091]">
          {TEXTOS_JORNADA.intencao.titulo}
        </Heading>
        <Text type="supporting" className="text-sm text-[#616191]">{TEXTOS_JORNADA.intencao.descricao}</Text>
      </header>

      {mensagemSucesso && (
        <div aria-live="polite">
          <Banner
            status="success"
            title="Intenção registrada"
            description={mensagemSucesso}
          />
        </div>
      )}

      {erro && (
        erroConsentimento ? (
          <BloqueioConsentimento
            role="alert"
            aria-live="polite"
            className="flex flex-col gap-3"
            descricao={erro}
            onIrParaConsentimentos={onIrParaConsentimentos}
            rotuloBotao={TEXTOS_JORNADA.intencao.irParaConsentimentos}
          />
        ) : (
          <div role="alert" aria-live="polite" className="flex flex-col gap-3">
            <Banner
              status="error"
              title="Atenção"
              description={erro}
            />
          </div>
        )
      )}

      <form onSubmit={handleSubmit} className="flex flex-col gap-6">
        {/* Atividades desejadas */}
        <Card width="100%">
          <div className="flex flex-col gap-4 p-5">
            <header className="flex flex-col gap-1">
              <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                {TEXTOS_JORNADA.intencao.atividades.titulo}
              </Heading>
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.atividades.descricao}
              </Text>
            </header>

            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 flex flex-col gap-1">
                <label
                  htmlFor="input-nova-atividade"
                  className="text-sm font-medium text-[#000091]"
                >
                  {TEXTOS_JORNADA.intencao.atividades.nova}
                </label>
                <input
                  id="input-nova-atividade"
                  type="text"
                  value={novaAtividade}
                  onChange={(e) => setNovaAtividade(e.target.value)}
                  placeholder="Ex: Análise de indicadores de desempenho"
                  disabled={salvando}
                  className="border border-[#616191]/30 rounded p-2 text-sm bg-[#FFFFFF] outline-none w-full"
                />
              </div>
              <div className="self-end">
                <Button
                  type="button"
                  variant="secondary"
                  label={TEXTOS_JORNADA.intencao.atividades.adicionar}
                  onClick={handleAdicionarAtividade}
                  isDisabled={salvando || !novaAtividade.trim()}
                />
              </div>
            </div>

            {erroAtividade && (
              <div role="alert" aria-live="polite">
                <Text type="supporting" className="text-xs text-red-600">
                  <span className="font-medium">{erroAtividade}</span>
                </Text>
              </div>
            )}

            {atividades.length === 0 ? (
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.atividades.vazio}
              </Text>
            ) : (
              <ul className="flex flex-col gap-2 pt-2 border-t border-[#616191]/20">
                {atividades.map((item, idx) => (
                  <li
                    key={`ativ-${idx}`}
                    className="flex items-center justify-between gap-3 p-2 border border-[#616191]/20 rounded bg-[#FFFFFF]"
                  >
                    <Text type="body">{item}</Text>
                    <Button
                      type="button"
                      variant="ghost"
                      label={TEXTOS_JORNADA.intencao.atividades.remover}
                      onClick={() => handleRemoverAtividade(idx)}
                      isDisabled={salvando}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>

        {/* Motivos */}
        <Card width="100%">
          <div className="flex flex-col gap-4 p-5">
            <header className="flex flex-col gap-1">
              <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                {TEXTOS_JORNADA.intencao.motivos.titulo}
              </Heading>
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.motivos.descricao}
              </Text>
            </header>

            <div className="flex flex-col sm:flex-row gap-2">
              <div className="flex-1 flex flex-col gap-1">
                <label
                  htmlFor="input-novo-motivo"
                  className="text-sm font-medium text-[#000091]"
                >
                  {TEXTOS_JORNADA.intencao.motivos.novo}
                </label>
                <input
                  id="input-novo-motivo"
                  type="text"
                  value={novoMotivo}
                  onChange={(e) => setNovoMotivo(e.target.value)}
                  placeholder="Ex: Busco transição de carreira para ter maior flexibilidade"
                  disabled={salvando}
                  className="border border-[#616191]/30 rounded p-2 text-sm bg-[#FFFFFF] outline-none w-full"
                />
              </div>
              <div className="self-end">
                <Button
                  type="button"
                  variant="secondary"
                  label={TEXTOS_JORNADA.intencao.motivos.adicionar}
                  onClick={handleAdicionarMotivo}
                  isDisabled={salvando || !novoMotivo.trim()}
                />
              </div>
            </div>

            {erroMotivo && (
              <div role="alert" aria-live="polite">
                <Text type="supporting" className="text-xs text-red-600">
                  <span className="font-medium">{erroMotivo}</span>
                </Text>
              </div>
            )}

            {motivos.length === 0 ? (
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.motivos.vazio}
              </Text>
            ) : (
              <ul className="flex flex-col gap-2 pt-2 border-t border-[#616191]/20">
                {motivos.map((item, idx) => (
                  <li
                    key={`mot-${idx}`}
                    className="flex items-center justify-between gap-3 p-2 border border-[#616191]/20 rounded bg-[#FFFFFF]"
                  >
                    <Text type="body">{item}</Text>
                    <Button
                      type="button"
                      variant="ghost"
                      label={TEXTOS_JORNADA.intencao.motivos.remover}
                      onClick={() => handleRemoverMotivo(idx)}
                      isDisabled={salvando}
                    />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </Card>

        {/* Parâmetros: Horas, Orçamento e UF */}
        <Card width="100%">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-5">
            {/* Horas semanais */}
            <div className="flex flex-col gap-1">
              <label htmlFor="input-horas-semana" className="text-sm font-medium text-[#000091]">
                {TEXTOS_JORNADA.intencao.horas.rotulo}
              </label>
              <input
                id="input-horas-semana"
                type="number"
                min={1}
                max={80}
                step={1}
                required
                value={horasSemana}
                onChange={(e) => {
                  setHorasSemana(e.target.value);
                  setErroHoras(null);
                }}
                placeholder="Ex: 30"
                disabled={salvando}
                className="border border-[#616191]/30 rounded p-2 text-sm bg-[#FFFFFF] outline-none w-full"
              />
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.horas.descricao}
              </Text>
              {erroHoras && (
                <div role="alert" aria-live="polite">
                  <Text type="supporting" className="text-xs text-red-600">
                    <span className="font-medium">{erroHoras}</span>
                  </Text>
                </div>
              )}
            </div>

            {/* Orçamento mensal */}
            <div className="flex flex-col gap-1">
              <label htmlFor="input-orcamento-mensal" className="text-sm font-medium text-[#000091]">
                {TEXTOS_JORNADA.intencao.orcamento.rotulo}
              </label>
              <input
                id="input-orcamento-mensal"
                type="number"
                min={0}
                max={100000}
                step={1}
                value={orcamento}
                onChange={(e) => {
                  setOrcamento(e.target.value);
                  setErroOrcamento(null);
                }}
                placeholder="Ex: 500 (opcional)"
                disabled={salvando}
                className="border border-[#616191]/30 rounded p-2 text-sm bg-[#FFFFFF] outline-none w-full"
              />
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.orcamento.descricao}
              </Text>
              {erroOrcamento && (
                <div role="alert" aria-live="polite">
                  <Text type="supporting" className="text-xs text-red-600">
                    <span className="font-medium">{erroOrcamento}</span>
                  </Text>
                </div>
              )}
            </div>

            {/* UF */}
            <div className="flex flex-col gap-1">
              <label htmlFor="seletor-uf-intencao" className="text-sm font-medium text-[#000091]">
                {TEXTOS_JORNADA.intencao.uf.rotulo}
              </label>
              <select
                id="seletor-uf-intencao"
                required
                value={uf}
                onChange={(e) => {
                  setUf(e.target.value);
                  setErroUf(null);
                }}
                disabled={salvando}
                className="border border-[#616191]/30 rounded p-2 text-sm bg-[#FFFFFF] outline-none w-full"
              >
                <option value="">{TEXTOS_JORNADA.intencao.uf.selecione}</option>
                {UFS_BRASIL.map((sigla) => (
                  <option key={sigla} value={sigla}>
                    {sigla}
                  </option>
                ))}
              </select>
              <Text type="supporting" className="text-xs text-[#616191]">
                {TEXTOS_JORNADA.intencao.uf.descricao}
              </Text>
              {erroUf && (
                <div role="alert" aria-live="polite">
                  <Text type="supporting" className="text-xs text-red-600">
                    <span className="font-medium">{erroUf}</span>
                  </Text>
                </div>
              )}
            </div>
          </div>
        </Card>

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-2">
          <Button
            type="submit"
            variant="primary"
            label={
              salvando
                ? TEXTOS_JORNADA.intencao.salvando
                : TEXTOS_JORNADA.intencao.salvar
            }
            isDisabled={salvando}
            isLoading={salvando}
          />

          {onAvancar && (
            <Button
              type="button"
              variant="secondary"
              label={TEXTOS_JORNADA.intencao.avancar}
              onClick={onAvancar}
              isDisabled={salvando}
            />
          )}
        </div>
      </form>
    </div>
  );
}
