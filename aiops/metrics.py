"""Prometheus metrics for the triage service."""
from __future__ import annotations

from prometheus_client import Counter, Histogram

TRIAGE_REQUESTS = Counter(
    "aiops_triage_requests_total",
    "Total triage requests handled.",
    ["outcome"],  # "matched" | "no_match"
)

TRIAGE_DURATION = Histogram(
    "aiops_triage_duration_seconds",
    "Time spent producing a triage result.",
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

SIGNALS_PER_INCIDENT = Histogram(
    "aiops_signals_per_incident",
    "Number of signals in each triaged incident.",
    buckets=(1, 5, 10, 25, 50, 100, 250, 500),
)
