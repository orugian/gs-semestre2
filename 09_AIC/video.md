# Vídeo pitch integrador — AIC (máx. 7 min)

**Link (YouTube, Não listado):** [HUMANO — preencher]
**Obrigatório:** ≤ 7 min · YouTube **Não listado** · rosto de quem narra · **sem música de fundo** · nomes e RMs na primeira ou na última tela · link testado em janela anônima.

## Preparação (antes de gravar)
1. Docker com Oracle e Mongo de teste: `docker compose -f app\docker-compose.yml --profile teste up -d --wait`.
2. Para usar a persona existente, API contra o banco do **app**: `powershell -File ..\.kaiser\ferramentas\subir_api_teste.ps1 -App`; web: `cd app\web; pnpm run dev` → `http://localhost:5173`. O modo padrão sem `-App` usa o schema de testes e não é a demonstração dessa persona. Esse auxiliar pertence à máquina de demonstração, não ao clone. O [README de execução local](<../README.md>) usa bancos de teste e não recria a persona. Para navegar em resultados já salvos, **omitir `-ComLLM`**; habilitar chamadas reais somente após reconfirmar a autorização de gasto. Conferir o isolamento da outbox antes de gravar.
3. Persona de demonstração já criada e sinalizada ("Persona de demonstração" no cabeçalho), com consentimentos, currículo confirmado e competências revisadas. **Não usar dados pessoais reais.**
4. Abas prontas: app (Minha transição, Mercado, Painel técnico), `docs/uml/img/02_2_componentes.png`, quadro Kanban do grupo, terminal com o simulador de Cloud, Wokwi (se a gravação incluir o firmware).
5. [HUMANO] Anotar 1–2 ideias da live de lançamento que inspiraram a proposta (o grupo precisa citar com as próprias palavras).

## Roteiro com tempos

| Tempo | Conteúdo | Tela |
|---|---|---|
| 0:00–0:20 | Abertura: nome do projeto, nomes e RMs. | Slide de abertura com rosto |
| 0:20–1:10 | **3.1 Problema e público:** profissionais graduados e experientes em transição de carreira decidem com pouca evidência; anúncios e cursos prometem demais. Público: quem tem experiência, pouco tempo e precisa saber o que já tem, o que falta e como o mercado formal se comporta na UF. **ODS 4 (meta 4.4), ODS 10 e ODS 8 (8.5/8.6).** Ideias da live: [HUMANO]. | Rosto + slide curto |
| 1:10–2:30 | **3.2 Construção e integração:** a web (React) fala com a API Python (FastAPI); dados relacionais no Oracle e textos redigidos no MongoDB (Data Science); currículo só vai à IA redigido e confirmado (Cyber/LGPD); modelos de previsão e rede neural sobre microdados do Novo Caged (ML, RNA), com avaliação temporal e nenhum modelo promovido sem passar no critério; estatística municipal (Estatística); bancada IoT com ESP32 e dois sensores (AICSS); API de leituras com CSV e indicadores (CTP); Lambda + RDS na AWS (Cloud). Mostrar o diagrama de componentes e explicar **um fluxo** de ponta a ponta. | `docs/uml/img/02_2_componentes.png` e `03_…` |
| 2:30–5:00 | **3.3 Demonstração:** (a) Mercado: série observada com fonte e período, previsão retrospectiva marcada como tal, painel técnico com as métricas lado a lado (a rede neural aparece e não foi promovida); (b) Minha transição: currículo colado → texto redigido → confirmar → competências sugeridas com trecho de origem → confirmar e "não possuo"; (c) comparação de 2 destinos: obrigatórios não atendidos sempre visíveis, sem nota única; (d) escolher destino → plano com checkpoints; (e) exercício: resposta aberta avaliada critério a critério, com trecho; "Discordo"; (f) mostrar duas execuções separadas: o ESP32 **no Wokwi** enviou 6 leituras à API isolada e ao **CSV**, sem envio à nuvem; o **simulador por software** enviou diretamente à **Lambda**, com logs no CloudWatch e linhas no RDS. Ao usar as capturas, comparar por ID: o alerta CloudWatch de 16/11 é o **id 8** (46 °C), também visível no SELECT; os ids 12–19 são da rodada seguinte. Papel da IA: sugere e avalia com critérios explícitos, **não decide**. Validação: testes automatizados (API, web, Lambda) e resultados do ML. **Evoluções futuras** ditas em voz alta: MFA, exclusão de conta, mercado no Oracle, sentimento real na nuvem (hoje negado pela conta). | App ao vivo |
| 5:00–6:10 | **4 Gestão:** como o trabalho foi dividido em fatias com teste antes do código, quadro Kanban, revisão independente nas partes de risco, controle de prazo e cortes (de 6 para 3 destinos no ML). [HUMANO] contar uma dificuldade real e como foi resolvida. | Kanban do grupo |
| 6:10–6:50 | **Condições reais de uso:** acessibilidade (rótulos, teclado, contraste), segurança (cookie seguro, CSRF, limite de tentativas), proteção de dados (consentimento por finalidade, redação, nada de PII nos logs), sustentabilidade (serverless, modelos leves em CPU). Limites honestos: dados de mercado são admissões formais, não oportunidades; persona de demonstração. | Rosto |
| 6:50–7:00 | Fechamento e nomes/RMs (se não estiverem na abertura). | Slide final |

## Frases que NÃO usar
"vagas", "probabilidade de emprego", "vale a pena", "nota de compatibilidade", "a IA decide", "100% seguro".

## Checklist
- [ ] ≤ 7 min  - [ ] YouTube não listado  - [ ] rosto de quem narra  - [ ] sem música de fundo
- [ ] código e/ou hardware em funcionamento  - [ ] nomes e RMs na 1ª ou última tela  - [ ] link testado
- [ ] ideias da live citadas  - [ ] evoluções futuras identificadas como tal
