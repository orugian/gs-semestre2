# Vídeo — Redes Neurais (demonstração funcional; roteiro planejado para 5 min)

**Link (YouTube não listado ou Google Drive com acesso habilitado):** [HUMANO — preencher]
**Conteúdo exigido (critério "Demonstração funcional da aplicação em vídeo"):** o modelo funcionando com dados que não foram usados no treino, as entradas e as saídas, e como ele se integra à solução CitizenTech.

## Preparação (antes de gravar)
1. `07_RedesNeurais/notebook.ipynb` aberto **já executado**. O notebook carrega o modelo treinado de `.dados/artefatos/rna/20261115_r29_aceite`; não reexecutar o treino gravando.
2. Figuras à mão: `evidencias/figuras/curvas_treinamento_rna.png`, `rna_real_vs_previsto_sp.png`, `rna_erro_por_serie.png`.
3. App web e API locais conforme o [README](<../README.md#rodar-a-aplicação>), com o snapshot de Mercado configurado. Abrir a aba **Painel técnico** (sem login nem LLM), destino "Analista de Monitoramento/IoT Industrial", UF SP.
4. Não mostrar `app/.env` nem caminhos com dados pessoais.

## Roteiro com tempos

| Tempo | Fala (resumo) | Tela |
|---|---|---|
| 0:00–0:30 | Problema: quem está em transição de carreira escolhe destino sem saber quanto o emprego formal absorve. A rede estima **admissões formais do próximo trimestre** (t+1 a t+3) por destino e UF. Entrada: 52 variáveis depois do pré-processamento (lags, médias e somas móveis de admissões e desligamentos, mês, e destino e UF em one-hot). Saída: um número de admissões. | Notebook, célula de abertura e §1 |
| 0:30–1:00 | Dados: Novo Caged (MTE), 5.589 registros, 202001–202509, 3 destinos × 27 UFs. 55 de 81 séries elegíveis. Treino 202101–202409, embargo de 3 meses, validação 202501–202509 (495 linhas). Holdout 2026 fechado. | Notebook §2–§3 |
| 1:00–1:40 | Arquitetura: MLP em PyTorch, 52 → 64 → 32 → 1, ReLU, dropout 0,1, 5.505 parâmetros. Por que MLP: o dado é tabular com lags já calculados; CNN e RNN não acrescentam estrutura aqui. | Notebook §4 (saída do `MLPRegressor`) |
| 1:40–2:20 | Treino: Adam, lr 0,001, batch 128, até 200 épocas com early stopping (paciência 15) numa janela interna com embargo. Refit no treino inteiro com 55 épocas. Mostrar as curvas de perda. | Notebook §5; `curvas_treinamento_rna.png` |
| 2:20–2:55 | Refinamento: configuração A [64, 32], dropout 0,1, lr 0,001 → MAE médio no CV **32,70** (±8,42). Configuração B [128, 64], dropout 0,2, lr 0,0005 → **42,26** (±8,48). A rede menor generalizou melhor; A foi escolhida pelo CV do treino, não pela validação 2025. | Notebook §6 |
| 2:55–3:40 | **Demonstração com dados fora do treino:** a célula §8 transforma as 495 linhas de 2025 e roda a inferência; a diferença máxima para as previsões gravadas é 0. Mostrar a tabela de entrada → previsão → realizado (ex.: Dados/BI, UF 23, 202501: soma de 3 meses 59, sazonal 88, MLP 88,3, realizado 79). | Notebook §8 |
| 3:40–4:15 | Avaliação na validação 2025: MLP MAE **31,65**, RMSE 73,67, WAPE 11,21%, contra o baseline sazonal com MAE 33,60 (5,78% de redução). Nenhuma previsão negativa. Limite: em séries pequenas, como IoT, a rede fica perto dos baselines. | Notebook §7; `rna_real_vs_previsto_sp.png`, `rna_erro_por_serie.png` |
| 4:15–4:50 | Integração: as previsões vão para o snapshot de mercado, que a API expõe em `GET /mercado/{destino}/modelos`. No app, a aba Painel técnico mostra a MLP ao lado dos baselines, marcada como **não promovida**. O número mostrado à pessoa continua sendo o baseline sazonal: promover exige o teste no holdout 2026. | App web, aba Painel técnico |
| 4:50–5:00 | O que falta: avaliar no holdout 2026 e medir a estabilidade por UF antes de promover. Nomes e RMs. | Notebook, considerações finais |

## Cuidados
- Não dizer que a rede "está em produção" ou "é o modelo final": ela não foi promovida.
- O ganho de 5,78% é agregado nas 495 linhas; não vale para toda UF ou série, e as linhas se sobrepõem no tempo (não são 495 observações independentes).
- A previsão é de admissões de um grupo de ocupações numa UF, nunca de contratação individual.
