"""A realistic sample incident and a CLI demo that prints a triage result.

    python -m aiops.sample
"""
from __future__ import annotations

import json

from .models import Incident, Signal
from .triage import TriageEngine

SAMPLE = Incident(
    id="INC-2043",
    title="Checkout API returning 503s",
    signals=[
        Signal(source="api-gateway", kind="log", severity="critical",
               message="502 Bad Gateway from upstream checkout-svc"),
        Signal(source="checkout-svc", kind="log", severity="critical",
               message="TimeoutError: timeout acquiring connection from pool"),
        Signal(source="postgres", kind="metric", metric="db_connections_active", value=98.0,
               severity="warning"),
        Signal(source="checkout-svc", kind="metric", metric="p99_latency_ms", value=2400.0,
               severity="warning"),
        Signal(source="checkout-svc", kind="metric", metric="error_rate", value=0.31,
               severity="critical"),
    ],
)


def main() -> int:
    result = TriageEngine().triage(SAMPLE)
    print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
