"""Episode-scoped stdio forwarding to the existing remote MCP service."""
from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .evidence import canonical
from .remote_clients import ClientError, CloudflareAccess, RemoteLabClient, identifier, role_token_file


PROTOCOLS = {"2025-11-25", "2025-03-26", "2024-11-05"}
METHODS = {"initialize", "ping", "tools/list", "tools/call", "notifications/initialized"}


def protocol_error(request_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


class MCPRemoteBridge:
    def __init__(self, remote: RemoteLabClient, run_id: str, role: str = "red"):
        if role not in {"red", "blue"}:
            raise ClientError("MCP bridge role must be red or blue")
        self.remote, self.run_id, self.role = remote, identifier(run_id), role

    async def handle(self, message: object) -> dict | None:
        request_id = message.get("id") if isinstance(message, dict) else None
        valid_id = type(request_id) in {str, int, type(None)}
        if (not isinstance(message, dict) or message.get("jsonrpc") != "2.0"
                or not isinstance(message.get("method"), str)
                or message.get("method") not in METHODS
                or not valid_id):
            return protocol_error(request_id if valid_id else None, -32600, "Unsupported MCP request")
        method, params = message["method"], message.get("params", {})
        if not isinstance(params, dict):
            return protocol_error(request_id, -32602, "Invalid MCP parameters")
        if method == "initialize" and params.get("protocolVersion") not in PROTOCOLS:
            return protocol_error(request_id, -32602, "Unsupported MCP protocol version")
        if method == "tools/call":
            arguments = params.get("arguments")
            if (not isinstance(params.get("name"), str) or not params["name"].startswith(self.role + ".")
                    or not isinstance(arguments, dict) or arguments.get("run_id") != self.run_id):
                return protocol_error(request_id, -32602, "Tool call is outside this bridge's role or episode")
        try:
            response = await self.remote.request("POST", "/mcp/" + self.role, message)
            if "id" not in message:
                return None
            if (not isinstance(response, dict) or response.get("jsonrpc") != "2.0"
                    or type(response.get("id")) is not type(request_id) or response.get("id") != request_id
                    or ("result" in response) == ("error" in response)):
                raise ClientError("Invalid MCP response")
            if method == "initialize" and "result" in response:
                if (not isinstance(response["result"], dict)
                        or response["result"].get("protocolVersion") not in PROTOCOLS):
                    raise ClientError("Unsupported server protocol")
            return response
        except ClientError:
            # Never forward raw exception/response text which may contain credentials.
            if "id" not in message:
                return None
            return protocol_error(request_id, -32001, "Remote MCP unavailable; check Access and episode credentials")


async def run_stdio(bridge: MCPRemoteBridge, reader=None, writer=None):
    reader, writer = reader or sys.stdin, writer or sys.stdout
    for line in reader:
        if not line.strip():
            continue
        if len(line.encode()) > 1_000_000:
            response = protocol_error(None, -32600, "MCP request exceeds size limit")
        else:
            try:
                message = json.loads(line)
            except ValueError:
                response = protocol_error(None, -32700, "Parse error")
            else:
                response = await bridge.handle(message)
        if response is not None:
            writer.write(canonical(response).decode() + "\n")
            writer.flush()


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description="Forward one episode's MCP role to its protected remote lab")
    value.add_argument("--endpoint", required=True, help="The configured HTTPS application origin")
    value.add_argument("--run-id", required=True)
    value.add_argument("--role", choices=["red", "blue"], default="red")
    value.add_argument("--role-token-file", required=True, help="Owner-only file containing a role token")
    value.add_argument("--cloudflared", default="cloudflared")
    return value


async def _main(args):
    remote = RemoteLabClient(args.endpoint, role_token_file(args.role_token_file),
                             CloudflareAccess(args.endpoint, args.cloudflared))
    try:
        await run_stdio(MCPRemoteBridge(remote, args.run_id, args.role))
    finally:
        await remote.aclose()


def main():
    args = parser().parse_args()
    try:
        asyncio.run(_main(args))
    except (ClientError, KeyboardInterrupt):
        print("Remote MCP stopped. Check the private configuration and authentication.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
