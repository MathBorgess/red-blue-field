import io
import json
import zipfile

import httpx
import pytest

from red_blue_field.api import create_app
from red_blue_field.cloud import CloudSandboxAdapter
from red_blue_field.config import Settings
from red_blue_field.evidence import verify_export
from red_blue_field.mcp import run_stdio_loop
from red_blue_field.models import Action, RunRequest
from red_blue_field.signing import generate_keypair, verify_signature


async def test_mcp_role_separation_and_http_lifecycle(client, app):
    r_ready = (await client.get("/api/readiness")).json()
    assert r_ready["mcp_red"] == "ready"
    assert r_ready["mcp_blue"] == "ready"

    created = (await client.post("/api/runs", json={"scenario_id": "S01", "profile": "A", "mode": "manual"})).json()
    run_id = created["id"]
    creds = (await client.get(f"/api/runs/{run_id}/credentials")).json()
    red_headers = {"Authorization": "Bearer " + creds["participant_token"]}
    blue_headers = {"Authorization": "Bearer " + creds["blue_token"]}

    # Initialize and negotiate 2025-11-25
    init_resp = await client.post(
        "/mcp/red",
        headers=red_headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
    )
    assert init_resp.status_code == 200
    assert init_resp.json()["result"]["protocolVersion"] == "2025-11-25"

    # Role separation: red token cannot list or call blue MCP server, and vice versa
    cross_red = await client.post("/mcp/blue", headers=red_headers, json={"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert cross_red.status_code == 401
    cross_blue = await client.post("/mcp/red", headers=blue_headers, json={"jsonrpc": "2.0", "id": 3, "method": "tools/list"})
    assert cross_blue.status_code == 401

    red_list = (await client.post("/mcp/red", headers=red_headers, json={"jsonrpc": "2.0", "id": 4, "method": "tools/list"})).json()["result"]
    blue_list = (await client.post("/mcp/blue", headers=blue_headers, json={"jsonrpc": "2.0", "id": 5, "method": "tools/list"})).json()["result"]
    assert len(red_list["tools"]) == 10
    assert len(blue_list["tools"]) == 10
    assert red_list["catalog_sha256"] != blue_list["catalog_sha256"]

    # Red discovers services and tests web endpoint with idempotency
    call_args = {
        "name": "red.test_web",
        "arguments": {
            "run_id": run_id,
            "resource": "fielddesk",
            "profile": "read_ticket",
            "parameters": {"ticket_id": "ticket-beta"},
            "idempotency_key": "idem-web-1",
        },
    }
    web_1 = (await client.post("/mcp/red", headers=red_headers, json={"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": call_args})).json()
    structured = web_1["result"]["structuredContent"]
    assert structured["status"] == "ok"
    assert structured["target_effect"]["changed"] is True

    # Repeat identical idempotency_key -> returns cached operation_id without consuming extra step budget
    web_2 = (await client.post("/mcp/red", headers=red_headers, json={"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": call_args})).json()
    assert web_2["result"]["structuredContent"]["operation_id"] == structured["operation_id"]
    assert app.state.lab.runs[run_id].limits.tool_calls == 1

    # Reusing idempotency_key with altered parameters is rejected
    bad_idem = {
        "name": "red.test_web",
        "arguments": {
            **call_args["arguments"],
            "parameters": {"ticket_id": "ticket-alpha"},
        },
    }
    conflict = (await client.post("/mcp/red", headers=red_headers, json={"jsonrpc": "2.0", "id": 8, "method": "tools/call", "params": bad_idem})).json()
    assert conflict["error"]["code"] == -32602

    # Blue queries events, diffs configuration, and revokes session + restores
    ev_resp = (
        await client.post(
            "/mcp/blue",
            headers=blue_headers,
            json={"jsonrpc": "2.0", "id": 9, "method": "tools/call", "params": {"name": "blue.query_events", "arguments": {"run_id": run_id}}},
        )
    ).json()["result"]["structuredContent"]
    seqs = [e["sequence"] for e in ev_resp["tool_result"]["events"]]
    assert seqs

    revoke = (
        await client.post(
            "/mcp/blue",
            headers=blue_headers,
            json={
                "jsonrpc": "2.0",
                "id": 10,
                "method": "tools/call",
                "params": {
                    "name": "blue.revoke_session",
                    "arguments": {
                        "run_id": run_id,
                        "reason": "Cross-tenant read observed in gateway telemetry",
                        "evidence_sequences": [seqs[-1]],
                        "idempotency_key": "blue-rev-1",
                    },
                },
            },
        )
    ).json()["result"]["structuredContent"]
    assert revoke["status"] == "ok"
    assert app.state.lab.runs[run_id].fixture.state("session_revoked") is True

    # Stop run via MCP red
    stopped = (
        await client.post(
            "/mcp/red",
            headers=red_headers,
            json={
                "jsonrpc": "2.0",
                "id": 11,
                "method": "tools/call",
                "params": {"name": "red.stop_run", "arguments": {"run_id": run_id, "reason": "Audit complete", "idempotency_key": "stop-1"}},
            },
        )
    ).json()["result"]["structuredContent"]
    assert stopped["status"] == "stopped"
    assert verify_export(app.state.lab.runs[run_id].collector.root)["valid"]


async def test_mcp_stdio_transport(app):
    lab = app.state.lab
    run = await lab.create(RunRequest(scenario_id="S01", profile="B", mode="manual"))
    in_buf = io.StringIO(
        json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
        + "\n"
        + json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        + "\n"
        + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "red.get_scope", "arguments": {"run_id": run.id}}})
        + "\n"
    )
    out_buf = io.StringIO()
    await run_stdio_loop(lab.mcp_red, token=run.tokens["red"], reader=in_buf, writer=out_buf)
    lines = [json.loads(line) for line in out_buf.getvalue().splitlines() if line.strip()]
    assert len(lines) == 2
    assert lines[0]["result"]["serverInfo"]["role"] == "red"
    assert lines[1]["result"]["structuredContent"]["tool_result"]["scope"]["scope_id"] == f"scope-{run.id}"


async def test_planner_workbench_tool_profile_and_auto_worker_reset(tmp_path):
    calls = []

    def worker_handler(request: httpx.Request):
        calls.append((request.method, request.url.path))
        if request.url.path == "/tools/run":
            body = json.loads(request.content)
            return httpx.Response(200, json={"status": "executed", "exit_code": 0, "stdout": f"profile={body['profile']}", "stderr": "", "profile": "A"})
        if request.url.path == "/convert":
            return httpx.Response(200, json={"status": "executed", "exit_code": 0, "stdout": "", "stderr": "", "profile": "A"})
        if request.url.path.startswith("/proof/"):
            return httpx.Response(200, json={"present": True, "marker": "proof-1234", "profile": "A"})
        if request.url.path == "/reset":
            return httpx.Response(200, json={"reset": True, "generation": 2, "removed_markers": 1, "proof_files_remaining": 0, "profile": "A"})
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok", "profile": "A"})
        return httpx.Response(404)

    settings = Settings(
        data_dir=tmp_path,
        control_token="test-control-token-" + "x" * 24,
        worker_a_url="http://worker-a.internal:8080",
        worker_a_token="worker-a-token-" + "y" * 24,
        auto_recreate_workers=True,
    )
    app = create_app(settings)
    lab = app.state.lab
    try:
        # Patch httpx.AsyncClient in tools module to use mock worker transport for worker-a.internal
        orig_client = httpx.AsyncClient

        def patched_client(*args, **kwargs):
            kwargs["transport"] = httpx.MockTransport(worker_handler)
            return orig_client(*args, **kwargs)

        import red_blue_field.tools as tools_mod
        tools_mod.httpx.AsyncClient = patched_client
        try:
            # 1. Planner proposes and executes tool_profile in S11
            run11 = await lab.create(RunRequest(scenario_id="S11", profile="A", mode="manual"))
            node = run11.add_hypothesis(Action(name="tool_profile", arguments={"profile": "sqlite_check"}, reason="Check SQLite version in worker"))
            assert node is not None
            await lab.step(run11)
            assert run11.history[-1]["observation"]["status"] == "ok"
            assert "sqlite_check" in run11.history[-1]["observation"]["result"]["stdout"]

            # 2. S12 with profile C + auto_recreate_workers=True achieves full 'restored' recovery_status
            run12 = await lab.create(RunRequest(scenario_id="S12", profile="C", guardrail_variant="application_vulnerable"))
            await lab.drive(run12)
            assert run12.episode["attacker_success"] is True
            assert run12.worker_restored is True
            assert run12.episode["effect_assessment"]["recovery_status"] == "restored"
            assert ("POST", "/reset") in calls
        finally:
            tools_mod.httpx.AsyncClient = orig_client
    finally:
        await lab.close()


async def test_distinct_reviewer_identities_and_external_ed25519_signing(client, app, tmp_path):
    lab = app.state.lab
    run = await lab.create(RunRequest(scenario_id="S01", profile="A"))
    await lab.drive(run)

    # Distinct verifier identity for finding
    finding_resp = await client.post(
        f"/api/runs/{run.id}/findings",
        json={
            "status": "confirmed",
            "reason": "Cross-tenant read verified in state-after.json by independent reviewer",
            "evidence_refs": ["state-after.json"],
            "severity": "high",
            "verifier_id": "human:auditor-maria",
        },
    )
    assert finding_resp.status_code == 200
    assert finding_resp.json()["verifier_id"] == "human:auditor-maria"

    # Distinct reviewer identity for competency assessment
    assess_resp = await client.post(
        f"/api/runs/{run.id}/assessments",
        json={
            "competency": "Access Control Auditing",
            "level": "independent",
            "evidence_refs": ["state-after.json"],
            "explanation": "Demonstrated cross-tenant isolation check and evidence verification.",
            "reviewer_id": "human:evaluator-carlos",
        },
    )
    assert assess_resp.status_code == 200
    assert assess_resp.json()["reviewer"] == "human:evaluator-carlos"
    assert assess_resp.json()["review_kind"] == "external_human_verified"

    # External Ed25519 evidence signing
    priv_path = tmp_path / "auditor.key"
    pub_path = tmp_path / "auditor.pub.json"
    pub_meta = generate_keypair(priv_path, pub_path, signer_id="human:auditor-maria")
    priv_hex = priv_path.read_text().strip()

    # Operator self-signing is rejected
    bad_sign = await client.post(
        f"/api/runs/{run.id}/sign",
        json={"signer_id": "human:operator", "private_key_hex": priv_hex},
    )
    assert bad_sign.status_code == 422

    sign_resp = await client.post(
        f"/api/runs/{run.id}/sign",
        json={"signer_id": "human:auditor-maria", "private_key_hex": priv_hex},
    )
    assert sign_resp.status_code == 200
    verified = verify_signature(run.collector.root, public_key_hex=pub_meta["public_key_hex"], expected_signer="human:auditor-maria")
    assert verified["signed"] is True
    assert verified["key_id"] == pub_meta["key_id"]

    # Export ZIP includes signature.json
    export_resp = await client.get(f"/api/runs/{run.id}/export")
    assert export_resp.status_code == 200
    with zipfile.ZipFile(io.BytesIO(export_resp.content)) as zf:
        assert "signature.json" in zf.namelist()


async def test_cloud_sandbox_adapter_contract_and_teardown(tmp_path):
    cfg_path = tmp_path / "aws-sandbox.json"
    cfg_path.write_text(
        json.dumps(
            {
                "schema_version": "0.1.0",
                "provider": "aws_sandbox",
                "account_id": "123456789012",
                "region": "us-east-1",
                "sandbox_prefix": "rbf-sandbox-ep1",
                "cost_cap_usd": 5.0,
                "per_operation_cost_usd": 0.002,
                "roles": {
                    "provisioner": "arn:aws:iam::123456789012:role/rbf-provisioner",
                    "participant": "arn:aws:iam::123456789012:role/rbf-participant",
                    "blue": "arn:aws:iam::123456789012:role/rbf-blue",
                    "observer": "arn:aws:iam::123456789012:role/rbf-observer",
                    "teardown": "arn:aws:iam::123456789012:role/rbf-teardown",
                },
                "resources": {"S13": "arn:aws:s3:::rbf-sandbox-ep1-bucket"},
            }
        )
    )
    settings = Settings(
        data_dir=tmp_path / "data",
        control_token="test-control-token-" + "x" * 24,
        aws_config=cfg_path,
    )
    app = create_app(settings)
    lab = app.state.lab
    try:
        assert lab.cloud_adapter.ready() is True
        run = await lab.create(RunRequest(scenario_id="S13", profile="A", environment="cloud_live", reviewer="scripted_reviewer"))
        await lab.drive(run)
        assert run.status == "complete"
        assert run.episode["attacker_success"] is True
        assert "cloud-teardown.json" in run.collector.artifacts
        teardown = json.loads(run.collector.path("cloud-teardown.json").read_text())
        assert teardown["teardown_role"].endswith("rbf-teardown")
        assert verify_export(run.collector.root)["valid"]
    finally:
        await lab.close()
