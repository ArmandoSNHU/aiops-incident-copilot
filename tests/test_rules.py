from aiops.models import Signal
from aiops.rules import RULES, Rule, evaluate


def _rule(cause):
    return next(r for r in RULES if r.cause == cause)


def test_keyword_and_metric_both_produce_evidence():
    signals = [
        Signal(source="svc", kind="log", message="timeout acquiring connection from pool"),
        Signal(source="db", kind="metric", metric="db_connections_active", value=97.0),
    ]
    ev = _rule("Database connection pool exhaustion").match(signals)
    assert len(ev) == 2
    assert any("db_connections_active" in e.detail for e in ev)


def test_metric_below_threshold_does_not_match():
    signals = [Signal(source="db", kind="metric", metric="db_connections_active", value=10.0)]
    assert _rule("Database connection pool exhaustion").match(signals) == []


def test_evaluate_returns_only_matching_rules():
    signals = [Signal(source="host", kind="log", message="no space left on device")]
    matched = {r.cause for r, _ in evaluate(signals)}
    assert matched == {"Disk full"}
