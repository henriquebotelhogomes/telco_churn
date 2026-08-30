"""M3 - RetainIQ: telemetria — métricas de negócio (Prometheus) + ring buffer de drift."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Mapping
from typing import Any

import pandas as pd
from prometheus_client import Counter, Gauge

from churn_prediction.config import settings
from churn_prediction.data.contracts import REQUIRED_COLUMNS

# Métricas de negócio expostas em GET /metrics
predictions_total = Counter(
    "churn_predictions_total",
    "Total de predições de churn servidas pela API",
    ["endpoint"],
)
risk_level_total = Counter(
    "churn_risk_level_total",
    "Predições por nível de risco",
    ["level"],
)
drift_buffer_rows = Gauge(
    "churn_drift_buffer_rows",
    "Linhas canônicas acumuladas no ring buffer de drift",
)

_CANONICAL_COLUMNS = set(REQUIRED_COLUMNS)


class DriftBuffer:
    """Ring buffer (deque com maxlen) de linhas canônicas EN-US validadas.

    A inferência só faz append — o cálculo de drift acontece fora do caminho
    crítico, apenas via POST /api/v1/admin/drift/refresh.
    """

    def __init__(self, maxlen: int) -> None:
        self.buffer: deque[dict[str, Any]] = deque(maxlen=maxlen)

    def append(self, canonical_row: Mapping[str, Any]) -> None:
        row = {k: v for k, v in canonical_row.items() if k in _CANONICAL_COLUMNS}
        self.buffer.append(row)
        drift_buffer_rows.set(len(self.buffer))

    def extend(self, rows: Iterable[Mapping[str, Any]]) -> None:
        for row in rows:
            self.append(row)

    def clear(self) -> None:
        self.buffer.clear()
        drift_buffer_rows.set(0.0)

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(list(self.buffer))

    def __len__(self) -> int:
        return len(self.buffer)


drift_buffer = DriftBuffer(maxlen=settings.ring_buffer_maxlen)
