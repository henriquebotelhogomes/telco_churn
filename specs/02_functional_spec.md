# 02 — Especificação Funcional

> Define **o que** o RetainIQ faz, do ponto de vista do usuário, com casos de uso
> rastreáveis (`RF-XX`) e estado de entrega (`MVP` / `V1` / `Futuro`).

---

## 1. Personas

| Persona | Objetivo | Dor atual |
|---------|----------|-----------|
| **Camila — Líder de Customer Success** | Reduzir churn com a equipe que tem | Descobre cancelamento tarde demais; não sabe priorizar |
| **Rafael — Head de Receita** | Proteger e prever MRR/ARR | Não consegue quantificar receita em risco |
| **Bruno — Engenheiro de Dados** | Conectar dados sem virar dono do problema | Pipelines frágeis, modelos sem manutenção |
| **Admin de Conta** | Gerir usuários, papéis e segurança | Falta de RBAC e auditoria |

---

## 2. Mapa de Capacidades

```
RetainIQ
├── Onboarding & Conexão de Dados
├── Predição de Churn (scoring)
├── Explicabilidade (drivers do risco)
├── Priorização (risco × valor)
├── Playbooks & Ações de Retenção
├── Simulação ("what-if")
├── Cohorts & Analytics
├── Monitoramento de Modelo (MLOps)
└── Administração (tenants, RBAC, billing, auditoria)
```

---

## 3. Casos de Uso e Requisitos Funcionais

### 3.1 Onboarding e Conexão de Dados
- **RF-01** `MVP` — O sistema **DEVE** permitir upload de CSV de clientes
  (compatível com o schema Telco) para scoring imediato.
- **RF-02** `V1` — O sistema **DEVERIA** oferecer conectores (Postgres, BigQuery,
  Snowflake, S3) com agendamento de sincronização.
- **RF-03** `V1` — O sistema **DEVE** validar o schema de entrada e reportar
  erros de qualidade de dados de forma legível (linha, coluna, motivo).

### 3.2 Predição (Scoring)
- **RF-10** `MVP` — O sistema **DEVE** calcular a **probabilidade de churn**
  (0–1) e uma **classe de risco** (Baixo/Médio/Alto) por cliente.
- **RF-11** `MVP` — O sistema **DEVE** expor scoring **individual** (tempo real)
  e em **lote** (batch).
- **RF-12** `V1` — O sistema **DEVERIA** estimar a **janela temporal** de risco
  (ex.: risco nos próximos 30/60/90 dias).
- **RF-13** `MVP` — Cada predição **DEVE** registrar a **versão do modelo** usada
  (rastreabilidade).

### 3.3 Explicabilidade
- **RF-20** `MVP` — Para cada cliente, o sistema **DEVE** apresentar os
  **principais fatores** que aumentam/diminuem o risco (SHAP local).
- **RF-21** `V1` — O sistema **DEVERIA** apresentar **importância global** das
  features no nível do tenant.
- **RF-22** `V1` — As explicações **DEVEM** ser traduzidas para linguagem de
  negócio (ex.: "Contrato mensal" em vez de `Contract=Month-to-month`).

### 3.4 Priorização
- **RF-30** `MVP` — O sistema **DEVE** ordenar clientes por **risco ponderado
  pelo valor** (ex.: `score × MRR`), produzindo uma fila de ação.
- **RF-31** `V1` — O sistema **DEVERIA** permitir **segmentos/filtros**
  salvos (ex.: "Alto risco + Fibra + Contrato mensal").

### 3.5 Playbooks e Ações
- **RF-40** `V1` — O sistema **DEVERIA** recomendar **playbooks de retenção**
  por driver de risco (ex.: oferta de fidelidade para contrato mensal).
- **RF-41** `V1` — O usuário **DEVE** poder registrar a **ação tomada** e o
  **resultado** (reteve / cancelou) para fechar o loop.
- **RF-42** `Futuro` — Integração outbound (e-mail/CRM) para disparar ações.

### 3.6 Simulação "What-if"
- **RF-50** `V1` — O sistema **DEVERIA** permitir alterar atributos de um cliente
  e recalcular o risco em tempo real (ex.: "se migrar para contrato anual").

### 3.7 Cohorts e Analytics
- **RF-60** `V1` — O sistema **DEVERIA** exibir **evolução do churn** e **receita
  em risco** por coorte e período.
- **RF-61** `V1` — O sistema **DEVE** exibir métricas de modelo
  (ROC-AUC, recall, precisão) ao longo do tempo.

### 3.8 Monitoramento de Modelo (MLOps)
- **RF-70** `V1` — O sistema **DEVE** detectar e alertar **data drift** e
  **concept drift**.
- **RF-71** `V1` — O sistema **DEVERIA** permitir **re-treino** versionado e
  **rollback** de modelo.
- **RF-72** `V1` — O sistema **DEVE** manter um **registro de modelos** com
  métricas, dataset e data de promoção.

### 3.9 Administração e Segurança
- **RF-80** `MVP` — O sistema **DEVE** ter **autenticação** e **isolamento por
  tenant**.
- **RF-81** `V1` — O sistema **DEVE** suportar **RBAC** (Admin, Analista, Leitor).
- **RF-82** `V1` — O sistema **DEVE** registrar **trilha de auditoria** das ações
  sensíveis (quem, o quê, quando).
- **RF-83** `Futuro` — SSO (OIDC/SAML) e SCIM para contas enterprise.

---

## 4. Jornada do Usuário (fluxo principal)

```
1. Login (tenant) ─▶ 2. Conectar/Upload dados ─▶ 3. Scoring em lote
        │
        ▼
4. Dashboard: fila priorizada por receita em risco
        │
        ▼
5. Abrir cliente ─▶ ver score + drivers (SHAP) + simulação what-if
        │
        ▼
6. Escolher playbook ─▶ registrar ação ─▶ acompanhar resultado
        │
        ▼
7. Analytics: impacto das ações + saúde do modelo
```

---

## 5. Regras de Negócio-Chave

- **RN-01** — O custo de um **Falso Negativo** (perder cliente sem prever) é
  maior que o de um Falso Positivo; o **recall** da classe churn é priorizado
  (herdado da decisão original do projeto).
- **RN-02** — Toda predição exibida ao usuário **DEVE** ser acompanhada da versão
  do modelo e do timestamp, garantindo reprodutibilidade.
- **RN-03** — Classes de risco padrão: `Baixo < 0.35 ≤ Médio < 0.65 ≤ Alto`
  (limiares configuráveis por tenant).

---

## 6. Requisitos de Internacionalização

- **RF-90** `MVP` — A interface e a API de negócio **DEVEM** suportar
  **Português (pt-BR)** e **Inglês (en-US)**. O padrão *Adapter* já existente
  (PT → schema do modelo) é generalizado para um **mapa de tradução por locale**.

---

## 7. Fora de Escopo (nesta fase)

- Orquestração de campanhas de marketing multicanal completas.
- Modelos de *uplift/causalidade* avançados (avaliados como `Futuro`).
- Data residency por região regulatória (mapeado em `08_security.md`).

