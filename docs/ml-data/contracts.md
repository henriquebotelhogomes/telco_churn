# Contratos de Dados com Pandera

Para evitar falhas silenciosas e corrupção de dados no pipeline de Machine Learning, o RetainIQ implementa contratos estritos com a biblioteca **Pandera**.

---

## 📜 Esquema de Validação em Runtime

O schema `ClienteSchema` valida:
- Tipos de dados de cada coluna (`int`, `float`, `str`).
- Intervalos válidos (ex: `tenure >= 0`, `MonthlyCharges >= 0`).
- Domínios de categorias permitidas para variáveis categóricas (ex: `Contract` deve ser `'Month-to-month'`, `'One year'` ou `'Two year'`).

```python
import pandera as pa
from pandera.typing import Series

class ClienteDataContract(pa.DataFrameModel):
    tenure: Series[int] = pa.Field(ge=0, le=120)
    MonthlyCharges: Series[float] = pa.Field(ge=0.0)
    TotalCharges: Series[float] = pa.Field(ge=0.0, nullable=True)
    Contract: Series[str] = pa.Field(isin=["Month-to-month", "One year", "Two year"])
    
    class Config:
        strict = False
        coerce = True
```
