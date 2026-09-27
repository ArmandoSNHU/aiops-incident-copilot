"""Typed request/response models for the triage API."""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Signal(BaseModel):
    """One observation: a log line, an alert, or a metric sample."""
    source: str = Field(..., description="Emitting component, e.g. 'api-gateway' or 'db'")
    kind: str = Field("log", description="'log', 'alert', or 'metric'")
    message: str = ""
    metric: Optional[str] = None
    value: Optional[float] = None
    severity: Severity = Severity.info
    timestamp: Optional[str] = None


class Incident(BaseModel):
    id: str
    title: str = ""
    signals: List[Signal] = Field(default_factory=list)


class Evidence(BaseModel):
    source: str
    detail: str


class Hypothesis(BaseModel):
    cause: str
    confidence: float
    evidence: List[Evidence]
    next_steps: List[str]


class TriageResult(BaseModel):
    incident_id: str
    summary: str
    signal_count: int
    hypotheses: List[Hypothesis]
