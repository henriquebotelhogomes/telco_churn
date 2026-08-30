# 📉 RetainIQ — Customer Retention Intelligence & MLOps Platform

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.2+-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.8+-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.3+-38B2AC?style=flat&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![XGBoost](https://img.shields.io/badge/XGBoost-1.7+-F37626?style=flat&logo=xgboost&logoColor=white)](https://xgboost.readthedocs.io/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4+-F7931E?style=flat&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy_2.0-Async_ORM-D71F00?style=flat&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![Pandera](https://img.shields.io/badge/Pandera-Contract_Validation-FF6F00?style=flat)](https://pandera.readthedocs.io/)
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Tests](https://img.shields.io/badge/Tests-72_Passing-success?style=flat&logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![Coverage](https://img.shields.io/badge/Coverage-90.88%25-brightgreen?style=flat)](https://github.com/henriquebotelhogomes/telco_churn)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?style=flat&logo=github-actions&logoColor=white)](https://github.com/features/actions)

> **Plataforma de Inteligência de Retenção e MLOps:** Uma solução completa de Inteligência Artificial aplicada ao negócio que vai além da simples previsão de cancelamento (*churn*). O RetainIQ fecha o ciclo operacional: **Prediz o risco $\rightarrow$ Explica os fatores com TreeSHAP $\rightarrow$ Prescreve ações comerciais com ROI $\rightarrow$ Gera roteiros com GenAI $\rightarrow$ Mede o desfecho real de retenção $\rightarrow$ Retreina os modelos continuamente com Quality Gate**.

---

## 📌 Índice

1. [Visão Geral e Problema de Negócio](#-visão-geral-e-problema-de-negócio)
2. [Arquitetura do Sistema](#-arquitetura-do-sistema)
3. [Diferenciais de Engenharia e Ciência de Dados](#-diferenciais-de-engenharia-e-ciência-de-dados)
4. [Modelagem, Métricas e Benchmark de Modelos](#-modelagem-métricas-e-benchmark-de-modelos)
5. [Explicabilidade com TreeSHAP & Prescrição What-If](#-explicabilidade-com-treeshap--prescrição-what-if)
6. [MLOps: Champion/Challenger, Shadow Scoring e Continuous Training](#-mlops-championchallenger-shadow-scoring-e-continuous-training)
7. [Observabilidade, Monitoramento de Drift e Métricas Prometheus](#-observabilidade-monitoramento-de-drift-e-métricas-prometheus)
8. [Copilot GenAI de Retenção & Negociação](#-copilot-genai-de-retenção--negociação)
9. [Persistência Relacional, Closed-Loop e Dossiê Executivo](#-persistência-relacional-closed-loop-e-dossiê-executivo)
10. [Frontend Cockpit (React 19 + TypeScript)](#-frontend-cockpit-react-19--typescript)
11. [Catálogo Completo da API REST](#-catálogo-completo-da-api-rest)
12. [Estrutura do Repositório](#-estrutura-do-repositório)
13. [Qualidade de Código e Testes Automatizados](#-qualidade-de-código-e-testes-automatizados)
14. [Como Executar o Projeto](#-como-executar-o-projeto)
15. [Documentação e Especificações do Projeto](#-documentação-e-especificações-do-projeto)

---

## 💼 Visão Geral e Problema de Negócio

Em modelos de assinatura e telecomunicações, a perda de clientes (*churn*) é o principal detrator do crescimento sustentável e da lucratividade. Adquirir um novo cliente custa de **5 a 7 vezes mais** do que reter um cliente atual (CAC vs. LTV).

A maioria dos projetos de Machine Learning limita-se a calcular uma probabilidade de cancelamento isolada em um Jupyter Notebook, sem integração com a operação de negócios. O **RetainIQ** foi construído para resolver o ciclo completo de ponta a ponta:

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│ 1. PREDIZER     │       │ 2. EXPLICAR     │       │ 3. PRESCREVER   │
│ Risco e MRR     ├──────►│ SHAP Waterfall  ├──────►│ Playbook com    │
│ em perigo       │       │ Motivos reais   │       │ ROI anual       │
└─────────────────┘       └─────────────────┘       └────────┬────────┘
                                                             │
┌─────────────────┐       ┌─────────────────┐       ┌────────▼────────┐
│ 6. RETREINAR    │       │ 5. APRENDER     │       │ 4. NEGOCIAR     │
│ Continuous      │◄──────┤ Desfecho real   │◄──────┤ Copilot GenAI   │
│ Training & Gate │       │ (Ground Truth)  │       │ com tom tailored│
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### O Que o RetainIQ Entrega:
- **Priorização Financeira:** Ordena a fila de atendimento não apenas pelo risco de churn, mas pelo **MRR em Risco** ($\text{Mensalidade} \times \text{Probabilidade}$), garantindo que as contas de maior impacto financeiro sejam atendidas primeiro.
- **Explicabilidade Determinística:** Apresenta exatamente quais atributos elevaram ou reduziram a probabilidade de cada cliente via **TreeSHAP**.
- **Prescrição Comercial com Projeção de ROI:** O *Simulador What-If* calcula o novo risco estimado e a economia financeira anual para cada plano de ação.
- **Copilot GenAI:** Gera abordagens comerciais personalizadas para WhatsApp, Call Center e E-mail, com alternância de tom e fallback algorítmico caso a LLM esteja indisponível.
- **Fechamento de Ciclo (Closed-Loop):** Registra o desfecho real do cliente (*Ground Truth*) e calcula o **MRR Histórico Preservado** e a taxa de sucesso de cada estratégia.
- **Governança de Modelos:** Suporte nativo a múltiplos algoritmos (*Champion/Challenger*), *Shadow Scoring* em tempo real e retreino contínuo automatizado (*Continuous Training*).

---

## 🏛️ Arquitetura do Sistema

O projeto é estruturado em uma arquitetura desacoplada, assíncrona e orientada a contratos estritos:

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FRONTEND COCKPIT                                     │
│                     (React 19 + TypeScript + Vite + Tailwind CSS + shadcn)              │
│  ┌─────────────────────────┬──────────────────────────┬──────────────────────────────┐  │
│  │   Dashboard Executivo   │   Fila de Riscos (Table) │   Laboratório de MLOps       │  │
│  │   • KPIs de MRR Salvo   │   • Customer 360 Drawer  │   • Multi-Model Registry     │  │
│  │   • Gráficos Dual-Axis  │   • Gráficos TreeSHAP    │   • Shadow Scoring           │  │
│  │   • Dossiê C-Level      │   • Simulador What-If    │   • Continuous Training      │  │
│  │   • Evolução Temporal   │   • Copilot GenAI        │   • Evidently Data Drift     │  │
│  └─────────────────────────┴──────────────────────────┴──────────────────────────────┘  │
└────────────────────────────────────────────┬────────────────────────────────────────────┘
                                             │ HTTP REST / JSON (Porta 8000)
┌────────────────────────────────────────────▼────────────────────────────────────────────┐
│                                   FASTAPI BACKEND                                       │
│                                                                                         │
│  ┌─────────────────────────────────┐       ┌─────────────────────────────────────────┐  │
│  │     Data Validation Layer       │       │       Continuous Training Engine        │  │
│  │  • Pandera Schema Contracts     │       │  • Background Retraining Worker         │  │
│  │  • Dual Ingestion (JSON / CSV)  │       │  • PR-AUC Quality Gate Validation       │  │
│  │  • Normalização PT-BR / EN-US   │       │  • Promoção Atômica sem Downtime        │  │
│  └────────────────┬────────────────┘       └────────────────────▲────────────────────┘  │
│                   │                                             │                       │
│  ┌────────────────▼────────────────┐       ┌────────────────────┴────────────────────┐  │
│  │   Explainability & Simulation   │       │        Model Registry & Serving         │  │
│  │  • TreeSHAP Exact Tree Explainer│       │  • Champion / Challenger Pattern        │  │
│  │  • Prescrição de Playbooks      │       │  • Shadow Scoring em Tempo Real         │  │
│  │  • Simulador What-If & ROI      │       │  • XGBoost, HistGB, RF, Logistic Reg.   │  │
│  └────────────────┬────────────────┘       └────────────────────▲────────────────────┘  │
│                   │                                             │                       │
│  ┌────────────────▼────────────────┐       ┌────────────────────┴────────────────────┐  │
│  │     Copilot GenAI Assistant     │       │   Persistência Relacional Assíncrona    │  │
│  │  • Provedores Gemini / OpenAI   │       │  • SQLAlchemy 2.0 Async (SQLite / PG)   │  │
│  │  • Fallback Algorítmico 100%    │       │  • Registro de Ground Truth e MRR Salvo │  │
│  │  • Variação de Tom Customizada  │       │  • Gerador de Dossiê Executivo HTML/PDF │  │
│  └─────────────────────────────────┘       └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Diferenciais de Engenharia e Ciência de Dados

1. **Zero Data Leakage no Pré-processamento:**  
   Pipelines de transformação construídos com `Pipeline` e `ColumnTransformer` do Scikit-Learn. Todos os parâmetros estatísticos (*imputação, scaling e one-hot encoding*) são aprendidos estritamente no conjunto de treino e aplicados de forma isolada nos conjuntos de validação e teste.

2. **Validação de Esquemas em Tempo de Execução (Pandera):**  
   Os dados de entrada são submetidos a contratos estritos de tipos, intervalos válidos e coerência lógica através do **Pandera**, garantindo que anomalias sejam barradas na borda antes de alcançar o pipeline de Machine Learning.

3. **Ingestão Dual Flexível:**  
   O backend suporta nativamente:
   - Requisições JSON com chaves em Português (`tempo_contrato_meses`, `valor_mensalidade`, etc.).
   - Arquivos CSV no padrão original internacional Telco Churn (`tenure`, `MonthlyCharges`, `TotalCharges`, etc.) com tradução automática.

4. **Operações Assíncronas e Não-Bloqueantes:**  
   FastAPI configurado com endpoints assíncronos (`async/await`) e **SQLAlchemy 2.0 Async ORM**, garantindo alta vazão e baixo consumo de memória mesmo sob concorrência intensa.

5. **Explicabilidade Exata em Milissegundos:**  
   Integração direta com **TreeSHAP** pré-calculado sobre a base dos modelos em árvore, permitindo gerar relatórios explicativos instantâneos para a interface web.

---

## 📊 Modelagem, Métricas e Benchmark de Modelos

### Por Que PR-AUC e Brier Score?
Em problemas de cancelamento de clientes, a base é tipicamente desbalanceada (no dataset Telco Churn, apenas $\approx 26.5\%$ dos clientes deram churn).

- **ROC-AUC:** Mede a capacidade geral de ranqueamento, mas pode ser excessivamente otimista em bases desbalanceadas.
- **PR-AUC (Precision-Recall AUC):** Avalia diretamente o equilíbrio entre encontrar os clientes em risco (*Recall*) sem gerar falsos alarmes (*Precision*). É a métrica oficial de Quality Gate do RetainIQ.
- **Brier Score:** Mede a calibração da probabilidade prevista. Quanto menor o valor ($0.0$ a $1.0$), mais confiável é a probabilidade para tomada de decisão financeira.

### Tabela Comparativa de Performance (Conjunto de Teste Independente)

Avaliação em **1.409 amostras estratificadas de teste**:

| Modelo / Algoritmo | Papel | ROC-AUC | PR-AUC | F1-Score | Recall | Precision | Brier Score | Latência de Inferência |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **XGBoost Classifier** | **Champion** | `0.8142` | `0.6107` | `0.5841` | `0.5401` | `0.6358` | `0.1412` | **0.034 ms** |
| **HistGradientBoosting** | Challenger | `0.8328` | `0.6392` | `0.6110` | `0.5722` | `0.6554` | `0.1387` | **0.035 ms** |
| **Regressão Logística** | Challenger | `0.8414` | `0.6324` | `0.6083` | `0.5642` | `0.6598` | `0.1365` | **0.023 ms** |
| **Random Forest** | Challenger | `0.8193` | `0.6058` | `0.5793` | `0.5294` | `0.6399` | `0.1430` | **0.049 ms** |

---

## 🔍 Explicabilidade com TreeSHAP & Prescrição What-If

### 1. Gráfico Waterfall de SHAP Divergente
Para cada cliente avaliado, o modelo decompõe a probabilidade de churn a partir do valor base global ($E[f(x)] \approx 26.5\%$), identificando o impacto de cada variável:
- 🔴 **Barras Vermelhas ($+ \Delta$ Risco):** Atributos que elevam o risco (ex: contrato mensal *Month-to-month*, suporte técnico ausente, pagamento via cheque eletrônico).
- 🟢 **Barras Verdes ($- \Delta$ Risco):** Atributos de proteção (ex: contrato de 2 anos, pagamento automático via cartão, longo tempo de casa).

```
Contrato Mês a Mês    [██████████████████████] +24.2%  (Eleva Risco)
Sem Suporte Técnico   [██████████]             +11.5%  (Eleva Risco)
Fibra Óptica Sem BKP  [██████]                 +6.8%   (Eleva Risco)
Débito Automático     [████████]               -8.4%   (Reduz Risco)
Tempo de Casa (32m)   [██████████████]         -14.1%  (Reduz Risco)
```

### 2. Simulador Prescritivo What-If
Permite que o operador comercial selecione ações corretivas antes de entrar em contato com o cliente:
- Migrar contrato para Anual ou Bianual.
- Conceder pacote de suporte técnico prioritário gratuito.
- Ativar débito automático com desconto de fidelidade.

O simulador recalcula a inferência em tempo real, exibindo a **probabilidade original $\rightarrow$ probabilidade simulada** e a **economia anual esperada ($ROI$)**.

---

## 🔄 MLOps: Champion/Challenger, Shadow Scoring e Continuous Training

```
  ┌───────────────────────────────────────────────────────────┐
  │                 CLIENT INGESTION REQUEST                  │
  └─────────────────────────────┬─────────────────────────────┘
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │              CHAMPION INFERENCE (FastAPI)                 │ ◄── Resposta do Cliente
  │               (Ex: XGBoost - 0.034 ms)                    │     (< 10 ms SLA)
  └─────────────────────────────┬─────────────────────────────┘
                                │
            (Assíncrono / Não-bloqueante em Background)
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │                 SHADOW SCORING ENGINE                     │
  │  • HistGradientBoosting   • Logistic Regression  • RF     │
  │  • Telemetria de Acordo (%) & Divergência Média (Δ Prob) │
  └─────────────────────────────┬─────────────────────────────┘
                                │
        (Se Data Drift detectado ou Retreino Manual)
                                │
                                ▼
  ┌───────────────────────────────────────────────────────────┐
  │             CONTINUOUS TRAINING (CT) PIPELINE             │
  │  1. Treina todos os modelos candidatos                    │
  │  2. Valida Quality Gate: PR-AUC(Novo) >= PR-AUC(Champion) │
  │  3. Promoção Atômica com Zero Downtime                    │
  │  4. Auditoria persistente em ModelTrainingJob             │
  └───────────────────────────────────────────────────────────┘
```

1. **Champion/Challenger Dinâmico:**  
   O modelo **Champion** responde imediatamente a todas as requisições de produção. O `ModelManager` gerencia o catálogo em memória com troca a quente (*hot-swap*), permitindo promover qualquer modelo *Challenger* com uma única chamada de API sem reiniciar o servidor.

2. **Shadow Scoring em Tempo Real:**  
   A cada predição de produção, uma tarefa em segundo plano executa a inferência nos 3 modelos concorrentes sem impactar o tempo de resposta do usuário. A telemetria calcula:
   - Taxa de Concordância (% de decisões idênticas).
   - Divergência Média de Probabilidade ($\Delta$ Prob).
   - Latência comparativa de cada algoritmo.

3. **Continuous Training (CT) com Quality Gate Automatizado:**  
   O pipeline de retreino pode ser disparado sob demanda via interface/API ou de forma automatizada quando um alerta de *Data Drift* é acionado:
   - Re-treina e avalia todos os 4 algoritmos com validação cruzada estratificada.
   - **Quality Gate Rigoroso:** O novo candidato só substitui o Champion se $PR\text{-}AUC_{\text{novo}} \ge PR\text{-}AUC_{\text{champion}}$. Caso contrário, a promoção é bloqueada e o evento é auditado no banco de dados.

---

## 📈 Observabilidade, Monitoramento de Drift e Métricas Prometheus

1. **Métricas Nativas Prometheus (`/metrics`):**
   - `churn_predictions_total`: Contador global de predições distribuídas por nível de risco (`baixo`, `medio`, `alto`, `critico`).
   - `churn_prediction_latency_seconds`: Histograma de latência de inferência com percentis $p50$, $p90$, $p99$.
   - `model_active_champion_info`: Indicador do modelo ativo em produção.

2. **Monitoramento de Data Drift com Evidently AI (`/api/v1/metrics/drift`):**
   - Armazena as últimas 500 inferências em um *Ring Buffer* de baixo custo de memória.
   - Compara a distribuição dos dados recebidos em produção contra os dados de referência de treinamento usando testes estatísticos (**Kolmogorov-Smirnov** para variáveis numéricas e **Chi-Square** para categóricas).
   - Cache inteligente de relatórios para evitar computação redundante.

---

## 🤖 Copilot GenAI de Retenção & Negociação

O RetainIQ integra um assistente inteligente de IA Generativa para auxiliar equipes de atendimento e negociação:

- **Multi-Provedor:** Suporte nativo a **Google Gemini** (`gemini-1.5-flash`) e **OpenAI** (`gpt-4o-mini`).
- **Resiliência com Fallback Algorítmico 100%:** Caso nenhuma chave de API esteja configurada ou ocorra timeout de rede, um motor determinístico de regras de negócio assume instantaneamente a geração sem falhas para o operador.
- **Estrutura do Roteiro Gerado:**
  1. *Diagnóstico do Cliente:* Resumo dos principais motivadores de churn identificados pelo SHAP.
  2. *Proposta de Valor:* Oferta calculada pelo Simulador com projeção de desconto e fidelização.
  3. *Script de Atendimento:* Script passo a passo para o analista (Abertura empática, Quebra de objeções, Fechamento).
  4. *Mensagens Prontas:* Textos formatados para envio imediato via WhatsApp e E-mail.
- **Motor de Tons:** Alternância dinâmica de estilo de comunicação com um clique (**Empático**, **Firme**, **Consultivo**, **Direto**).

---

## 💾 Persistência Relacional, Closed-Loop e Dossiê Executivo

### Fechamento de Ciclo Analítico (Closed-Loop)
O sistema mantém rastreabilidade de todas as ações tomadas através de tabelas relacionais assíncronas no SQLite / PostgreSQL:
- **`RetentionPlaybookAction`:** Registra qual playbook foi aplicado a qual cliente, a redução de risco estimada, a economia esperada e o analista responsável.
- **`CustomerOutcome`:** Registra o desfecho real do cliente após 30, 60 ou 90 dias (*cancelou* vs. *permaneceu retido*) e a receita real preservada.
- **`ModelTrainingJob`:** Auditoria completa de todas as execuções de retreinamento contínuo, métricas de PR-AUC e status de promoção.

### Dossiê Executivo de Retenção C-Level (PDF/HTML)
Exportação instantânea de relatório executivo (*print-ready*) contendo:
- Indicadores financeiros consolidados (MRR Total em Risco vs. MRR Histórico Preservado).
- Tabela de eficiência por playbook de retenção (% de sucesso real e ROI).
- Top 10 Contas Críticas com maior risco financeiro e seus fatores SHAP determinantes.
- Diagnóstico completo do ecossistema de MLOps.

---

## 🖥️ Frontend Cockpit (React 19 + TypeScript)

Interface web construída sem templates engessados ou frameworks lentos (Zero-Streamlit):

- **Stack Moderna:** React 19, TypeScript 5.8, Vite, Tailwind CSS 4, Radix UI e TanStack Table.
- **Dashboard Executivo:** Cards de KPI financeiros, gráfico de distribuição de risco, gráfico de MRR esperado e **gráfico Dual-Axis de Evolução Temporal** (Área para volumes e Linha para Taxa de Retenção %).
- **Tabela de Riscos Interativa:** Ordenação por MRR em perigo, paginação, filtros por nível de severidade e busca rápida por cliente.
- **Customer 360 Drawer:** Painel lateral contendo medidor de risco, gráfico TreeSHAP, simulador What-If, histórico de ações e o Copilot GenAI.
- **Laboratório MLOps:** Painel de Champion vs. Challengers com promoção atômica, telemetria de Shadow Scoring, monitoramento de Data Drift e disparador de Continuous Training.

---

## 🌐 Catálogo Completo da API REST

A API segue as melhores práticas RESTful com documentação OpenAPI interativa (Swagger UI) disponível em `/docs`:

| Endpoint | Método | Categoria | Descrição |
|---|:---:|:---:|---|
| `/health` | GET | Infraestrutura | Liveness probe para orquestradores (`{"status": "ok"}`) |
| `/metrics` | GET | Telemetria | Métricas padrão Prometheus (latências, contadores, status) |
| `/api/v1/predict` | POST | Predição | Predição individual com SHAP Top 3, playbook e persistência |
| `/api/v1/predict/batch` | POST | Predição | Predição em lote via payload JSON ou upload de CSV |
| `/api/v1/simulate` | POST | Prescrição | Simulador *What-If* com cálculo de novo risco e ROI |
| `/api/v1/copilot/generate-script` | POST | GenAI | Assistente de negociação (WhatsApp, Call Center, E-mail) |
| `/api/v1/models` | GET | MLOps | Catálogo completo do Dynamic Model Registry |
| `/api/v1/models/promote` | POST | MLOps | Promoção atômica de modelo para Champion sem downtime |
| `/api/v1/models/shadow-metrics` | GET | MLOps | Telemetria de Shadow Scoring e concordância em tempo real |
| `/api/v1/admin/train/auto-retrain` | POST | Continuous Training | Disparo assíncrono do pipeline de retreino com Quality Gate |
| `/api/v1/admin/train/jobs` | GET | Continuous Training | Histórico e auditoria de jobs de retreinamento contínuo |
| `/api/v1/playbooks/apply` | POST | Retenção | Aplica playbook de retenção e registra ação no banco |
| `/api/v1/playbooks/history` | GET | Retenção | Histórico de playbooks aplicados com filtros por cliente |
| `/api/v1/outcomes/record` | POST | Closed-Loop | Registra o desfecho real de churn (*Ground Truth*) |
| `/api/v1/analytics/retention-efficiency` | GET | Analytics | KPIs de conversão, eficácia e ROI real por playbook |
| `/api/v1/analytics/temporal-evolution` | GET | Analytics | Série histórica de predições, retenções e taxa percentual |
| `/api/v1/analytics/executive-report/download` | GET | Relatórios | Download do Dossiê Executivo C-Level (HTML/PDF print-ready) |
| `/api/v1/metrics/drift` | GET | Observabilidade | Relatório de Data Drift estatístico com Evidently AI |

---

## 📁 Estrutura do Repositório

```
telco_churn/
├── src/churn_prediction/             # Pacote Python Principal
│   ├── api/                          # Camada de Apresentação & API
│   │   ├── main.py                   # FastAPI app, rotas REST e endpoints
│   │   └── schemas.py                # Contratos Pydantic v2 (Input/Output)
│   ├── db/                           # Camada de Persistência Assíncrona
│   │   ├── database.py               # Engine assíncrono do SQLAlchemy 2.0
│   │   └── models.py                 # Entidades: Predictions, Playbooks, Outcomes, Jobs
│   ├── models/                       # Camada de Machine Learning & MLOps
│   │   ├── train.py                  # Treinamento dos 4 modelos candidatos
│   │   ├── registry.py               # Dynamic Model Registry (Champion/Challenger)
│   │   ├── shadow.py                 # Telemetria de Shadow Scoring em background
│   │   ├── continuous_training.py    # Pipeline de Continuous Training & Quality Gate
│   │   ├── explainability.py         # Explicabilidade TreeSHAP e prescrições
│   │   ├── copilot.py                # Assistente GenAI (Gemini/OpenAI/Fallback)
│   │   └── reporting.py              # Gerador do Dossiê Executivo C-Level
│   ├── data/                         # Camada de Dados e Validação
│   │   ├── loader.py                 # Ingestão e split estratificado dos dados
│   │   ├── contracts.py              # Contratos estritos de dados com Pandera
│   │   └── preprocessor.py           # Pipelines Scikit-Learn sem data leakage
│   └── monitoring/                   # Observabilidade & Métricas
│       ├── drift.py                  # Detecção de Data Drift com Evidently AI
│       └── metrics.py                # Instrumentação Prometheus nativa
│
├── frontend/                         # Frontend Cockpit (React 19 + TypeScript)
│   ├── src/
│   │   ├── components/
│   │   │   ├── dashboard/            # KpiCards, RiskCharts (Dual-Axis), ExecutiveDossier
│   │   │   ├── customers/            # CustomersTable, Customer360, CopilotAssistant
│   │   │   ├── mlops/                # ModelRegistryLab, ContinuousTrainingPanel, Drift
│   │   │   └── charts/               # ShapWaterfall, RiskGauge
│   │   ├── api/                      # Client HTTP e hooks TanStack Query
│   │   └── pages/                    # DashboardPage, CustomersPage, MlopsPage
│   └── package.json                  # Dependências frontend (Vite, React, Tailwind)
│
├── tests/                            # Suíte de Testes Automatizados (Pytest)
│   ├── test_api.py                   # Testes de integração de todos os endpoints REST
│   ├── test_models.py                # Testes de treinamento, inferência e métricas
│   ├── test_continuous_training.py   # Testes do Quality Gate e retreino assíncrono
│   ├── test_copilot.py               # Testes do Copilot GenAI e motor de fallback
│   ├── test_contracts.py             # Testes de validação de contratos Pandera
│   └── test_reporting.py             # Testes do gerador de Dossiê Executivo
│
├── specs/                            # Especificações de Engenharia e Arquitetura
│   ├── 00_index.md                   # Índice mestre da documentação
│   ├── 04_architecture.md            # Diagramas C4 e decisões estruturais
│   └── 12_global_scaleup_architecture.md # Arquitetura Enterprise (Kafka, Feast, K8s)
│
├── PRD_PHASE_2_GLOBAL_SCALEUP.md     # PRD Executivo para Escala Global de Hiperescala
├── Dockerfile                        # Multi-Stage Dockerfile (Node 22 + Python 3.12)
├── pyproject.toml                    # Configuração de dependências e ferramentas com uv
└── README.md                         # Documentação Principal do Projeto
```

---

## 🧪 Qualidade de Código e Testes Automatizados

O projeto adota padrões rigorosos de engenharia de software com tipagem estática e testes contínuos:

- **72 Testes Automatizados no Backend (`pytest`):** Cobrem validação de contratos, inferência de modelos, shadow scoring, retreinamento com quality gate, persistência assíncrona e endpoints REST.
- **14 Testes Unitários no Frontend (`vitest`):** Testes de renderização de componentes, cálculos e formatações financeiras.
- **Cobertura de Código de 90.88%:** Monitorada continuamente com barreira de reprovação automática no CI se a cobertura cair abaixo de $80\%$.
- **Linter & Type Checking:**
  - Python: `ruff` (linter e formatador ultrarrápido) e `mypy` (verificação estrita de tipos).
  - TypeScript: `tsc -b` (zero erros de tipagem).

```bash
# Executar suíte completa de testes backend com relatório de cobertura:
uv run pytest tests/ -v --cov=churn_prediction --cov-fail-under=80

# Executar testes unitários do frontend:
cd frontend && npm test
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- **Python 3.12+** instalado.
- Gerenciador de pacotes **[`uv`](https://docs.astral.sh/uv/)** (recomendado para performance instantânea) ou `pip`.
- **Node.js 20+** e `npm` (para o frontend).
- **Docker** (opcional, para execução em container unificado).

---

### Opção 1: Execução via Docker (Recomendado)

A imagem multi-stage compila o frontend TypeScript e o serve estaticamente através do backend FastAPI na porta `8000`:

```bash
# 1. Construir a imagem Docker
docker build -t retainiq-platform .

# 2. Executar o container
docker run -p 8000:8000 retainiq-platform
```

Acesse no navegador:
- **Plataforma RetainIQ:** 👉 [http://localhost:8000/](http://localhost:8000/)
- **Documentação da API (Swagger UI):** 👉 [http://localhost:8000/docs](http://localhost:8000/docs)
- **Métricas Prometheus:** 👉 [http://localhost:8000/metrics](http://localhost:8000/metrics)

---

### Opção 2: Desenvolvimento Local

```bash
# 1. Clonar o repositório
git clone https://github.com/henriquebotelhogomes/telco_churn.git
cd telco_churn

# 2. Instalar dependências do backend
uv sync

# 3. Treinar os modelos iniciais do catálogo (XGBoost, RF, HistGB, Logistic Regression)
uv run python -m churn_prediction.models.train

# 4. Instalar dependências e buildar o frontend
cd frontend
npm install
npm run build
cd ..

# 5. Iniciar o servidor FastAPI
uv run uvicorn churn_prediction.api.main:app --app-dir src --reload --port 8000
```

Se desejar executar o frontend com **Hot Module Replacement (HMR)** durante o desenvolvimento:
```bash
# Em um segundo terminal:
cd frontend
npm run dev
# Acesse em http://localhost:5173 (com proxy reverso automático para o backend na porta 8000)
```

---

## 📚 Documentação e Especificações do Projeto

Para detalhes aprofundados sobre a modelagem técnica, arquitetura de dados e visão de produto, consulte as especificações completas na pasta [`specs/`](specs/):

- [`specs/01_product_vision.md`](specs/01_product_vision.md) — Visão de produto, proposta de valor e personas.
- [`specs/03_technical_spec.md`](specs/03_technical_spec.md) — Especificação técnica, contratos e fluxo de dados.
- [`specs/04_architecture.md`](specs/04_architecture.md) — Arquitetura de referência e diagramas C4.
- [`specs/06_observability_traceability.md`](specs/06_observability_traceability.md) — Estratégia de telemetria, logs estruturados e drift.
- [`specs/12_global_scaleup_architecture.md`](specs/12_global_scaleup_architecture.md) — Blueprint para escala global (Kafka, Feast, K8s, Istio).
- [`PRD_PHASE_2_GLOBAL_SCALEUP.md`](PRD_PHASE_2_GLOBAL_SCALEUP.md) — PRD Executivo da Fase 2 para arquitetura de hiperescala.

---

## 📄 Licença

Este projeto é distribuído sob a licença MIT. Consulte o arquivo `LICENSE` para obter mais informações.