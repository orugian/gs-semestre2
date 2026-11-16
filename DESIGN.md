# Direção Visual — Documentação CitizenTech

<!-- impeccable:design-schema 1 -->

## Escopo e Contexto

Este documento define as decisões de design, tokens e padrões de interação aplicados exclusivamente ao artefato **`docs/panorama_projeto.html`**, caderno de orientação visual e continuidade do projeto CitizenTech (FIAP Global Solution 2026.2).

Não altera o frontend da aplicação web (`app/web`), nem seus componentes React/Tailwind. As decisões de produto permanecem ancoradas em `PRODUCT.md` e `docs/plano_desenvolvimento.md`.

## Acabamentos e limites do aceite

- Ação principal logo após o propósito; no mobile, ações secundárias repetidas ficam só na navegação.
- Cabeçalhos dos nós empilham nome e estado para evitar palavras quebradas; conectores e separadores usam `slate-600`.
- Contador da aba ativa usa `slate-900`, eliminando o contraste insuficiente da transparência anterior.
- Sem JavaScript, nove painéis e nove âncoras permanecem disponíveis; controles inertes são ocultados.
- Contraste/tipografia foram medidos nos estados exercitados. Isso não constitui auditoria WCAG integral, teste físico de toque ou regressão do aplicativo.

## Diagnóstico e Evolução (Rodada 2)

A versão inicial foi rejeitada por densidade excessiva (5.376 palavras expostas no documento, tabela com rolagem lateral forçada e diagramas comprimidos).
Na Rodada 2, as correções estritas eliminaram os seguintes defeitos materiais detectados em testes reais com navegadores:
1. **Tipografia:** Eliminação total de fontes abaixo de 12px real; aplicação de `max(12px, 0.85em)` em `code`/`pre` e mínimo de 12px em rótulos, metadados e contadores.
2. **Contraste WCAG AA (≥ 4.5:1):** Correção do rodapé da barra lateral (`#cbd5e1` sobre `#0f172a`, atingindo 12.0:1) e de elementos de etapa sobre fundo claro (`#334155`/`#475569` sobre `#ffffff`, atingindo 7.6:1 a 10.4:1).
3. **Bordas Estruturais (≤ 1px):** Remoção de todas as bordas laterais e superiores de 3px e 4px nos nós e cartões; diferenciação visual realizada por fundo sutil, tipografia e badges temáticos.
4. **Foco Acessível:** Supressão do contorno azul retangular nos títulos `<h2>` programaticamente focados após navegação (`outline: none`), mantendo anéis de foco nítidos de 2px exclusivamente nos controles interativos (`:focus-visible`).
5. **Ícones Vetoriais:** Substituição integral de emojis e glifos (`✓`, `○`, `📄`, `👤`, `•`) por ícones vetoriais SVG padronizados e texto conciso.
6. **Navegação Móvel em Grade:** Substituição da barra móvel com rolagem lateral por uma grade de 2 linhas exibindo todos os 5 rótulos de área sem necessidade de rolagem ou pan horizontal.
7. **Simplificação de Disciplinas:** Remoção do filtro de status redundante (evitando descompasso de estado com teclado, seleção móvel e deep links diretos) e eliminação de cartões aninhados no detalhe da matéria, consolidando tarefas humanas em uma única faixa violeta integrada.

## Direção Confirmada: Roteiro de Orientação por Camadas

- **Identificador:** Direção 4 do conjunto fundamentado (`seed:a6b2ec02977de17f`).
- **Conceito:** Interface de orientação técnica baseada em camadas progressivas de informação. A interface expõe uma única área contextual por vez, permitindo ao usuário transitar entre Visão Geral, Arquitetura e Sistema, Disciplinas, Próximos Passos e Fontes.

## Arquitetura da Informação e Navegação

O panorama organiza-se em **cinco áreas temáticas**:
1. **Visão geral (`#visao-geral`):** Propósito essencial do CitizenTech em lead curto (≤ 35 palavras), faixa tripartite de maturidade visual ("Já funciona", "Em construção", "Para entregar"), frentes em execução imediata, nota explícita de governança e ações rápidas. Contagem estrita inferior a 400 palavras visíveis no primeiro viewport.
2. **Sistema (`#sistema`):** Duas leituras complementares: (a) jornada do usuário em 6 etapas cronológicas com conectores direcionais; (b) arquitetura em 3 fluxos colapsáveis via `<details>` nativos (Mercado, Pessoa e Sensores), com conectores vetoriais SVG reais e reflow vertical no mobile. Destaca a separação entre ciência offline e serving, o armazenamento seguro de texto redigido no MongoDB (não documento bruto) e o gate obrigatório de consentimento antes da LLM.
3. **Disciplinas (`#disciplinas`):** Padrão Mestre/Detalhe puro com 9 matérias acessíveis por lista lateral no desktop e `<select>` nativo no mobile. O painel ativo organiza-se em 3 colunas limpas ("Já existe", "Falta fechar", "Arquivos e evidências") e uma faixa violeta de fechamento ("Precisa de você").
4. **Próximos passos (`#proximos-passos`):** Três trilhas operacionais independentes: "Em andamento" (S10 e S4), "Depois" (sequência de integração da jornada) e "Com a equipe" (tarefas acadêmicas humanas: nomes/RMs, Data Modeler, 4 prints AWS §82–86, 5 vídeos acadêmicos e envio no Portal).
5. **Fontes (`#fontes`):** Repositório de referências documentais, enunciados oficiais, notas de auditoria do snapshot e tabelas de resultados científicos (ML, RNA e Estatística D11) recolhidas em `<details>`, com unidades métricas precisas e diagnósticos de ajuste.

### Regras de Comportamento e Interação

- **Exibição única:** Apenas uma das 5 áreas fica visível por vez na visualização interativa com JS ativo.
- **Deep Linking e Histórico:** Sincronização bidirecional com o hash da URL (`#visao-geral`, `#sistema`, `#disciplinas`, `#proximos-passos`, `#fontes` e `#disc-01` a `#disc-09`), suportando histórico Back/Forward (`popstate` e `hashchange`).
- **Navegação por Teclado:** Suporte completo na lista de disciplinas via `ArrowDown`, `ArrowUp`, `Home` e `End`, com seleção e foco sincronizados.
- **Fallback sem JavaScript:** Sem JS ativo, o documento renderiza todas as seções de forma sequencial e acessível com âncoras locais.

## Sistema de Tokens e Componentes

### 1. Paleta de Cores e Contraste

- **Fundos e Estrutura:**
  - Trilho lateral (Desktop): Slate 900 (`#0f172a`) e Slate 800 (`#1e293b`)
  - Fundo geral da página: Slate 50 (`#f8fafc`)
  - Superfícies de cartões e painéis: Branco puro (`#ffffff`)
  - Bordas estruturais (todas ≤ 1px): Slate 200 (`#e2e8f0`) e Slate 300 (`#cbd5e1`)
- **Tipografia:**
  - Texto primário sobre claro: Slate 900 (`#0f172a`) — Contraste 17.8:1
  - Texto secundário sobre claro: Slate 700 (`#334155`) — Contraste 10.3:1
  - Texto atenuado sobre claro: Slate 600 (`#475569`) — Contraste 7.6:1
  - Texto sobre fundo escuro (`#0f172a`): Branco (`#ffffff`, 17.8:1), Slate 200 (`#e2e8f0`, 14.3:1) e Slate 300 (`#cbd5e1`, 12.0:1)
- **Cores Semânticas de Estado (Todas WCAG AA ≥ 4.5:1):**
  - **Integrado / Base integrada:** Fundo `#dcfce7`, Borda `#86efac`, Texto `#14532d` (Contraste 8.3:1), Destaque `#15803d`
  - **Em andamento:** Fundo `#fef3c7`, Borda `#fde047`, Texto `#78350f` (Contraste 8.1:1), Destaque `#b45309`
  - **Pacote gerado / Ciência:** Fundo `#dbeafe`, Borda `#93c5fd`, Texto `#1e3a8a` (Contraste 8.5:1), Destaque `#2563eb`
  - **Ação humana (Equipe):** Fundo `#f3e8ff`, Borda `#d8b4fe`, Texto `#581c87` (Contraste 9.2:1), Destaque `#7c3aed`
  - **Planejado / Pendente:** Fundo `#f1f5f9`, Borda `#cbd5e1`, Texto `#0f172a` (Contraste 16.3:1), Destaque `#475569`

### 2. Tipografia e Escala

- **Família sans:** `"Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif`
- **Família mono:** `"Cascadia Code", "Consolas", "Courier New", monospace`
- **Escala de Tamanhos (Nunca abaixo de 12px):**
  - H1: 2rem a 2.25rem (32–36px desktop / 28px mobile), peso 700
  - H2: 1.5rem (24px), peso 700
  - H3: 1.125rem a 1.25rem (18–20px), peso 700
  - Lead: 1.0625rem (17px), entrelinha 1.6
  - Corpo padrão: 1rem (16px), entrelinha 1.5
  - Cartões e botões: 14px, peso 500–600
  - Metadados, listas e legendas: 13px, entrelinha 1.45
  - Badges, contadores, tags e mono: 12px (mínimo absoluto)
  - `code` / `pre`: `max(12px, 0.85em)`

### 3. Layout e Responsividade

- **Desktop (≥ 1025px):** Trilho lateral fixo de 240px; área de conteúdo com padding de 32px 40px e largura máxima de 1180px.
- **Tablet (641px a 1024px):** Cabeçalho móvel aderente no topo com navegação em 2 linhas de botões (3 + 2); lista de disciplinas alternada para `<select>` nativo; colunas adaptadas para 1 coluna vertical.
- **Mobile (360px a 640px):** Cabeçalho compacto com os 5 botões de área 100% visíveis sem pan ou rolagem horizontal; nós dos fluxos de arquitetura reorganizados verticalmente com setas SVG giradas em 90 graus (`↓`); padding confortável de 16px lateral; toque mínimo de 44×44px em todos os controles.

### 4. Acessibilidade

- Alvos táteis: Dimensão mínima de 44×44px garantida em todos os links de navegação, botões de abas e seletores nativos.
- Foco visual: `:focus-visible` com `outline: 2px solid var(--blue-accent); outline-offset: 2px`.
- Landmarks semânticos: `<header>`, `<aside>`, `<nav>`, `<main>`, `<section>`, `<details>`, `<summary>` e `<select>`.
- Semântica ARIA: `aria-current="page"` na navegação de área ativa, `role="tablist"` e `role="tab"` na lista de disciplinas, `aria-selected` no item ativo.
