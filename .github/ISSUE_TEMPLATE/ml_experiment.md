---
name: 🧪 ML Model Experiment
about: Propor um novo experimento de modelagem, hiperparâmetros ou engenharia de features
title: "[EXPERIMENT] "
labels: ["data-science", "mlops", "experiment"]
assignees: ""
---

### 🔬 Hipótese Científica
Qual alteração de features, algoritmo (ex: CatBoost, XGBoost, TabNet) ou hiperparâmetros você propõe testar?

### 🎯 Métricas de Sucesso
- **Baseline Atual (CatBoost Champion):** ROC-AUC: `0.864` | PR-AUC: `0.672`
- **Meta do Experimento:** Aumento de PR-AUC $\ge +0.015$ ou redução de latência $p99 < 3\text{ms}$.

### 📦 Features Utilizadas
- Novas features de telemetria de rede (QoE)?
- Novas variáveis de sentimento ou CRM?

### 🛡️ Quality Gate & Validação
- Como o modelo se comportará contra data drift no Evidently?
- Qual o impacto no simulador What-If e explicabilidade TreeSHAP?
