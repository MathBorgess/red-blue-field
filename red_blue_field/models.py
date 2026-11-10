from __future__ import annotations

from typing import Any, Literal, Annotated
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
    target_driver: Literal["scripted", "openai_external"] = "scripted"
    target_smoke: bool = False
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


class TargetAdvance(StrictModel):
    expected_revision: int = Field(ge=0)
    stage: Literal["model", "tool"]


class TargetPrepare(StrictModel):
    lease_token: str = Field(min_length=24, max_length=200)
    input_tokens: int = Field(ge=1, le=12000)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    expected_revision: int = Field(ge=0)


class TargetUsage(StrictModel):
    input_tokens: int = Field(ge=0, le=12000)
    output_tokens: int = Field(ge=0, le=2000)
    cached_input_tokens: int = Field(default=0, ge=0, le=12000)


class TargetToolOutput(StrictModel):
    kind: Literal["tool_call"]
    call_id: str = Field(min_length=1, max_length=200)
    name: str = Field(min_length=1, max_length=80)
    arguments: dict[str, Any]


class TargetMessageOutput(StrictModel):
    kind: Literal["message"]
    text: str = Field(max_length=16000)


class TargetResult(StrictModel):
    lease_token: str = Field(min_length=24, max_length=200)
    reservation_id: str = Field(min_length=1, max_length=200)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    response_id: str = Field(min_length=1, max_length=200)
    provider_request_id: str | None = Field(default=None, max_length=200)
    model: str = Field(min_length=1, max_length=100)
    service_tier: str = Field(max_length=50)
    status: str = Field(max_length=50)
    usage: TargetUsage
    output: Annotated[TargetToolOutput | TargetMessageOutput, Field(discriminator="kind")]


class TargetFailure(StrictModel):
    lease_token: str = Field(min_length=24, max_length=200)
    reservation_id: str | None = Field(default=None, max_length=200)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    submitted: bool
    reason: str = Field(min_length=3, max_length=500)


class ReviewDecision(StrictModel):
    decision: Literal["approve", "deny"]
    reason: str = Field(min_length=3, max_length=2000)
    operation_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    reviewer_id: str | None = Field(default=None, pattern=r"^human:[a-zA-Z0-9._-]{2,64}$")


class FindingDecision(StrictModel):
    status: Literal["confirmed", "needs_validation", "rejected"]
    reason: str = Field(min_length=8, max_length=4000)
    evidence_refs: list[str] = Field(default_factory=list)
    severity: Literal["low", "medium", "high", "critical"] | None = None
    decisive_unknown: str | None = None
    validation_plan: str | None = None
    verifier_id: str | None = Field(default=None, pattern=r"^human:[a-zA-Z0-9._-]{2,64}$")


class Assessment(StrictModel):
    competency: str = Field(min_length=2, max_length=100)
    level: Literal["not_assessed", "guided", "independent", "transfer"]
    evidence_refs: list[str] = Field(default_factory=list)
    explanation: str = Field(min_length=8, max_length=4000)
    assistance: str = Field(default="", max_length=2000)
    gaps: str = Field(default="", max_length=2000)
    reviewer_id: str | None = Field(default=None, pattern=r"^human:[a-zA-Z0-9._-]{2,64}$")


class SignRequest(StrictModel):
    signer_id: str = Field(pattern=r"^human:[a-zA-Z0-9._-]{2,64}$")
    private_key_hex: str = Field(pattern=r"^[a-fA-F0-9]{64}$")


class CampaignRequest(StrictModel):
    scenarios: list[str] = Field(default_factory=lambda: ["S01", "S02", "S03", "S04"], min_length=1, max_length=18)
    profiles: list[Literal["A", "B", "C", "D"]] = Field(default_factory=lambda: ["A", "B", "C"])
    repetitions: int = Field(default=1, ge=1, le=10)
    paired_benign: bool = True
    mode: Literal["scripted", "agent_assisted", "bounded_autonomous"] = "scripted"
    budget: Budget = Field(default_factory=Budget)
