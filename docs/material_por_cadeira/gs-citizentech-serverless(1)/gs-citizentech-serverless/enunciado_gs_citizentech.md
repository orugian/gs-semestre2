# Global Solution — CitizenTech
## Ingestão Serverless de Dados de Campo: AWS Lambda + RDS + IA

### Cenário

A tecnologia já faz parte do dia a dia das pessoas, mas problemas antigos continuam de pé: enchentes que pegam o bairro de surpresa, queimadas que chegam antes do aviso, estiagem que compromete a safra do pequeno produtor, serviços públicos que só descobrem o problema depois que ele aconteceu. A Global Solution deste semestre pede soluções **CitizenTech**: tecnologia criada a partir das necessidades reais das pessoas, da grande cidade à comunidade mais remota, com o cidadão no centro da inovação.

Nesta entrega você constrói a espinha dorsal de uma CitizenTech: a camada de nuvem que **recebe os dados do mundo real e os transforma em informação útil**. Sensores em uma ponte, um drone sobrevoando a lavoura e o celular de um morador do bairro passam a enviar leituras para a mesma API serverless, que registra, classifica e persiste tudo o que chega — pronto para alimentar um painel, um alerta ou uma decisão do poder público.

A ideia central é entender que "IA e nuvem" quase nunca começam treinando modelo. Começam com **dado chegando, dado registrado e dado confiável**; o modelo pronto, consumido por API, entra depois para dar sentido a esse dado.

### Desafio

Publique uma API serverless na AWS que receba as leituras de um dispositivo de campo (ESP32, drone ou aplicativo do cidadão), **mostre no log tudo o que chegou**, classifique o nível de risco da leitura e grave o resultado em um banco PostgreSQL gerenciado.

Como nem todo grupo terá hardware disponível, o dispositivo pode ser **simulado por software**: um script que envia o mesmo JSON que o ESP32 enviaria. A API não distingue um do outro — e é justamente essa indiferença entre o sensor real e o simulador que faz o projeto testável.

### O que você vai exercitar

- Expor uma função Lambda pela Function URL e tratar rotas e método HTTP (GET e POST).
- Ler o corpo de uma requisição vinda de um dispositivo e validar os campos obrigatórios.
- Registrar a telemetria no CloudWatch Logs de forma legível, incluindo o descarte de leituras inválidas.
- Persistir o dado no RDS PostgreSQL a partir de uma função serverless.
- Consumir um modelo de IA pronto por API (Hugging Face) ou um serviço gerenciado (Amazon Comprehend), guardando o token em variável de ambiente e sem segredo no código.
- Simular o comportamento de um dispositivo IoT para validar a ponta a ponta sem depender de hardware.

### Pré-requisitos

Conta AWS com permissão para criar função Lambda e instância RDS PostgreSQL. A função **não** deve ser criada dentro de uma VPC, para que tenha saída para a internet sem configuração adicional. Se você já publicou a função `challenge-api` com Function URL e banco acessível nas atividades anteriores, reaproveite essa base: aqui ela ganha a rota de ingestão.

### Arquitetura

```
ESP32 / drone / app do cidadão          (dispositivo real ou simulador)
            |  HTTPS POST  {dispositivo, gps, métrica, valor, relato}
            v
     AWS Lambda (Function URL)          rota POST /ocorrencias
            |-- log  -> CloudWatch Logs (payload, dispositivo, classificação)
            |-- IA   -> Hugging Face ou Amazon Comprehend (classifica o relato)
            v
     Amazon RDS PostgreSQL              tabela ocorrencias
            |
            v
     Painel / alerta ao cidadão         (consumo via GET /ocorrencias)
```

### Requisitos obrigatórios

1. **Defina o cenário CitizenTech do grupo.** Escolha o problema, quem é o cidadão beneficiado, qual métrica o dispositivo mede e qual o limiar que caracteriza risco. Exemplos: nível de córrego em centímetros, concentração de fumaça em ppm, umidade do solo em porcentagem, temperatura ambiente. O cenário escolhido deve aparecer no README.

2. **Crie a tabela `ocorrencias`** no RDS PostgreSQL, com identificação do dispositivo, tipo, coordenadas, métrica, valor, relato em texto, resultado da análise, nível de risco e data/hora. O script de criação vai na entrega.

3. **Crie a rota `POST /ocorrencias`** na Lambda. Ela deve ler o JSON do corpo, validar os campos obrigatórios (`dispositivo_id`, `metrica`, `valor`), devolver `400` quando faltar campo e `201` com o registro criado quando der certo. Mantenha `GET /health` e acrescente `GET /ocorrencias` para listar o que já foi gravado.

4. **Registre no log tudo o que chega.** A função precisa gravar no CloudWatch, em linhas separadas e legíveis: o payload bruto recebido, os dados interpretados (dispositivo, tipo, GPS, métrica e valor), o resultado da classificação e o `id` gerado na gravação. Leituras inválidas e valores em nível crítico devem sair como `WARNING`.

5. **Classifique o nível de risco** da leitura comparando o valor com os limiares do seu cenário, devolvendo `normal`, `atencao` ou `critico`. Essa classificação é local, não depende de rede e deve funcionar sempre.

6. **Grave o resultado no banco** e devolva na resposta o `id` do registro, o nível de risco e se a leitura dispara alerta ao cidadão.

7. **Construa o simulador do dispositivo.** Um script que assuma a identidade de um ESP32 ou de um drone e envie uma sequência de leituras para a Function URL, com valores evoluindo ao longo do tempo até cruzar o limiar crítico. O simulador deve imprimir, a cada envio, o que mandou e o que a API respondeu. Quem tiver a placa física pode entregar o firmware no lugar do script — o JSON enviado é o mesmo.

8. **Teste de ponta a ponta.** Rode o simulador em um cenário normal e em um cenário de risco, e comprove no CloudWatch que as leituras chegaram e no banco que foram gravadas.

### Camada de IA

Além do limiar numérico, a API deve classificar o **relato em texto** que acompanha a ocorrência — o que o morador escreveu ao registrar o problema. Escolha um caminho e justifique a escolha na entrega:

**Caminho A — Hugging Face (recomendado).** Gere um token gratuito do tipo *Read*, cadastre-o na Lambda como variável de ambiente `HF_TOKEN` e envie o texto ao modelo `cardiffnlp/twitter-xlm-roberta-base-sentiment`, devolvendo o rótulo de maior pontuação com a confiança. A chamada usa apenas `urllib`: nenhuma biblioteca nova entra no pacote. Mantenha o *timeout* da função em 30 segundos. Atenção: o endpoint correto hoje é `https://router.huggingface.co/hf-inference/models/{modelo}` — o antigo `api-inference.huggingface.co` foi desativado e responde erro 410.

**Caminho B — Amazon Comprehend.** Quem tiver permissão de IAM pode anexar a política `ComprehendReadOnly` à role da Lambda e trocar apenas a função de análise pela detecção de sentimento do Comprehend, com idioma `pt`. O restante da API não muda.

Em qualquer caminho, a falha do modelo **não pode derrubar a ingestão**: se o serviço de IA não responder, a leitura ainda precisa ser classificada por limiar, gravada no banco e registrada no log.

### Entregáveis

- Function URL da Lambda em funcionamento.
- Endpoint do RDS PostgreSQL (sem a senha).
- Script de criação da tabela `ocorrencias`.
- Arquivo final da função Lambda e o código do simulador (ou o firmware do ESP32).
- Quatro evidências em imagem: a variável de ambiente cadastrada; o simulador enviando as leituras; o trecho do CloudWatch Logs com o payload chegando e a classificação; a consulta no banco com as ocorrências gravadas.
- README com o cenário CitizenTech escolhido, o cidadão beneficiado, os limiares adotados, o caminho de IA usado e o porquê, e o passo a passo para reproduzir a solução.
- Vídeo de até 5 minutos demonstrando o simulador enviando dados, o log recebendo e o banco gravando.

### Critérios de avaliação

| Critério | Peso |
|---|---|
| Ingestão funcionando: POST recebendo, validando e respondendo corretamente | 25% |
| Observabilidade: log claro do que chega, do que é classificado e do que é descartado | 20% |
| Persistência: modelo de dados coerente e gravação consistente no RDS | 20% |
| Camada de IA integrada com token protegido e falha tratada sem derrubar a ingestão | 15% |
| Simulador do dispositivo e teste de ponta a ponta | 10% |
| Aderência ao CitizenTech: problema real, cidadão identificado, ODS justificado | 10% |

### Conexão com os ODS

Identifique no README a quais Objetivos de Desenvolvimento Sustentável a solução se conecta e de que forma contribui. Os mais diretos neste desafio são o **ODS 3 — Saúde e bem-estar**, o **ODS 10 — Redução das desigualdades** e o **ODS 11 — Cidades e comunidades sustentáveis**, já que levar monitoramento e alerta a lugares onde a infraestrutura é limitada é exatamente o tipo de desigualdade que a tecnologia pode reduzir.
