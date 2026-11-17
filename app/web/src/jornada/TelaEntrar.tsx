import {FormEvent, useState} from 'react';
import {Banner} from '@astryxdesign/core/Banner';
import {Button} from '@astryxdesign/core/Button';
import {Card} from '@astryxdesign/core/Card';
import {Heading} from '@astryxdesign/core/Heading';
import {Text} from '@astryxdesign/core/Text';
import {TextInput} from '@astryxdesign/core/TextInput';
import {mensagemDeErro} from '../api/cliente';
import {entrar, obterMe, registrar, Usuario} from '../api/conta';
import {TEXTOS_JORNADA} from './textos';

export interface TelaEntrarProps {
  onLoginSucesso: (usuario: Usuario) => void;
}

export function TelaEntrar({onLoginSucesso}: TelaEntrarProps) {
  const [modo, setModo] = useState<'entrar' | 'criar'>('entrar');
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [carregando, setCarregando] = useState(false);
  const [mensagemErro, setMensagemErro] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setMensagemErro(null);

    const emailLimpo = email.trim();
    if (!emailLimpo) {
      setMensagemErro('Informe seu e-mail.');
      return;
    }

    if (senha.length < 10) {
      setMensagemErro(TEXTOS_JORNADA.auth.senhaCurta);
      return;
    }

    setCarregando(true);
    try {
      if (modo === 'criar') {
        await registrar(emailLimpo, senha);
      }
      await entrar(emailLimpo, senha);
      const usuario = await obterMe();
      onLoginSucesso(usuario);
    } catch (err: unknown) {
      setMensagemErro(mensagemDeErro(err, TEXTOS_JORNADA.auth.erroGenericoLogin));
    } finally {
      setCarregando(false);
    }
  };

  const alternarModo = () => {
    setModo((atual) => (atual === 'entrar' ? 'criar' : 'entrar'));
    setMensagemErro(null);
  };

  return (
    <div className="flex flex-col items-center justify-center p-4 w-full">
      <Card width="100%" maxWidth={480}>
        <div className="flex flex-col gap-5 p-6">
          <header className="flex flex-col gap-1">
            <Heading level={2} className="!font-['Barlow_Condensed'] font-semibold text-2xl tracking-tight text-[#000091]">
              {modo === 'entrar'
                ? TEXTOS_JORNADA.auth.entrar
                : TEXTOS_JORNADA.auth.criarConta}
            </Heading>
            <Text type="supporting" className="text-sm text-[#616191]">
              {modo === 'entrar'
                ? 'Acesse sua área da jornada para gerenciar currículo e competências.'
                : 'Cadastre-se para iniciar o mapeamento de competências com privacidade.'}
            </Text>
          </header>

          {mensagemErro && (
            <div role="alert" aria-live="polite">
              <Banner
                status="error"
                title="Não foi possível prosseguir"
                description={mensagemErro}
              />
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <TextInput
              label={TEXTOS_JORNADA.auth.email}
              type="email"
              value={email}
              onChange={(val) => setEmail(val)}
              autoComplete="email"
              isRequired
              isDisabled={carregando}
              placeholder="seu.email@exemplo.com"
            />

            <TextInput
              label={TEXTOS_JORNADA.auth.senha}
              type="password"
              value={senha}
              onChange={(val) => setSenha(val)}
              autoComplete={modo === 'entrar' ? 'current-password' : 'new-password'}
              isRequired
              isDisabled={carregando}
              description="Mínimo de 10 caracteres."
            />

            <div className="flex flex-col gap-3 pt-2">
              <Button
                type="submit"
                variant="primary"
                label={
                  modo === 'entrar'
                    ? TEXTOS_JORNADA.auth.entrar
                    : TEXTOS_JORNADA.auth.criarConta
                }
                isDisabled={carregando}
                isLoading={carregando}
              />

              <Button
                type="button"
                variant="ghost"
                label={
                  modo === 'entrar'
                    ? TEXTOS_JORNADA.auth.alternarParaCriar
                    : TEXTOS_JORNADA.auth.alternarParaEntrar
                }
                onClick={alternarModo}
                isDisabled={carregando}
              />
            </div>
          </form>
        </div>
      </Card>
    </div>
  );
}
