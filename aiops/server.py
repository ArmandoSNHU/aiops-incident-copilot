"""FastAPI service: health, Prometheus metrics, and incident triage.

    uvicorn aiops.server:app --port 8000
"""
from __future__ import annotations

import os
import time

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import __version__
from .llm import OllamaNarrator, PlainNarrator
from .logging_config import configure
from .metrics import SIGNALS_PER_INCIDENT, TRIAGE_DURATION, TRIAGE_REQUESTS
from .models import Incident, TriageResult
from .triage import TriageEngine

log = configure(os.environ.get("LOG_LEVEL", "INFO"))

# Narrator: offline by default; set AIOPS_MODE=ollama to synthesize summaries with a local model.
_narrator = OllamaNarrator() if os.environ.get("AIOPS_MODE", "offline").lower() == "ollama" else PlainNarrator()
_engine = TriageEngine(narrator=_narrator)

app = FastAPI(
    title="aiops-incident-copilot",
    description="AI-assisted incident triage: signals in, ranked evidence-cited causes out.",
    version=__version__,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__, "mode": os.environ.get("AIOPS_MODE", "offline")}


@app.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/triage", response_model=TriageResult)
def triage(incident: Incident) -> TriageResult:
    start = time.perf_counter()
    result = _engine.triage(incident)
    TRIAGE_DURATION.observe(time.perf_counter() - start)
    SIGNALS_PER_INCIDENT.observe(result.signal_count)
    TRIAGE_REQUESTS.labels(outcome="matched" if result.hypotheses else "no_match").inc()
    log.info(
        "triaged incident",
        extra={"fields": {
            "incident_id": result.incident_id,
            "signals": result.signal_count,
            "hypotheses": len(result.hypotheses),
            "top_cause": result.hypotheses[0].cause if result.hypotheses else None,
        }},
    )
    return result
