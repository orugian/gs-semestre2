# S5 — aceite independente e integração em 15/11/2026

**Verificado pelo orquestrador.** Merge `c391eac` em `main`, commits da fatia `1e409a5` e `b94b0de`. O trabalho original não commitado foi preservado, corrigido, commitado e integrado; o worktree também permanece disponível.

## RED independente e contraexemplos

O teste público original de registro/login/perfil foi copiado sem alterações para um worktree de `main` com somente a rota mínima de registro501. Comando em `app/api`:

```powershell
uv run pytest tests/test_auth.py::test_ciclo_completo_registro_login_me -q -o markers=oracle
```

Saída real: `AssertionError: assert501==201`, saída1. A falha ocorreu na asserção do status de registro, não em importação/sintaxe ou conexão. Isso comprova a sensibilidade do teste sobre base+esqueleto; não é reconstrução retroativa da ordem de autoria TDD.

Antes de executar o rascunho adversarial, foram corrigidos seus próprios defeitos: login de preparação não consome uma tentativa do teste de limite por e-mail; tokens adulterados partem de sessão aceita e alteram uma propriedade por vez. Os casos sem Oracle passaram7/7; os16 casos dependentes foram identificados separadamente, nunca usados como prova de integração quando não executados.

Contraexemplos novos confirmaram6falhas: ausência deiat/jti aceita; expiração com string/dict/list produzindoTypeError; senha gigante chegando ao banco antes da validação400. O `agy` corrigiu os casos na rodada2 e acrescentou validação de tipos, fail-closed, purga do limitador e prova de isolamento em processo novo, sem manipular `sys.modules` para mascarar a suíte.

## Oracle real, sem segredos em arquivos

O usuário autorizou expressamente criar **outro schema exclusivo no Oracle Docker local**, com privilégios mínimos e senha gerada somente em memória. Foi usado `CT_S5_TESTE_651E903F48`; o schema anterior `CT_S5_TESTE` e seus dados não foram alterados. A senha não aparece neste documento, em comandos expandidos ou em arquivos; foi esquecida ao encerrar o runner.

O mesmo processo seguro manteve as variáveis de conexão para executar as etapas abaixo. Comando em cada componenteAPI:

```powershell
uv run pytest -q -rs --tb=short -o addopts=''
uv run ruff check .
```

| Etapa executada pelo orquestrador | Resultado real |
|---|---|
| Worktree após rodada2 do implementador | 204passed, zero skips, 101,57s; ruff limpo |
| Worktree após adjudicação/correções pequenas | 208passed, zero skips, 102,97s; ruff limpo |
| **Main após merge** | **208passed, zero skips, 104,44s; ruff limpo** |

Aviso único: depreciação Starlette/TestClient sobre uso dehttpx. Não houve exclusão de testes nem substituição de Oracle por fake. Os testes de autorização exercitam duas contas e persistência relacional real; SQL usa binds.

O runner terminou com saída0 e o Oracle foi parado com `docker stop`, sem excluir schema, volume ou dados. Os logs completos ficam na trilha local `.kaiser/reports/`, sem senha.

## Revisão independente via agy

Nova chamada `agy --mode plan --print-timeout20m`, somente leitura, sobre patch **de três pontos** do candidato `1e409a5`, contrato e adendo; sem acesso ao relatório do autor. Saída0, sem bloqueadores estáticos. As referências de linha do relatório correspondem em parte ao patch, não necessariamente às linhas locais das fontes.

Adjudicação pelo orquestrador:

| Achado | Decisão |
|---|---|
| RV-S5-01: rate limit por processo | Aceito como limitação explícita do contrato/README; não há coordenação entre workers. |
| RV-S5-02: logout global | Aceito: incremento da versão do usuário invalida todas as sessões atuais, conforme contrato. |
| RV-S5-03:409 no cadastro revela existência | Aceito como risco residual declarado, requerido pelo contrato. |
| RV-S5-04: import do driver ausente pode escapar do503 | Aceito como dívida de ambiente não sincronizado; não reproduzido dinamicamente. O pacote está no lock e a execução real usou `uv`. Não mover import para o topo a ponto de quebrar CTP isolado. |
| RV-S5-05: leitura redundante de configuração | Corrigido: reutilização da configuração já validada no login. |
| RV-S5-06: segredo só whitespace | Reproduzido e corrigido com RED/GREEN: configuração com32espaços/tabulações é recusada. |
| Achado próprio adicional: expiração vazia | Reproduzido e corrigido: default60 somente quando variável ausente; string vazia/espaços é configuração inválida503. |

Os quatro últimos contraexemplos de configuração pertinentes deram **4failed/38passed** antes das correções; a suíte final real passou208testes. As alterações pós-revisão foram de poucas linhas em `b94b0de` e **não receberam segunda revisão independente**.

Gitleaks inicialmente bloqueou uma string de teste de segredo curto como falso positivo. Ela foi substituída por `"x" *31`, mantendo/reforçando o teste de limite32. Teste específico1passed; nova varredura limpa. Não houve exceção no detector nem `--no-verify`.

## Regressão integrada e limites

Também executado nesta sessão em `main`: ML110passed, Cloud50passed, Tools20passed, ruff limpo nesses componentes; Web1teste e build/typecheck passaram.

**Entregue nesta fatia:** rotas de autenticação/perfil/consentimentos, sessão por cookie, CSRF, rate limit, autorização por proprietário e persistênciaOracle.

**Não verificado/não entregue por esta fatia:** tela de autenticação, smoke em navegador real, MFA/recuperação/rotaçãoJWT, coordenação distribuída de taxa, execução no OracleFIAP e demonstração humana em vídeo. Não existe alegação de segurança absoluta ou ausência de todo timingattack baseada em revisão estática.

Sem leitura de`.env`, abertura do holdout, exclusão de dados ou push. A evidência inicial permanece preservada em [aceite parcial](<20261115_s5_aceite_parcial.txt>).
