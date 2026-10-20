from __future__ import annotations

import asyncio
import hmac
import io
import json
import secrets
import time
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import Field

from .config import Settings
from .engine import Lab, TERMINAL
from .evidence import digest, now, verify_export
from .fielddesk import Denied
from .models import Action, Assessment, CampaignRequest, FindingDecision, ReviewDecision, RunRequest, StrictModel
from .security import Halt, NeedsReview
from .tools import CASE_TOOLS, INTERNAL_CALL


class TextBody(StrictModel):
    body: str = Field(max_length=12000)


class SearchBody(StrictModel):
    query: str = Field(max_length=2000)


class ConfigBody(StrictModel):
    instruction: str = Field(max_length=12000)


class RefundBody(StrictModel):
    name: str = "refund"
    amount: int = Field(ge=1, le=100000)
    recipient: str = Field(max_length=80)
    key: str = Field(max_length=100)
    approval: str | None = Field(default=None, max_length=200)


class CloudBody(StrictModel):
    operation: str = Field(max_length=80)


class Proposal(StrictModel):
    action: Action
    parent_id: str | None = None
    claim: str = Field(min_length=3, max_length=2000)
    falsification: str = Field(min_length=3, max_length=2000)


class ResponseBody(StrictModel):
    response: str = Field(max_length=80)
    reason: str = Field(min_length=3, max_length=2000)
    actor: Literal['human', 'external_agent'] = 'human'
    external_session_id: str | None = Field(default=None, pattern=r'^[a-f0-9]{32}$')
    evidence_sequences: list[int] = Field(default_factory=list, max_length=30)


class ToolProfile(StrictModel):
    profile: str = Field(pattern=r'^(http_headers|nmap_local|sqlmap_fixture|filesystem|system|crypto|python|network|metasploit_version)$')


class StepBody(StrictModel):
    expected_hypothesis_id: str = Field(pattern=r'^h-[a-f0-9]{12}$')


def create_app(settings: Settings | None = None) -> FastAPI:
    lab = Lab(settings or Settings())

    @asynccontextmanager
    async def lifespan(app):
        yield
        await lab.close()

    app = FastAPI(title="red-blue-field", version="0.4.0", lifespan=lifespan)
    app.state.lab = lab

    @app.middleware("http")
    async def boundaries(request: Request, call_next):
        length = request.headers.get("content-length", "0")
        if not length.isdigit() or int(length) > 128 * 1024:
            return JSONResponse({"detail": "Request exceeds size limit"}, 413)
        if request.method in {'POST', 'PUT', 'PATCH'}:
            chunks, size = [], 0
            async for chunk in request.stream():
                size += len(chunk)
                if size > 128 * 1024:
                    return JSONResponse({'detail': 'Request exceeds size limit'}, 413)
                chunks.append(chunk)
            request._body = b''.join(chunks)
        # The lab has no CORS access. Reject cross-origin browser control requests.
        origin = request.headers.get("origin")
        if origin and origin.rstrip("/") != str(request.base_url).rstrip("/"):
            return JSONResponse({"detail": "Cross-origin requests are disabled"}, 403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self'; script-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(Denied)
    async def denied_handler(request, error: Denied):
        run = getattr(request.state, 'participant_run', None)
        if run and not INTERNAL_CALL.get() and run.status not in TERMINAL:
            async with run.lock:
                observation = {'status': 'denied', 'reason': error.reason, 'layer': error.layer}
                name = getattr(request.state, 'participant_tool', 'unknown')
                run.blocking_layer = error.layer
                run.history.append({'action': {'name': name}, 'observation': observation})
                run.emit('policy', 'policy.evaluated', {'origin': 'manual_http', **observation})
                await run.blue.observe(run, Action(name=name), observation)
                run.flush()
        return JSONResponse({"detail": {"reason": error.reason, "layer": error.layer}}, 403)

    @app.exception_handler(ValueError)
    async def value_handler(request, error: ValueError):
        return JSONResponse({"detail": str(error)}, 422)

    @app.exception_handler(Halt)
    async def halt_handler(request, error):
        run = getattr(request.state, 'participant_run', None)
        if run and not INTERNAL_CALL.get():
            async with run.lock:
                await lab.finish(run, error.reason)
        return JSONResponse({"detail": error.reason}, 409)

    @app.exception_handler(NeedsReview)
    async def review_handler(request, error):
        return JSONResponse({"detail": "Human review required", "review_id": error.review['id']}, 409)

    def control(x_control_token: str = Header(default="")):
        if not hmac.compare_digest(x_control_token.encode(), lab.settings.control_token.encode()):
            raise HTTPException(401, "Control token required")

    def get_run(run_id: str):
        if run_id not in lab.runs:
            raise HTTPException(404, "Run not active in this process; inspect its persisted record")
        return lab.runs[run_id]

    async def participant(request: Request, run_id: str, authorization: str = Header(default="")):
        run = get_run(run_id)
        token = authorization.removeprefix("Bearer ")
        if not token or not run.tokens.get('red') or not hmac.compare_digest(token.encode(), run.tokens["red"].encode()):
            raise HTTPException(401, "Episode-scoped participant identity required")
        internal = INTERNAL_CALL.get()
        if not internal:
            await run.lock.acquire()
        try:
            if not internal:
                request.state.participant_run = run
            if run.status in TERMINAL:
                raise Denied("Episode is closed", "tool_gateway")
            run.limits.check()
            run.limits.request()
            if run.fixture.state("session_revoked"):
                raise Denied("Participant session revoked", "tool_gateway")
            segment = request.url.path.split('/')[3]
            tool = {'inventory': 'inventory', 'tickets': 'read_ticket', 'search': 'search', 'document': 'write_document',
                    'configuration': 'configure', 'refund': 'refund', 'cloud': 'cloud'}.get(segment)
            if tool and tool not in CASE_TOOLS[run.request.scenario_id]:
                raise Denied("Endpoint outside scenario scope", "tool_gateway")
            if not internal and segment != 'actions':
                run.limits.tool()
            if not internal:
                request.state.participant_run = run
                request.state.participant_tool = tool or segment
                run.emit('tool', 'tool.requested', {'origin': 'manual_http', 'endpoint': segment, 'method': request.method})
            yield run
        finally:
            if not internal:
                try:
                    if run.status not in TERMINAL:
                        run.flush()
                finally:
                    run.lock.release()

    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.4.0"}

    @app.get("/api/readiness", dependencies=[Depends(control)])
    async def readiness():
        return {"local_services": True, "scripted_agents": True, "model_broker": lab.broker.ready(),
                "workers_configured": bool(lab.settings.worker_a_url and lab.settings.worker_b_url),
                "cloud_emulator": True, "cloud_live": "not_enabled_in_local_experiment",
                "mcp_red": "excluded", "mcp_blue": "excluded", "recovered_interruptions": lab.interrupted,
                "environment": "local lab; cloud provider and model execution are separately configured"}

    @app.get("/api/scenarios", dependencies=[Depends(control)])
    async def scenarios():
        return lab.catalog

    @app.get("/api/runs", dependencies=[Depends(control)])
    async def runs():
        return lab.store.list("runs")

    @app.post("/api/runs", dependencies=[Depends(control)], status_code=201)
    async def create(request: RunRequest):
        return (await lab.create(request)).public()

    @app.get("/api/runs/{run_id}", dependencies=[Depends(control)])
    async def inspect(run_id: str):
        value = lab.store.get("runs", run_id)
        if value is None:
            raise HTTPException(404, "Unknown episode")
        return value

    @app.post("/api/runs/{run_id}/start", dependencies=[Depends(control)])
    async def start(run_id: str):
        run = get_run(run_id)
        lab.start(run)
        return run.public()

    @app.post("/api/runs/{run_id}/step", dependencies=[Depends(control)])
    async def step(run_id: str, body: StepBody | None = None):
        return await lab.step(get_run(run_id), expected_hypothesis_id=body.expected_hypothesis_id if body else None)

    @app.post("/api/runs/{run_id}/stop", dependencies=[Depends(control)])
    async def stop(run_id: str):
        return await lab.stop(get_run(run_id))

    @app.post("/api/runs/{run_id}/finish", dependencies=[Depends(control)])
    async def finish(run_id: str):
        run = get_run(run_id)
        async with run.lock:
            await lab.finish(run, "completed")
        return run.public()

    @app.get("/api/runs/{run_id}/credentials", dependencies=[Depends(control)])
    async def credentials(run_id: str):
        run = get_run(run_id)
        if run.status in TERMINAL:
            raise HTTPException(409, 'Episode capabilities are closed; create a new episode')
        # Deliberately a controller-only capability minting/inspection operation.
        return {"participant_token": run.tokens["red"], "target_base_path": f"/lab/{run_id}", "expires_at": run.scope["valid_until"]}

    @app.get("/api/runs/{run_id}/state", dependencies=[Depends(control)])
    async def state(run_id: str):
        return get_run(run_id).fixture.snapshot()

    @app.get("/api/runs/{run_id}/events", dependencies=[Depends(control)])
    async def events(run_id: str, after: int = -1):
        run = get_run(run_id)
        return [e for e in run.collector.events if e["sequence"] > after]

    @app.get("/api/runs/{run_id}/stream", dependencies=[Depends(control)])
    async def stream(run_id: str, after: int = -1):
        run = get_run(run_id)
        async def generate():
            cursor = after
            while True:
                for e in run.collector.events:
                    if e["sequence"] > cursor:
                        yield "data: " + json.dumps(e, ensure_ascii=False) + "\n\n"
                        cursor = e["sequence"]
                if run.status in TERMINAL:
                    break
                yield ": heartbeat\n\n"
                await asyncio.sleep(0.5)
        return StreamingResponse(generate(), media_type="text/event-stream")

    @app.get("/api/runs/{run_id}/hypotheses", dependencies=[Depends(control)])
    async def hypotheses(run_id: str):
        run = get_run(run_id)
        return {"nodes": run.hypotheses, "frontier": run.frontier}

    @app.post("/api/runs/{run_id}/hypotheses", dependencies=[Depends(control)], status_code=201)
    async def propose(run_id: str, proposal: Proposal):
        run = get_run(run_id)
        if run.status in TERMINAL:
            raise HTTPException(409, "Episode is closed")
        async with run.lock:
            parent = next((n for n in run.hypotheses if n["hypothesis_id"] == proposal.parent_id), None)
            if proposal.parent_id and parent is None:
                raise HTTPException(422, "Parent must belong to this episode")
            node = run.add_hypothesis(proposal.action, parent, proposal.claim, proposal.falsification)
            run.flush()
        return {"node": node, "pending": run.frontier}

    @app.get("/api/runs/{run_id}/reviews", dependencies=[Depends(control)])
    async def reviews(run_id: str):
        return lab.store.list("reviews", run_id)

    @app.post("/api/runs/{run_id}/reviews/{review_id}", dependencies=[Depends(control)])
    async def decide(run_id: str, review_id: str, decision: ReviewDecision):
        run = get_run(run_id)
        async with run.lock:
            if run.status in TERMINAL:
                raise HTTPException(409, "Episode closed")
            value = run.reviews.decide(review_id, decision.operation_hash, decision.decision, decision.reason)
            run.status = "prepared"
            run.flush()
        return value

    @app.post("/api/runs/{run_id}/blue", dependencies=[Depends(control)])
    async def respond(run_id: str, body: ResponseBody):
        run = get_run(run_id)
        async with run.lock:
            if run.status in TERMINAL:
                raise HTTPException(409, "Closed episodes are immutable; create a new episode for retest")
            if body.actor == 'external_agent':
                if not body.external_session_id or not body.evidence_sequences:
                    raise HTTPException(422, 'External defense needs session identity and observed evidence')
                if any(n < 0 or n >= len(run.collector.events) or run.collector.events[n]['actor'] not in {'tool', 'target', 'policy', 'blue'} for n in body.evidence_sequences):
                    raise HTTPException(422, 'Defense evidence must refer to authenticated episode observations')
            result = await lab.respond(run, body.response, body.reason, reviewer=body.actor == 'human',
                external_session_id=body.external_session_id if body.actor == 'external_agent' else None,
                evidence_sequences=body.evidence_sequences)
            run.flush()
            return result

    @app.get("/api/runs/{run_id}/artifacts", dependencies=[Depends(control)])
    async def artifacts(run_id: str):
        return get_run(run_id).manifest().get("artifacts", []) or json.loads((get_run(run_id).collector.root / "manifest.json").read_text())["artifacts"]

    @app.get("/api/runs/{run_id}/artifacts/{name:path}", dependencies=[Depends(control)])
    async def artifact(run_id: str, name: str):
        run = get_run(run_id)
        if name not in run.collector.artifacts and name != "manifest.json":
            raise HTTPException(404, "Artifact is not in the collector manifest")
        return FileResponse(run.collector.path(name), filename=Path(name).name)

    @app.get("/api/runs/{run_id}/export", dependencies=[Depends(control)])
    async def export(run_id: str):
        run = get_run(run_id)
        async with run.lock:
            if run.status not in TERMINAL:
                raise HTTPException(409, "Finish the episode before export")
            verify_export(run.collector.root)
            data = io.BytesIO()
            with zipfile.ZipFile(data, "w", zipfile.ZIP_DEFLATED) as archive:
                for name in ["manifest.json", *run.collector.artifacts]:
                    archive.writestr(name, run.collector.path(name).read_bytes())
            return Response(data.getvalue(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{run_id}.zip"'})

    @app.post("/api/runs/{run_id}/findings", dependencies=[Depends(control)])
    async def finding(run_id: str, body: FindingDecision):
        run = get_run(run_id)
        if run.status not in TERMINAL:
            raise HTTPException(409, "Finish the episode before independent review")
        refs = body.evidence_refs
        if not refs or any(ref not in run.collector.artifacts for ref in refs):
            raise HTTPException(422, "Existing runtime artifact references are required")
        if body.status == "confirmed" and (not run.episode or run.episode["attacker_success"] is not True):
            raise HTTPException(422, "Confirmation requires a verified target effect")
        identifier = "finding-" + secrets.token_hex(8)
        record = dict(schema_version="0.2.0", finding_id=identifier, run_id=run.id, source_revision=run.source_revision,
            status=body.status, title=run.scenario["title"], finder_id="red:" + run.request.mode,
            verifier_id="human:operator", independent_verification_ref="verification-" + identifier + ".json",
            trust_boundary=run.scenario["surface"], trace_refs=["events.jsonl"], runtime_evidence_refs=refs,
            severity=body.severity if body.status == "confirmed" else None,
            decisive_unknown=body.decisive_unknown if body.status == "needs_validation" else None,
            validation_plan=body.validation_plan, rejection_reason=body.reason if body.status == "rejected" else None,
            remediation_ref="remediation-" + identifier + ".json" if body.status == "confirmed" else None, retest_ref=None)
        try:
            lab.contracts.validate("finding", record)
        except Exception as error:
            raise HTTPException(422, "Finding does not meet the evidence contract: " + str(error)[:200])
        run.collector.json(record["independent_verification_ref"], {"reviewer": "human:operator", "reason": body.reason, "evidence_refs": refs})
        if record["remediation_ref"]:
            run.collector.json(record["remediation_ref"], {"proposed_control": run.scenario["blue_control"], "retest_status": "pending"})
        with lab.store.connect() as db:
            db.execute("INSERT INTO findings VALUES(?,?,?)", (identifier, run_id, json.dumps(record)))
        run.collector.jsonl("findings.jsonl", lab.store.list("findings", run.id), "findings")
        run.emit("verifier", "finding.verified", {"finding_id": identifier, "status": body.status, "reviewer": "human:operator"}, refs)
        run.flush()
        return record

    @app.get("/api/runs/{run_id}/assessments", dependencies=[Depends(control)])
    async def assessments(run_id: str):
        return lab.store.list("assessments", run_id)

    @app.post("/api/runs/{run_id}/assessments", dependencies=[Depends(control)])
    async def assess(run_id: str, body: Assessment):
        run = get_run(run_id)
        if run.status not in TERMINAL:
            raise HTTPException(409, "Finish the episode before assessment")
        if body.level != "not_assessed" and (not body.evidence_refs or any(r not in run.collector.artifacts for r in body.evidence_refs)):
            raise HTTPException(422, "Assessment requires existing evidence")
        record = {**body.model_dump(), "reviewer": "human:operator", "timestamp": now(), "review_kind": "operator_reported"}
        with lab.store.connect() as db:
            db.execute("INSERT INTO assessments(run_id,body) VALUES(?,?)", (run_id, json.dumps(record)))
        run.collector.json("assessments.json", lab.store.list("assessments", run_id))
        run.emit("reviewer", "state.observed", {"assessment": record})
        run.flush()
        return record

    @app.get("/api/runs/{run_id}/learning-report", dependencies=[Depends(control)])
    async def learning_report(run_id: str):
        run = get_run(run_id)
        records = lab.store.list("assessments", run_id)
        reviews = lab.store.list("reviews", run_id)
        report = "# Aprendizado e supervisão humana\n\n"
        report += f"Episódio: `{run_id}`. Cenário: {run.scenario['title']}.\n\n"
        report += "## Resultado observado\n\n```json\n" + json.dumps(run.episode, ensure_ascii=False, indent=2) + "\n```\n\n"
        report += "## Competências\n\n"
        if not records:
            report += "Estado: `not_assessed`. A revisão humana permanece pendente.\n\n"
        for item in records:
            report += f"- {item['competency']}: {item['level']}. {item['explanation']} Evidências: {', '.join(item['evidence_refs'])}.\n"
        report += "\n## Intervenções\n\n"
        for review in reviews:
            report += f"- {review['id']}: {review['status']}. {review['reason']} Operação: `{review['operation_hash']}`.\n"
        report += "\n## Limites\n\n" + "\n".join("- " + text for text in run.limitations)
        report += "\n\nO parecer descreve avaliações do operador; identidade de um revisor externo exige registro separado.\n"
        return Response(report, media_type="text/markdown; charset=utf-8")

    @app.get("/api/campaigns", dependencies=[Depends(control)])
    async def campaigns():
        return lab.store.list("campaigns")

    @app.post("/api/campaigns", dependencies=[Depends(control)], status_code=201)
    async def create_campaign(body: CampaignRequest):
        return await lab.campaign(body)

    @app.get("/api/campaigns/{campaign_id}", dependencies=[Depends(control)])
    async def campaign(campaign_id: str):
        body = lab.store.get("campaigns", campaign_id)
        if not body:
            raise HTTPException(404, "Unknown campaign")
        episodes = [lab.store.get("runs", rid) for rid in body["runs"]]
        valid = [r for r in episodes if r and r.get("episode") and r["episode"]["validity"] == "valid"]
        adversarial = [r for r in valid if not r["request"]["benign"]]
        benign = [r for r in valid if r["request"]["benign"]]
        return {**body, "summary": {"scheduled": body["scheduled"], "completed": len(episodes), "valid": len(valid),
            "attacker_success": sum(r["episode"]["attacker_success"] is True for r in adversarial), "adversarial_valid": len(adversarial),
            "benign_valid": len(benign), "benign_utility": sum(r["episode"]["legitimate_task_success"] is True for r in benign),
            "unknown": sum(bool(r and r.get("episode") and r["episode"]["outcome"] == "unknown") for r in episodes)}}

    @app.post("/api/campaigns/{campaign_id}/stop", dependencies=[Depends(control)])
    async def stop_campaign(campaign_id: str):
        body = lab.store.get("campaigns", campaign_id)
        if not body:
            raise HTTPException(404, "Unknown campaign")
        body["status"] = "stopped"
        lab.store.put("campaigns", campaign_id, body)
        task = lab.campaign_tasks.get(campaign_id)
        if task:
            task.cancel()
        return body

    async def observed(run, name, result):
        if not INTERNAL_CALL.get():
            ref = run.collector.json(f'manual-output-{len(run.collector.events)}.json', result, 'tool_output')
            observation = {'status': 'ok', 'result': result}
            run.history.append({'action': {'name': name}, 'observation': observation})
            run.emit('tool', 'tool.executed', {'name': name, 'origin': 'manual_http', 'result': result}, [ref])
            await run.blue.observe(run, Action(name=name), observation)
        return result

    # Target routes: independent participant identity; deliberately vulnerable profile A.
    @app.get("/lab/{run_id}/inventory")
    async def inventory(run=Depends(participant)):
        return await observed(run, 'inventory', {"service": "FieldDesk", "endpoints": ["tickets/ticket-alpha", "tickets/ticket-beta", "search", "configuration"],
                "tenant": "tenant-a", "release": "synthetic-lab-0.4"})

    @app.get("/lab/{run_id}/tickets/{ticket_id}")
    async def ticket(ticket_id: str, run=Depends(participant)):
        return await observed(run, 'read_ticket', run.fixture.ticket(ticket_id))

    @app.post("/lab/{run_id}/search")
    async def search(body: SearchBody, run=Depends(participant)):
        return await observed(run, 'search', run.fixture.search(body.query))

    @app.get("/lab/{run_id}/search")
    async def get_search(query: str = "", run=Depends(participant)):
        return await observed(run, 'search', run.fixture.search(query))

    @app.put("/lab/{run_id}/document")
    async def write_document(body: TextBody, run=Depends(participant)):
        return await observed(run, 'write_document', run.fixture.write_document(body.body))

    @app.get("/lab/{run_id}/document")
    async def document(run=Depends(participant)):
        return await observed(run, 'write_document', {"body": run.fixture.document()})

    @app.put("/lab/{run_id}/configuration")
    async def config(body: ConfigBody, run=Depends(participant)):
        return await observed(run, 'configure', run.fixture.configure(body.instruction, "participant"))

    @app.post("/lab/{run_id}/refund")
    async def refund(body: RefundBody, run=Depends(participant)):
        if not INTERNAL_CALL.get():
            run.reviews.gate({'name': 'refund', 'amount': body.amount, 'recipient': body.recipient})
        return await observed(run, 'refund', run.fixture.refund(body.key, body.amount, body.recipient, body.approval))

    @app.post("/lab/{run_id}/cloud")
    async def cloud(body: CloudBody, run=Depends(participant)):
        allowed = {"S13": {"inspect", "grant_private", "read_private"}, "S14": {"inspect", "open_private_network", 'connect_private'},
                   "S15": {"inspect", "disable_service", 'healthcheck'}, "S18": {"inspect", "read_private"}}
        if body.operation not in allowed.get(run.request.scenario_id, set()):
            raise Denied("Cloud operation outside scenario", "tool_gateway")
        if not INTERNAL_CALL.get() and body.operation not in {'inspect', 'read_private', 'connect_private', 'healthcheck'}:
            run.reviews.gate({'name': 'cloud', 'operation': body.operation})
        return await observed(run, 'cloud', run.fixture.cloud(body.operation))

    @app.post('/lab/{run_id}/actions')
    async def participant_action(body: Action, run=Depends(participant)):
        result = await run.tools.execute(body)
        ref = run.collector.json(f'manual-action-{len(run.collector.events)}.json', {'action': body.model_dump(), 'result': result}, 'tool_output')
        run.emit('tool', 'tool.executed', {'name': body.name, 'origin': 'manual_http', 'result': result}, [ref])
        run.history.append({'action': body.model_dump(), 'observation': {'status': 'ok', 'result': result}})
        await run.blue.observe(run, body, {'status': 'ok', 'result': result})
        return result

    @app.post('/api/runs/{run_id}/tools', dependencies=[Depends(control)])
    async def tool_profile(run_id: str, body: ToolProfile):
        import httpx
        run = get_run(run_id)
        async with run.lock:
            if run.status in TERMINAL:
                raise HTTPException(409, 'Episode is closed')
            if run.request.scenario_id not in {'S11', 'S12'}:
                raise Denied('Tool workbench requires S11 or S12', 'tool_gateway')
            run.limits.tool()
            run.reviews.gate({'name': 'tool_profile', 'profile': body.profile})
            a = run.fixture.profile == 'A'
            url = lab.settings.worker_a_url if a else lab.settings.worker_b_url
            worker_token = lab.settings.worker_a_token if a else lab.settings.worker_b_token
            if not url or not worker_token:
                raise HTTPException(409, 'Start the disposable Docker workers first')
            run.emit('tool', 'tool.requested', {'profile': body.profile, 'target': 'worker_loopback'})
            async with httpx.AsyncClient(timeout=85, follow_redirects=False, trust_env=False) as client:
                result = await client.post(url.rstrip('/') + '/tools/run', headers={'Authorization': 'Bearer ' + worker_token}, json={**body.model_dump(), 'episode_id': run.id})
                value = result.json()
            ref = run.collector.json(f'tool-profile-{len(run.collector.events)}.json', value, 'tool_output')
            run.emit('tool', 'runner.command', {'profile': body.profile, 'http_status': result.status_code, 'target': 'worker_loopback'}, [ref])
            run.flush()
            return value

    lab.target_app = app
    static = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static), name="static")

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(static / "index.html")

    return app
