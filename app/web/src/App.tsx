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
import {MatrizPixels} from './visual/MatrizPixels';

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
        <div className="min-h-screen bg-[#F2F2F2] text-[#000091] flex flex-col w-full">
          {/* Cabeçalho em faixa azul #0000F2 com matriz de pixels */}
          <header className="relative w-full bg-[#0000F2] text-[#F2F2F2] border-b border-[#000091] overflow-hidden">
            {/* Matriz de pixels decorativa (three.js) ao fundo/à direita */}
            <div className="absolute inset-0 pointer-events-none overflow-hidden">
              <MatrizPixels
                tamanhoCelula={12}
                className="w-full h-full opacity-80 [mask-image:linear-gradient(to_right,rgba(0,0,0,0.12)_0%,rgba(0,0,0,0.12)_42%,rgba(0,0,0,1)_75%)]"
              />
            </div>

            <div className="relative mx-auto flex max-w-6xl flex-col gap-2 px-4 py-8 sm:px-6 sm:py-10 z-10 w-full">
              <Heading
                level={1}
                className="!text-[#F2F2F2] !font-['Barlow_Condensed'] text-4xl sm:text-6xl md:text-7xl font-semibold tracking-[-0.02em] leading-none"
              >
                CitizenTech
              </Heading>
              <p className="text-sm sm:text-base text-[#F5F5F5] font-['Barlow_Semi_Condensed'] max-w-2xl font-normal opacity-95">
                Compare caminhos de transição de carreira com evidências do mercado formal.
              </p>
            </div>
          </header>

          {/* Barra clara de abas colada à faixa */}
          <div className="w-full bg-[#FFFFFF] border-b border-[#616191]/20 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
            <div className="mx-auto max-w-6xl px-4 sm:px-6 w-full">
              <TabList value={aba} onChange={setAba} role="tablist">
                <Tab value="mercado" label="Mercado" panelId="painel-mercado" />
                <Tab value="painel_tecnico" label="Painel técnico" panelId="painel-tecnico" />
                <Tab value="jornada" label="Minha transição" panelId="painel-jornada" />
              </TabList>
            </div>
          </div>

          {/* Área de conteúdo com largura máxima confortável (~1200px) e respiro */}
          <main className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8 w-full min-w-0 flex-1">
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
        </div>
      </Theme>
    </InternationalizationProvider>
  );
}
