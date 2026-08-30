# Explicabilidade com TreeSHAP & Simulador What-If

O RetainIQ adota a teoria de jogos cooperativos através do **TreeSHAP (SHapley Additive exPlanations)** para explicar exatamente o motivo por trás de cada predição individual.

---

## 🔍 Decomposição Aditiva do Risco

Para cada cliente com vetor de features $x$, o valor de saída do modelo $f(x)$ é decomposto como a soma do valor base $E[f(z)]$ mais as contribuições marginais $\phi_i$ de cada variável:

$$f(x) = E[f(z)] + \sum_{i=1}^{M} \phi_i(x)$$

- Se $\phi_i > 0$, a feature $i$ empurrou a probabilidade para cima (**vermelho / aumenta risco**).
- Se $\phi_i < 0$, a feature $i$ empurrou a probabilidade para baixo (**verde / reduz risco**).

---

## 🧪 Simulador Prescritivo What-If

O simulador permite avaliar ações comerciais antes do contato com o cliente:
1. Altera atributos no vetor de features do cliente (ex: migração para contrato anual).
2. Recalcula o score de risco instantaneamente no modelo ativo.
3. Projeta a economia anual esperada:
   $$\text{ROI Esperado} = \text{Mensalidade} \times 12 \times \Delta p(\text{Churn})$$
