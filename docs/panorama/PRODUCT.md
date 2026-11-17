# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

Produto: profissionais graduados e experientes comparando caminhos de transição de carreira técnica. Não é seleção de candidatos por empregadores nem recolocação automática.

Superfície documental (`docs/panorama_projeto.html`): reconstrução visual do panorama do projeto para o responsável técnico e a equipe de desenvolvimento compreenderem em segundos o propósito, a arquitetura, o estado técnico, as pendências por disciplina e os próximos passos operacionais. O formato é offline, responsivo e baseado em navegação contextual em camada única para eliminar a densidade cognitiva rejeitada na versão anterior.

## Product Purpose

O CitizenTech organiza trajetórias profissionais, distingue competências declaradas de demonstradas e apoia a comparação transparente com demandas reais do mercado de trabalho.

A superfície visual `panorama_projeto.html` é um guia interno de orientação e continuidade técnica. Seu objetivo é expor com clareza factual a fronteira entre o que já está integrado, o que está em andamento e o que depende de ação humana ou entregas futuras, recusando relatórios contínuos monolíticos e promessas de funcionalidades não construídas.

A autoridade de decisões de produto continua em [plano aprovado](<../plano_desenvolvimento.md>), [proposta](<../proposta_transicao_carreira.md>) e [CLAUDE.md](<../../CLAUDE.md>). Este documento não altera as decisões D01–D25.

## Operating Context

Projeto acadêmico FIAP Global Solution 2026.2, composto por 9 disciplinas integradas, com prazo final fixado em 19/11/2026 às 23h55.

Snapshot documental congelado em 16/11/2026 às ~11h34 (commit base `18e72aa`). As tarefas manuais acadêmicas (preenchimento de nomes/RMs em PDFs gerados, modelagem no Oracle SQL Developer Data Modeler, gravação de 5 vídeos acadêmicos e submissão no Portal FIAP) são de responsabilidade direta dos integrantes humanos.

## Capabilities and Constraints

- **Mercado e Ciência:** Pipeline Caged segregado com estimativas retrospectivas de admissões de 2025, modelos clássicos (Ridge, Random Forest, HistGradientBoosting) e rede neural MLP em PyTorch integrados; snapshot estático servido pela API FastAPI; MongoDB Atlas ativo com 6 model cards publicados; amostra pontual de anúncios Adzuna de 16/11 (6 chamadas + 1 smoke, contador 7/12) servida pelo snapshot, sem constituir contagem de mercado em tempo real.
- **Jornada Pessoal:** Backend de currículo, experiências, redação defensiva de PII e confirmação prévia integrado em main (`18e72aa`, fatia S9); persistência em MongoDB de texto redigido e campos permitidos (não arquivos brutos); telas web da jornada pessoal ainda ausentes.
- **Frentes em Andamento:** S10 (extração de competências via LLM com barreira PII e termos ESCO) e S4 (deploy serverless no AWS Learner Lab com Lambda, RDS PostgreSQL e Amazon Comprehend).
- **Domínio e Comparação:** Módulo de domínio puro de comparação de destinos (competências × requisitos) integrado (S11); rotas `/me/comparacoes` aguardam a conclusão de S10.
- **Entregas Acadêmicas:** Empacotador E09 já executado, gerando notebooks executáveis, base municipal tratada e relatórios PDF (21 páginas de Estatística e 12 páginas de slides de ML). Nomes e RMs permanecem com placeholders `[HUMANO — preencher]`. Nenhuma submissão foi enviada ao Portal FIAP.
- **Catálogo de Transições:** Rubricas dos 6 destinos aprovadas pelo grupo em 16/11 (mínimos 0,5 objetiva e 0,5 LLM); MVP de produto focado em 3 destinos (R29). Campo de hash `status_rubricas` no manifesto mantido por integridade imutável.
- **Bancos de Dados:** Instância Oracle local (DDL 19c) em uso ativo; Oracle FIAP formalmente excluído por decisão da equipe.
- **Governança Preditiva:** Holdout 2026 fechado; nenhum modelo preditivo promovido para produção; aplicação exibe a estimativa sazonal retrospectiva de 2025. Ganho preditivo não constitui garantia de contratação.
- **Superfície Panorama:** Arquivo HTML estático e autossuficiente (`docs/panorama_projeto.html`) com CSS e JS leves inline, sem dependências externas, fontes de rede ou chamadas assíncronas. Executa 100% offline via protocolo `file://`.

## Evidence on Hand

Fontes factuais de referência: [estado.md](<../estado.md>), [plano_desenvolvimento.md](<../plano_desenvolvimento.md>), [manifesto de entregas](<../entregas_manifesto.json>), [evidência ML/RNA](<../../05_ML/evidencias/20261115_modelos_mvp_aceite.md>) e [evidência D11 Estatística](<../../08_Estatistica/evidencias/20261115_d11_aceite.md>).

Os resultados preditivos e estatísticos refletem coortes retrospectivas específicas (ML/RNA: 3 destinos MVP, superior+, 55 séries, 495 linhas; Estatística D11: 6 destinos, 229 municípios SP) e não devem ser generalizados como métricas de produção.

## Product Principles

1. **Distinguir camadas de maturidade:** Separar nitidamente código integrado, frentes em andamento, pacotes gerados pelo empacotador, revisões humanas e submissões finais.
2. **Precisão de dados:** Declarar fonte, coorte, horizonte temporal e unidades métricas de cada resultado. Caged mede admissões formais; Adzuna é amostra pontual de anúncios.
3. **Privacidade irrestrita:** Nenhuma informação pessoal ou identificador sensível trafega para serviços externos ou modelos de linguagem sem higienização e confirmação explícita prévia do usuário.
4. **Sem falsos sucessos:** Não apresentar simulações como código finalizado nem ocultar limitações técnicas ou modelos não promovidos.
5. **Orientação imediata:** A interface de documentação deve permitir que o desenvolvedor e o avaliador identifiquem pendências concretas em poucos segundos, sem sobrecarga textual (limite de 400 palavras na abertura).

## Accessibility & Inclusion

Texto integral em português claro e direto; contraste mínimo de 4.5:1 para texto normal e 3:1 para elementos de interface (WCAG AA); navegação fluida por teclado com anéis de foco visíveis de 2px nos controles interativos; alvos táteis mínimos de 44×44px; fontes mínimas de 12px real; ausência de bordas accent superiores a 1px; suporte a preferências de movimento reduzido (`prefers-reduced-motion`); compatibilidade com impressão e visualização sem perda estrutural em viewports desktop (1440px, 1280px), tablet (768px) e mobile (390px, 360px).
