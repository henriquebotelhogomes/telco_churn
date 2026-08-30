# Catálogo de Endpoints REST (FastAPI)

Abaixo está a especificação dos principais endpoints REST disponíveis na versão `/api/v1`.

---

## 🧭 Endpoints da Plataforma

| Endpoint | Método | Categoria | Descrição |
|---|:---:|:---:|---|
| `/health` | `GET` | Infraestrutura | Liveness probe para Kubernetes / Docker (`{"status": "ok"}`) |
| `/metrics` | `GET` | Telemetria | Métricas padrão Prometheus de latência e contadores |
| `/api/v1/predict` | `POST` | Predição | Predição individual com SHAP Top 3, playbook e persistência |
| `/api/v1/predict/batch` | `POST` | Predição | Predição em lote via JSON ou upload de CSV |
| `/api/v1/simulate` | `POST` | Prescrição | Simulador *What-If* com cálculo de novo risco e ROI |
| `/api/v1/copilot/generate-script` | `POST` | GenAI | Assistente de negociação (WhatsApp, Call Center, E-mail) |
| `/api/v1/models` | `GET` | MLOps | Catálogo completo do Dynamic Model Registry |
| `/api/v1/models/promote` | `POST` | MLOps | Promoção atômica de modelo para Champion sem downtime |
| `/api/v1/models/shadow-metrics` | `GET` | MLOps | Telemetria de Shadow Scoring e concordância em tempo real |
| `/api/v1/admin/train/auto-retrain` | `POST` | Continuous Training | Disparo assíncrono do pipeline de retreino com Quality Gate |
| `/api/v1/admin/train/jobs` | `GET` | Continuous Training | Histórico e auditoria de jobs de retreinamento contínuo |
| `/api/v1/playbooks/apply` | `POST` | Retenção | Aplica playbook de retenção e registra ação no banco |
| `/api/v1/playbooks/history` | `GET` | Retenção | Histórico de playbooks aplicados com filtros por cliente |
| `/api/v1/outcomes/record` | `POST` | Closed-Loop | Registra o desfecho real de churn (*Ground Truth*) |
| `/api/v1/analytics/retention-efficiency` | `GET` | Analytics | KPIs de conversão, eficácia e ROI real por playbook |
| `/api/v1/analytics/temporal-evolution` | `GET` | Analytics | Série histórica de predições, retenções e taxa percentual |
| `/api/v1/analytics/executive-report/download` | `GET` | Relatórios | Download do Dossiê Executivo C-Level (HTML/PDF print-ready) |
| `/api/v1/metrics/drift` | `GET` | Observabilidade | Relatório de Data Drift estatístico com Evidently AI |
