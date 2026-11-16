import {useEffect, useRef, useState} from 'react';
import {Badge} from '@astryxdesign/core/Badge';
import {Button} from '@astryxdesign/core/Button';
import {Heading} from '@astryxdesign/core/Heading';
import {Spinner} from '@astryxdesign/core/Spinner';
import {Step, Stepper} from '@astryxdesign/core/Stepper';
import {Text} from '@astryxdesign/core/Text';
import {ErroApi} from '../api/cliente';
import {RespostaExtracao} from '../api/competencias';
import {obterMe, sair, Usuario} from '../api/conta';
import {TelaComparacao} from './TelaComparacao';
import {TelaCompetencias} from './TelaCompetencias';
import {TelaConsentimentos} from './TelaConsentimentos';
import {TelaCurriculo} from './TelaCurriculo';
import {TelaEntrar} from './TelaEntrar';
import {TelaIntencao} from './TelaIntencao';
import {TEXTOS_JORNADA} from './textos';

export function AreaJornada() {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregandoUsuario, setCarregandoUsuario] = useState(true);
  const [avisoSessao, setAvisoSessao] = useState<string | null>(null);

  const [etapaAtiva, setEtapaAtiva] = useState(0);
  const [extracao, setExtracao] = useState<RespostaExtracao | null>(null);

  const tituloEtapaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelado = false;
    setCarregandoUsuario(true);

    obterMe()
      .then((dados) => {
        if (!cancelado) {
          setUsuario(dados);
          setAvisoSessao(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelado) {
          setUsuario(null);
          if (err instanceof ErroApi && err.status === 401) {
            // Sessão ainda não iniciada - comportamento normal
          }
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
      setAvisoSessao(null);
      setEtapaAtiva(0);
      setExtracao(null);
    }
  };

  const handleLoginSucesso = (usr: Usuario) => {
    setUsuario(usr);
    setAvisoSessao(null);
    setEtapaAtiva(0);
  };

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
        avisoSessao={avisoSessao}
      />
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full max-w-5xl mx-auto">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 p-4 border rounded">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-3 flex-wrap">
            <Heading level={2}>{TEXTOS_JORNADA.titulo}</Heading>
            {usuario.persona_demo === 'S' && (
              <Badge variant="purple" label={TEXTOS_JORNADA.personaDemo} />
            )}
          </div>
          <Text type="supporting">{usuario.email}</Text>
        </div>

        <div className="flex items-center gap-2">
          <Button
            label={TEXTOS_JORNADA.sair}
            variant="secondary"
            onClick={handleLogout}
          />
        </div>
      </header>

      <nav aria-label="Etapas da jornada">
        <Stepper activeStep={etapaAtiva} onStepClick={setEtapaAtiva}>
          <Step step={0} label={TEXTOS_JORNADA.etapas.consentimentos} />
          <Step step={1} label={TEXTOS_JORNADA.etapas.intencao} />
          <Step step={2} label={TEXTOS_JORNADA.etapas.curriculo} />
          <Step step={3} label={TEXTOS_JORNADA.etapas.competencias} />
          <Step step={4} label={TEXTOS_JORNADA.etapas.comparacao} />
        </Stepper>
      </nav>

      <div
        ref={tituloEtapaRef}
        tabIndex={-1}
        className="outline-none flex flex-col gap-4"
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
          <TelaComparacao />
        )}
      </div>
    </div>
  );
}
