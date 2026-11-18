# Kit de gravação dos vídeos — CitizenTech

Tudo o que um integrante precisa para gravar os vídeos **no próprio computador**, a partir de um clone do GitHub. Os scripts usam **só bancos de teste locais** e **não enviam nada à AWS**. Nenhum deles mostra senhas na tela.

## Quais vídeos gravar

| Vídeo | Duração | Obrigatório | Roteiro |
|---|---|---|---|
| **AIC** (pitch integrador) | até **7 min** | sim (sem ele, AIC não pontua) | [aic.md](aic.md) |
| **Machine Learning** | até 5 min | sim | [ml.md](ml.md) |
| **Redes Neurais** | sem limite no enunciado (planejado para 5 min) | sim (vale 1 ponto) | [rna.md](rna.md) |
| **Cybersecurity** | até 5 min | sim | [cyber.md](cyber.md) |
| **Cloud** | até 5 min | sim | [cloud.md](cloud.md) |

AICSS, Data Science, CTP e Estatística **não pedem vídeo**.

Regras que valem para todos: **YouTube "Não listado"** (ML e RNA aceitam também Google Drive com acesso liberado), link testado numa **janela anônima**, sem mostrar senhas, `app\.env`, e-mails reais ou o cabeçalho da conta AWS. O **AIC** exige ainda **rosto de quem narra**, **sem música de fundo** e **nomes e RMs** na abertura ou no fechamento.

Integrantes: Guilherme Orugian (RM572882) · Lucas Henrique (RM571901) · Rodrigo Bettio (RM573725).

## Preparar o computador (uma vez, ~15 min na primeira vez)

Precisa de: **Windows**, [uv](https://docs.astral.sh/uv/), **Node.js 24 + pnpm**, **Docker Desktop** aberto e ~6 GB livres.

```powershell
git clone https://github.com/orugian/gs-semestre2.git
cd gs-semestre2
powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\preparar.ps1
```

O `preparar.ps1` cria `app\.env` com senhas locais aleatórias (se ainda não existir), sobe os bancos de teste no Docker, cria as tabelas e instala as dependências. Se algo faltar, ele diz o quê.

## Na hora de gravar

| Para… | Comando (na raiz do repositório) |
|---|---|
| Abrir a aplicação (Mercado, Painel técnico, cadastro) | `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1` |
| Abrir com a IA ligada (extração de competências e correção do exercício) | `... gravacao\subir_app.ps1 -ComIA` — precisa de `OPENROUTER_API_KEY` no seu `app\.env` (peça ao Guilherme) |
| Criar a persona fictícia "Marina" já com a jornada inteira | `... gravacao\criar_conta_demo.ps1` (depois de `subir_app.ps1 -ComIA`) |
| Demonstração Cloud sem AWS (emulador + banco local) | `... gravacao\cloud_local.ps1` |

Para encerrar, feche as janelas que os scripts abrem.

## O que já está pronto para mostrar

- Capturas da AWS real: [06_Cloud/evidencias](../06_Cloud/evidencias/)
- Diagramas UML: [docs/uml/img](../docs/uml/img/)
- Quadro de gestão (para o AIC): [kanban.md](kanban.md)
- Notebooks **já executados**: [05_ML/notebook.ipynb](../05_ML/notebook.ipynb) e [07_RedesNeurais/notebook.ipynb](../07_RedesNeurais/notebook.ipynb). Abra no VS Code ou no GitHub; **não reexecute** (o treino depende de dados que ficam fora do repositório).
- Wokwi executado: [01_AICSS/evidencias](../01_AICSS/evidencias/) (capturas dos 3 cenários)

## Depois de publicar

Mande os links ao Guilherme. Ele confere duração e acesso e preenche o campo **Link** em cada `0X_*/video.md`.
