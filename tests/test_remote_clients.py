import base64
import io
import json
import subprocess

import httpx
import pytest

from red_blue_field.mcp_bridge import MCPRemoteBridge, run_stdio
from red_blue_field.real_target_worker import load_api_key
from red_blue_field.remote_clients import (
    AuthenticationRequired, ClientError, CloudflareAccess, RemoteLabClient, https_origin, role_token_file,
)


ROLE = "role-token-" + "r" * 32
ACCESS = "access-session-" + "a" * 32


@pytest.mark.parametrize("value", ["http://lab.example", "https://user:pw@lab.example", "https://lab.example/a",
                                   "https://lab.example?token=x", "https://lab.example/#x", "https://lab.example:8443"])
def test_only_configured_https_origin(value):
    with pytest.raises(ClientError):
        https_origin(value)


def test_credentials_require_private_file_and_never_source_shell(tmp_path):
    path = tmp_path / "role"
    path.write_text(ROLE)
    path.chmod(0o644)
    with pytest.raises(ClientError):
        role_token_file(path)
    path.chmod(0o600)
    assert role_token_file(path) == ROLE
    link = tmp_path / "symlink"
    link.symlink_to(path)
    with pytest.raises(ClientError):
        role_token_file(link)
    env = tmp_path / ".env.local"
    marker = tmp_path / "executed"
    env.write_text('OPENAI_API_KEY=sk-' + 't' * 30 + '\nOTHER=$(touch ' + str(marker) + ')\n')
    env.chmod(0o600)
    assert load_api_key(env={}, env_file=env) == "sk-" + "t" * 30
    assert not marker.exists()
    env.write_text("OPENAI_API_KEY=sk-" + "x" * 25 + "\nOPENAI_API_KEY=sk-" + "y" * 25)
    with pytest.raises(ClientError):
        load_api_key(env={}, env_file=env)


def jwt(exp):
    payload = base64.urlsafe_b64encode(json.dumps({"exp": exp}).encode()).decode().rstrip("=")
    return "header." + payload + ".signature"


def test_access_helper_uses_fixed_argv_and_requires_fresh_session():
    calls = []
    def runner(args, **kwargs):
        calls.append((args, kwargs))
        return subprocess.CompletedProcess(args, 0, jwt(2000), "")
    access = CloudflareAccess("https://lab.example/", runner=runner, clock=lambda: 1000)
    assert access() == jwt(2000)
    assert access() == jwt(2000)
    assert len(calls) == 1
    assert calls[0][0] == ["cloudflared", "access", "token", "--app", "https://lab.example"]
    assert calls[0][1]["capture_output"] is True
    expired = CloudflareAccess("https://lab.example", runner=lambda *a, **kw: subprocess.CompletedProcess([], 0, jwt(900), ""), clock=lambda: 1000)
    with pytest.raises(AuthenticationRequired):
        expired()


@pytest.mark.asyncio
async def test_remote_rejects_redirect_without_forwarding_credentials():
    requests = []
    def transport(request):
        requests.append(request)
        return httpx.Response(302, headers={"Location": "https://other.example/steal"})
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        remote = RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=http)
        with pytest.raises(AuthenticationRequired):
            await remote.request("POST", "/mcp/red", {"jsonrpc": "2.0"})
    assert len(requests) == 1
    assert requests[0].url.host == "lab.example"
    assert requests[0].headers["Authorization"] == "Bearer " + ROLE
    assert requests[0].headers["cf-access-token"] == ACCESS


@pytest.mark.asyncio
async def test_bridge_binds_role_episode_and_preserves_ids_notifications():
    seen = []
    def transport(request):
        body = json.loads(request.content)
        seen.append(body)
        if "id" not in body:
            return httpx.Response(202)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": {"tools": []}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        bridge = MCPRemoteBridge(RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=http), "episode-a")
        for role, run in [("blue", "episode-a"), ("red", "episode-b")]:
            response = await bridge.handle({"jsonrpc": "2.0", "id": 9, "method": "tools/call",
                                           "params": {"name": role + ".get_scope", "arguments": {"run_id": run}}})
            assert response["error"]["code"] == -32602
        assert not seen
        response = await bridge.handle({"jsonrpc": "2.0", "id": "request-42", "method": "tools/list"})
        assert response["id"] == "request-42"
        assert await bridge.handle({"jsonrpc": "2.0", "method": "notifications/initialized"}) is None
        assert len(seen) == 2


@pytest.mark.asyncio
async def test_bridge_stdio_errors_never_emit_transport_credentials():
    def transport(request):
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": 1, "result": {"accidental_token": ROLE}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        bridge = MCPRemoteBridge(RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=http), "episode-a")
        output = io.StringIO()
        await run_stdio(bridge, io.StringIO('{broken\n{"jsonrpc":"2.0","id":1,"method":"tools/list"}\n'), output)
        lines = [json.loads(x) for x in output.getvalue().splitlines()]
        assert lines[0]["error"]["code"] == -32700
        assert lines[1]["error"]["code"] == -32001
        assert ROLE not in output.getvalue() and ACCESS not in output.getvalue()


@pytest.mark.asyncio
async def test_remote_path_cannot_be_an_arbitrary_endpoint():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda r: pytest.fail("must not send"))) as http:
        remote = RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=http)
        for path in ["https://other.example/mcp/red", "/target/../control", "/target/a?key=x", "/api/runs"]:
            with pytest.raises(ClientError):
                await remote.request("GET", path)


@pytest.mark.asyncio
async def test_bridge_malformed_protocol_data_fails_closed():
    sent = []
    def transport(request):
        body = json.loads(request.content)
        sent.append(body)
        return httpx.Response(200, json={"jsonrpc": "2.0", "id": body["id"], "result": [], "error": {}})
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport)) as http:
        bridge = MCPRemoteBridge(RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=http), "episode-a")
        for bad in [[], {"jsonrpc": "2.0", "id": {}, "method": "tools/list"},
                    {"jsonrpc": "2.0", "id": 1, "method": []},
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "future"}}]:
            assert "error" in await bridge.handle(bad)
        assert not sent
        response = await bridge.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        assert response["error"]["code"] == -32001


@pytest.mark.asyncio
async def test_bridge_allows_server_version_negotiation(app):
    """A client's valid version proposal need not be in the bridge's own set."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app)) as http:
        bridge = MCPRemoteBridge(RemoteLabClient("https://lab.example", ROLE, lambda: ACCESS, client=http), "episode-a")
        response = await bridge.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                        "params": {"protocolVersion": "2026-12-31"}})
        assert response["result"]["protocolVersion"] == "2025-11-25"
        for invalid in [None, 20261125, "2026-02-30", "20261125"]:
            rejected = await bridge.handle({"jsonrpc": "2.0", "id": 2, "method": "initialize",
                                            "params": {"protocolVersion": invalid}})
            assert rejected["error"]["code"] == -32602
