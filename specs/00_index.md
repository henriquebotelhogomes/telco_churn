# 📚 Specs — RetainIQ (Customer Retention Intelligence SaaS)

> Documentação de produto, arquitetura e engenharia para a evolução do projeto
> **Telco Churn Prediction** em um SaaS profissional de retenção de clientes.

Este diretório contém a **especificação completa** que guia a transição de um
repositório técnico de Machine Learning para um produto **SaaS multi-tenant**,
observável, seguro e escalável — pensado para impressionar recrutadores
exigentes e demonstrar maturidade de engenharia de ponta a ponta.

> ⚠️ **Escopo desta fase:** apenas documentação. Nenhuma linha de código de
> produto é escrita aqui. O objetivo é definir *o quê*, *por quê* e *como*
> antes de implementar.

---

## 🗂️ Índice dos Documentos

| #  | Documento | Descrição |
|----|-----------|-----------|
| 01 | [`01_product_vision.md`](./01_product_vision.md) | Visão de produto, proposta de valor, público-alvo, posicionamento e modelo de negócio |
| 02 | [`02_functional_spec.md`](./02_functional_spec.md) | Especificação funcional: personas, jornadas, casos de uso e funcionalidades |
| 03 | [`03_technical_spec.md`](./03_technical_spec.md) | Especificação técnica de alto nível: stack, contratos, domínios e fluxo de dados |
| 04 | [`04_architecture.md`](./04_architecture.md) | Arquitetura de referência, componentes, diagramas C4 e padrões |
| 05 | [`05_non_functional_requirements.md`](./05_non_functional_requirements.md) | Requisitos não funcionais (SLOs, qualidade, conformidade) |
| 06 | [`06_observability_traceability.md`](./06_observability_traceability.md) | Estratégia de observabilidade, rastreabilidade e MLOps monitoring |
| 07 | [`07_performance_scalability.md`](./07_performance_scalability.md) | Estratégia de performance, caching e escalabilidade |
| 08 | [`08_security.md`](./08_security.md) | Estratégia de segurança, privacidade e conformidade |
| 09 | [`09_frontend_ux.md`](./09_frontend_ux.md) | Proposta de frontend, design system e experiência do usuário |
| 10 | [`10_roadmap.md`](./10_roadmap.md) | Roadmap de evolução em fases e marcos demonstráveis |
| 11 | [`11_risks_assumptions_adr.md`](./11_risks_assumptions_adr.md) | Riscos, premissas e Architecture Decision Records (ADRs) |
| 12 | [`12_global_scaleup_architecture.md`](./12_global_scaleup_architecture.md) | Arquitetura de nível Global Scale-Up / Enterprise Tier-1 (Kafka, Feast, K8s, GDPR) |

---

## 🎯 Resumo Executivo (TL;DR)

O projeto atual prediz **churn** (cancelamento) de clientes de telecom servindo
um modelo XGBoost via FastAPI. A proposta é transformá-lo no **RetainIQ**: uma
plataforma SaaS que não apenas *prevê* o churn, mas **explica, prioriza e
recomenda ações de retenção**, integrando-se ao stack de dados de empresas
B2B/B2C de assinatura.

**Diferenciais técnicos demonstrados:**

- Arquitetura **multi-tenant** com isolamento lógico e segurança por design.
- **MLOps de verdade**: versionamento de modelo, feature store, monitoramento de
  *drift* e re-treino orquestrado.
- **Explicabilidade** (SHAP) tratada como cidadã de primeira classe do produto.
- **Observabilidade completa** (logs estruturados, métricas, tracing distribuído).
- **Frontend de classe mundial** em React + TypeScript com design system próprio.
- **Engenharia de plataforma**: IaC, CI/CD, ambientes efêmeros e contratos de API.

---

## 🧭 Como ler esta documentação

- **Recrutador / Tech Lead avaliando:** comece pelo `01` (visão) e `04`
  (arquitetura), depois `06`–`08` (engenharia) e `09` (frontend).
- **Product Manager:** `01`, `02` e `10`.
- **Engenheiro implementando:** `03`, `04`, `05`, `11` e os documentos de área.

---

## 📌 Convenções

- **RFC 2119**: as palavras *DEVE*, *NÃO DEVE*, *DEVERIA*, *PODE* indicam nível
  de obrigatoriedade dos requisitos.
- **IDs rastreáveis**: requisitos funcionais (`RF-XX`), não funcionais (`RNF-XX`)
  e decisões (`ADR-XX`) são referenciáveis entre documentos.
- **Estado**: cada funcionalidade é marcada como `MVP`, `V1` ou `Futuro`.

