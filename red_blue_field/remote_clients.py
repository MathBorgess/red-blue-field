"""Credential-safe HTTPS transport for the episode-scoped remote clients.

No caller-supplied URL is ever taken from model output. Authentication errors
stop the caller; this module never starts a login or retries a request.
"""
from __future__ import annotations

import base64
import json
import os
import re
import stat
import subprocess
import time
from pathlib import Path
from typing import Callable
from urllib.parse import urlsplit

import httpx


class ClientError(RuntimeError):
    """A safe error whose text never contains a response body or credential."""


class AuthenticationRequired(ClientError):
    pass


def https_origin(value: str) -> str:
    try:
        parsed = urlsplit(value)
        valid = (parsed.scheme == "https" and parsed.hostname and not parsed.username
                 and not parsed.password and parsed.port in {None, 443}
                 and parsed.path in {"", "/"} and not parsed.query and not parsed.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise ClientError("Configure one HTTPS origin without credentials, path, or query")
    return "https://" + parsed.netloc.rstrip("/")


def identifier(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value):
        raise ClientError("Invalid episode or job identifier")
    return value


def private_text(path: str | Path, *, maximum: int = 16384) -> str:
    """Read only an owner-only regular file, refusing the final symlink."""
    try:
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or info.st_mode & 0o077 or info.st_size > maximum):
                raise ClientError("Credential file must be an owner-only regular file")
            with os.fdopen(fd, "r", encoding="utf-8", closefd=False) as stream:
                value = stream.read(maximum + 1)
            if len(value.encode()) > maximum:
                raise ClientError("Credential file exceeds its size limit")
            return value
        finally:
            os.close(fd)
    except (OSError, UnicodeError):
        raise ClientError("Cannot read the private credential file") from None


def role_token_file(path: str | Path) -> str:
    token = private_text(path).strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{16,4096}", token):
        raise ClientError("Role token file must contain only one opaque token")
    return token


class CloudflareAccess:
    """Retrieve an existing application session without emitting its JWT."""

    def __init__(self, origin: str, executable: str = "cloudflared", *, runner=None,
                 clock: Callable[[], float] = time.time):
        self.origin = https_origin(origin)
        self.executable, self.runner, self.clock = executable, runner or subprocess.run, clock
        self._token, self._expires = "", 0.0

    def __call__(self) -> str:
        if self._token and self._expires > self.clock() + 30:
            return self._token
        self._token, self._expires = "", 0.0
        try:
            result = self.runner(
                [self.executable, "access", "token", "--app", self.origin],
                capture_output=True, text=True, check=False, timeout=30,
            )
            token = result.stdout.strip()
            if result.returncode or not re.fullmatch(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", token):
                raise ValueError
            payload = json.loads(base64.urlsafe_b64decode(token.split(".")[1] + "=="))
            if not isinstance(payload, dict):
                raise ValueError
            expires = payload.get("exp")
            if type(expires) not in {int, float} or expires <= self.clock() + 30:
                raise ValueError
        except (OSError, subprocess.SubprocessError, ValueError, TypeError, UnicodeError):
            raise AuthenticationRequired("Renew Cloudflare Access authentication manually before continuing") from None
        # Freshness only; Cloudflare validates authenticity and audience at the edge.
        self._token, self._expires = token, expires
        return token


class RemoteLabClient:
    def __init__(self, origin: str, role_token: str, access_token: Callable[[], str], *,
                 client: httpx.AsyncClient | None = None):
        self.origin = https_origin(origin)
        if not re.fullmatch(r"[A-Za-z0-9_.-]{16,4096}", role_token):
            raise ClientError("Invalid role token")
        self._role_token, self._access_token = role_token, access_token
        self._last_access = ""
        self._owned = client is None
        self.client = client or httpx.AsyncClient(timeout=15, follow_redirects=False, trust_env=False)

    @property
    def secrets(self) -> tuple[str, ...]:
        return tuple(x for x in (self._role_token, self._last_access) if x)

    def reject_secret_echo(self, value: object) -> None:
        encoded = json.dumps(value, ensure_ascii=False)
        if any(secret in encoded for secret in self.secrets):
            raise ClientError("Refused a response containing a transport credential")

    async def request(self, method: str, path: str, body: dict | None = None) -> dict | None:
        if (not re.fullmatch(r"/(?:mcp/(?:red|blue)|target/[A-Za-z0-9_/-]+)", path)
                or ".." in path or "//" in path or method not in {"GET", "POST"}):
            raise ClientError("Remote path is outside the client protocol")
        self._last_access = self._access_token()
        if not self._last_access or "\n" in self._last_access or "\r" in self._last_access:
            raise AuthenticationRequired("Cloudflare Access token is unavailable")
        try:
            response = await self.client.request(
                method, self.origin + path, json=body,
                headers={"Authorization": "Bearer " + self._role_token,
                         "cf-access-token": self._last_access, "Accept": "application/json"},
                follow_redirects=False,
            )
        except httpx.HTTPError:
            raise ClientError("Remote transport failed; no automatic retry was performed") from None
        if 300 <= response.status_code < 400:
            raise AuthenticationRequired("Remote redirect refused; renew Access authentication manually")
        if response.status_code in {401, 403}:
            raise AuthenticationRequired("Access or episode-role authentication was rejected")
        if response.status_code in {202, 204} and not response.content:
            return None
        if not 200 <= response.status_code < 300:
            raise ClientError(f"Remote request rejected (HTTP {response.status_code})")
        if len(response.content) > 2_000_000:
            raise ClientError("Remote response exceeds the client size limit")
        try:
            value = response.json()
        except ValueError:
            raise ClientError("Remote endpoint did not return protocol JSON") from None
        if not isinstance(value, dict):
            raise ClientError("Remote endpoint returned an invalid protocol object")
        self.reject_secret_echo(value)
        return value

    async def aclose(self):
        if self._owned:
            await self.client.aclose()
