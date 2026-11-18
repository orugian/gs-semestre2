# Roteiro de gravação — Redes Neurais (demonstração funcional; ~5 min)

**Exigido pelo enunciado (critério "Demonstração funcional da aplicação em vídeo", 1 ponto):** o modelo funcionando com dados que **não** foram usados no treino, as entradas e as saídas, e como se integra à solução. O enunciado não fixa duração; o roteiro foi planejado para 5 min. YouTube não listado ou Google Drive com acesso liberado.

## Antes de gravar

1. Abra `07_RedesNeurais\notebook.ipynb` no VS Code (ou no GitHub). Ele **já está executado**: só role. **Não reexecute**.
2. Figuras à mão em `07_RedesNeurais\evidencias\figuras\`: `curvas_treinamento_rna.png`, `rna_real_vs_previsto_sp.png`, `rna_erro_por_serie.png`.
3. Na raiz: `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1`. Em http://localhost:5173, aba **Painel técnico**, destino "Analista de Monitoramento/IoT Industrial", UF SP.

## Gravação

| Tempo | O que dizer | Tela |
|---|---|---|
| 0:00–0:30 | A rede estima **admissões formais do próximo trimestre** por destino e UF. Entrada: 52 variáveis (lags, médias e somas móveis de admissões e desligamentos, mês, destino e UF). Saída: um número de admissões. | Notebook, abertura e §1 |
| 0:30–1:00 | Dados: Novo Caged, 202001–202509, 3 destinos × 27 UFs; 55 de 81 séries. Treino até 202409, embargo de 3 meses, validação 202501–202509 (495 linhas). | Notebook §2–3 |
| 1:00–1:40 | Arquitetura: MLP em PyTorch, 52 → 64 → 32 → 1, ReLU, dropout 0,1, 5.505 parâmetros. Por que MLP: dado tabular com lags já calculados. | Notebook §4 |
| 1:40–2:20 | Treino: Adam, lr 0,001, batch 128, até 200 épocas com parada antecipada (paciência 15). Mostre as curvas de perda. | Notebook §5; curvas |
| 2:20–2:55 | Refinamento: configuração A [64, 32] → MAE no CV **32,70**; B [128, 64] → **42,26**. A menor generalizou melhor; a escolha usou o CV do treino, não a validação 2025. | Notebook §6 |
| 2:55–3:40 | **Demonstração com dados fora do treino:** a célula §8 roda a inferência nas 495 linhas de 2025 e confere com as previsões gravadas (diferença máxima 0). Mostre uma linha: entrada → previsão → realizado (ex.: Dados/BI, UF 23, 202501: sazonal 88, MLP 88,3, realizado 79). | Notebook §8 |
| 3:40–4:15 | Avaliação: MLP MAE **31,65**, RMSE 73,67, WAPE 11,21%, contra o sazonal 33,60 (5,78% menor). Em séries pequenas (IoT) fica perto dos baselines. | Notebook §7; figuras |
| 4:15–4:50 | Integração: as previsões vão para o snapshot de mercado, exposto pela API; o **Painel técnico** mostra a MLP ao lado dos baselines, **não promovida**. O número exibido à pessoa continua sendo o baseline sazonal. | App, Painel técnico |
| 4:50–5:00 | Próximo passo: avaliar no teste de 2026 antes de promover. Nomes e RMs. | Notebook, final |

## Não diga
"Está em produção", "é o modelo final". O ganho de 5,78% é agregado; não vale para toda UF e as linhas se sobrepõem no tempo.

## Checklist
- [ ] dados fora do treino mostrados (§8) · [ ] entrada e saída explicadas · [ ] integração com o app mostrada · [ ] nomes e RMs · [ ] link testado
