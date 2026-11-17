# Revisão de conformidade nº 2 — adjudicação do orquestrador

**Revisão independente:**16/11/2026, noite. **Atualização do aceite Wokwi e pacote:**17/11/2026, madrugada. Prazo:19/11/2026 às23h55. **Não é aprovação final da entrega.**

Revisão independente por nova chamada `agy --mode plan --print-timeout 20m`, sem participação na autoria; exit **0 às 22h51**. Contrato e relatório bruto preservados fora do Git em [contrato](<../../.kaiser/contratos/REV-conformidade-2.md>) e [relatório](<../../.kaiser/reports/REV-conformidade-2.md>). O bruto é autorrelato não confiável: as decisões abaixo foram confrontadas com os arquivos e execuções do orquestrador. Não foram reexecutadas análises/modelos nem aberto o holdout.

## 1. Situação por disciplina

| Disciplina | Verificado nesta sessão / evidência disponível | Falta para fechar |
|---|---|---|
| AICSS | **Atualização17/11:** agente executou Wokwi,3cenários/6HTTP201/6linhas CSV; LED0/1/1, PWM1.000Hz só no crítico comprovado por VCD; [prints/Serial/CSV](<../01_AICSS/evidencias/20261117_wokwi_aceite.md>). Relatório/PDF atualizado no pacote | Bancada física e Wokwi→AWS não foram medidos, mas não são apresentados como feitos. Demonstração com chave real exige o projeto privado/rotação de D24; este ensaio usou só chave fictícia e API isolada. |
| Cyber | Relatório corrigido, controles implementados/propostos separados; RED/GREEN E2E e axe registrados; PDF de 12 páginas, com os três RMs. [Aceite web](<../02_Cybersecurity/evidencias/20261116_s15_e2e_aceite.md>) | Vídeo de até 5 min e link real. Detalhamento do operador/transferência internacional na tela de consentimentos permanece pendência explícita, não tela inexistente. |
| Data Science | DDL/consultas e evidências Oracle local + Mongo já disponíveis; PDF identificado de 7 páginas | Modelo lógico e relacional reais pelo **AGENTE**, conforme determinação do usuário17/11/D25 atualizado; execução/exportações ainda pendentes. Mermaid não comprova execução no Data Modeler. Oracle FIAP continua fora do escopo por decisão anterior, sem alegar execução nele. |
| CTP | Código FastAPI isolado, requisitos e evidências JSON/CSV/indicadores existentes; PDF de 8 páginas identificado | Conferência/submissão humana. Templates Flask do professor permanecem intactos, explicitamente separados da solução. |
| ML | Notebook e slides identificados; PDF de 12 páginas; somente capa Markdown do notebook mudou | Vídeo de até 5 min e link. Execução científica anterior preservada; não foi repetida nem retunada nesta sessão. |
| Cloud | Health real pós-reinício humano: HTTP200, status=ok/banco=ok; originais dos três prints preservados e cópias privadas com SHA igual; versões tarjadas rastreadas | Prints do simulador e consulta RDS; refazer CloudWatch de descarte/chave inválida/alerta; vídeo até 5 min. Comprehend AccessDenied: resiliência demonstrada, **não** resultado válido de sentimento. |
| RNA | Notebook identificado, código/saídas/metadados preservados | Vídeo funcional obrigatório e link. Não abrir 2026 para gravar a demonstração; usar a inferência retrospectiva já existente, rotulada como validação. |
| Estatística | PDF de 21 páginas, PY e CSV presentes; três RMs no PDF; cópias verificadas pelo empacotador | Postar **PDF + PY + CSV separados**, sem ZIP. A análise não foi reexecutada nesta sessão. |
| AIC | Roteiro e UML disponíveis; identificação do grupo confirmada | Vídeo obrigatório até 7 min, YouTube não listado, rosto visível, sem música, nomes/RMs na abertura/fecho; ideias reais da live e relato de gestão pelos alunos. Roteiro não equivale a vídeo entregue. |

## 2. Achados adjudicados

| ID | Decisão | Evidência / ação |
|---|---|---|
| RC2-01 | **Aceito, bloqueador humano** | AIC exige vídeo para pontuar; link ausente. Não fabricar gravação ou conteúdo da live. |
| RC2-02 | **Aceito, pendência humana** | Vídeo RNA obrigatório; vídeos ML/Cyber/Cloud também pendentes. Os limites e critérios são os dos respectivos enunciados, sem calcular nota garantida. |
| RC2-03 | **Aceito, requisito de modelagem pendente** | Data Modeler ainda não executado. Em17/11 o usuário transferiu expressamente a tarefa ao agente; gerar/verificar os artefatos reais, não solicitar que o grupo faça a modelagem. |
| RC2-04 | **Aceito, fechado com execução17/11** | Wokwi3cenários até o CSV, prints reais e GPIO/VCD verificados. Ngrok e CPUmax falharam e foram registrados; túnel Cloudflare/CPU padrão passou sem alterar regras. Túneis/API encerrados; sem teste físico, sem envio desse lote à AWS. |
| RC2-05 | **Aceito, formato de evidência Cloud** | TXT de execução/SQL não substitui as imagens exigidas. Não renderizar saída histórica como se fosse captura do console AWS. |
| RC2-06 | **Aceito e corrigido** | Restavam referências a laboratório/consentimentos “em desenvolvimento” no §6 de Cyber e §9 de Cloud. Atualizadas para o que está integrado; Cyber regenerado novamente com limite de 15 páginas. A pendência real do texto de operador/transferência internacional foi preservada. |
| RC2-07 | **Sem mudança AWS** | O typo `RATE_KIMIT_POR_MINUTO` no console está documentado; ausência da variável correta usa padrão 30, mesmo valor. Sugestão de renomear não foi tratada como autorização para alterar AWS. |
| RC2-08 | **Mantido por decisão prévia** | Templates Flask do professor não removidos. O documento CTP informa quais arquivos constituem a solução. |
| RC2-09 | **Afirmação do revisor rejeitada/corrigida** | O bruto dizia que o cabeçalho de `analise.py:5` continha identificação; a leitura real mostrou que não. Identificação adicionada somente à docstring da fonte portátil; cópia é regenerada pelo empacotador, sem editar lógica estatística. |
| RC2-10 | **Generalizações rejeitadas** | “100% dos requisitos” de Estatística, inferências de disponibilidade contínua e contagens/pesos sem execução não são aceite. O revisor não executou notebooks, não contou PDFs com parser e não chamou a AWS. Não propagamos essas alegações como verificadas. |

## 3. Verificação independente do orquestrador

- **Web:** Playwright em main, API teste recém-iniciada após normalização IPv4 → **3 passed, 1 skipped**; o skip é somente persona sem credenciais do app nesse ambiente. Persona executada separadamente contra API app `-App -ComLLM` → **1 passed**. Não houve alteração da persona.
- **Acessibilidade:** 11 telas + modal sem violações axe nas severidades medidas; nome do diálogo conferido por asserção explícita, pois axe isolado não detectou o defeito do diálogo nativo. Isso não certifica toda a WCAG.
- **Regressão web:** **61 passed**, até 6 workers, typecheck/build OK; bundle principal ~918,48 kB, aviso de tamanho permanece.
- **Ferramentas:** `uv run pytest -q` em tools → **43 passed**, incluindo 9 testes host de firmware.
- **Firmware:** CLI/core/bibliotecas isolados, compilação real com 2 jobs → exit0, programa 1.046.369 bytes (79%), RAM global47.188 bytes (14%). Warnings externos OneWire mantidos; não foi simulado por esse comando.
- **PDFs finais:** parser PyPDF executado após Wokwi: **AICSS10, Cyber12, Data Science7, CTP8, ML12, Estatística21** páginas; três RMs em todos, Cyber≤15. Três imagens Wokwi incorporadas em2200×1400 (páginas7/7/8), medidas25,11/12,07/4,96 presentes no texto. Não foi revisão visual completa da paginação.
- **Notebooks:** conferida ausência de outputs de erro armazenados e identificação em fontes/cópias. Comparação com HEAD confirmou que apenas a primeira célula Markdown mudou; código, outputs e metadados restantes idênticos. **Não reexecutados**.
- **Empacotamento:** gerar e `--verificar --dados ../.dados` → **OK**; repetir após qualquer alteração adicional de fonte/entrega.
- **Nuvem:** health HTTP200/status=ok/banco=ok após reinício humano. Isso não comprova novamente os cenários Cloud nem sentimento.

## 4. Guardrails e próximos gates

Não promover modelos, retunar com 2025, abrir holdout 2026, mexer em S5-auth/S5-red ou apagar dados. Push somente para gs-semestre2, com gitleaks e checagem do exit code.

Gate Wokwi fechado em17/11 (evidência real de simulação, sem confundir com hardware físico). Próximos gates: obter imagens Cloud/Data Modeler e links de vídeo → atualizar os documentos afetados e PDFs → repetir empacotador/verificação → conferência humana e Portal. O estado operacional acompanha o trabalho em [estado](<estado.md>); este parecer não constitui entrega concluída.
