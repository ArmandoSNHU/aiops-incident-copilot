"""Narrators turn ranked hypotheses into a human summary.

`PlainNarrator` is deterministic and offline. `OllamaNarrator` asks a local LLM
to write the summary when one is running.
"""
from __future__ import annotations

from typing import List

from .models import Hypothesis, Incident


class PlainNarrator:
    """Template-based summary — no model, always available."""

    def summarize(self, incident: Incident, hypotheses: List[Hypothesis]) -> str:
        if not hypotheses:
            return (
                f"Analyzed {len(incident.signals)} signal(s); no known failure pattern matched. "
                "Escalate for manual review."
            )
        top = hypotheses[0]
        step = top.next_steps[0] if top.next_steps else "Investigate the cited evidence."
        return (
            f"Analyzed {len(incident.signals)} signal(s). Most likely cause: "
            f"{top.cause} (confidence {top.confidence:.0%}), backed by {len(top.evidence)} "
            f"piece(s) of evidence. Recommended first step: {step}"
        )


class OllamaNarrator:
    """LLM-written summary via a local Ollama server (default llama3.2)."""

    def __init__(self, model: str = "llama3.2", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host.rstrip("/")

    def summarize(self, incident: Incident, hypotheses: List[Hypothesis]) -> str:
        import requests  # lazy import: offline path needs no dependency

        lines = []
        for i, h in enumerate(hypotheses[:3], 1):
            ev = "; ".join(e.detail for e in h.evidence[:3])
            lines.append(f"{i}. {h.cause} (confidence {h.confidence:.0%}) — evidence: {ev}")
        ranked = "\n".join(lines) or "No ranked hypotheses."
        prompt = (
            "You are an SRE assistant. Given ranked root-cause hypotheses for an incident, "
            "write a 2-3 sentence summary for an on-call engineer. Be specific, cite the top "
            "cause and its evidence, and state the single best next action.\n\n"
            f"Incident: {incident.title or incident.id}\n{ranked}\n\nSummary:"
        )
        resp = requests.post(
            f"{self.host}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()["response"].strip()
