import {useCallback, useEffect, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Text} from '@astryxdesign/core/Text';
import {mensagemDeErro} from '../api/cliente';
import {
  concederConsentimento,
  Consentimento,
  FinalidadeConsentimento,
  listarConsentimentos,
  revogarConsentimento,
} from '../api/conta';
import {formatarDataHora, TEXTOS_JORNADA} from './textos';

export interface TelaConsentimentosProps {
  onAvancar?: () => void;
}

interface ItemFinalidade {
  chave: FinalidadeConsentimento;
  titulo: string;
  descricao: string;
  avisoRevogacao?: string;
}

const FINALIDADES: ItemFinalidade[] = [
  {
    chave: 'perfil',
    titulo: TEXTOS_JORNADA.consentimentos.finalidades.perfil.titulo,
    descricao: TEXTOS_JORNADA.consentimentos.finalidades.perfil.descricao,
  },
  {
    chave: 'curriculo_llm',
    titulo: TEXTOS_JORNADA.consentimentos.finalidades.curriculo_llm.titulo,
    descricao: TEXTOS_JORNADA.consentimentos.finalidades.curriculo_llm.descricao,
    avisoRevogacao:
      TEXTOS_JORNADA.consentimentos.finalidades.curriculo_llm.avisoRevogacao,
  },
  {
    chave: 'laboratorio_nuvem',
    titulo: TEXTOS_JORNADA.consentimentos.finalidades.laboratorio_nuvem.titulo,
    descricao: TEXTOS_JORNADA.consentimentos.finalidades.laboratorio_nuvem.descricao,
  },
];

export function TelaConsentimentos({
  onAvancar,
}: TelaConsentimentosProps) {
  const [consentimentos, setConsentimentos] = useState<Consentimento[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [processandoChave, setProcessandoChave] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const carregarConsentimentos = useCallback(async () => {
    try {
      setCarregando(true);
      setErro(null);
      const resp = await listarConsentimentos();
      setConsentimentos(resp.itens || []);
    } catch (err: unknown) {
      setErro(mensagemDeErro(err, 'Não foi possível carregar as autorizações.'));
    } finally {
      setCarregando(false);
    }
  }, []);

  useEffect(() => {
    carregarConsentimentos();
  }, [carregarConsentimentos]);

  const obterConsentimentoAtivo = (finalidade: FinalidadeConsentimento) => {
    return consentimentos.find(
      (c) => c.finalidade === finalidade && c.revogado_em === null
    );
  };

  const handleConceder = async (finalidade: FinalidadeConsentimento) => {
    // Só chama se não houver um ativo daquela finalidade
    if (obterConsentimentoAtivo(finalidade)) return;

    try {
      setProcessandoChave(finalidade);
      setErro(null);
      await concederConsentimento(finalidade);
      await carregarConsentimentos();
    } catch (err: unknown) {
      setErro(mensagemDeErro(err, 'Erro ao conceder autorização.'));
    } finally {
      setProcessandoChave(null);
    }
  };

  const handleRevogar = async (consentimentoId: string, finalidade: string) => {
    try {
      setProcessandoChave(finalidade);
      setErro(null);
      await revogarConsentimento(consentimentoId);
      await carregarConsentimentos();
    } catch (err: unknown) {
      setErro(mensagemDeErro(err, 'Erro ao revogar autorização.'));
    } finally {
      setProcessandoChave(null);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full max-w-4xl mx-auto">
      <header className="flex flex-col gap-2">
        <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl sm:text-3xl tracking-tight text-[#000091]">
          {TEXTOS_JORNADA.consentimentos.titulo}
        </Heading>
        <Text type="supporting" className="text-sm text-[#616191]">
          {TEXTOS_JORNADA.consentimentos.descricao}
        </Text>
      </header>

      {erro && (
        <div role="alert" aria-live="polite">
          <Banner
            status="error"
            title="Erro nas autorizações"
            description={erro}
          />
        </div>
      )}

      {carregando ? (
        <div className="flex items-center justify-center p-8" aria-live="polite">
          <Spinner label="Carregando autorizações..." />
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          {FINALIDADES.map((item) => {
            const consentimentoAtivo = obterConsentimentoAtivo(item.chave);
            const estaAtivo = Boolean(consentimentoAtivo);
            const emProcesso = processandoChave === item.chave;

            return (
              <Card key={item.chave} width="100%">
                <div
                  data-testid={`cartao-consentimento-${item.chave}`}
                  className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-5"
                >
                  <div className="flex flex-col gap-2 flex-1">
                    <div className="flex items-center gap-3 flex-wrap">
                      <Heading level={3} className="!font-['Barlow_Condensed'] font-semibold text-xl text-[#000091]">
                        {item.titulo}
                      </Heading>
                      {estaAtivo ? (
                        <Badge
                          variant="success"
                          label={TEXTOS_JORNADA.consentimentos.ativoDesde(
                            formatarDataHora(consentimentoAtivo?.concedido_em)
                          )}
                        />
                      ) : (
                        <Badge
                          variant="neutral"
                          label={TEXTOS_JORNADA.consentimentos.naoConcedido}
                        />
                      )}
                    </div>
                    <Text type="body">{item.descricao}</Text>

                    {estaAtivo && item.avisoRevogacao && (
                      <Text type="supporting" className="text-xs text-[#616191]">{item.avisoRevogacao}</Text>
                    )}
                  </div>

                  <div className="flex items-center gap-2 self-start sm:self-center">
                    {estaAtivo ? (
                      <Button
                        label={TEXTOS_JORNADA.consentimentos.revogar}
                        variant="secondary"
                        onClick={() =>
                          consentimentoAtivo &&
                          handleRevogar(consentimentoAtivo.id, item.chave)
                        }
                        isDisabled={emProcesso}
                        isLoading={emProcesso}
                      />
                    ) : (
                      <Button
                        label={TEXTOS_JORNADA.consentimentos.conceder}
                        variant="primary"
                        onClick={() => handleConceder(item.chave)}
                        isDisabled={emProcesso}
                        isLoading={emProcesso}
                      />
                    )}
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {onAvancar && (
        <div className="flex justify-end pt-4">
          <Button
            label={TEXTOS_JORNADA.consentimentos.avancarCurriculo}
            variant="primary"
            onClick={onAvancar}
          />
        </div>
      )}
    </div>
  );
}
