# Registro de decisões — reorganização do código (untangle), 17/11/2026

Pedido do usuário: repositório organizado, fácil de entender e de replicar. Escopo aprovado: **web, tools, cloud (só testes/organização, nunca o código implantado da Lambda) e api**. `app/ml` congelado (holdout, model cards e notebooks dependem dele). Comportamento público não muda; corpos de erro `{erro, detalhes}` e status HTTP ficam idênticos.

Diagnóstico completo (IDs H/N/S/X): relatório somente leitura de 17/11. Cada correção abaixo vem acima dos problemas que resolve.

## Feito

- **Entregas declaradas num lugar só** — o empacotador passa a cobrir os 6 relatórios PDF (com título e limite de 15 p em Cyber) e gera os `requirements.txt` de ML/RNA com versões conferidas no `uv.lock` (lista declarada no empacotador, não extraída automaticamente).
  - PDFs de AICSS, Cyber, Data Science e CTP fora do manifesto: `--verificar` não os via.
  - `05_ML/requirements.txt` e `07_RedesNeurais/requirements.txt` do esqueleto (tensorflow, sem `citizentech_ml`) não instalavam o que os notebooks importam.
- **Replicação documentada e executável** — `README.md` na raiz, `app/tools/ambiente_teste.ps1`, `app/tools/testar_tudo.ps1`, `.env.example` completo e portável.
  - Variáveis `PG_TESTE_*`, `ORACLE_TESTE_*` e o schema `CT_TESTE_*` só existiam em scripts fora do repositório.
  - `.env.example` com caminhos absolutos da máquina e variáveis mortas (`APP_ENV`, `CITIZENTECH_TMP`, `ADZUNA_MAX_CHAMADAS`, `ORACLE_FIAP_*`); 14 variáveis lidas pelo código sem documentação.
- **Documentos fora de uso saem da superfície** — `docs/historico/` (inclui o panorama interno); `.gitignore` cobre originais com PII e estado da ferramenta de design.

- **Interface no design system NOUS** (S16, `48be785`) — tokens só em `app/web/src/estilo/tema.css`; matriz de pixels three.js isolada em `src/visual/`; foco visível em todos os controles.
- **API e tools desembaraçados** (S17, `fde8f6e`) — catálogo lido num módulo só (`citizentech/catalogo.py`), utilidades de banco, consentimento como dependência única, erros de domínio fora da camada de dados, serviço de leituras, retentativas da LLM em laço, laboratório por dado (`tem_laboratorio`), `tools/_comum.py`, conftest aplicando 001–007 com as regras de `aplicar_ddl.py`, contrato de hash com a Lambda.
- **Cópia de CTP autocontida** — `leituras/rotas.py` deixa de importar `laboratorio` (tarde, dentro de `try`): a app completa registra o gancho do relato em `main.py` (`leituras/ganchos.py`); o modo isolado não registra nada. Teste `test_copia_ctp_e_autocontida` impede regressão.
  - A cópia entregue em `04_CTP_Python/codigo` registrava `ModuleNotFoundError` a cada leitura com sessão (verificado rodando-a isolada).

- **Interface organizada por responsabilidade** (S18, merge `a14ebef`): requisições e mensagens de erro passam pelo cliente comum; as listas e os rótulos do domínio ficam em [dominio/](<../app/web/src/dominio/>); [navegacao.ts](<../app/web/src/mercado/navegacao.ts>) trata o estado da URL. O plano tem um único dono do estado. O componente de bloqueio por consentimento substitui quatro cópias; não foi feita uma divisão geral das telas.
- **Tabela do painel técnico** (`d8700ab`): o teste de regressão detectou que a região cortava a última linha (MLP); o painel passou a comportar as seis linhas sem rolagem vertical. O teste de foco e o teste da tabela ficam em [e2e/](<../app/web/e2e/>).

- **Ambiente de QA local** (S19, merge `8dbe4f7`): instalação incompleta agora interrompe a regressão. No Windows, `ambiente_teste.ps1` aceita só o Oracle do compose e usuário de teste, desabilita integrações externas, gera chaves efêmeras e cria runtime separado. Os testes de preparo usam configurações fictícias; a regressão foi repetida com os serviços locais. A revisão do README apontou a criação das tabelas em schema novo: o guia agora distingue listar os DDL de aplicá-los com `--confirmar`.

## Decidido não fazer (com motivo)

- Alterar `app/cloud/src` (Lambda implantada e evidenciada): só testes de paridade (C14).
- Limites de validação entre API e web (C3): não foi criada uma rota nem verificada paridade automática de todos os limites. Rever quando mudar uma validação pública.
- Polling do laboratório com backoff (X3) e aviso de sessão expirada (C11): decisões de produto, ficam como estão; o aviso morto é removido.
