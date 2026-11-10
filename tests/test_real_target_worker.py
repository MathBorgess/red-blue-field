import asyncio
import json

import httpx
import pytest

from red_blue_field.evidence import digest
from red_blue_field.models import Action, RunRequest
from red_blue_field.real_target_worker import MODEL, OpenAIResponsesClient, TargetWorker, public_output
from red_blue_field.remote_clients import ClientError, RemoteLabClient


KEY = "sk-" + "test-only-key-" * 4
ROLE = "target-role-" + "t" * 32
ACCESS = "access-session-" + "a" * 32
LEASE = "lease-" + "l" * 32


async def approve_model(client, run):
    state = (await client.get(f"/api/runs/{run.id}/target")).json()
    response = await client.post(f"/api/runs/{run.id}/target/advance", json={
        "stage": "model", "expected_revision": state["revision"],
    })
    assert response.status_code == 200, response.text


async def apply_proposed_tool(client, run):
    state = (await client.get(f"/api/runs/{run.id}/target")).json()
    response = await client.post(f"/api/runs/{run.id}/target/advance", json={
        "stage": "tool", "expected_revision": state["revision"],
    })
    assert response.status_code == 200, response.text


def request_body():
    return {"model": MODEL, "service_tier": "default", "max_output_tokens": 2000,
            "store": False, "parallel_tool_calls": False, "reasoning": {"effort": "none"},
            "instructions": "Use only the synthetic episode functions.",
            "input": [{"role": "user", "content": "Summarize the synthetic document."}],
            "tools": [{"type": "function", "name": name, "description": "Synthetic function",
                       "strict": True, "parameters": {"type": "object", "properties": {},
                                                         "required": [], "additionalProperties": False}}
                      for name in ["read_document", "read_internal_note", "save_draft"]]}


def job():
    request = request_body()
    return {"job_id": "job-1", "lease_token": LEASE, "revision": 2,
            "request": request, "request_sha256": digest(request)}


def completion():
    return {"id": "resp-test-1", "model": MODEL, "service_tier": "default", "status": "completed",
            "usage": {"input_tokens": 234, "output_tokens": 20, "input_tokens_details": {"cached_tokens": 0}},
            "output": [{"type": "function_call", "call_id": "call-1", "name": "read_document",
                        "arguments": '{"document_id":"document-1"}'}]}


@pytest.mark.asyncio
async def test_real_backend_fake_provider_requires_each_human_advance(app, client, tmp_path):
    """Exercise the actual HTTP/job/spend/effect boundary without network or a model."""
    app.state.lab.settings.real_target_enabled = True
    run = await app.state.lab.create(RunRequest(
        scenario_id="S02", mode="manual", target_driver="openai_external", benign=True,
    ))
    await run.tools.execute(Action(name="target_task"))
    responses = [completion(), {
        **completion(), "id": "resp-test-2", "output": [{
            "type": "function_call", "call_id": "call-save", "name": "save_draft",
            "arguments": json.dumps({"content": "Authorized synthetic summary", "source": "document"}),
        }],
    }, {**completion(), "id": "resp-test-3", "output": [{
        "type": "message", "role": "assistant", "content": [{
            "type": "output_text", "text": "Draft saved.",
        }],
    }]}]
    requests = []

    def provider_http(request):
        assert request.url.host == "api.openai.com"
        payload = json.loads(request.content)
        assert run.tokens["target"] not in request.content.decode()
        assert ACCESS not in request.content.decode()
        if request.url.path.endswith("input_tokens"):
            return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 234})
        requests.append(payload)
        return httpx.Response(200, json=responses[len(requests) - 1], headers={"x-request-id": "req-offline-integration"})

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app)) as lab_http:
        async with httpx.AsyncClient(transport=httpx.MockTransport(provider_http)) as api_http:
            remote = RemoteLabClient("https://lab.example", run.tokens["target"], lambda: ACCESS, client=lab_http)
            worker = TargetWorker(remote, OpenAIResponsesClient(KEY, client=api_http), run.id,
                                  receipt_dir=tmp_path / "worker-receipts")
            assert (await worker.once())["status"] == "idle"
            await approve_model(client, run)
            assert (await worker.once())["status"] == "reported"
            state = (await client.get(f"/api/runs/{run.id}/target")).json()
            assert state["status"] == "awaiting_tool"
            assert not run.fixture.snapshot()["effects"]
            assert (await worker.once())["status"] == "idle"
            assert len(requests) == 1
            await apply_proposed_tool(client, run)
            await approve_model(client, run)
            await worker.once()
            assert not run.fixture.snapshot()["effects"]
            assert any(item.get("type") == "function_call_output" for item in requests[-1]["input"])
            await apply_proposed_tool(client, run)
            assert len(run.fixture.snapshot()["effects"]) == 1
            await approve_model(client, run)
            await worker.once()
    state = (await client.get(f"/api/runs/{run.id}/target")).json()
    assert state["status"] == "completed" and state["model_calls"] == 3
    assert state["spending"]["requests"] == 3
    assert not state["spending"]["blocked"]
    receipts = list((tmp_path / "worker-receipts").glob("*.json"))
    assert len(receipts) == 3
    assert all(json.loads(p.read_text())["provider_request_id"] == "req-offline-integration" for p in receipts)


@pytest.mark.asyncio
async def test_real_backend_provider_timeout_preserves_reservation_and_blocks(app, client):
    app.state.lab.settings.real_target_enabled = True
    run = await app.state.lab.create(RunRequest(scenario_id="S02", mode="manual", target_driver="openai_external"))
    await run.tools.execute(Action(name="target_task"))
    await approve_model(client, run)
    generated = []

    def provider_http(request):
        if request.url.path.endswith("input_tokens"):
            return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": 234})
        generated.append(request.url.path)
        raise httpx.ReadTimeout("Uncertain fake provider response", request=request)

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app)) as lab_http:
        async with httpx.AsyncClient(transport=httpx.MockTransport(provider_http)) as api_http:
            remote = RemoteLabClient("https://lab.example", run.tokens["target"], lambda: ACCESS, client=lab_http)
            worker = TargetWorker(remote, OpenAIResponsesClient(KEY, client=api_http), run.id)
            with pytest.raises(ClientError, match="reconcile"):
                await worker.once()
    state = (await client.get(f"/api/runs/{run.id}/target")).json()
    assert state["status"] == "blocked" and state["spending"]["blocked"]
    assert state["spending"]["reserved_nano_usd"] > 0 and len(generated) == 1
    assert not run.fixture.snapshot()["effects"]


class Harness:
    def __init__(self, *, available=True, provider_response=None, count=234, fail=None):
        self.available, self.fail, self.count = available, fail, count
        self.job = job()
        self.reply = provider_response or completion()
        self.events, self.lab_bodies, self.provider_bodies = [], [], []

    def lab(self, req):
        body = json.loads(req.content) if req.content else None
        self.events.append(req.url.path)
        self.lab_bodies.append((req.url.path, body))
        assert req.headers["authorization"] == "Bearer " + ROLE
        assert req.headers["cf-access-token"] == ACCESS
        if req.url.path.endswith("/job"):
            return httpx.Response(200, json=self.job) if self.available else httpx.Response(204)
        if req.url.path.endswith("/prepare"):
            if self.fail == "prepare":
                return httpx.Response(409)
            return httpx.Response(200, json={"reservation_id": "reservation-1", "submit_allowed": True,
                                           "model": MODEL, "max_output_tokens": 2000, "service_tier": "default"})
        if req.url.path.endswith("/result") and self.fail == "result":
            raise httpx.ReadTimeout("uncertain receipt delivery", request=req)
        return httpx.Response(200, json={"status": "recorded"})

    def provider(self, req):
        body = json.loads(req.content)
        self.events.append(req.url.path)
        self.provider_bodies.append((req.url.path, body))
        assert req.url.host == "api.openai.com"
        assert req.headers["authorization"] == "Bearer " + KEY
        assert ROLE not in req.content.decode() and ACCESS not in req.content.decode() and LEASE not in req.content.decode()
        if req.url.path.endswith("/input_tokens"):
            if self.fail == "count":
                return httpx.Response(500, text="private provider error " + KEY)
            return httpx.Response(200, json={"object": "response.input_tokens", "input_tokens": self.count})
        if self.fail == "provider":
            raise httpx.ReadTimeout("private diagnostic " + KEY, request=req)
        if self.fail == "cancel":
            raise asyncio.CancelledError
        if self.fail == "redirect":
            return httpx.Response(307, headers={"Location": "https://other.example/steal"})
        return httpx.Response(200, json=self.reply, headers={"x-request-id": "req-test-42"})

    async def run(self, tmp_path=None):
        async with httpx.AsyncClient(transport=httpx.MockTransport(self.lab)) as lab_http:
            async with httpx.AsyncClient(transport=httpx.MockTransport(self.provider)) as api_http:
                remote = RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=lab_http)
                provider = OpenAIResponsesClient(KEY, client=api_http)
                return await TargetWorker(remote, provider, "episode-a", receipt_dir=tmp_path).once()


@pytest.mark.asyncio
async def test_idle_does_not_count_generate_or_create_receipts(tmp_path):
    harness = Harness(available=False)
    result = await harness.run(tmp_path / "receipts")
    assert result["status"] == "idle" and result["model_calls"] == 0
    assert harness.events == ["/target/episode-a/job"]
    assert not (tmp_path / "receipts").exists()


@pytest.mark.asyncio
async def test_exact_input_count_and_reservation_precede_one_generation(tmp_path):
    harness = Harness()
    result = await harness.run(tmp_path / "receipts")
    assert result["status"] == "reported" and result["model_calls"] == 1
    assert harness.events == ["/target/episode-a/job", "/v1/responses/input_tokens",
                              "/target/episode-a/jobs/job-1/prepare", "/v1/responses",
                              "/target/episode-a/jobs/job-1/result"]
    count_payload = harness.provider_bodies[0][1]
    for field in ["input", "tools", "instructions", "reasoning", "parallel_tool_calls", "model"]:
        assert count_payload[field] == harness.job["request"][field]
    assert "store" not in count_payload and "max_output_tokens" not in count_payload
    assert harness.provider_bodies[1][1] == harness.job["request"]
    prepare = next(body for path, body in harness.lab_bodies if path.endswith("/prepare"))
    assert prepare["request_sha256"] == digest(harness.provider_bodies[1][1])
    receipt = next(body for path, body in harness.lab_bodies if path.endswith("/result"))
    assert receipt["output"] == {"kind": "tool_call", "call_id": "call-1", "name": "read_document",
                                  "arguments": {"document_id": "document-1"}}
    paths = list((tmp_path / "receipts").glob("*.json"))
    assert len(paths) == 1 and paths[0].stat().st_mode & 0o777 == 0o600
    persisted = paths[0].read_text()
    assert all(value not in persisted for value in [KEY, ROLE, ACCESS, LEASE])
    assert json.loads(persisted)["provider_request_id"] == "req-test-42"


@pytest.mark.asyncio
@pytest.mark.parametrize("failure,count", [("count", 1), ("prepare", 1), (None, 12001)])
async def test_count_or_reservation_failure_never_submits_model(failure, count):
    harness = Harness(fail=failure, count=count)
    with pytest.raises(ClientError):
        await harness.run()
    assert "/v1/responses" not in harness.events
    failure_body = next(body for path, body in harness.lab_bodies if path.endswith("/failure"))
    assert failure_body["submitted"] is False


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["provider", "redirect", "result"])
async def test_uncertain_paid_submission_is_reported_without_retry(failure, tmp_path):
    harness = Harness(fail=failure)
    with pytest.raises(ClientError) as error:
        await harness.run(tmp_path / "receipts")
    assert harness.events.count("/v1/responses") == 1
    failure_body = next(body for path, body in harness.lab_bodies if path.endswith("/failure"))
    assert failure_body["submitted"] is True and failure_body["reservation_id"] == "reservation-1"
    assert KEY not in str(error.value)
    if failure == "result":
        receipt = json.loads(next((tmp_path / "receipts").glob("*.json")).read_text())
        assert receipt["response_id"] == "resp-test-1"


@pytest.mark.asyncio
@pytest.mark.parametrize("mutate", [
    lambda req: req.update(model="other-model"),
    lambda req: req["tools"].append({"type": "web_search"}),
    lambda req: req.update(input=[{"role": "user", "content": [{"type": "input_image", "image_url": "https://other.example"}]}]),
    lambda req: req.update(instructions=ROLE),
])
async def test_job_cannot_add_models_hosted_tools_media_or_credentials(mutate):
    harness = Harness()
    mutate(harness.job["request"])
    harness.job["request_sha256"] = digest(harness.job["request"])
    with pytest.raises(ClientError):
        await harness.run()
    assert not harness.provider_bodies


@pytest.mark.asyncio
async def test_hash_mismatch_prevents_even_count_request():
    harness = Harness()
    harness.job["request"]["input"][0]["content"] = "Changed after approval"
    with pytest.raises(ClientError):
        await harness.run()
    assert not harness.provider_bodies


@pytest.mark.asyncio
async def test_incomplete_usage_is_reported_but_no_tool_is_fabricated():
    response = completion()
    response.update(status="incomplete", output=[])
    harness = Harness(provider_response=response)
    result = await harness.run()
    assert result["provider_status"] == "incomplete"
    receipt = next(body for path, body in harness.lab_bodies if path.endswith("/result"))
    assert receipt["status"] == "incomplete"
    assert receipt["output"] == {"kind": "message", "text": ""}


@pytest.mark.asyncio
async def test_reasoning_or_secret_output_is_not_exported(tmp_path):
    for output in [
        [{"type": "reasoning", "summary": [{"type": "summary_text", "text": "private internal text"}]}],
        [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": KEY}]}],
    ]:
        reply = completion()
        reply["output"] = output
        harness = Harness(provider_response=reply)
        with pytest.raises(ClientError):
            await harness.run(tmp_path / "receipts")
        assert not any(path.endswith("/result") for path, _ in harness.lab_bodies)
        assert all(KEY not in json.dumps(body) and "private internal text" not in json.dumps(body)
                   for _, body in harness.lab_bodies)
        for path in (tmp_path / "receipts").glob("*.json"):
            assert KEY not in path.read_text() and "private internal text" not in path.read_text()


@pytest.mark.asyncio
async def test_cancel_during_paid_submission_reports_uncertainty_without_retry():
    harness = Harness(fail="cancel")
    with pytest.raises(asyncio.CancelledError):
        await harness.run()
    assert harness.events.count("/v1/responses") == 1
    failure = next(body for path, body in harness.lab_bodies if path.endswith("/failure"))
    assert failure["submitted"] is True and failure["reservation_id"] == "reservation-1"


@pytest.mark.asyncio
async def test_unsupported_provider_output_retains_only_charge_metadata(tmp_path):
    reply = completion()
    reply["output"] = [{"type": "reasoning", "encrypted_content": "opaque-do-not-save", "summary": []}]
    harness = Harness(provider_response=reply)
    with pytest.raises(ClientError):
        await harness.run(tmp_path / "receipts")
    receipt = json.loads(next((tmp_path / "receipts").glob("*.json")).read_text())
    assert receipt["response_id"] == "resp-test-1"
    assert receipt["requires_reconciliation"] is True
    assert receipt["usage"]["input_tokens"] == 234
    assert "output" not in receipt and "opaque-do-not-save" not in json.dumps(receipt)


def test_multiple_function_calls_are_not_implicitly_executed_or_merged():
    reply = completion()
    reply["output"] *= 2
    with pytest.raises(ClientError):
        public_output(reply)
