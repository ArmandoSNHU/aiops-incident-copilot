from aiops.sample import SAMPLE
from aiops.triage import TriageEngine
from aiops.models import Incident


def test_sample_incident_ranks_db_pool_first():
    result = TriageEngine().triage(SAMPLE)
    assert result.hypotheses, "expected at least one hypothesis"
    top = result.hypotheses[0]
    assert top.cause == "Database connection pool exhaustion"
    assert top.confidence > 0.6
    assert top.evidence and top.next_steps
    # hypotheses are sorted by descending confidence
    confidences = [h.confidence for h in result.hypotheses]
    assert confidences == sorted(confidences, reverse=True)
    assert "Database connection pool exhaustion" in result.summary


def test_no_match_gives_empty_hypotheses_and_escalation_summary():
    incident = Incident(id="INC-0", signals=[])
    result = TriageEngine().triage(incident)
    assert result.hypotheses == []
    assert "no known failure pattern" in result.summary.lower()


def test_confidence_is_bounded():
    result = TriageEngine().triage(SAMPLE)
    assert all(0.0 < h.confidence <= 0.95 for h in result.hypotheses)
