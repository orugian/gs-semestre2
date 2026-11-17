# Handoff CitizenTech — fechamento17/11/2026

Leia primeiro [estado §0](<estado.md>), depois só os documentos necessários. Esta retomada foi concluída; **não repetir S15 ou investigar novamente o upload Wokwi**.

## Feito e onde está a prova

- S15 integrada/publicada em `e7c533a`; [RED/GREEN e persona](<../02_Cybersecurity/evidencias/20261116_s15_e2e_aceite.md>). Docs/compilação/revisão2 publicados em `f10ffd2`; boot Wokwi em `409e975`.
- Wokwi pelo agente: **3cenários,6HTTP201,6CSV**, GPIOLED0/1/1 e buzzer1.000Hz apenas no crítico. [Aceite completo, imagens, Serial, VCD e limites](<../01_AICSS/evidencias/20261117_wokwi_aceite.md>), [manifesto/hashes](<../01_AICSS/evidencias/20261117_wokwi_manifesto.json>). É execução efetiva de **simulação**, não bancada física; placa sem sensores permaneceu intacta.
- AICSS§5.2/PDF atualizado com três imagens e medidas; PDF10p. Demais PDFs: Cyber12, DS7, CTP8, ML12, Estatística21. Três RMs em todos; empacotador --verificar OK e tools43passed. [Adjudicação da revisão2](<revisao_conformidade_2.md>) não constitui aprovação acadêmica total.
- Lote final de Wokwi está no commit que contém este handoff/estado; consulte Git/remote antes de presumir pendência de commit. Somente gs-semestre2, sem force e sempre gitleaks staged/intervalo.

## Não perder estes limites

Wokwi→API CTP isolada→CSV foi verificado; **não Wokwi→AWS**. Os6eventos ficaram pendente_nuvem, worker desativado. Dados/chave fictícios e gateway público monitorado; nenhum segredo real ou conta pessoal. Projeto efêmero não foi publicado/salvo; demo com chave real exige projeto privado/rotação de D24 e TLS/CA adequado. O ngrok falhou na fase TLS, CPUmax também; Cloudflare HTTPS/CPU padrão passou os mesmos testes. Não deduzir a causa exata no servidor sem evidência.

Todos os túneis/APIs/browsers próprios encerrados. Worktrees S5-auth/S5-red, agy30832 da outra frente, Docker/volumes/dados foram preservados. Disco17,1GB na última checagem. Ferramentas portáteis fora do repo; relatórios/diagnósticos retidos para auditoria, não limpar tmp global com outra frente ativa. Não retunar2025, promover modelo, abrir holdout2026, reabrir fatias integradas ou apagar dados.

## Próximo passo humano

Obter imagens Cloud exigidas, modelos/exportações Data Modeler e vídeos/URLs/ideias reais da live. [Estado §4](<estado.md>) detalha limites e formatos. Então conferir os arquivos fornecidos, copiar originais privados antes de tarjar (não mover), atualizar PDFs e repetir empacotador --verificar. Não converter evidência local em suposto print AWS. Confirmar Lab/health antes de nova demonstração; health antigo não assegura disponibilidade atual. Portal é humano e ainda não foi submetido.

## Skills sugeridas

`diagnose`/`tdd` se aparecer regressão; `agent-reach` para documentação pública; `managing-python-dependencies` antes de Python; `wordcraft` para documentos/PDF usando o pipeline Edge do projeto; `impeccable` para UI/a11y; `handoff` no próximo checkpoint. Implementação via agy (D14); aceite/segredos/integração pelo orquestrador. Não repetir conteúdo já registrado nos aceites.
