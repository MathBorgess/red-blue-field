"""Offline contract/effect tests: simulated worker receipts, never provider calls."""
import json

import httpx
import pytest

from red_blue_field.config import Settings
from red_blue_field.api import create_app
from red_blue_field.evidence import digest, verify_export
from red_blue_field.models import Action, RunRequest
from red_blue_field.target_jobs import MODEL


async def real_run(app, **kwargs):
    app.state.lab.settings.real_target_enabled = True
    return await app.state.lab.create(RunRequest(scenario_id="S02", mode="manual", target_driver="openai_external", **kwargs))


async def approved_job(client, run, activate=True):
    if activate:
        await run.tools.execute(Action(name="target_task"))
    current = (await client.get(f"/api/runs/{run.id}/target")).json()
    r = await client.post(f"/api/runs/{run.id}/target/advance", json={"expected_revision": current["revision"], "stage": "model"})
    assert r.status_code == 200, r.text
    headers = {"Authorization": "Bearer " + run.tokens["target"]}
    job = (await client.get(f"/target/{run.id}/job", headers=headers)).json()
    assert digest(job["request"]) == job["request_sha256"]
    assert (await client.get(f"/target/{run.id}/job", headers=headers)).status_code == 204
    return job, headers


async def prepared_job(client, run, activate=True):
    job, headers = await approved_job(client, run, activate)
    body = {"lease_token": job["lease_token"], "request_sha256": job["request_sha256"],
            "input_tokens": 100, "expected_revision": job["revision"]}
    r = await client.post(f"/target/{run.id}/jobs/{job['job_id']}/prepare", json=body, headers=headers)
    assert r.status_code == 200, r.text
    return job, headers, r.json()


def receipt(job, permit, output, **changes):
    return {"lease_token": job["lease_token"], "request_sha256": job["request_sha256"],
            "reservation_id": permit["reservation_id"], "response_id": "resp-offline-test", "model": MODEL,
            "service_tier": "default", "status": "completed", "usage": {"input_tokens": 100, "output_tokens": 20},
            "output": output, **changes}


async def receive(client, run, job, headers, permit, output, **changes):
    r = await client.post(f"/target/{run.id}/jobs/{job['job_id']}/result", json=receipt(job, permit, output, **changes), headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


async def advance_tool(client, run):
    current = (await client.get(f"/api/runs/{run.id}/target")).json()
    return await client.post(f"/api/runs/{run.id}/target/advance", json={"expected_revision": current["revision"], "stage": "tool"})


async def test_opt_in_and_separate_investigator_mode(app):
    with pytest.raises(ValueError, match="disabled"):
        await app.state.lab.create(RunRequest(scenario_id="S02", mode="manual", target_driver="openai_external"))
    app.state.lab.settings.real_target_enabled = True
    for values in [dict(scenario_id="S01", mode="manual"), dict(scenario_id="S02", mode="scripted")]:
        with pytest.raises(ValueError, match="requires S02"):
            await app.state.lab.create(RunRequest(target_driver="openai_external", **values))


async def test_red_only_proposes_model_and_never_falls_back(app, client, monkeypatch):
    async def fail(*args):
        pytest.fail("Synthetic target must not run for real driver")
    monkeypatch.setattr("red_blue_field.tools.target_decision", fail)
    run = await real_run(app)
    body = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "red.test_agent", "arguments":
            {"run_id": run.id, "surface": "target_task", "idempotency_key": "operator-proposal"}}}
    r = await client.post("/mcp/red", json=body, headers={"Authorization": "Bearer " + run.tokens["red"]})
    assert r.status_code == 200
    assert r.json()["result"]["structuredContent"]["tool_result"]["status"] == "needs_human_model_advance"
    state = (await client.get(f"/api/runs/{run.id}/target")).json()
    assert state["can_advance_model"] and not state["pending_job"]
    assert state["spending"]["requests"] == 0
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as unprivileged:
        r = await unprivileged.post(f"/api/runs/{run.id}/target/advance", json={"stage": "model", "expected_revision": state["revision"]},
                                   headers={"Authorization": "Bearer " + run.tokens["red"]})
        assert r.status_code == 401


async def test_role_job_binding_and_one_shot_prepare(app, client):
    run = await real_run(app)
    job, headers = await approved_job(client, run)
    bad = await client.get(f"/target/{run.id}/job", headers={"Authorization": "Bearer " + run.tokens["red"]})
    assert bad.status_code == 401
    body = {"lease_token": job["lease_token"], "input_tokens": 100, "expected_revision": job["revision"], "request_sha256": "0" * 64}
    path = f"/target/{run.id}/jobs/{job['job_id']}/prepare"
    assert (await client.post(path, json=body, headers=headers)).status_code == 403
    body["request_sha256"] = job["request_sha256"]
    assert (await client.post(path, json=body, headers=headers)).status_code == 200
    assert (await client.post(path, json=body, headers=headers)).status_code == 403
    public = (await client.get(f"/api/runs/{run.id}/target")).text
    assert job["lease_token"] not in public and run.tokens["target"] not in public


async def test_model_tool_proposal_waits_for_human_and_preserves_export(app, client):
    run = await real_run(app, benign=True)
    job, headers, permit = await prepared_job(client, run)
    tool = {"kind": "tool_call", "call_id": "call-save", "name": "save_draft", "arguments": {"content": "Authorized synthetic summary", "source": "document"}}
    state = await receive(client, run, job, headers, permit, tool)
    assert state["status"] == "awaiting_tool" and state["can_advance_tool"]
    assert run.fixture.snapshot()["effects"] == []
    assert (await advance_tool(client, run)).status_code == 200
    assert len(run.fixture.snapshot()["effects"]) == 1
    assert (await advance_tool(client, run)).status_code == 403
    job, headers, permit = await prepared_job(client, run, activate=False)
    state = await receive(client, run, job, headers, permit, {"kind": "message", "text": "Draft saved."})
    assert state["status"] == "completed"
    await app.state.lab.finish(run, "completed")
    assert run.record_kind == "model_run" and run.episode["metrics"]["model_calls"] == 2
    assert run.episode["legitimate_task_success"] and not run.episode["attacker_success"]
    assert verify_export(run.collector.root)["valid"]
    manifest = json.loads((run.collector.root / "manifest.json").read_text())
    assert manifest["model_configuration"][0]["model_id"] == MODEL


@pytest.mark.parametrize("profile,allowed", [("A", True), ("B", False)])
async def test_backend_policy_is_independent_of_model_output(app, client, profile, allowed):
    run = await real_run(app, profile=profile)
    job, headers, permit = await prepared_job(client, run)
    proposal = {"kind": "tool_call", "call_id": "call-policy-probe", "name": "save_draft",
                "arguments": {"content": run.fixture.canary(), "source": "internal_note"}}
    await receive(client, run, job, headers, permit, proposal)
    assert (await advance_tool(client, run)).status_code == 200
    effects = run.fixture.snapshot()["effects"]
    assert bool(effects) is allowed
    assert run.blocking_layer == ("none" if allowed else "tool_gateway")


async def test_a_b_have_identical_model_requests(app, client):
    a, b = await real_run(app, profile="A"), await real_run(app, profile="B")
    ja, _ = await approved_job(client, a)
    jb, _ = await approved_job(client, b)
    assert ja["request"] == jb["request"]


async def test_stop_in_flight_rejects_late_callback_and_blocks_spend(app, client):
    run = await real_run(app)
    job, headers, permit = await prepared_job(client, run)
    r = await client.post(f"/api/runs/{run.id}/stop")
    assert r.status_code == 200 and r.json()["status"] == "interrupted"
    late = await client.post(f"/target/{run.id}/jobs/{job['job_id']}/result", headers=headers,
                            json=receipt(job, permit, {"kind": "message", "text": "Late output"}))
    assert late.status_code == 403
    assert app.state.lab.targets.ledger.snapshot()["blocked"]
    assert not run.fixture.snapshot()["effects"]


async def test_incomplete_receipt_reconciles_usage_but_blocks_pilot(app, client):
    run = await real_run(app)
    job, headers, permit = await prepared_job(client, run)
    state = await receive(client, run, job, headers, permit, {"kind": "message", "text": ""}, status="incomplete")
    assert state["status"] == "blocked" and state["spending"]["blocked"]
    assert state["spending"]["spent_nano_usd"] > 0
    assert run.limits.total_tokens == 120 and run.limits.cost_usd > 0
    assert run.fixture.snapshot()["effects"] == []


async def test_prepare_ack_loss_does_not_free_reservation(app, client):
    run = await real_run(app)
    job, headers, _ = await prepared_job(client, run)
    path = f"/target/{run.id}/jobs/{job['job_id']}/failure"
    body = {"lease_token": job["lease_token"], "request_sha256": job["request_sha256"], "reservation_id": None,
            "submitted": False, "reason": "Prepare reply lost before provider call"}
    r = await client.post(path, headers=headers, json=body)
    assert r.status_code == 200 and r.json()["spending"]["blocked"]
    assert r.json()["spending"]["reserved_nano_usd"] > 0


async def test_episode_zero_model_budget_prevents_reservation(app, client):
    from red_blue_field.models import Budget
    run = await real_run(app, budget=Budget(max_model_calls=0))
    job, headers = await approved_job(client, run)
    r = await client.post(f"/target/{run.id}/jobs/{job['job_id']}/prepare", headers=headers,
                         json={"lease_token": job["lease_token"], "request_sha256": job["request_sha256"], "input_tokens": 100,
                               "expected_revision": job["revision"]})
    assert r.status_code == 403 and run.limits.model_calls == 0
    assert app.state.lab.targets.ledger.snapshot()["requests"] == 0


async def test_pending_jobs_recover_interrupted_without_credentials(app, client):
    run = await real_run(app)
    await prepared_job(client, run)
    reloaded = create_app(Settings(data_dir=app.state.lab.settings.data_dir, control_token=app.state.lab.settings.control_token,
                                  real_target_enabled=True))
    restored = reloaded.state.lab.runs[run.id]
    assert restored.status == "interrupted" and restored.tokens == {}
    assert reloaded.state.lab.targets.public(restored)["status"] == "interrupted"
    assert reloaded.state.lab.targets.ledger.snapshot()["blocked"]
    await reloaded.state.lab.close()


async def test_mutated_fixture_invalidates_model_proposal_before_effect(app, client):
    run = await real_run(app)
    job, headers, permit = await prepared_job(client, run)
    await receive(client, run, job, headers, permit, {"kind": "tool_call", "call_id": "call-state-bound", "name": "save_draft",
                  "arguments": {"content": "Authorized summary", "source": "document"}})
    run.fixture.write_document("A different synthetic document revision")
    assert (await advance_tool(client, run)).status_code == 403
    assert run.fixture.snapshot()["effects"] == []


async def test_fixture_change_in_flight_blocks_charge_and_late_proposal(app, client):
    run = await real_run(app)
    job, headers, permit = await prepared_job(client, run)
    run.fixture.write_document("Changed while model request was in flight")
    r = await client.post(f"/target/{run.id}/jobs/{job['job_id']}/result", headers=headers,
                         json=receipt(job, permit, {"kind": "message", "text": "Stale answer"}))
    assert r.status_code == 403 and app.state.lab.targets.ledger.snapshot()["blocked"]
    assert not run.fixture.snapshot()["effects"]


async def test_crash_between_reserve_and_submit_recovers_without_blocking_or_reinfer(app, client):
    run = await real_run(app)
    job, _ = await approved_job(client, run)
    targets = app.state.lab.targets
    reserved = targets.ledger.reserve(run.id, job["job_id"], job["job_id"], 100)
    persisted = targets._job(run, job["job_id"])
    persisted["reservation_id"] = reserved["reservation_id"]
    targets._put_job(run, persisted)
    reloaded = create_app(Settings(data_dir=app.state.lab.settings.data_dir, control_token=app.state.lab.settings.control_token,
                                  real_target_enabled=True))
    spending = reloaded.state.lab.targets.ledger.snapshot()
    assert not spending["blocked"] and spending["reserved_nano_usd"] == 0
    assert reloaded.state.lab.runs[run.id].status == "interrupted"
    await reloaded.state.lab.close()


async def test_identical_a_b_request_content_has_distinct_submission_identity(app, client):
    a = await real_run(app, profile="A")
    ja, ha, pa = await prepared_job(client, a)
    await receive(client, a, ja, ha, pa, {"kind": "message", "text": "First completed offline receipt"})
    b = await real_run(app, profile="B")
    jb, hb, pb = await prepared_job(client, b)
    assert ja["request_sha256"] == jb["request_sha256"]
    assert ja["job_id"] != jb["job_id"] and pa["reservation_id"] != pb["reservation_id"]
    await receive(client, b, jb, hb, pb, {"kind": "message", "text": "Second completed offline receipt"})
    spending = app.state.lab.targets.ledger.snapshot()
    assert spending["requests"] == 2 and not spending["blocked"]


@pytest.mark.parametrize("target_status", ["completed", "blocked"])
async def test_restart_preserves_terminal_target_state(app, client, target_status):
    run = await real_run(app)
    job, headers, permit = await prepared_job(client, run)
    await receive(client, run, job, headers, permit, {"kind": "message", "text": "Final public output"},
                  status="completed" if target_status == "completed" else "incomplete")
    await app.state.lab.finish(run, "completed")
    before = app.state.lab.targets.public(run)
    reloaded = create_app(Settings(data_dir=app.state.lab.settings.data_dir,
                                  control_token=app.state.lab.settings.control_token, real_target_enabled=True))
    after = reloaded.state.lab.targets.public(reloaded.state.lab.runs[run.id])
    assert before["status"] == after["status"] == target_status
    assert after["revision"] == before["revision"] and after["last_output"] == before["last_output"]
    await reloaded.state.lab.close()


async def test_failed_post_effect_state_write_cannot_replay_tool(app, client, monkeypatch):
    run = await real_run(app, benign=True)
    job, headers, permit = await prepared_job(client, run)
    await receive(client, run, job, headers, permit, {"kind": "tool_call", "call_id": "call-once", "name": "save_draft",
                  "arguments": {"content": "A single authorized synthetic draft", "source": "document"}})
    targets = app.state.lab.targets
    before = targets.public(run)
    original_put = targets._put_state

    def fail_after_fixture_commit(current, state):
        if (state["status"] == "awaiting_model" and state.get("tool_attempt", {}).get("status") == "completed"
                and len(current.fixture.snapshot()["effects"]) == 1):
            raise OSError("Injected control-state failure after fixture commit")
        original_put(current, state)

    monkeypatch.setattr(targets, "_put_state", fail_after_fixture_commit)
    with pytest.raises(OSError, match="after fixture commit"):
        await advance_tool(client, run)
    monkeypatch.setattr(targets, "_put_state", original_put)
    consumed = targets.public(run)
    assert consumed["status"] == "applying_tool" and consumed["requires_reconciliation"]
    assert consumed["pending_tool"] is None and consumed["revision"] > before["revision"]
    assert len(run.fixture.snapshot()["effects"]) == 1
    assert (await advance_tool(client, run)).status_code == 403
    retry = await client.post(f"/api/runs/{run.id}/target/advance", json={"stage": "tool", "expected_revision": before["revision"]})
    assert retry.status_code == 403 and len(run.fixture.snapshot()["effects"]) == 1
