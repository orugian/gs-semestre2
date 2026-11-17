import {useEffect, useRef, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Button} from '@astryxdesign/core/Button';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Step, Stepper} from '@astryxdesign/core/Stepper';
import {Text} from '@astryxdesign/core/Text';
import {RespostaExtracao} from '../api/competencias';
import {obterMe, sair, Usuario} from '../api/conta';
import {obterPlano, RespostaCaminho} from '../api/plano';
import {TelaComparacao} from './TelaComparacao';
import {TelaCompetencias} from './TelaCompetencias';
import {TelaConsentimentos} from './TelaConsentimentos';
import {TelaCurriculo} from './TelaCurriculo';
import {TelaEntrar} from './TelaEntrar';
import {TelaExercicio} from './TelaExercicio';
import {TelaIntencao} from './TelaIntencao';
import {TelaLaboratorio} from './TelaLaboratorio';
import {TelaPlano} from './TelaPlano';
import {TEXTOS_JORNADA} from './textos';

export function AreaJornada() {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregandoUsuario, setCarregandoUsuario] = useState(true);

  const [etapaAtiva, setEtapaAtiva] = useState(0);
  const [extracao, setExtracao] = useState<RespostaExtracao | null>(null);
  const [planoAtivo, setPlanoAtivo] = useState<RespostaCaminho | null>(null);

  const tituloEtapaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregandoUsuario(true);

    obterMe()
      .then((dados) => {
        if (!cancelado) {
          setUsuario(dados);

          // Carrega o plano ativo se houver (404 = sem plano)
          obterPlano()
            .then((respPlano) => {
              if (!cancelado && respPlano && respPlano.plano) {
                setPlanoAtivo(respPlano);
              }
            })
            .catch(() => {
              if (!cancelado) {
                setPlanoAtivo(null);
              }
            });
        }
      })
      .catch(() => {
        if (!cancelado) {
          setUsuario(null);
          setPlanoAtivo(null);
        }
      })
      .finally(() => {
        if (!cancelado) {
          setCarregandoUsuario(false);
        }
      });

    return () => {
      cancelado = true;
    };
  }, []);

  // Foco movido para o título da etapa ao avançar (A11y)
  useEffect(() => {
    if (usuario) {
      tituloEtapaRef.current?.focus();
    }
  }, [etapaAtiva, usuario]);

  const handleLogout = async () => {
    try {
      await sair();
    } catch {
      // Ignora erro no logout
    } finally {
      setUsuario(null);
      setEtapaAtiva(0);
      setExtracao(null);
      setPlanoAtivo(null);
    }
  };

  const handleLoginSucesso = (usr: Usuario) => {
    setUsuario(usr);
    setEtapaAtiva(0);
    obterPlano()
      .then((resp) => {
        if (resp && resp.plano) setPlanoAtivo(resp);
      })
      .catch(() => setPlanoAtivo(null));
  };

  const mostrarLaboratorio =
    planoAtivo?.destino_id === 'analista_monitoramento_iot';

  if (carregandoUsuario) {
    return (
      <div className="flex items-center justify-center p-12" aria-live="polite">
        <Spinner label="Verificando autenticação..." />
      </div>
    );
  }

  if (!usuario) {
    return (
      <TelaEntrar
        onLoginSucesso={handleLoginSucesso}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 rounded bg-[#FFFFFF] shadow-[inset_0_0_0_1px_rgba(0,0,242,0.15)]">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3 flex-wrap">
            <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl tracking-tight text-[#000091]">
              {TEXTOS_JORNADA.titulo}
            </Heading>
            {usuario.persona_demo === 'S' && (
              <Badge variant="purple" label={TEXTOS_JORNADA.personaDemo} />
            )}
          </div>
          <Text type="supporting" className="text-xs text-[#616191]">{usuario.email}</Text>
        </div>

        <div className="flex items-center gap-2">
          <Button
            label={TEXTOS_JORNADA.sair}
            variant="secondary"
            onClick={handleLogout}
          />
        </div>
      </header>

      <nav aria-label="Etapas da jornada" className="w-full overflow-x-auto py-1">
        <Stepper activeStep={etapaAtiva} onStepClick={setEtapaAtiva}>
          <Step step={0} label={TEXTOS_JORNADA.etapas.consentimentos} />
          <Step step={1} label={TEXTOS_JORNADA.etapas.intencao} />
          <Step step={2} label={TEXTOS_JORNADA.etapas.curriculo} />
          <Step step={3} label={TEXTOS_JORNADA.etapas.competencias} />
          <Step step={4} label={TEXTOS_JORNADA.etapas.comparacao} />
          <Step step={5} label={TEXTOS_JORNADA.etapas.plano} />
          <Step step={6} label={TEXTOS_JORNADA.etapas.exercicio} />
          {mostrarLaboratorio && (
            <Step step={7} label={TEXTOS_JORNADA.etapas.laboratorio} />
          )}
        </Stepper>
      </nav>

      <div
        ref={tituloEtapaRef}
        key={etapaAtiva}
        tabIndex={-1}
        className="outline-none flex flex-col gap-4 transicao-etapa"
      >
        {etapaAtiva === 0 && (
          <TelaConsentimentos
            onAvancar={() => setEtapaAtiva(1)}
          />
        )}

        {etapaAtiva === 1 && (
          <TelaIntencao
            onAvancar={() => setEtapaAtiva(2)}
            onIrParaConsentimentos={() => setEtapaAtiva(0)}
          />
        )}

        {etapaAtiva === 2 && (
          <TelaCurriculo
            onIrParaConsentimentos={() => setEtapaAtiva(0)}
            onSugerirSucesso={(resp) => {
              setExtracao(resp);
              setEtapaAtiva(3);
            }}
          />
        )}

        {etapaAtiva === 3 && (
          <TelaCompetencias extracaoInicial={extracao} />
        )}

        {etapaAtiva === 4 && (
          <TelaComparacao
            planoAtivo={planoAtivo}
            onDestinoEscolhido={(novoPlano) => {
              setPlanoAtivo(novoPlano);
              setEtapaAtiva(5);
            }}
            onIrParaPlano={() => setEtapaAtiva(5)}
          />
        )}

        {etapaAtiva === 5 && (
          <TelaPlano
            plano={planoAtivo}
            onPlanoAtualizado={setPlanoAtivo}
            onIrParaComparacao={() => setEtapaAtiva(4)}
            onFazerExercicio={() => setEtapaAtiva(6)}
            onIrParaLaboratorio={() => setEtapaAtiva(7)}
          />
        )}

        {etapaAtiva === 6 && (
          <TelaExercicio
            destinoId={planoAtivo?.destino_id || 'analista_monitoramento_iot'}
            onIrParaConsentimentos={() => setEtapaAtiva(0)}
            onVoltarParaPlano={() => setEtapaAtiva(5)}
          />
        )}

        {etapaAtiva === 7 && mostrarLaboratorio && (
          <TelaLaboratorio
            onIrParaConsentimentos={() => setEtapaAtiva(0)}
            onVoltarParaPlano={() => setEtapaAtiva(5)}
          />
        )}
      </div>
    </div>
  );
}
