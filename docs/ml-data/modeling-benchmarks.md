# Modelagem & Benchmarks de Modelos

Esta seção detalha as estratégias de pré-processamento, pipeline de treino e a matriz comparativa de performance dos algoritmos implementados.

---

## 🛡️ Pré-processamento & Zero Data Leakage

O pipeline de dados é estruturado utilizando `ColumnTransformer` do Scikit-Learn:
- **Variáveis Numéricas (`tenure`, `MonthlyCharges`, `TotalCharges`):** Imputação pela mediana e padronização robusta via `RobustScaler`.
- **Variáveis Categóricas (`Contract`, `PaymentMethod`, `InternetService`, etc.):** Imputação pelo valor mais frequente e codificação com `OneHotEncoder(handle_unknown='ignore')`.

Todos os transformadores são ajustados (*fit*) **exclusivamente no conjunto de treino** (80% das amostras) e aplicados (*transform*) no conjunto de teste independente (20% das amostras / 1.409 clientes).

---

## 📊 Matriz Comparativa no Conjunto de Teste

| Algoritmo | Papel | ROC-AUC | PR-AUC | F1-Score | Recall | Precision | Brier Score | Latência |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **XGBoost** | **Champion** | `0.8142` | `0.6107` | `0.5841` | `0.5401` | `0.6358` | `0.1412` | `0.034 ms` |
| **HistGradientBoosting** | Challenger | `0.8328` | `0.6392` | `0.6110` | `0.5722` | `0.6554` | `0.1387` | `0.035 ms` |
| **Regressão Logística** | Challenger | `0.8414` | `0.6324` | `0.6083` | `0.5642` | `0.6598` | `0.1365` | `0.023 ms` |
| **Random Forest** | Challenger | `0.8193` | `0.6058` | `0.5793` | `0.5294` | `0.6399` | `0.1430` | `0.049 ms` |

---

## 🎯 Por Que Otimizamos para PR-AUC?

Devido ao desbalanceamento natural da taxa de cancelamento ($\approx 26.5\%$), a curva **Precision-Recall (PR-AUC)** é a métrica principal para o negócio:

$$PR\text{-}AUC = \int_{0}^{1} \text{Precision}(R) \, dR$$

Um modelo com alto PR-AUC garante que as ofertas de retenção e descontos financeiros sejam direcionados prioritariamente para quem realmente tinha probabilidade de cancelar, evitando perda desnecessária de margem.
