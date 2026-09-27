"""The triage engine: correlate signals into ranked, cited hypotheses."""
from __future__ import annotations

from typing import List, Optional

from .llm import PlainNarrator
from .models import Hypothesis, Incident, TriageResult
from .rules import RULES, Rule, evaluate


def _confidence(rule: Rule, evidence_count: int) -> float:
    """A bounded, explainable confidence: prior weight + evidence, capped at 0.95."""
    base = 0.45 + 0.10 * (rule.weight - 1.0)
    score = base + 0.12 * evidence_count
    return round(max(0.05, min(0.95, score)), 2)


class TriageEngine:
    def __init__(self, rules: List[Rule] = RULES, narrator: Optional[object] = None):
        self.rules = rules
        self.narrator = narrator or PlainNarrator()

    def triage(self, incident: Incident) -> TriageResult:
        hypotheses: List[Hypothesis] = []
        for rule, evidence in evaluate(incident.signals, self.rules):
            hypotheses.append(
                Hypothesis(
                    cause=rule.cause,
                    confidence=_confidence(rule, len(evidence)),
                    evidence=evidence,
                    next_steps=list(rule.next_steps),
                )
            )
        # Highest confidence first; break ties by amount of evidence.
        hypotheses.sort(key=lambda h: (h.confidence, len(h.evidence)), reverse=True)
        summary = self.narrator.summarize(incident, hypotheses)
        return TriageResult(
            incident_id=incident.id,
            summary=summary,
            signal_count=len(incident.signals),
            hypotheses=hypotheses,
        )
