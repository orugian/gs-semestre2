# Cybersecurity

> Disciplina (nome oficial): **Cognitive Cybersecurity**  
> Entrega no Portal do Aluno até **19/11/2026 às 23h55**. Fonte completa: `docs/GS2_2026_enunciados.md` e `docs/material_por_cadeira/`.

## Resumo do desafio

Analisar os riscos de segurança cibernética da solução CitizenTech e implementar mecanismos de proteção compatíveis com o projeto. O grupo deverá identificar ameaças e vulnerabilidades, propor controles de segurança e demonstrar ao menos uma proteção aplicada ao protótipo, considerando também privacidade e LGPD.

## Tema: Protótipo CitizenTech com Dados e IA para um Público Definido

As equipes deverão desenvolver uma solução CitizenTech baseada em dados e inteligência artificial para atender uma necessidade real de um público específico.

Exemplos de público:
- Agricultores familiares
- Pessoas idosas
- Comunidades em áreas de risco
- Escolas públicas
- Moradores de áreas rurais
- Pessoas com deficiência
- Agentes de saúde
- Cooperativas
- Pequenos empreendedores

Cada equipe deverá escolher **apenas um público-alvo e um problema principal**.

## Desafio da disciplina de Cybersecurity

A equipe deverá atuar como uma **consultoria de segurança** responsável por avaliar os riscos do protótipo CitizenTech desenvolvido. O objetivo é identificar vulnerabilidades, ameaças e controles de segurança adequados ao contexto da solução.

O trabalho deverá demonstrar como a cibersegurança contribui para a proteção:
- dos usuários;
- dos dados;
- dos modelos de IA;
- da infraestrutura;
- da privacidade;
- da conformidade com a LGPD.

## Requisitos técnicos

**1. Descrição da solução CitizenTech** — Apresentar:
- problema escolhido;
- público-alvo;
- uso de IA;
- dados utilizados;
- arquitetura simplificada.

Exemplo: `Usuário | Aplicação | Banco de Dados | Modelo de IA`

**2. Mapeamento de Superfície de Ataque** — Identificar pelo menos:

| Componente | Exemplos |
|---|---|
| Usuários | Acesso indevido, Senha fraca |
| Aplicação | SQL Injection, XSS, Falha de autenticação |
| API | Abuso de requisições |
| Banco de Dados | Vazamento, Exposição indevida |
| Modelo de IA | Manipulação de dados, Model poisoning |

**3. Matriz de Riscos** — Apresentar **no mínimo 5 riscos**. Exemplo:

| Risco | Impacto | Probabilidade |
|---|---|---|
| Roubo de credenciais | Alto | Médio |
| Vazamento de dados | Alto | Alto |
| Ataque à API | Médio | Alto |
| Engenharia Social | Alto | Médio |
| Alteração do modelo de IA | Alto | Baixo |

**4. Controles de Segurança** — Propor controles para os riscos identificados. Exemplos:

| Controle | Exemplos |
|---|---|
| Autenticação | MFA, Política de senhas |
| Firewall/WAF | Proteção da aplicação |
| Backup | Recuperação de incidentes |
| Criptografia | Dados em trânsito, Dados em repouso |
| Monitoramento | Logs, Alertas |

**5. Demonstração Obrigatória** — O grupo deverá implementar **pelo menos UMA proteção funcionando**. Exemplos aceitos:
- Opção 1: Proxy com bloqueio de categorias.
- Opção 2: Firewall/UFW bloqueando acesso.
- Opção 3: Rate Limiting.
- Opção 4: Validação de login.
- Opção 5: Registro de logs.
- Opção 6: Criptografia de dados.
- Opção 7: Hash de integridade.
- Opção 8: Controle de acesso baseado em perfil.

**Não basta propor. É necessário demonstrar com evidências.**

**6. LGPD** — Responder:
- Quais dados pessoais são tratados?
- Quais dados sensíveis podem existir?
- Quais proteções serão aplicadas?
- Como o usuário será informado?

**7. Engenharia Social** — Apresentar:

| Item | Exemplos |
|---|---|
| Cenário de ataque | Phishing, WhatsApp falso, E-mail falso |
| Contramedidas | Treinamento, Conscientização, MFA |

## Entregáveis

**PDF (máximo: 15 páginas)**, contendo:
- Solução CitizenTech
- Arquitetura
- Riscos
- Controles
- LGPD
- Demonstração

**Vídeo Pitch (máximo: 5 minutos)**, contendo:
- problema;
- solução;
- riscos;
- proteção implementada.

## Critérios de avaliação

| Critério | Pontos |
|---|---:|
| Identificação de ameaças e vulnerabilidades | 2 |
| Qualidade da análise de riscos | 2 |
| Implementação de proteção funcional | 3 |
| Privacidade e LGPD | 1 |
| Justificativa técnica das escolhas | 1 |
| Apresentação/Pitch | 1 |
| **Total** | **10** |
