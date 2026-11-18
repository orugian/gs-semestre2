# Roteiro de gravação — Cybersecurity (até 5 min)

**Exigido pelo enunciado:** problema · solução · riscos · proteção implementada. Não precisa de rosto.

## Antes de gravar (5 min)

1. Na raiz do repositório: `powershell -NoProfile -ExecutionPolicy Bypass -File gravacao\subir_app.ps1` (não precisa de IA).
2. Abra um terminal novo, aumente a fonte (Ctrl + roda do mouse) e deixe pronto, **sem executar**:
   ```powershell
   cd app\tools
   uv run --frozen python demo_protecoes.py --base http://127.0.0.1:8000
   ```
3. Abra `02_Cybersecurity\relatorio.pdf` nas seções da **matriz de riscos** e da **LGPD**.
4. Abra http://localhost:5173 na aba **Minha transição**.
5. Feche e-mail, chats e qualquer janela com dados pessoais. Não mostre `app\.env`.

## Gravação

| Tempo | O que dizer (resumo; use suas palavras) | Tela |
|---|---|---|
| 0:00–0:30 | "Profissionais em transição de carreira decidem com pouca evidência e entregam currículo a vários sites. O CitizenTech compara destinos sem nota única e usa IA no currículo — por isso a segurança é central." | App, Minha transição |
| 0:30–1:10 | Arquitetura: web → API → Oracle e MongoDB → IA só com texto redigido e confirmado → laboratório IoT → Lambda e RDS na AWS. | PDF, diagrama da §1 |
| 1:10–2:10 | Riscos: matriz com 10 riscos. Os residuais mais altos: vazamento de dado do currículo; RDS público e Function URL sem autenticação obrigatória (exceção acadêmica: a Lambda fica fora de VPC); falso recrutador (engenharia social). | PDF, matriz |
| 2:10–4:10 | **Demonstração ao vivo:** rode o `demo_protecoes.py`. Comente cada linha: senha curta → 400; cookie HttpOnly e Secure; token adulterado → 401; POST sem CSRF → 403; CPF, e-mail e telefone fictícios redigidos; usuário B não lê o currículo de A → 404; IA bloqueada antes da confirmação → 403; logout invalida a sessão; força bruta → 429. Termine mostrando `falhas=0`. | Terminal |
| 4:10–4:40 | LGPD: consentimento por finalidade e revogável; o original do currículo não é guardado; a pessoa vê e edita o texto antes da IA; o provedor de IA é chamado com `data_collection=deny`. | PDF, LGPD |
| 4:40–5:00 | O que fica para produção: MFA, RDS privado, WAF, exclusão de conta. Nomes e RMs. | PDF ou slide |

## Não diga

"100% seguro", "inviolável", "LGPD garantida", "sem riscos". Diga "reduz", "mitiga", "risco residual".

## Se algo der errado

- `demo_protecoes.py` mostra `FALHOU` em alguma linha: pare a gravação e avise o grupo; não edite a saída.
- `Conexão recusada`: a API não está no ar; rode de novo o `subir_app.ps1`.

## Checklist
- [ ] até 5 min · [ ] `falhas=0` na tela · [ ] nenhuma senha/e-mail real na tela · [ ] nomes e RMs · [ ] YouTube não listado · [ ] link testado em janela anônima
