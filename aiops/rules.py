"""Deterministic correlation rules mapping signal patterns to likely causes.

Each rule scans an incident's signals for its keywords (in logs/alerts) and its
metric threshold, and returns the evidence it matched. This is the offline core
of triage — explainable and testable, with no model required.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from .models import Evidence, Signal


@dataclass(frozen=True)
class Rule:
    cause: str
    keywords: Tuple[str, ...] = ()
    metric: Optional[str] = None
    op: Optional[str] = None          # ">" or "<"
    threshold: Optional[float] = None
    weight: float = 1.0               # prior strength of this cause
    next_steps: Tuple[str, ...] = ()

    def match(self, signals: List[Signal]) -> List[Evidence]:
        evidence: List[Evidence] = []
        for s in signals:
            if s.message and s.kind in ("log", "alert"):
                low = s.message.lower()
                if any(k in low for k in self.keywords):
                    evidence.append(Evidence(source=s.source, detail=s.message))
            if (
                self.metric
                and s.kind == "metric"
                and s.metric == self.metric
                and s.value is not None
            ):
                hit = (self.op == ">" and s.value > self.threshold) or (
                    self.op == "<" and s.value < self.threshold
                )
                if hit:
                    evidence.append(
                        Evidence(source=s.source, detail=f"{s.metric}={s.value} ({self.op}{self.threshold})")
                    )
        return evidence


RULES: List[Rule] = [
    Rule(
        cause="Database connection pool exhaustion",
        keywords=("connection pool", "too many connections", "timeout acquiring connection"),
        metric="db_connections_active", op=">", threshold=90, weight=1.2,
        next_steps=(
            "Check active vs. max DB connections and recent connection growth.",
            "Look for a slow query or a leaked connection holding the pool.",
            "Temporarily raise pool size / add a read replica if saturation is real.",
        ),
    ),
    Rule(
        cause="Memory pressure / OOM",
        keywords=("out of memory", "oomkilled", "cannot allocate memory"),
        metric="mem_usage_pct", op=">", threshold=90, weight=1.1,
        next_steps=(
            "Inspect the OOMKilled pod/container and its memory limit.",
            "Correlate with a recent deploy or a traffic spike.",
            "Raise the limit or fix the leak; add a memory alert below the limit.",
        ),
    ),
    Rule(
        cause="Upstream dependency failing (5xx)",
        keywords=("502", "503", "504", "upstream", "connection refused", "bad gateway"),
        metric="error_rate", op=">", threshold=0.05, weight=1.0,
        next_steps=(
            "Identify which upstream is returning 5xx and check its health.",
            "Verify DNS/service discovery and network path to the dependency.",
            "Fail over or shed load; open a circuit breaker if flapping.",
        ),
    ),
    Rule(
        cause="Latency / saturation",
        keywords=("timeout", "slow response", "high latency", "request timed out"),
        metric="p99_latency_ms", op=">", threshold=1000, weight=0.9,
        next_steps=(
            "Check CPU and p99 latency against the deploy timeline.",
            "Profile the slow endpoint; look for N+1 queries or lock contention.",
            "Scale out or add caching for the hot path.",
        ),
    ),
    Rule(
        cause="Disk full",
        keywords=("no space left on device", "disk full", "write failed"),
        metric="disk_usage_pct", op=">", threshold=95, weight=1.0,
        next_steps=(
            "Find the volume that is full and the largest recent growth.",
            "Rotate/ship logs; clear temp and old artifacts.",
            "Expand the volume and add a disk-usage alert below 90%.",
        ),
    ),
    Rule(
        cause="Expired certificate / auth failure",
        keywords=("certificate expired", "certificate has expired", "token expired", "401 unauthorized"),
        weight=1.0,
        next_steps=(
            "Check the certificate/secret expiry and rotation job.",
            "Confirm clock sync between services.",
            "Rotate the credential and add an expiry alert 30 days out.",
        ),
    ),
]


def evaluate(signals: List[Signal], rules: List[Rule] = RULES):
    """Return (rule, evidence) for every rule that matched at least one signal."""
    return [(r, ev) for r in rules if (ev := r.match(signals))]
