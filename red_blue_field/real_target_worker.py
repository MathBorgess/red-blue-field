"""One human-approved S02 model request; never a tool executor.

The controller owns authorization, cost admission and effects. This worker
counts the exact input, obtains its reservation, submits once, and reports only
public output/usage. It never retries an uncertain paid operation.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import uuid
from pathlib import Path

import httpx
from jsonschema import Draft202012Validator

from .evidence import canonical, digest
from .remote_clients import ClientError, CloudflareAccess, RemoteLabClient, identifier, private_text, role_token_file


MODEL = "gpt-5.4-mini-2026-03-17"
API_ORIGIN = "https://api.openai.com"
FUNCTIONS = {"read_document", "read_internal_note", "save_draft"}
COUNT_FIELDS = {"model", "input", "instructions", "tools", "parallel_tool_calls", "reasoning", "tool_choice"}
REQUEST_FIELDS = COUNT_FIELDS | {"service_tier", "max_output_tokens", "store"}


def load_api_key(env: dict | None = None, env_file: str | Path | None = None) -> str:
    """Resolve one key without sourcing a shell file or changing global env."""
    value = (os.environ if env is None else env).get("OPENAI_API_KEY", "")
    if env_file is not None:
        candidates = []
        for line in private_text(env_file).splitlines():
            match = re.fullmatch(r"\s*(?:export\s+)?OPENAI_API_KEY\s*=\s*(.*?)\s*", line)
            if match:
                candidates.append(match[1].strip("\"'"))
        if len(candidates) != 1:
            raise ClientError("The private env file must define OPENAI_API_KEY exactly once")
        value = candidates[0]
    if not isinstance(value, str) or not re.fullmatch(r"sk-[A-Za-z0-9_-]{20,}", value):
        raise ClientError("A valid dedicated OPENAI_API_KEY is required")
    return value


def _valid_input(items: object) -> bool:
    if not isinstance(items, list) or not 1 <= len(items) <= 200:
        return False
    for item in items:
        if not isinstance(item, dict):
            return False
        kind = item.get("type", "message")
        if kind == "message":
            if (set(item) - {"type", "role", "content"}
                    or item.get("role") not in {"system", "developer", "user", "assistant"}):
                return False
            content = item.get("content")
            if isinstance(content, str):
                continue
            if (not isinstance(content, list) or not content
                    or any(not isinstance(c, dict) or set(c) - {"type", "text"}
                           or c.get("type") not in {"input_text", "output_text"}
                           or not isinstance(c.get("text"), str) for c in content)):
                return False
        elif kind == "function_call":
            if (set(item) - {"type", "call_id", "name", "arguments", "id"}
                    or item.get("name") not in FUNCTIONS
                    or not isinstance(item.get("call_id"), str)
                    or not isinstance(item.get("arguments"), str)):
                return False
        elif kind == "function_call_output":
            if (set(item) - {"type", "call_id", "output", "id"}
                    or not isinstance(item.get("call_id"), str) or not isinstance(item.get("output"), str)):
                return False
        else:
            return False
    return True


def validate_request(request: object) -> dict:
    if not isinstance(request, dict) or set(request) - REQUEST_FIELDS:
        raise ClientError("Target request contains unsupported options")
    if (request.get("model") != MODEL or request.get("service_tier") != "default"
            or type(request.get("max_output_tokens")) is not int or request["max_output_tokens"] != 2000
            or request.get("store") is not False or request.get("parallel_tool_calls") is not False
            or request.get("reasoning") != {"effort": "none"} or not _valid_input(request.get("input"))
            or not isinstance(request.get("tool_choice", "auto"), str)
            or request.get("tool_choice", "auto") not in {"auto", "none", "required"}
            or ("instructions" in request and not isinstance(request["instructions"], str))):
        raise ClientError("Target request is outside the approved model and input configuration")
    tools = request.get("tools")
    if not isinstance(tools, list) or len(tools) != len(FUNCTIONS):
        raise ClientError("Target requires its fixed function catalog")
    names = set()
    for tool in tools:
        if (not isinstance(tool, dict) or set(tool) - {"type", "name", "description", "parameters", "strict"}
                or tool.get("type") != "function" or tool.get("strict") is not True
                or tool.get("name") not in FUNCTIONS or tool["name"] in names
                or not isinstance(tool.get("description", ""), str)
                or not isinstance(tool.get("parameters"), dict)):
            raise ClientError("Only the approved strict functions are permitted")
        try:
            Draft202012Validator.check_schema(tool["parameters"])
        except Exception:
            raise ClientError("Invalid target function schema") from None
        names.add(tool["name"])
    if names != FUNCTIONS or len(canonical(request)) > 1_000_000:
        raise ClientError("Target input or catalog exceeds its configured boundary")
    return request


def public_output(value: dict) -> dict:
    """Allow only one function proposal or a public assistant message."""
    items = value.get("output")
    if not isinstance(items, list):
        raise ClientError("Provider returned no public output list")
    calls, text = [], []
    for item in items:
        if not isinstance(item, dict):
            raise ClientError("Invalid provider output item")
        if item.get("type") == "function_call":
            if (item.get("name") not in FUNCTIONS or not isinstance(item.get("call_id"), str)
                    or not 1 <= len(item["call_id"]) <= 200 or not isinstance(item.get("arguments"), str)):
                raise ClientError("Provider proposed an unsupported function")
            try:
                arguments = json.loads(item["arguments"])
            except ValueError:
                raise ClientError("Provider returned invalid function arguments") from None
            if not isinstance(arguments, dict) or len(canonical(arguments)) > 16000:
                raise ClientError("Provider returned oversized function arguments")
            calls.append({"kind": "tool_call", "call_id": item["call_id"],
                          "name": item["name"], "arguments": arguments})
        elif item.get("type") == "message" and item.get("role") == "assistant":
            if not isinstance(item.get("content"), list):
                raise ClientError("Invalid public assistant message")
            for part in item["content"]:
                if not isinstance(part, dict):
                    raise ClientError("Invalid public assistant content")
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    text.append(part["text"])
                elif part.get("type") == "refusal" and isinstance(part.get("refusal"), str):
                    text.append(part["refusal"])
                else:
                    raise ClientError("Unsupported public assistant content")
        else:
            # Reasoning/encrypted items must never be persisted as public evidence.
            raise ClientError("Unexpected private or unsupported provider output")
    if len(calls) > 1 or (calls and text) or len("\n".join(text).encode()) > 64000:
        raise ClientError("Provider output is not one sequential public step")
    if calls:
        return calls[0]
    if not text and value.get("status") == "completed":
        raise ClientError("Completed response contains no public output")
    return {"kind": "message", "text": "\n".join(text)}


def normalized_receipt(value: dict) -> dict:
    if (not isinstance(value, dict) or not isinstance(value.get("id"), str)
            or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", value["id"])
            or value.get("model") != MODEL or value.get("service_tier") != "default"
            or value.get("status") not in {"completed", "incomplete", "failed", "cancelled"}):
        raise ClientError("Provider identity, model, tier or status did not match the request")
    usage = value.get("usage")
    if not isinstance(usage, dict):
        raise ClientError("Provider usage is missing; charge requires reconciliation")
    inp, out = usage.get("input_tokens"), usage.get("output_tokens")
    details = usage.get("input_tokens_details") or {}
    cached = details.get("cached_tokens", 0) if isinstance(details, dict) else None
    if (any(type(n) is not int or n < 0 for n in (inp, out, cached)) or cached > inp):
        raise ClientError("Provider usage is invalid; charge requires reconciliation")
    return {"response_id": value["id"], "model": value["model"], "service_tier": value["service_tier"],
            "status": value["status"], "usage": {"input_tokens": inp, "output_tokens": out,
                                                     "cached_input_tokens": cached}, "output": public_output(value)}


class OpenAIResponsesClient:
    def __init__(self, api_key: str, *, client: httpx.AsyncClient | None = None):
        self._api_key = api_key
        self._owned = client is None
        self.client = client or httpx.AsyncClient(timeout=60, follow_redirects=False, trust_env=False)

    async def _post(self, path: str, body: dict) -> dict:
        # Endpoint and paths are code constants; neither comes from a job/model.
        if path not in {"/v1/responses/input_tokens", "/v1/responses"}:
            raise ClientError("Unsupported provider endpoint")
        try:
            response = await self.client.post(API_ORIGIN + path, json=body,
                                             headers={"Authorization": "Bearer " + self._api_key},
                                             follow_redirects=False)
        except httpx.HTTPError:
            raise ClientError("Provider transport failed; no automatic retry was performed") from None
        if not 200 <= response.status_code < 300 or len(response.content) > 2_000_000:
            raise ClientError("Provider rejected the request or returned an oversized response")
        try:
            value = response.json()
        except ValueError:
            raise ClientError("Provider returned invalid JSON") from None
        if not isinstance(value, dict):
            raise ClientError("Provider returned an invalid response object")
        request_id = response.headers.get("x-request-id", "")
        value.pop("_provider_request_id", None)
        if re.fullmatch(r"[A-Za-z0-9_-]{1,200}", request_id):
            value["_provider_request_id"] = request_id
        return value

    async def count(self, request: dict) -> int:
        # Non-input generation options (store, output cap and tier) are not
        # count endpoint parameters. Every input-bearing option is included.
        value = await self._post("/v1/responses/input_tokens", {k: v for k, v in request.items() if k in COUNT_FIELDS})
        count = value.get("input_tokens")
        if value.get("object") != "response.input_tokens" or type(count) is not int or not 1 <= count <= 12000:
            raise ClientError("Full input token count is unavailable or exceeds 12000")
        return count

    async def generate(self, request: dict) -> dict:
        return await self._post("/v1/responses", request)

    async def aclose(self):
        if self._owned:
            await self.client.aclose()


def write_receipt(directory: Path | None, body: dict) -> None:
    if directory is None:
        return
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    if directory.is_symlink() or directory.stat().st_uid != os.geteuid() or directory.stat().st_mode & 0o077:
        raise ClientError("Receipt directory must be owner-only and not a symlink")
    path = directory / (identifier(body["job_id"]) + "-" + uuid.uuid4().hex + ".json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(body) + b"\n")


def charge_metadata(value: object) -> dict:
    """Preserve bounded billing identifiers, never arbitrary model items."""
    if not isinstance(value, dict):
        return {"provider_metadata": "unavailable"}
    result = {}
    for name in ("id", "model", "service_tier", "status", "_provider_request_id"):
        item = value.get(name)
        if isinstance(item, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,200}", item):
            result["response_id" if name == "id" else name.lstrip("_")] = item
    usage = value.get("usage")
    if isinstance(usage, dict):
        result["usage"] = {k: usage[k] for k in ("input_tokens", "output_tokens")
                           if type(usage.get(k)) is int and 0 <= usage[k] <= 1_000_000_000}
    return result


class TargetWorker:
    def __init__(self, remote: RemoteLabClient, provider: OpenAIResponsesClient, run_id: str, *,
                 receipt_dir: Path | None = None):
        self.remote, self.provider, self.run_id = remote, provider, identifier(run_id)
        self.receipt_dir = receipt_dir

    async def once(self) -> dict:
        job = await self.remote.request("GET", f"/target/{self.run_id}/job")
        if job is None:
            return {"status": "idle", "run_id": self.run_id, "model_calls": 0}
        job_id = identifier(job.get("job_id"))
        lease = job.get("lease_token")
        if not isinstance(lease, str) or not lease or "\n" in lease or "\r" in lease:
            raise ClientError("Target job has no valid lease")
        path = f"/target/{self.run_id}/jobs/{job_id}"
        request_hash, reservation, submitted = job.get("request_sha256"), None, False
        stage = "request_validation_failed"

        async def report_failure():
            try:
                await self.remote.request("POST", path + "/failure", {
                    "lease_token": lease, "reservation_id": reservation, "request_sha256": request_hash,
                    "submitted": submitted, "reason": stage,
                })
            except ClientError:
                # The controller's persistent reservation remains unavailable.
                pass

        try:
            request = validate_request(job.get("request"))
            if request_hash != digest(request) or type(job.get("revision")) is not int:
                raise ClientError("Target request hash or revision did not match")
            encoded = canonical(request).decode()
            if any(secret in encoded for secret in (*self.remote.secrets, self.provider._api_key, lease)):
                raise ClientError("Target request contains an authentication credential")
            stage = "input_count_failed"
            count = await self.provider.count(request)
            stage = "prepare_failed"
            grant = await self.remote.request("POST", path + "/prepare", {
                "lease_token": lease, "input_tokens": count, "request_sha256": request_hash,
                "expected_revision": job["revision"],
            })
            if isinstance(grant, dict):
                reservation = grant.get("reservation_id")
            if (not isinstance(grant, dict) or grant.get("submit_allowed") is not True
                    or not isinstance(reservation, str) or not reservation
                    or grant.get("model") != MODEL or grant.get("max_output_tokens") != 2000
                    or grant.get("service_tier") != "default"):
                raise ClientError("Controller did not authorize the exact provider request")
            stage, submitted = "provider_result_uncertain", True
            raw = await self.provider.generate(request)
            try:
                receipt = normalized_receipt(raw)
            except ClientError:
                metadata = {"run_id": self.run_id, "job_id": job_id, "request_sha256": request_hash,
                            "reservation_id": reservation, "requires_reconciliation": True, **charge_metadata(raw)}
                self.remote.reject_secret_echo(metadata)
                if self.provider._api_key not in canonical(metadata).decode() and lease not in canonical(metadata).decode():
                    write_receipt(self.receipt_dir, metadata)
                raise
            receipt_body = {"run_id": self.run_id, "job_id": job_id,
                            "request_sha256": request_hash, "reservation_id": reservation, **receipt}
            if "_provider_request_id" in raw:
                receipt_body["provider_request_id"] = raw["_provider_request_id"]
            self.remote.reject_secret_echo(receipt_body)
            if self.provider._api_key in canonical(receipt_body).decode() or lease in canonical(receipt_body).decode():
                raise ClientError("Public receipt contains an authentication credential")
            write_receipt(self.receipt_dir, receipt_body)
            stage = "result_delivery_uncertain"
            await self.remote.request("POST", path + "/result", {
                "lease_token": lease, "reservation_id": reservation, "request_sha256": request_hash, **receipt,
                **({"provider_request_id": raw["_provider_request_id"]} if "_provider_request_id" in raw else {}),
            })
            return {"status": "reported", "run_id": self.run_id, "job_id": job_id,
                    "provider_status": receipt["status"], "model_calls": 1}
        except asyncio.CancelledError:
            # Best effort only, bounded and with no new provider operation.
            failure = asyncio.create_task(report_failure())
            try:
                await asyncio.wait_for(asyncio.shield(failure), timeout=3)
            except (asyncio.CancelledError, TimeoutError):
                failure.cancel()
            raise
        except Exception:
            await report_failure()
            raise ClientError("Target step stopped; reconcile the job before any new model request") from None


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Handle one human-approved real-target job without executing tools")
    value.add_argument("--endpoint", required=True)
    value.add_argument("--run-id", required=True)
    value.add_argument("--role-token-file", required=True, help="Owner-only target-role token file")
    value.add_argument("--env-file", help="Owner-only env file; read only OPENAI_API_KEY")
    value.add_argument("--cloudflared", default="cloudflared")
    value.add_argument("--receipt-dir", type=Path, default=Path("artifacts/private/worker-receipts"))
    value.add_argument("--once", action="store_true", default=True, help="One job only (also the default)")
    return value


async def _main(args):
    remote = RemoteLabClient(args.endpoint, role_token_file(args.role_token_file),
                             CloudflareAccess(args.endpoint, args.cloudflared))
    provider = OpenAIResponsesClient(load_api_key(env_file=args.env_file))
    try:
        print(json.dumps(await TargetWorker(remote, provider, args.run_id, receipt_dir=args.receipt_dir).once()))
    finally:
        await provider.aclose()
        await remote.aclose()


def main():
    args = parser().parse_args()
    try:
        asyncio.run(_main(args))
    except (ClientError, KeyboardInterrupt):
        print("Target worker stopped. Check the private configuration and reconcile any pending job.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
