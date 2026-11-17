# QA de teclado e foco — 17/11/2026

**Natureza:** sondagem executada pelo agente com Playwright (Edge headless) contra a API local de **teste** (bancos de teste, segredos efêmeros) e o Vite em `localhost:5173`. Script descartável fora do repositório (`.kaiser/tmp/qa_teclado.spec.ts`); nenhum arquivo do app foi alterado. **Não** é auditoria WCAG completa nem teste com leitor de tela; complementa o axe já registrado no [aceite S15](<20261116_s15_e2e_aceite.md>).

## O que foi feito

Navegação só com `Tab`, `Enter` e `Space`, registrando o elemento focado e o estilo de foco calculado (`outline`/`box-shadow`) em cada passo.

| Tela | Tabs | Elementos distintos | Sem indicador visível de foco |
|---|---:|---:|---|
| Mercado | 20 | 5 | 2 elementos: seletores **Destino profissional** e **UF** (`outline: none`, sem sombra) |
| Entrar | 12 | 6 | 2 elementos: campos **E-mail** e **Senha** — só a borda escurece levemente |
| Consentimentos | 15 | 12 | nenhum |
| Intenção | 25 | 19 | nenhum |

Fluxo funcional por teclado (passou): criar conta preenchendo o formulário e enviando com `Enter`; conceder autorização com `Space` e com `Enter`; avançar de etapa com `Enter`. Ao trocar de etapa, o foco vai para o título da nova etapa ("Intenção profissional"). Ordem de tabulação segue a ordem visual; a navegação de etapas tem 7 botões com nome acessível ("Ir para a etapa N: …").

## Achado

**Indicador de foco fraco ou ausente** nos seletores da tela Mercado e nos campos de login (WCAG 2.4.7 *Foco visível*). Capturas em `.kaiser/tmp/foco_mercado_*.png` e `foco_entrar_*.png` (fora do Git). O axe não acusa isso porque a regra não é automatizável.

**Corrigido em 17/11 à tarde** (aprovação do usuário), no redesign S16 (merge `48be785`): anel `:focus-visible` de 2px `#000091` com deslocamento de 2px em todos os controles (`#F2F2F2` sobre o azul do cabeçalho). Teste automatizado `app/web/e2e/foco_visivel.spec.ts`: **RED reproduzido em main antes da correção** ("Selector Destino: Elemento focado sem indicador visível (outline: none 3px, shadow: none)"; idem "Campo E-mail") e **GREEN depois**; suíte E2E completa e axe sem violações sérias/críticas nas 11 telas + modal.

## Não verificado

Leitor de tela (NVDA/Narrador), zoom 200%/reflow, contraste em modo de alto contraste do Windows, e as telas Currículo, Competências, Comparação, Plano, Exercício/Discordo e Laboratório por teclado.
