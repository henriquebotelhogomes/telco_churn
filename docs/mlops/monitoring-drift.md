# Data Drift & Métricas Prometheus

A observabilidade de MLOps do RetainIQ combina monitoramento estatístico de distribuição de dados e telemetria de infraestrutura.

---

## 📉 Detecção de Data Drift com Evidently AI

O sistema mantém um **Ring Buffer** em memória com as últimas 500 inferências recebidas:
- **Variáveis Numéricas:** Teste Kolmogorov-Smirnov de duas amostras ($p\text{-value} < 0.05$).
- **Variáveis Categóricas:** Teste Qui-Quadrado ($\chi^2$).
- **Relatório em Cache:** Evita recalcular o teste estatístico a cada requisição HTTP.

---

## 📊 Métricas Prometheus Nativas (`/metrics`)

- `churn_predictions_total`: Contador particionado por nível de risco (`baixo`, `medio`, `alto`, `critico`).
- `churn_prediction_latency_seconds`: Histograma com buckets de latência.
- `model_active_champion_info`: Gauge indicando o modelo em produção.
