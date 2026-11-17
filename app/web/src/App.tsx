import {useEffect, useState} from 'react';
import {Heading} from '@astryxdesign/core/Heading';
import {TabList, Tab} from '@astryxdesign/core/TabList';
import {InternationalizationProvider} from '@astryxdesign/core/i18n';
import ptBR from '@astryxdesign/core/locales/pt-BR.generated.js';
import {Theme} from '@astryxdesign/core/theme';
import {neutralTheme} from '@astryxdesign/theme-neutral/built';
import {formatarUrlNavegacao, lerEstadoUrl} from './mercado/formatacao';
import {TelaMercado} from './mercado/TelaMercado';
import {PainelTecnico} from './mercado/PainelTecnico';
import {AreaJornada} from './jornada/AreaJornada';

export default function App() {
  const [inicial] = useState(() => {
    if (typeof window !== 'undefined') {
      return lerEstadoUrl(window.location.search, window.location.hash);
    }
    return {aba: 'mercado' as const, destino: 'analista_dados_bi', uf: 'SP'};
  });

  const [aba, setAba] = useState<string>(inicial.aba);
  const [destino, setDestino] = useState<string>(inicial.destino);
  const [uf, setUf] = useState<string>(inicial.uf);

  // Sincroniza estado na URL com history.replaceState
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const novaUrl = formatarUrlNavegacao(
        {aba: aba as 'mercado' | 'painel_tecnico' | 'jornada', destino, uf},
        window.location.pathname || '/'
      );
      const urlAtual = `${window.location.pathname || '/'}${window.location.search}${window.location.hash}`;
      if (novaUrl !== urlAtual) {
        window.history.replaceState(null, '', novaUrl);
      }
    }
  }, [aba, destino, uf]);

  // Atualiza estado interno caso a URL mude via navegação do histórico
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const onLocationChange = () => {
      const atualizado = lerEstadoUrl(window.location.search, window.location.hash);
      setAba(atualizado.aba);
      setDestino(atualizado.destino);
      setUf(atualizado.uf);
    };

    window.addEventListener('popstate', onLocationChange);
    window.addEventListener('hashchange', onLocationChange);
    return () => {
      window.removeEventListener('popstate', onLocationChange);
      window.removeEventListener('hashchange', onLocationChange);
    };
  }, []);

  return (
    <InternationalizationProvider locale="pt-BR" messages={{'pt-BR': ptBR}}>
    <Theme theme={neutralTheme}>
      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 sm:p-6 w-full max-w-full min-w-0">
        <header className="flex flex-col gap-2">
          <Heading level={1}>CitizenTech</Heading>
        </header>

        <TabList value={aba} onChange={setAba} role="tablist">
          <Tab value="mercado" label="Mercado" panelId="painel-mercado" />
          <Tab value="painel_tecnico" label="Painel técnico" panelId="painel-tecnico" />
          <Tab value="jornada" label="Minha transição" panelId="painel-jornada" />
        </TabList>

        {aba === 'mercado' ? (
          <TelaMercado
            destino={destino}
            onDestinoChange={setDestino}
            uf={uf}
            onUfChange={setUf}
          />
        ) : aba === 'painel_tecnico' ? (
          <PainelTecnico
            destino={destino}
            onDestinoChange={setDestino}
            uf={uf}
            onUfChange={setUf}
          />
        ) : (
          <section id="painel-jornada" role="tabpanel" aria-label="Minha transição">
            <AreaJornada />
          </section>
        )}
      </main>
    </Theme>
    </InternationalizationProvider>
  );
}
