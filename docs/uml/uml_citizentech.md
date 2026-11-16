# CitizenTech — modelos UML da solução

> Diagramas em Mermaid (o GitHub os renderiza). As imagens em `docs/uml/img/` são geradas a partir deste arquivo por `app/tools/renderizar_mermaid.py`. Os diagramas descrevem o que está **implementado** em `main`; o que é evolução futura aparece marcado como tal.

## 1. Casos de uso

```mermaid
flowchart TB
  P([Profissional em transição])
  subgraph S[Sistema CitizenTech]
    direction LR
    subgraph J[Jornada]
      direction TB
      UC1[Criar conta e entrar] --> UC2[Conceder e revogar consentimentos] --> UC3[Registrar intenção] --> UC4[Enviar currículo e revisar texto redigido] --> UC5[Revisar competências sugeridas pela IA]
    end
    subgraph D2[Decisão e prática]
      direction TB
      UC6[Comparar até 3 destinos] --> UC8[Escolher destino e seguir o plano] --> UC9[Exercício diagnóstico: refazer ou discordar] --> UC10[Sessão de laboratório e relato]
      UC7[Ver mercado formal observado e previsto]
    end
    UC11[Enviar leituras]
    UC12[Revisar rubricas e requisitos do catálogo]
  end
  G([Grupo curador do catálogo])
  DV([Dispositivo da bancada: ESP32 ou simulador])
  N([Nuvem AWS: Lambda e RDS])
  P --> J
  P --> D2
  DV --> UC11
  UC11 -. outbox .-> N
  G --> UC12
```

## 2. Componentes

```mermaid
flowchart TB
  subgraph Navegador
    WEB[app/web<br/>React 19 + Astryx]
  end
  subgraph API[app/api — FastAPI]
    AUTH[auth + consentimentos]
    CV[curriculo<br/>redação de PII]
    COMP[competencias<br/>extração LLM]
    CMP[comparacao<br/>regras sem score]
    PLN[plano]
    AVA[avaliacao<br/>50/50 + rubrica]
    LAB[laboratorio]
    LEI[leituras CTP<br/>CSV + indicadores]
    OUT[outbox SQLite<br/>worker]
    MER[mercado<br/>snapshot + Adzuna]
  end
  ORA[(Oracle<br/>dados relacionais)]
  MON[(MongoDB Atlas<br/>textos redigidos, model cards)]
  LLM[[OpenRouter<br/>DeepSeek / fallback]]
  ML[app/ml<br/>baselines, RF, HGB, MLP]
  SNAP[(Snapshot de mercado<br/>Novo Caged, hash SHA-256)]
  ESP[ESP32 / simulador]
  LAMBDA[[AWS Lambda CP-2<br/>Function URL]]
  RDS[(RDS PostgreSQL<br/>ocorrencias)]
  CW[[CloudWatch Logs]]
  CMPH[[Amazon Comprehend]]

  WEB -->|HTTPS, cookie + CSRF| API
  AUTH & CMP & PLN & AVA & LAB & COMP --> ORA
  CV & COMP & AVA --> MON
  COMP & AVA -->|texto redigido e confirmado| LLM
  MER --> SNAP
  ML -->|gera| SNAP
  ML -->|model cards| MON
  ESP -->|POST /leituras + X-Device-Key| LEI
  LEI --> OUT -->|POST /ocorrencias| LAMBDA
  LAMBDA --> RDS
  LAMBDA --> CW
  LAMBDA -. sentimento do relato .-> CMPH
```

## 3. Sequência — currículo até competências (D22, T15)

```mermaid
sequenceDiagram
  actor P as Pessoa
  participant W as Web
  participant A as API
  participant M as MongoDB
  participant O as Oracle
  participant L as LLM (OpenRouter)
  P->>W: cola o texto do currículo
  W->>A: POST /me/experiencias (CSRF)
  A->>A: exige consentimento perfil e redige PII
  A->>M: grava só o texto redigido + SHA-256
  A-->>W: texto redigido + contagem de redações
  P->>W: revisa, edita e confirma
  W->>A: POST /me/curriculo/confirmar-envio
  A->>A: exige curriculo_llm e redige de novo o texto editado
  P->>W: Sugerir competências
  W->>A: POST /me/competencias/extrair
  A->>A: quota 5/24 h
  A->>L: texto delimitado como dado + lista fechada ESCO (JSON Schema)
  L-->>A: candidatas com trecho de origem
  A->>A: descarta fora da lista, sem trecho ou trecho inexistente
  A->>O: grava candidatas pendentes (estado declarada)
  A->>M: metadados da extração (sem texto)
  A-->>W: candidatas + descartes
  P->>W: confirmar / rejeitar / não possuo
  W->>A: PATCH /me/competencias/{id}
```

## 4. Sequência — leitura de sensor até a nuvem (S2, S3, S4)

```mermaid
sequenceDiagram
  participant E as ESP32 / simulador
  participant A as API (leituras)
  participant C as CSV durável
  participant Q as Outbox SQLite
  participant W as Worker
  participant L as Lambda
  participant R as RDS
  E->>A: POST /leituras {metrica, valor, sessao...} + X-Device-Key
  A->>A: valida, classifica risco (limiares.json), limita por dispositivo
  A->>C: grava linha (fsync)
  A->>Q: pendência pendente_nuvem
  A-->>E: 201 {risco, alerta}
  loop a cada ciclo do worker
    W->>Q: pendências prontas
    W->>L: POST /ocorrencias (X-Device-Key, sem PII)
    L->>R: INSERT (idempotente por evento_id)
    L-->>W: 201 / 200 duplicata
    W->>Q: sincronizado (ou nova tentativa com backoff)
  end
```

## 5. Estados de um requisito na comparação (D07, T07)

```mermaid
stateDiagram-v2
  [*] --> desconhecida: sem informação
  desconhecida --> declarada: pessoa confirma competência sugerida
  desconhecida --> lacuna: pessoa informa "não possuo"
  declarada --> demonstrada: exercício com as duas partes no mínimo
  declarada --> lacuna: exercício abaixo do mínimo
  desconhecida --> desconhecida: exercício parcial (IA indisponível)
  lacuna --> demonstrada: nova tentativa no mínimo
```

## 6. Modelo de dados relacional (Oracle, DDL 001–007)

```mermaid
erDiagram
  USUARIO ||--o{ CONSENTIMENTO : concede
  USUARIO ||--o{ COMPETENCIA_USUARIO : declara
  USUARIO ||--o| INTENCAO : registra
  USUARIO ||--o{ COMPARACAO : faz
  COMPARACAO ||--|{ COMPARACAO_DESTINO : contem
  USUARIO ||--o{ CAMINHO_ESCOLHIDO : escolhe
  COMPARACAO |o--o{ CAMINHO_ESCOLHIDO : origina
  CAMINHO_ESCOLHIDO ||--|| PLANO : gera
  PLANO ||--|{ CHECKPOINT : tem
  USUARIO ||--o{ TENTATIVA : realiza
  USUARIO ||--o{ SESSAO_LABORATORIO : abre
  DESTINO ||--|{ REQUISITO_DESTINO : exige
  COMPETENCIA_ESCO ||--o{ REQUISITO_DESTINO : compoe
  DESTINO ||--|{ DESTINO_OCUPACAO : agrupa
  OCUPACAO_CBO ||--|| DESTINO_OCUPACAO : pertence
  USUARIO { varchar id PK
            varchar email UK
            varchar senha_hash
            char persona_demo }
  COMPETENCIA_USUARIO { varchar id PK
                        varchar esco_id
                        varchar revisao
                        varchar estado_evidencia }
  TENTATIVA { varchar id PK
              number nota_objetiva
              number nota_llm
              varchar resultado }
  CHECKPOINT { varchar id PK
               number ordem
               varchar tipo
               varchar status }
```

**Evolução futura (não implementada):** tabelas `mercado_mensal` e `fontes` no Oracle (hoje o mercado vem do snapshot versionado com hash), exclusão de conta pela API, MFA.
