from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Budget(StrictModel):
    max_steps: int = Field(default=40, ge=1, le=500)
    max_model_calls: int = Field(default=12, ge=0, le=200)
    max_total_tokens: int = Field(default=16000, ge=0, le=1_000_000)
    wall_time_seconds: int = Field(default=120, ge=1, le=3600)
    monetary_cap_usd: float = Field(default=1, ge=0, le=100)


class RunRequest(StrictModel):
    scenario_id: str = Field(default="S01", pattern=r"^S(0[1-9]|1[0-8])$")
    profile: Literal["A", "B", "C", "D"] = "B"
    mode: Literal["manual", "scripted", "agent_assisted", "bounded_autonomous"] = "scripted"
    reviewer: Literal["human_reviewer", "scripted_reviewer"] = "human_reviewer"
    environment: Literal["local_live", "cloud_emulated", "cloud_live"] | None = None
    seed: int = Field(default=1, ge=0, le=2**31 - 1)
    benign: bool = False
    guardrail_variant: Literal["profile_default", "application_vulnerable"] = "profile_default"
    max_depth: int = Field(default=4, ge=0, le=12)
    max_children: int = Field(default=3, ge=1, le=10)
    max_nodes: int = Field(default=40, ge=1, le=500)
    budget: Budget = Field(default_factory=Budget)


class Action(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    arguments: dict[str, Any] = Field(default_factory=dict)
    reason: str = Field(default="Teste da hipótese", max_length=1000)


class ReviewDecision(StrictModel):
    decision: Literal["approve", "deny"]
    reason: str = Field(min_length=3, max_length=2000)
    operation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")


class FindingDecision(StrictModel):
    status: Literal["confirmed", "needs_validation", "rejected"]
    reason: str = Field(min_length=8, max_length=4000)
    evidence_refs: list[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high", "critical"] | None = None
    decisive_unknown: str | None = None
    validation_plan: str | None = None


class Assessment(StrictModel):
    competency: str = Field(min_length=2, max_length=100)
    level: Literal["not_assessed", "guided", "independent", "transfer"]
    evidence_refs: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=8, max_length=4000)
    assistance: str = Field(default="", max_length=2000)
    gaps: str = Field(default="", max_length=2000)


class CampaignRequest(StrictModel):
    scenarios: list[str] = Field(default_factory=lambda: ["S01", "S02", "S03", "S04"], min_length=1, max_length=18)
    profiles: list[Literal["A", "B", "C", "D"]] = Field(default_factory=lambda: ["A", "B", "C"])
    repetitions: int = Field(default=1, ge=1, le=10)
    paired_benign: bool = True
    mode: Literal["scripted", "agent_assisted", "bounded_autonomous"] = "scripted"
    budget: Budget = Field(default_factory=Budget)
