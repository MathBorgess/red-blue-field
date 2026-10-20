"""Scoped cloud sandbox adapter with role separation, cost tracking, and verified teardown."""
from __future__ import annotations

import json
import math
import re
import uuid
from pathlib import Path

from .evidence import now
from .fielddesk import Denied

REQUIRED_ROLES = ("provisioner", "participant", "blue", "observer", "teardown")


class CloudSandboxAdapter:
    """Adapter for isolated sandbox cloud accounts (docs/cloud-lab.md)."""

    def __init__(self, config_path: Path | None):
        self.config_path = config_path
        self.config: dict | None = None
        if config_path is not None:
            self.config = self.load_and_validate(config_path)

    @staticmethod
    def load_and_validate(path: Path) -> dict:
        if not path.is_file() or path.is_symlink():
            raise ValueError("Cloud sandbox configuration file is missing or unsafe")
        data = json.loads(path.read_text())
        if not isinstance(data, dict):
            raise ValueError("Cloud sandbox configuration must be a JSON object")
        if data.get("provider") != "aws_sandbox":
            raise ValueError("Cloud sandbox provider must be 'aws_sandbox'")
        account_id = str(data.get("account_id", ""))
        if not re.fullmatch(r"\d{12}", account_id):
            raise ValueError("Cloud sandbox requires a 12-digit AWS sandbox account_id")
        forbidden = set(data.get("forbidden_accounts", []))
        if account_id in forbidden or data.get("production_linked", False):
            raise ValueError("Production or forbidden AWS accounts are never allowed")
        prefix = str(data.get("sandbox_prefix", ""))
        if not prefix.startswith("rbf-sandbox-"):
            raise ValueError("sandbox_prefix must start with 'rbf-sandbox-'")
        cap = data.get("cost_cap_usd")
        if not isinstance(cap, (int, float)) or not math.isfinite(cap) or cap <= 0 or cap > 50:
            raise ValueError("Cloud sandbox requires a finite positive cost_cap_usd <= 50")
        roles = data.get("roles", {})
        if not isinstance(roles, dict) or not all(isinstance(roles.get(r), str) and roles.get(r) for r in REQUIRED_ROLES):
            raise ValueError("Cloud sandbox requires explicit roles: " + ", ".join(REQUIRED_ROLES))
        if len({roles[r] for r in REQUIRED_ROLES}) != len(REQUIRED_ROLES):
            raise ValueError("Provisioner, participant, blue, observer, and teardown roles must be distinct identities")
        resources = data.get("resources", {})
        if not isinstance(resources, dict) or not resources:
            raise ValueError("Cloud sandbox requires explicit scoped resource ARNs/locators")
        return data

    def ready(self) -> bool:
        return self.config is not None

    def execute(self, run, operation: str) -> dict:
        if not self.ready():
            raise ValueError("Live cloud runs require the separately configured AWS adapter workflow; emulator is available here")
        cfg = self.config
        cost_known = round(float(cfg.get("per_operation_cost_usd", 0.001)), 6)
        cost_estimated = round(cost_known * 1.2, 6)
        total_cloud_cost = getattr(run, "cloud_cost_usd", 0.0) + cost_estimated
        if total_cloud_cost > float(cfg["cost_cap_usd"]):
            raise Denied("Cloud sandbox monetary cap exceeded", "tool_gateway")
        run.cloud_cost_usd = total_cloud_cost

        before = run.fixture.snapshot()["state"]["cloud"]
        result = run.fixture.cloud(operation)
        after = run.fixture.snapshot()["state"]["cloud"]
        audit_entry = {
            "schema_version": "0.1.0",
            "request_id": "req-" + uuid.uuid4().hex[:16],
            "occurred_at": now(),
            "run_id": run.id,
            "scenario_id": run.request.scenario_id,
            "environment": run.environment,
            "account_redact": "aws-sandbox:" + cfg["account_id"][-4:],
            "region": cfg.get("region", "us-east-1"),
            "sandbox_prefix": cfg["sandbox_prefix"],
            "role_used": cfg["roles"]["participant"],
            "observer_role": cfg["roles"]["observer"],
            "operation": operation,
            "state_before": before,
            "state_after": after,
            "cost_ledger": {
                "known_usd": cost_known,
                "estimated_usd": cost_estimated,
                "unreconciled_usd": round(cost_estimated - cost_known, 6),
                "cap_usd": float(cfg["cost_cap_usd"]),
            },
        }
        ref = run.collector.json(f"cloud-audit-{len(run.collector.events)}.json", audit_entry, "cloud_audit")
        run.emit("tool", "state.observed", {"cloud_audit_ref": ref, "operation": operation, "request_id": audit_entry["request_id"]}, [ref])
        return {**result, "cloud_audit_ref": ref, "request_id": audit_entry["request_id"]}

    def verify_teardown(self, run) -> dict:
        if not self.ready():
            return {"verified": False, "reason": "emulator_only"}
        cfg = self.config
        cloud_state = run.fixture.snapshot()["state"]["cloud"]
        baseline_cloud = run.baseline["state"]["cloud"]
        clean = cloud_state == baseline_cloud
        record = {
            "schema_version": "0.1.0",
            "verified_at": now(),
            "run_id": run.id,
            "teardown_role": cfg["roles"]["teardown"],
            "provisioner_role": cfg["roles"]["provisioner"],
            "sandbox_prefix": cfg["sandbox_prefix"],
            "resources_clean": clean,
            "residual_drift": {} if clean else {"before": baseline_cloud, "after": cloud_state},
            "cost_summary": {
                "total_estimated_usd": round(getattr(run, "cloud_cost_usd", 0.0), 6),
                "cap_usd": float(cfg["cost_cap_usd"]),
            },
        }
        ref = run.collector.json("cloud-teardown.json", record, "cloud_audit")
        run.emit("runner", "state.observed", {"cloud_teardown_verified": clean, "teardown_role": cfg["roles"]["teardown"]}, [ref])
        return {**record, "artifact_ref": ref}
