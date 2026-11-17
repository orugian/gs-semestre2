# Direção visual — aplicação web CitizenTech

<!-- impeccable:design-schema 1 -->

> Escopo: `app/web` (React 19 + Astryx 0.7.14 + Tailwind só para layout, D16a). A direção do panorama offline está em `docs/panorama/DESIGN.md` e vale só para `docs/panorama_projeto.html`.
> Fonte: design system **NOUS** (`DESIGN-SYSTEMS/NOUS/DESIGN.md`, extraído do Nous Portal), adotado por pedido do usuário em 17/11/2026.

## Mundo

Campo azul elétrico, tipografia condensada alta, linhas finas e um único momento de movimento: uma **matriz de pixels** (three.js) no cabeçalho, como um painel de sinalização que mostra o pulso de uma série. A superfície de trabalho é clara e silenciosa. Modo: **Operate** — a pessoa compara dados e conclui etapas; precisão e contenção vencem decoração.

## Cores (somente as medidas no NOUS)

| Token | Valor | Uso |
|---|---|---|
| `--ct-azul` (`surface`) | `#0000F2` | faixa do cabeçalho/rodapé, série observada, ação primária |
| `--ct-marinho` (`primary`) | `#000091` | texto forte sobre claro, foco, estado ativo, série prevista |
| `--ct-papel` (`surface-alt`) | `#F2F2F2` | fundo da área de trabalho; texto sobre azul |
| `--ct-branco` (`ink-secondary`) | `#FFFFFF` | painéis de conteúdo |
| `--ct-tinta` (`ink`) | `#F5F5F5` | texto corrido sobre azul |
| `--ct-linha` (`hairline`) | `#616191` | texto secundário sobre claro, divisórias |

Contrastes calculados (WCAG): `#F2F2F2` sobre `#0000F2` 8,22:1; `#000091` sobre `#F2F2F2` 13,31:1; `#0000F2` sobre `#FFFFFF` 9,2:1; `#616191` sobre `#F2F2F2` 5,17:1 e sobre `#FFFFFF` 5,79:1.

**Exceção declarada:** estados semânticos (erro, aviso, sucesso) continuam com as cores do tema Astryx, porque o NOUS não mediu nenhuma e eles carregam significado (falha, abstenção, requisito não atendido). Nunca são usados como decoração.

## Tipografia

As famílias do NOUS (Rules Gothic, Aeonik Fono) são comerciais e não podem ser distribuídas. Substitutas auto-hospedadas (`@fontsource`, licença OFL), escolhidas pelo mesmo caráter:

| Papel NOUS | Substituta | Uso |
|---|---|---|
| Rules Gothic Condensed / Compressed (display) | **Barlow Condensed** 500/600 | títulos, números grandes |
| Rules Condensed (body) | **Barlow Semi Condensed** 400/500 | texto corrido e controles |
| Aeonik Fono (caption) | **IBM Plex Mono** 400 | metadados, rótulos de natureza, eixos e tabelas numéricas |

Escala: display 56–80px (só no cabeçalho), h2 32px, h3 20px, corpo 16px/1.6, apoio 13px, legenda 12px. Tracking de display −0,02em. Algarismos tabulares em tabelas e eixos.

## Forma e profundidade

Raios 2–5px (`rounded.xs`–`lg`). Elevação por **anel interno de 1px** (sombra medida `inset 0 0 0 1px` azul a 20%), nunca sombra difusa com borda. Sem cartões aninhados.

## Foco

`:focus-visible` com contorno **2px sólido `#000091`, deslocamento 2px** em todo controle sobre fundo claro, e `#F2F2F2` sobre o azul. Inclui seletores, campos, abas, etapas e botões (corrige WCAG 2.4.7 registrado em 17/11).

## Movimento

- Um momento autoral: a matriz de pixels do cabeçalho, renderizada em baixa resolução e ampliada com `image-rendering: pixelated`; responde levemente ao ponteiro.
- Carregada sob demanda (`import()` de three.js), pausada fora da tela e com a aba oculta; `aria-hidden`.
- `prefers-reduced-motion: reduce` → um quadro estático. Sem WebGL → padrão de pixels em CSS.
- Microinterações de 120–200ms com `cubic-bezier(0.16, 1, 0.3, 1)` (troca de etapa, hover, abertura de detalhes). Nada de entrada idêntica em todas as seções.

## Linguagem honesta (T17)

Natureza do dado sempre em rótulo de texto (Observado / Estimativa retrospectiva / Amostra pontual), nunca só por cor. Séries distinguidas por cor **e** por traço/marcador.
