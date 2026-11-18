# Roteiro de gravação — AIC, pitch integrador (até 7 min)

**Obrigatório para pontuar em AIC.** Requisitos do enunciado: até **7 min** · YouTube **Não listado** · **rosto** de quem narra · **sem música de fundo** · **nomes e RMs** na primeira ou na última tela · link testado. O enunciado pede também: problema e público, como a solução foi pensada e construída, **gestão das entregas (Kanban/ágil)**, **UML** e **ODS**, e como as **ideias da live** de lançamento inspiraram o grupo.

## O grupo precisa trazer (não dá para inventar)
- [ ] **1–2 ideias da live** de lançamento que inspiraram a proposta, com as palavras do grupo.
- [ ] **Uma dificuldade real** de gestão e como foi resolvida.

## Antes de gravar (20 min)

1. Na raiz: `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1 -ComIA`.
   - Sem chave de IA, rode sem `-ComIA` e pule a extração de competências e a correção do exercício (mostre os resultados já existentes da persona).
2. `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\criar_conta_demo.ps1` → anote o e-mail e a senha **fora do vídeo**. Entre com ela em http://localhost:5173 › Minha transição.
3. Abas prontas: app (Mercado, Painel técnico, Minha transição), `docs/uml/img/02_2_componentes.png`, [kanban.md](kanban.md), capturas de `06_Cloud/evidencias/` e de `01_AICSS/evidencias/` (Wokwi).
4. Câmera ligada (rosto), microfone testado, **sem música**.

## Gravação

| Tempo | O que dizer | Tela |
|---|---|---|
| 0:00–0:20 | Nome do projeto, **nomes e RMs**. | Rosto + slide |
| 0:20–1:10 | **Problema e público:** profissionais graduados e experientes em transição de carreira decidem com pouca evidência. Público: quem tem experiência, pouco tempo, e precisa saber o que já tem, o que falta e como o mercado formal se comporta na sua UF. ODS 4 (meta 4.4), 8 e 10. **Ideias da live:** [o grupo]. | Rosto |
| 1:10–2:30 | **Construção:** web (React) → API (Python/FastAPI); Oracle e MongoDB (Data Science); currículo vai à IA só redigido e confirmado (Cyber); previsão e rede neural com dados do Novo Caged (ML, RNA); estatística municipal (Estatística); ESP32 com dois sensores (AICSS); API de leituras com CSV (CTP); Lambda + RDS na AWS (Cloud). Mostre o diagrama e explique **um fluxo** de ponta a ponta. | Diagrama UML |
| 2:30–5:00 | **Demonstração:** (a) Mercado: série observada com fonte; estimativa marcada como retrospectiva; Painel técnico com a rede neural não promovida. (b) Minha transição: currículo → texto redigido → confirmar → competências com trecho de origem → confirmar / "não possuo". (c) Comparar 2 destinos: obrigatórios não atendidos sempre visíveis, sem nota única. (d) Escolher destino → plano. (e) Exercício: resposta aberta avaliada critério a critério; botão "Discordo". (f) IoT e nuvem — **são duas execuções separadas**: o ESP32 no Wokwi enviou 6 leituras à API local e ao CSV; o simulador enviou à Lambda na AWS (capturas: log e banco). A IA **sugere e avalia com critérios; não decide**. | App + capturas |
| 5:00–6:10 | **Gestão:** trabalho dividido em fatias com teste antes do código, revisão nas partes de risco, controle de prazo e cortes (6 → 3 destinos). Mostre o quadro. **Dificuldade real:** [o grupo]. | [kanban.md](kanban.md) |
| 6:10–6:50 | **Uso real:** acessibilidade (teclado, foco visível, contraste), segurança (cookie seguro, CSRF, limite de tentativas), proteção de dados (consentimento por finalidade), sustentabilidade (serverless, modelos leves em CPU). Limites: dados de mercado são admissões formais, não vagas; a persona é fictícia. Evoluções futuras: MFA, exclusão de conta, sentimento real na nuvem. | Rosto |
| 6:50–7:00 | Fechamento, **nomes e RMs**. | Slide |

## Não diga
"Vagas", "probabilidade de emprego", "vale a pena", "nota de compatibilidade", "a IA decide", "100% seguro", "o Wokwi enviou para a AWS".

## Checklist
- [ ] até 7 min · [ ] rosto · [ ] sem música · [ ] nomes e RMs · [ ] ideias da live · [ ] Kanban · [ ] UML · [ ] ODS · [ ] dificuldade real · [ ] YouTube não listado · [ ] link testado em janela anônima
