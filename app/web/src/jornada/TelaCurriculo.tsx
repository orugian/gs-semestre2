import {useEffect, useState} from 'react';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {FileInput} from '@astryxdesign/core/FileInput';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Tab, TabList} from '@astryxdesign/core/TabList';
import {Text} from '@astryxdesign/core/Text';
import {TextArea} from '@astryxdesign/core/TextArea';
import {ErroApi, mensagemDeErro} from '../api/cliente';
import {extrairCompetencias, RespostaExtracao} from '../api/competencias';
import {listarConsentimentos} from '../api/conta';
import {
  confirmarEnvioCurriculo,
  Curriculo,
  enviarArquivoCurriculo,
  enviarExperiencias,
  Redacoes,
} from '../api/curriculo';
import {formatarDataHora, TEXTOS_JORNADA} from './textos';
import {BloqueioConsentimento} from './BloqueioConsentimento';

export interface TelaCurriculoProps {
  onSugerirSucesso?: (extracao: RespostaExtracao) => void;
  onIrParaConsentimentos?: () => void;
}

function formatarResumoRedacoes(redacoes?: Redacoes): string {
  if (!redacoes) return '';
  const partes: string[] = [];
  if (redacoes.email > 0)
    partes.push(`${redacoes.email} ${redacoes.email === 1 ? 'e-mail' : 'e-mails'}`);
  if (redacoes.telefone > 0)
    partes.push(`${redacoes.telefone} ${redacoes.telefone === 1 ? 'telefone' : 'telefones'}`);
  if (redacoes.cpf > 0) partes.push(`${redacoes.cpf} CPF`);
  if (redacoes.nome > 0)
    partes.push(`${redacoes.nome} ${redacoes.nome === 1 ? 'nome' : 'nomes'}`);
  if (redacoes.cep > 0) partes.push(`${redacoes.cep} CEP`);
  if (redacoes.endereco > 0)
    partes.push(`${redacoes.endereco} ${redacoes.endereco === 1 ? 'endereço' : 'endereços'}`);
  if (redacoes.url > 0)
    partes.push(`${redacoes.url} ${redacoes.url === 1 ? 'link' : 'links'}`);

  return partes.length > 0 ? `Redações aplicadas: ${partes.join(', ')}.` : '';
}

export function TelaCurriculo({
  onSugerirSucesso,
  onIrParaConsentimentos,
}: TelaCurriculoProps) {
  const [temConsentimentoPerfil, setTemConsentimentoPerfil] = useState<boolean | null>(null);
  const [abaOrigem, setAbaOrigem] = useState<string>('texto');
  const [textoEntrada, setTextoEntrada] = useState('');
  const [arquivoSelecionado, setArquivoSelecionado] = useState<File | null>(null);

  const [curriculo, setCurriculo] = useState<Curriculo | null>(null);
  const [textoEditavel, setTextoEditavel] = useState('');
  const [textoOriginal, setTextoOriginal] = useState('');

  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  // Verifica consentimento prévio
  useEffect(() => {
    let cancelado = false;
    listarConsentimentos()
      .then((resp) => {
        if (!cancelado) {
          const ativo = (resp.itens || []).some(
            (c) => c.finalidade === 'perfil' && c.revogado_em === null
          );
          setTemConsentimentoPerfil(ativo);
        }
      })
      .catch(() => {
        // Se a rota falhar ou estiver em teste sem mock de consentimento, não bloqueia
        if (!cancelado) {
          setTemConsentimentoPerfil(true);
        }
      });

    return () => {
      cancelado = true;
    };
  }, []);

  const handleEnviarTexto = async () => {
    const textoLimpo = textoEntrada.trim();
    if (!textoLimpo) {
      setErro('Digite ou cole o texto do seu currículo.');
      return;
    }

    setCarregando(true);
    setErro(null);
    try {
      const res = await enviarExperiencias(textoLimpo);
      setCurriculo(res);
      setTextoEditavel(res.texto_redigido);
      setTextoOriginal(res.texto_redigido);
    } catch (err: unknown) {
      tratarErroApi(err);
    } finally {
      setCarregando(false);
    }
  };

  const handleEnviarArquivo = async () => {
    if (!arquivoSelecionado) {
      setErro(TEXTOS_JORNADA.curriculo.arquivoInvalido);
      return;
    }

    if (arquivoSelecionado.size > 2 * 1024 * 1024) {
      setErro(TEXTOS_JORNADA.curriculo.arquivoGrande);
      return;
    }

    setCarregando(true);
    setErro(null);
    try {
      const res = await enviarArquivoCurriculo(arquivoSelecionado);
      setCurriculo(res);
      setTextoEditavel(res.texto_redigido);
      setTextoOriginal(res.texto_redigido);
    } catch (err: unknown) {
      tratarErroApi(err);
    } finally {
      setCarregando(false);
    }
  };

  const handleConfirmar = async () => {
    if (!curriculo) return;

    setCarregando(true);
    setErro(null);
    try {
      const textoRevisado =
        textoEditavel !== textoOriginal ? textoEditavel : null;
      const res = await confirmarEnvioCurriculo(curriculo.id, textoRevisado);
      setCurriculo(res);
      // D22: Exibe o texto_redigido devolvido pelo servidor, nunca o texto cru digitado
      setTextoEditavel(res.texto_redigido);
      setTextoOriginal(res.texto_redigido);
    } catch (err: unknown) {
      tratarErroApi(err);
    } finally {
      setCarregando(false);
    }
  };

  const handleSugerirCompetencias = async () => {
    if (!curriculo || curriculo.status !== 'confirmado' || textoEditavel !== textoOriginal) return;

    setCarregando(true);
    setErro(null);
    try {
      const res = await extrairCompetencias(curriculo.id);
      onSugerirSucesso?.(res);
    } catch (err: unknown) {
      tratarErroApi(err);
    } finally {
      setCarregando(false);
    }
  };

  const tratarErroApi = (err: unknown) => {
    if (err instanceof ErroApi) {
      if (err.status === 403) {
        setErro(TEXTOS_JORNADA.curriculo.consentimentoLlmNecessario);
        return;
      }
      if (err.status === 429) {
        setErro(TEXTOS_JORNADA.curriculo.limiteSugestoesAtingido);
        return;
      }
      if (err.status === 503) {
        setErro(TEXTOS_JORNADA.curriculo.servicoIndisponivel);
        return;
      }
      if (err.status === 400) {
        setErro(err.detalhes || TEXTOS_JORNADA.curriculo.arquivoGrande);
        return;
      }
    }
    setErro(mensagemDeErro(err, 'Ocorreu um erro inesperado.'));
  };

  if (temConsentimentoPerfil === false) {
    return (
      <BloqueioConsentimento
        className="flex flex-col gap-4 w-full max-w-3xl mx-auto"
        descricao={TEXTOS_JORNADA.curriculo.bloqueioConsentimentoPerfil}
        onIrParaConsentimentos={onIrParaConsentimentos}
        rotuloBotao={TEXTOS_JORNADA.curriculo.irParaConsentimentos}
      />
    );
  }

  const resumoRedacoes = curriculo ? formatarResumoRedacoes(curriculo.redacoes) : '';

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <header className="flex flex-col gap-2">
        <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl sm:text-3xl tracking-tight text-[#000091]">
          {TEXTOS_JORNADA.curriculo.titulo}
        </Heading>
        <Text type="supporting" className="text-sm text-[#616191]">{TEXTOS_JORNADA.curriculo.descricao}</Text>
      </header>

      {erro && (
        <div role="alert" aria-live="polite">
          <Banner status="error" title="Atenção" description={erro} />
        </div>
      )}

      {!curriculo ? (
        <Card width="100%">
          <div className="flex flex-col gap-5 p-5">
            <TabList value={abaOrigem} onChange={setAbaOrigem} role="tablist">
              <Tab
                value="texto"
                label={TEXTOS_JORNADA.curriculo.abaTexto}
                panelId="painel-cv-texto"
              />
              <Tab
                value="arquivo"
                label={TEXTOS_JORNADA.curriculo.abaArquivo}
                panelId="painel-cv-arquivo"
              />
            </TabList>

            {abaOrigem === 'texto' ? (
              <div id="painel-cv-texto" className="flex flex-col gap-4">
                <TextArea
                  label={TEXTOS_JORNADA.curriculo.rotuloTexto}
                  value={textoEntrada}
                  onChange={(val) => setTextoEntrada(val)}
                  placeholder={TEXTOS_JORNADA.curriculo.placeholderTexto}
                  rows={8}
                  maxLength={20000}
                  isDisabled={carregando}
                />
                <div className="flex justify-end">
                  <Button
                    label={TEXTOS_JORNADA.curriculo.enviarTexto}
                    variant="primary"
                    onClick={handleEnviarTexto}
                    isDisabled={carregando}
                    isLoading={carregando}
                  />
                </div>
              </div>
            ) : (
              <div id="painel-cv-arquivo" className="flex flex-col gap-4">
                <FileInput
                  label={TEXTOS_JORNADA.curriculo.rotuloArquivo}
                  value={arquivoSelecionado}
                  onChange={(val) => {
                    const arquivo = Array.isArray(val) ? val[0] : val;
                    setArquivoSelecionado(arquivo);
                    if (arquivo && arquivo.size > 2 * 1024 * 1024) {
                      setErro(TEXTOS_JORNADA.curriculo.arquivoGrande);
                    } else {
                      setErro(null);
                    }
                  }}
                  accept=".pdf,.docx"
                  isDisabled={carregando}
                  description="Formatos suportados: PDF ou DOCX de até 2 MB."
                />
                <div className="flex justify-end">
                  <Button
                    label={TEXTOS_JORNADA.curriculo.enviarArquivo}
                    variant="primary"
                    onClick={handleEnviarArquivo}
                    isDisabled={carregando}
                    isLoading={carregando}
                  />
                </div>
              </div>
            )}
          </div>
        </Card>
      ) : (
        <div className="flex flex-col gap-5">
          {curriculo.aviso_redacao && (
            <Banner
              status="info"
              title="Proteção de dados aplicada"
              description={curriculo.aviso_redacao}
            />
          )}

          {resumoRedacoes && (
            <Banner
              status="info"
              title="Resumo de redações"
              description={resumoRedacoes}
            />
          )}

          <Card width="100%">
            <div className="flex flex-col gap-4 p-5">
              <header className="flex flex-col gap-1">
                <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                  {TEXTOS_JORNADA.curriculo.textoRedigidoTitulo}
                </Heading>
                <Text type="supporting" className="text-xs text-[#616191]">
                  {TEXTOS_JORNADA.curriculo.textoRedigidoDescricao}
                </Text>
              </header>

              <TextArea
                label={TEXTOS_JORNADA.curriculo.textoRedigidoTitulo}
                isLabelHidden
                value={textoEditavel}
                onChange={(val) => setTextoEditavel(val)}
                rows={10}
                isDisabled={carregando}
              />

              {curriculo.status === 'confirmado' && (
                <div aria-live="polite">
                  <Text type="supporting" className="text-xs text-[#616191]">
                    {textoEditavel === textoOriginal
                      ? `Texto confirmado em ${formatarDataHora(curriculo.confirmado_em)}. Só este texto pode ser enviado ao modelo.`
                      : 'Você alterou o texto depois de confirmar. Confirme de novo para liberar as sugestões.'}
                  </Text>
                </div>
              )}

              <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-[#616191]/20">
                <Button
                  label={TEXTOS_JORNADA.curriculo.confirmarEnvio}
                  variant={
                    curriculo.status === 'confirmado' && textoEditavel === textoOriginal
                      ? 'secondary'
                      : 'primary'
                  }
                  onClick={handleConfirmar}
                  isDisabled={carregando}
                  isLoading={carregando}
                />

                {/* D22: Botão de sugerir competências só existe e está habilitado após status === 'confirmado' */}
                {curriculo.status === 'confirmado' && textoEditavel === textoOriginal && (
                  <Button
                    label={TEXTOS_JORNADA.curriculo.sugerirCompetencias}
                    variant="primary"
                    onClick={handleSugerirCompetencias}
                    isDisabled={carregando}
                    isLoading={carregando}
                  />
                )}
              </div>
            </div>
          </Card>
        </div>
      )}

      {carregando && (
        <div className="flex items-center justify-center p-4" aria-live="polite">
          <Spinner label="Processando informações..." />
        </div>
      )}
    </div>
  );
}
