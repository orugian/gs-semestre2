# Direção visual — documentação CitizenTech

## Escopo

Somente `docs/panorama_projeto.html`, caderno interno offline confirmado pelo usuário em16/11/2026. Não redefine a identidade do app nem altera React/Astryx/Tailwind. Produto e decisões permanecem em PRODUCT.md e no plano aprovado.

## Cena e modo

Modo Read: equipe e próximo desenvolvedor consultam um retrato do projeto no notebook ou telefone, em ambiente de trabalho iluminado, e precisam encontrar em segundos a fronteira entre feito, verificado e futuro. Superfície clara, contraste alto e impressão legível; não console de operação ao vivo.

## Direção

Caderno orientado por mapa: leitura editorial, índice lateral e uma figura central da arquitetura. Dados científicos aparecem como resultados com unidades/coorte, não como troféus. A matriz de disciplinas é o índice de obrigações, não uma coleção de cartões.

O contexto Impeccable foi carregado uma vez; seed de direção Read registrado na trilha com chave6a1602ee7c080b819fdc0fa3fcff4354, índice6. As referências culturais consideradas: caderno de revisão técnica, memorial de engenharia, atlas de evidências, parecer de conformidade, boletim de projeto, guia curatorial de visita e programa de congresso. A direção6 é traduzida em mapa numerado+legendas+fontes, respeitando o caderno pedido, não decoração de museu.

Referências desafiantes examinadas pelo texto de sistema, não por imagens: patente(competitiva na clareza do mapa, menos identificável para leitura geral); console escuro(recusado: aparentaria ferramenta ao vivo); seção de luz(recusada: variáveis físicas estranhas à tarefa); borda iridescente(recusada: cor sem função factual); trilho de edição(recusado: operação/movimento desnecessários). Disciplina retida: referências precisas por componente, separação por linhas e marco de parada explícito; sem copiar suas aparências. O caderno foi a escolha confirmada; não é rodada de branding.

## Tipografia e hierarquia

- Corpo Segoe UI/Arial/system sans, base17px, entrelinha1,6 e medida≤72ch.
- Títulos editoriais Georgia/serif local; H1≤64px desktop,36–42px mobile. Não depende de fonte remota.
- Monoespaçada só em caminhos, commits e medidas; números tabulares nos resultados.
- Sem kicker/eyebrow acima dos títulos, sem hero de métricas, gradiente, glass, textura gratuita, emojis ou cartões iguais como estrutura.

## Superfícies e estados

- Papel branco/cinza frio muito claro; tinta azul-noite; verde escuro apenas para verificado, âmbar escuro para gates e pendências.
- Status sempre por palavra além da cor: verificado, parcial, planejado, dependência humana.
- Separação por régua fina e respiro; sem grandes bordas laterais coloridas, sombra decorativa ou grid de fundo.
- Diagrama exato, sem ilustração figurativa. Aresta tracejada significa integração pendente e deve ter legenda textual.

## Composição e comportamento

- Cabeçalho de marca+snapshot; índice lateral desktop e navegação compacta mobile.
- Visão rápida → arquitetura → estado técnico → resultados →9disciplinas → próximos gates → fontes.
- Informações densas usam tabela com caption e cabeçalhos; em mobile, região de rolagem identificada quando necessária, nunca overflow do documento inteiro.
- Âncoras e links locais reais; detalhes nativos opcionais. Nenhum script, fetch, CDN, formulário, botão falso ou contador vivo.
- Foco visível, alvo de navegação≥44px, skip link, seleção temática; preferência por movimento reduzido respeitada. Sem animação necessária à leitura.
- Print: navegação escondida, corpo em fluxo, tabelas e legendas preservadas.

## Provas exigidas

Todos os números vêm das evidências existentes e têm natureza/temporalidade explícitas. Nenhum aluno/RM/segredo é replicado. Não abrir dados ou holdout para gerar o panorama. Verificar links, semântica e limites; renderizar em Edge desktop e mobile, inspecionar screenshots e executar detector Impeccable uma vez sobre o alvo pronto. Isso não é auditoriaWCAG integral nem testeE2E do produto.
