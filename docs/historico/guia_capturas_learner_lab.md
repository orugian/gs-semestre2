# Capturas que ainda faltam — Learner Lab / Cloud

> **Situação em 17/11/2026, 10h30 (UTC−3): as cinco capturas abaixo foram obtidas.** CW-C/CW-D/CW-K: prints do usuário (rodada de 16/11, e-mail tarjado, originais em `.dados/cloud/privado`). SIM e DB: capturados pelo agente na rodada nova de 17/11 (13:09–13:13 UTC). Ver [README Cloud §8](<../06_Cloud/README.md>) e [registro da rodada](<../06_Cloud/evidencias/20261117_rodada_function_url.txt>). **Opcional:** print CloudWatch da rodada de 17/11 (janela 13:09:50Z–13:13:00Z, ids 12–19). O restante deste guia fica como referência histórica.

**Atualizado em17/11/2026.** O usuário informou que o Learner Lab foi reativado. Isso é informação do usuário, **não** um novo teste de health; o agente deve confirmar `GET /health` antes da rodada. Este guia não registra capturas já realizadas nem autoriza mudar recursos/permissões.

Requisito literal: [Cloud, entregáveis](<../06_Cloud/ENUNCIADO.md#L76-L88>) e [inventário atual](<../06_Cloud/README.md#L148-L177>). O professor pede quatro **categorias** de imagem; uma categoria pode precisar de mais de uma captura para ficar legível.

## 1. Resumo: o que falta e de quem é

| ID | Captura | Onde | Responsável |
|---|---|---|---|
| CW-C | Alerta crítico com classificação e gravação | Console CloudWatch | Você captura após o agente enviar a leitura |
| CW-D | Descarte de payload inválido em WARNING | Console CloudWatch | Você captura após o teste negativo do agente |
| CW-K | Chave inválida em WARNING | Console CloudWatch | Você captura após o teste negativo do agente |
| SIM | Simulador enviando e recebendo respostas reais | Terminal, **fora do console AWS** | Agente prepara/executa; tenta a captura real, você só ajuda se ele não conseguir |
| DB | SELECT com ocorrências realmente gravadas | Cliente SQL, **não necessariamente no console AWS** | Agente consulta/prepara; tenta a captura real, você só ajuda se ele não conseguir |

**Não precisa refazer por padrão:** [variáveis Lambda já tarjadas](<../06_Cloud/evidencias/20261116_lambda_variaveis_ambiente.png>), [CloudWatch geral de ingestão](<../06_Cloud/evidencias/20261116_cloudwatch_3.png>), Function URL, conectividade RDS e security group já têm imagens. Reutilizar se continuarem válidas/legíveis; refazer só se configuração mudou ou o enquadramento estiver insuficiente. É recomendável ter uma nova imagem de ingestão normal para correlacionar a rodada, mas ela não deve ser apresentada como falta histórica já identificada.

**Data Modeler não é sua tarefa:** por determinação expressa de17/11, será executado pelo agente. Você só poderá ser solicitado a habilitar uma ferramenta/licença/acesso que impeça a automação, não a realizar a modelagem.

## 2. Antes de capturar

1. Abra o Learner Lab ativo e entre na AWS pelo botão do laboratório, não por outra conta. Região usada pelo projeto: **us-east-1 / Norte da Virgínia**.
2. Aguarde o agente confirmar health e executar uma rodada nova de testes. Ele deve informar **horário UTC/início-fim**, IDs dos eventos e IDs gravados. Não usar screenshots de logs antigos como se fossem dessa rodada.
3. O agente usa somente leituras/relatos sintéticos. Não enviar currículo, nome pessoal ou credenciais no payload. Nunca colocar chave em URL ou corpo de JSON; header real só em memória.
4. Antes do print, ocultar nome/e-mail/ID da conta no cabeçalho. **Nunca revelar senhas/tokens/chaves na tela**, nem para salvar um “original privado”. Originais com dados pessoais incidentais serão copiados para privado antes da tarja; segredos não devem ser capturados.
5. Não alterar SG, IAM, timeout, código ou variáveis para preparar as imagens. O typo de rate limit já está documentado; isso não é uma ordem para renomeá-lo no console.

## 3. Onde abrir os logs

**Caminho direto:** CloudWatch → **Logs / Grupos de logs** → **`/aws/lambda/CP-2`** → pesquisar todos os streams/eventos no intervalo informado pelo agente.

**Caminho pela função:** Lambda → **Functions / Funções** → **`CP-2`** → **Monitor / Monitorar** → **View CloudWatch logs / Ver logs no CloudWatch**.

Selecione o intervalo da execução nova (inicialmente “última hora”; depois restrinja). O navegador pode exibir hora local e os eventos UTC: use a janela/IDs que o agente forneceu. Expanda as mensagens, mantenha **timestamp + nível + texto** legíveis e, quando possível, RequestId para correlacionar chamadas.

### CW-C — crítico

Na mesma chamada, mostrar:
- `CLASSIFICACAO risco=critico ...`;
- **WARNING** `ALERTA CIDADAO: dispositivo ... em nivel critico (...)`;
- `GRAVADO NO RDS id=...`.

Enquadrar também o dispositivo/métrica/valor, por exemplo `lab-iot-bancada-01`, `temperatura_c` e46/50 se forem os valores enviados pelo simulador. Os valores/IDs devem ser os reais, não precisam ser iguais aos exemplos. Se não couber tudo legível, fazer duas imagens, mantendo identificação da mesma requisição.

Nome sugerido: `AAAAMMDD_cloudwatch_critico.png` (use a data real).

### CW-D — descarte

Depois que o agente enviar uma requisição sem um campo obrigatório, expandir a mensagem **WARNING**:

```text
LEITURA DESCARTADA - campo obrigatorio ausente: metrica
```

Ou o campo efetivamente omitido. Manter timestamp/nível/mensagem; a resposta **400** deve aparecer no terminal do teste preparado pelo agente. Essa requisição **não** deve ser apresentada como gravada com sucesso no RDS.

Nome sugerido: `AAAAMMDD_cloudwatch_descarte.png`.

### CW-K — chave inválida

Depois do teste com chave propositalmente inválida (não a chave real), mostrar **WARNING**:

```text
CHAVE INVALIDA dispositivo=...
```

Mostrar dispositivo, timestamp e RequestId quando disponível. A resposta **401** fica no terminal do teste. Não mostrar o valor da chave, nem mesmo como forma de “comprovar” o header. Esta chamada também não corresponde a uma inserção bem-sucedida.

Nome sugerido: `AAAAMMDD_cloudwatch_chave_invalida.png`.

**CW-D/CW-K podem estar em uma única captura** se ambas as mensagens e níveis ficarem legíveis; caso contrário, são dois prints.

### Ingestão normal — se for refazer na rodada nova

Mostrar `PAYLOAD RECEBIDO`, `DISPOSITIVO=...`, `CLASSIFICACAO risco=normal` e `GRAVADO NO RDS id=...`. O payload/valor deve corresponder ao terminal e ao SELECT. Pode haver mais de uma captura da mesma chamada.

Nome sugerido: `AAAAMMDD_cloudwatch_ingestao.png`.

### Alternativa de consulta — Logs Insights (opcional)

Selecione **somente** o grupo `/aws/lambda/CP-2` e a janela de tempo da rodada; esta consulta facilita encontrar as mensagens, sem alterar recursos:

```text
fields @timestamp, @requestId, @message
| filter @message like /PAYLOAD RECEBIDO|DISPOSITIVO=|CLASSIFICACAO|GRAVADO NO RDS|ALERTA CIDADAO|LEITURA DESCARTADA|CHAVE INVALIDA/
| sort @timestamp asc
| limit 200
```

A consulta filtra **mensagens**, não garante que todas sejam da mesma chamada. Use horário/RequestId/IDs para correlacionar. Não inventar resultado se ela não retornar linhas. Se usar a tela normal de eventos, não colar essa sintaxe no campo de filtro dela: a linguagem é diferente.

## 4. SIM — print do simulador, não do painel de configuração AWS

O agente prepara a execução real do simulador do projeto contra a **Function URL**, não localhost. A tela deve mostrar payload/valor enviado e resposta **201**, `id`, `nivel_risco`/`alerta`; precisa incluir caso normal e evolução até crítico.

O simulador atual oferece `--cenario normal --leituras 2` e `--cenario evolucao --leituras 6 --com-chave`, com URL/chave carregadas em memória pelo agente. Não colar credenciais no comando visível. Como referência, a evolução atual envia30,34,38,42,46,50°C, mas a captura deve refletir a execução feita. Duas imagens são aceitáveis se normal e crítico não couberem.

Nome sugerido: `AAAAMMDD_simulador_function_url.png` (ou sufixos `_normal`/`_risco`). PNG antigo de Wokwi→API isolada **não substitui** esta imagem.

## 5. DB — print da consulta real ao RDS

O console **RDS → Databases / Bancos de dados → `cp1-cloud`** mostra infraestrutura, não comprova as linhas da tabela. Não confundir o identificador da instância **cp1-cloud** com o banco do app **citizentech**. Não exigir um Query Editor incompatível com essa instância: usar cliente SQL/psql conectado ao RDS, com TLS `verify-full` e usuário de menor privilégio, preparado pelo agente.

Capturar **consulta + resultado** com colunas legíveis. Consulta somente de leitura, compatível com o schema atual:

```sql
SELECT id, evento_id, dispositivo_id, metrica, valor,
       nivel_risco, alerta, autenticado, analise_status, criado_em
FROM public.ocorrencias
WHERE dispositivo_id = 'lab-iot-bancada-01'
ORDER BY id DESC
LIMIT 20;
```

O agente pode restringi-la aos IDs/horário reais da nova rodada. Mostrar linhas normais/atencao/critico, IDs e datas que batam com simulador/logs; não confundir linhas históricas com inserções novas. Não exibir senha, conexão completa com credenciais ou campo de relato pessoal. Não é necessário capturar CREATE/ALTER/GRANT nem modificar o banco.

Nome sugerido: `AAAAMMDD_rds_ocorrencias.png`. O número de linhas **atual** deve ser lido do banco, não copiado das10linhas da execução de16/11 nem das6linhas do Wokwi local.

## 6. Variáveis Lambda — só se precisar atualizar a imagem existente

Lambda → `CP-2` → **Configuration / Configuração → Environment variables / Variáveis de ambiente**. Mostrar os nomes das variáveis de conexão/provedor e apenas valores não secretos, se for seguro. Valores de `DB_PASSWORD`, `DEVICE_KEY`, `HF_TOKEN` e quaisquer credenciais **nunca devem estar visíveis**. Não abrir/revelar valores para tirar print. Se o console os mostrar, interromper e ocultá-los antes da captura.

O resultado IA pode continuar `indisponivel` por AccessDenied/HF402. Mostrar a condição real; não exigir imagem de sentimento positivo/classificado se a conta não executou a análise.

## 7. Salvar e entregar ao agente

- Pasta: `06_Cloud/evidencias/`; nomes datados, sem sobrescrever arquivos anteriores e **sem commitar originais não revisados**. Pode fornecer os arquivos ao agente para ele salvar com segurança.
- O agente preserva cópias privadas dos originais com PII em `.dados/cloud/privado`, confere SHA, cria derivadas tarjadas e só então adiciona arquivos limpos ao Git. Preservar originais, não mover/apagar. Chaves/senhas não devem existir em nenhum desses prints.
- Não mudar o nível ou o texto do log, montar logs históricos como imagem nova ou acrescentar status/IDs numa edição de imagem. Tarja é só para privacidade, não para fabricar execução.
- Critério final: as quatro categorias do enunciado ficam cobertas por imagens legíveis; casos negativos e crítico têm logs reais; os IDs/valores/timestamps se correlacionam. O agente atualiza inventário/README e valida o pacote.
