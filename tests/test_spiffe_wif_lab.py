"""Deterministic authorization checks for the isolated SPIFFE/WIF exercise."""

from __future__ import annotations

import base64
import importlib.util
import json
import sys
from pathlib import Path

import httpx
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa, utils

from red_blue_field.fielddesk import Fixture


MODULE_PATH = Path(__file__).resolve().parents[1] / "FIELD" / "spiffe-wif-lab" / "mock_api.py"
POLICY_INPUTS = json.loads((MODULE_PATH.parent / "policy" / "test_inputs.json").read_text())[
    "fielddesk_test_inputs"]
SPEC = importlib.util.spec_from_file_location("fielddesk_mock_wif", MODULE_PATH)
assert SPEC and SPEC.loader
mock_api = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mock_api
SPEC.loader.exec_module(mock_api)


def b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def sign_svid(key, claims: dict, *, kid: str = "spire-key", algorithm: str = "ES256") -> str:
    header = {"alg": algorithm, "kid": kid, "typ": "JWT"}
    signing_input = ".".join(b64(json.dumps(item, separators=(",", ":")).encode())
                             for item in (header, claims))
    if algorithm == "ES256":
        der = key.sign(signing_input.encode(), ec.ECDSA(hashes.SHA256()))
        r, s = utils.decode_dss_signature(der)
        signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    else:
        signature = key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    return signing_input + "." + b64(signature)


def jwk_for(key, algorithm: str) -> dict:
    public = key.public_key().public_numbers()
    if algorithm == "ES256":
        return {"kty": "EC", "crv": "P-256", "alg": "ES256", "use": "sig", "kid": "spire-key",
                "x": b64(public.x.to_bytes(32, "big")), "y": b64(public.y.to_bytes(32, "big"))}
    return {"kty": "RSA", "alg": "RS256", "use": "sig", "kid": "spire-key",
            "n": b64(public.n.to_bytes((public.n.bit_length() + 7) // 8, "big")),
            "e": b64(public.e.to_bytes((public.e.bit_length() + 7) // 8, "big"))}


def synthetic_opa_decision(document: dict) -> bool:
    grant = document["grant"]
    resource = document["resource"]
    approved_right = {
        "actor": document["principal"]["sub"],
        "tenant_id": resource["tenant_id"],
        "action": document["action"],
        "resource_type": resource["type"],
        "resource_id": resource["id"],
    }
    payload_matches = (document["requested_payload"] is None and grant["approved_payload"] is None
                       if document["action"] == "ticket.read" else
                       document["requested_payload"] == grant["approved_payload"]
                       and isinstance(grant["approved_payload"], str)
                       and bool(grant["approved_payload"]))
    return bool(grant["active"] and
                approved_right in document["actor_rights"] and payload_matches and
                document["principal"] == {"sub": grant["actor"], "tenant_id": grant["tenant_id"]} and
                document["workload"]["spiffe_id"] == grant["workload_id"] and
                document["task"]["id"] == grant["task_id"] and
                document["action"] == grant["action"] and
                resource == {"type": grant["resource_type"], "id": grant["resource_id"],
                             "tenant_id": grant["tenant_id"]} and
                document["requested_tenant_id"] == resource["tenant_id"])


def harness(tmp_path, *, mode: str = "protected", algorithm: str = "ES256",
            task_kind: str = "read", opa_decider=None):
    tmp_path.mkdir(parents=True, exist_ok=True)
    now = [1_700_000_000.0]
    key = ec.generate_private_key(ec.SECP256R1()) if algorithm == "ES256" else rsa.generate_private_key(65537, 2048)
    settings = mock_api.Settings(
        spire_issuer="https://spire-oidc.local",
        spire_jwks_url="https://spire-oidc.local/keys",
        spiffe_agent_id="spiffe://fielddesk.test/agent",
        tls_ca_file=str(tmp_path / "local-ca.pem"),
        lab_mode=mode,
        lab_task_id="task-alpha" if task_kind == "read" else "task-insert-alpha",
        lab_task_kind=task_kind,
    )
    fixture = Fixture(tmp_path / "tickets.sqlite", "A" if mode in {"weak_tenant", "opa_guard"} else "B", seed=1,
                      canary="RBF_SYNTHETIC_TEST_CANARY")

    async def fetch_jwks():
        return {"keys": [jwk_for(key, algorithm)]}

    app = mock_api.create_app(settings, fixture, fetch_jwks, lambda: now[0],
                              opa_decider or synthetic_opa_decision)

    def svid(**overrides):
        claims = {"iss": settings.spire_issuer, "sub": settings.spiffe_agent_id, "aud": ["mock-wif"],
                  "iat": int(now[0]), "exp": int(now[0] + 300)}
        claims.update(overrides)
        return sign_svid(key, claims, algorithm=algorithm)

    return app, fixture, now, svid


async def exchange(client, token: str, task_id: str = "task-alpha"):
    return await client.post("/exchange", json={"task_id": task_id},
                             headers={"Authorization": "Bearer " + token})


def client_for(app):
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://lab.local")


def record_body(table_id="orders_table", target_tenant_id="tenant-a", record_payload="pedido: 994"):
    return {"table_id": table_id, "target_tenant_id": target_tenant_id,
            "record_payload": record_payload}


@pytest.mark.asyncio
async def test_malformed_identity_provider_response_is_unavailable(tmp_path):
    app, _, _, svid = harness(tmp_path)

    async def bad_jwks():
        return {"keys": "unusable"}

    app.state.broker.jwks_fetcher = bad_jwks
    async with client_for(app) as client:
        assert (await exchange(client, svid())).status_code == 503


@pytest.mark.asyncio
async def test_protected_grant_allows_one_authorized_read_only(tmp_path):
    app, fixture, _, svid = harness(tmp_path)
    async with client_for(app) as client:
        assert (await client.get("/health")).json() == {"status": "ok", "lab_mode": "protected"}
        assert (await client.post("/exchange", json={"task_id": "task-alpha"})).status_code == 401
        response = await exchange(client, svid())
        assert response.status_code == 200
        assert response.json()["expires_in"] == 60
        access = response.json()["access_token"]
        bearer = {"Authorization": "Bearer " + access}
        assert (await client.get("/tickets/ticket-beta", headers=bearer)).status_code == 403
        assert (await client.get("/tickets/ticket-alpha", headers=bearer)).json()["tenant"] == "tenant-a"
        assert (await client.get("/tickets/ticket-alpha", headers=bearer)).status_code == 401
        assert (await exchange(client, svid())).status_code == 401
    assert not any(effect["kind"] == "cross_tenant_read" for effect in fixture.snapshot()["effects"])
    assert all(access not in json.dumps(event) for event in app.state.broker.events)


@pytest.mark.asyncio
async def test_wrong_audience_only_passes_weak_audience_mode(tmp_path):
    protected, _, _, protected_svid = harness(tmp_path / "protected")
    weak, _, _, weak_svid = harness(tmp_path / "weak", mode="weak_audience")
    async with client_for(protected) as client:
        assert (await exchange(client, protected_svid(aud=["unrelated-service"]))).status_code == 401
    async with client_for(weak) as client:
        assert (await exchange(client, weak_svid(aud=["unrelated-service"]))).status_code == 200
        # Weak audience does not disable signature or issuer validation.
        bad = weak_svid(iss="https://untrusted-issuer.local", aud=["unrelated-service"])
        assert (await exchange(client, bad)).status_code == 401


@pytest.mark.asyncio
async def test_weak_tenant_exposes_synthetic_cross_tenant_effect(tmp_path):
    app, fixture, _, svid = harness(tmp_path, mode="weak_tenant")
    async with client_for(app) as client:
        access = (await exchange(client, svid())).json()["access_token"]
        response = await client.get("/tickets/ticket-beta", headers={"Authorization": "Bearer " + access})
        assert response.status_code == 200
        assert response.json()["tenant"] == "tenant-b"
        assert (await client.get("/tickets/ticket-alpha",
                                 headers={"Authorization": "Bearer " + access})).status_code == 401
    effects = fixture.snapshot()["effects"]
    assert any(effect["kind"] == "cross_tenant_read" and
               effect["data"]["ticket_id"] == "ticket-beta" for effect in effects)


@pytest.mark.asyncio
async def test_opa_guards_read_even_with_vulnerable_fixture(tmp_path):
    seen = []

    def decision(document):
        seen.append(document)
        return synthetic_opa_decision(document)

    app, fixture, _, svid = harness(tmp_path, mode="opa_guard", opa_decider=decision)
    assert fixture.profile == "A"
    async with client_for(app) as client:
        access = (await exchange(client, svid())).json()["access_token"]
        bearer = {"Authorization": "Bearer " + access}
        assert (await client.get("/tickets/ticket-beta", headers=bearer)).status_code == 403
        assert (await client.get("/tickets/ticket-alpha", headers=bearer)).status_code == 200
    assert not any(effect["kind"] == "cross_tenant_read" for effect in fixture.snapshot()["effects"])
    assert any(event["decision"] == "opa_deny" for event in app.state.broker.events)
    assert seen[0]["resource"] == {"type": "ticket", "id": "ticket-beta", "tenant_id": "tenant-b"}
    assert seen[-1] == POLICY_INPUTS["read"]


@pytest.mark.asyncio
async def test_opa_guards_insert_against_canonical_table_and_requested_tenant(tmp_path):
    seen = []

    def decision(document):
        seen.append(document)
        return synthetic_opa_decision(document)

    app, fixture, _, svid = harness(tmp_path, mode="opa_guard", task_kind="insert",
                                     opa_decider=decision)
    async with client_for(app) as client:
        access = (await exchange(client, svid(), task_id="task-insert-alpha")).json()["access_token"]
        bearer = {"Authorization": "Bearer " + access}
        mismatch = {**record_body(target_tenant_id="tenant-b"),
                    "user_sub": "admin", "spiffe_id": "spiffe://fielddesk.test/admin"}
        assert (await client.post("/records", json=mismatch, headers=bearer)).status_code == 422
        assert (await client.post("/records", json=record_body(target_tenant_id="tenant-b"),
                                  headers=bearer)).status_code == 403
        assert (await client.post("/records", json=record_body(record_payload="pedido: 995"),
                                  headers=bearer)).status_code == 403
        assert (await client.post("/records", json=record_body("orders_beta_table", "tenant-b"),
                                  headers=bearer)).status_code == 403
        with fixture.db() as db:
            assert db.execute("SELECT COUNT(*) FROM lab_order_records").fetchone()[0] == 0
        response = await client.post("/records", json=record_body(), headers=bearer)
        assert response.status_code == 201
        assert response.json()["table_id"] == "orders_table"
        assert (await client.post("/records", json=record_body(), headers=bearer)).status_code == 401
    assert seen[0]["principal"] == {"sub": "alice", "tenant_id": "tenant-a"}
    assert seen[0]["workload"] == {"spiffe_id": "spiffe://fielddesk.test/agent"}
    assert seen[0]["resource"] == {"type": "table", "id": "orders_table", "tenant_id": "tenant-a"}
    assert seen[0]["requested_payload"] == "pedido: 994"
    assert seen[0]["grant"]["approved_payload"] == "pedido: 994"
    assert seen[-1] == POLICY_INPUTS["insert"]
    with fixture.db() as db:
        rows = db.execute("SELECT table_id,tenant_id,payload FROM lab_order_records").fetchall()
    assert [tuple(row) for row in rows] == [("orders_table", "tenant-a", "pedido: 994")]
    assert not any(effect["kind"] == "cross_tenant_write" for effect in fixture.snapshot()["effects"])


@pytest.mark.asyncio
async def test_weak_tenant_insert_exposes_synthetic_cross_tenant_effect(tmp_path):
    app, fixture, _, svid = harness(tmp_path, mode="weak_tenant", task_kind="insert")
    async with client_for(app) as client:
        access = (await exchange(client, svid(), task_id="task-insert-alpha")).json()["access_token"]
        response = await client.post("/records", json=record_body(target_tenant_id="tenant-b",
                                                                    record_payload="pedido: 994"),
                                     headers={"Authorization": "Bearer " + access})
        assert response.status_code == 201
    assert any(effect["kind"] == "cross_tenant_write" for effect in fixture.snapshot()["effects"])


@pytest.mark.asyncio
@pytest.mark.parametrize("mode", ["weak_tenant", "opa_guard"])
async def test_insert_grant_rejects_unapproved_payload_in_same_tenant(tmp_path, mode):
    app, fixture, _, svid = harness(tmp_path, mode=mode, task_kind="insert")
    async with client_for(app) as client:
        access = (await exchange(client, svid(), task_id="task-insert-alpha")).json()["access_token"]
        bearer = {"Authorization": "Bearer " + access}
        assert (await client.post("/records", json=record_body(record_payload="pedido: 995"),
                                  headers=bearer)).status_code == 403
        assert (await client.post("/records", json=record_body(), headers=bearer)).status_code == 201
    with fixture.db() as db:
        rows = db.execute("SELECT payload FROM lab_order_records").fetchall()
    assert [row[0] for row in rows] == ["pedido: 994"]
    assert any(event["decision"] == "record_denied_payload" for event in app.state.broker.events)


@pytest.mark.asyncio
async def test_independent_alice_right_required_even_with_valid_task_grant(tmp_path):
    app, fixture, _, svid = harness(tmp_path, mode="opa_guard", task_kind="insert")
    with fixture.db() as db:
        db.execute("DELETE FROM lab_actor_rights WHERE actor=? AND action=?",
                   ("alice", "record.create"))
    async with client_for(app) as client:
        access = (await exchange(client, svid(), task_id="task-insert-alpha")).json()["access_token"]
        assert (await client.post("/records", json=record_body(),
                                  headers={"Authorization": "Bearer " + access})).status_code == 403
    with fixture.db() as db:
        assert db.execute("SELECT COUNT(*) FROM lab_order_records").fetchone()[0] == 0
    assert not fixture.snapshot()["effects"]
    assert any(event["decision"] == "opa_deny" for event in app.state.broker.events)


@pytest.mark.asyncio
@pytest.mark.parametrize("task_kind", ["read", "insert"])
async def test_opa_unavailable_fails_closed_without_resource_effect(tmp_path, task_kind):
    def unavailable(_document):
        raise mock_api.PolicyUnavailable("OPA offline")

    app, fixture, _, svid = harness(tmp_path, task_kind=task_kind, opa_decider=unavailable)
    task = "task-alpha" if task_kind == "read" else "task-insert-alpha"
    async with client_for(app) as client:
        access = (await exchange(client, svid(), task_id=task)).json()["access_token"]
        bearer = {"Authorization": "Bearer " + access}
        if task_kind == "read":
            assert (await client.get("/tickets/ticket-alpha", headers=bearer)).status_code == 503
        else:
            assert (await client.post("/records", json=record_body(), headers=bearer)).status_code == 503
    with fixture.db() as db:
        assert db.execute("SELECT COUNT(*) FROM lab_order_records").fetchone()[0] == 0
    assert not fixture.snapshot()["effects"]
    assert any(event["decision"] == "opa_unavailable" for event in app.state.broker.events)


@pytest.mark.asyncio
async def test_opa_missing_boolean_result_fails_closed(tmp_path):
    app, fixture, _, svid = harness(tmp_path, opa_decider=lambda _document: None)
    async with client_for(app) as client:
        access = (await exchange(client, svid())).json()["access_token"]
        assert (await client.get("/tickets/ticket-alpha",
                                 headers={"Authorization": "Bearer " + access})).status_code == 503
    assert not fixture.snapshot()["effects"]
    assert any(event["decision"] == "opa_unavailable" for event in app.state.broker.events)


@pytest.mark.asyncio
async def test_task_grant_cannot_change_action(tmp_path):
    read_app, read_fixture, _, read_svid = harness(tmp_path / "read")
    insert_app, insert_fixture, _, insert_svid = harness(tmp_path / "insert", task_kind="insert")
    async with client_for(read_app) as client:
        access = (await exchange(client, read_svid())).json()["access_token"]
        assert (await client.post("/records", json=record_body(),
                                  headers={"Authorization": "Bearer " + access})).status_code == 403
    async with client_for(insert_app) as client:
        access = (await exchange(client, insert_svid(), task_id="task-insert-alpha")).json()["access_token"]
        assert (await client.get("/tickets/ticket-alpha",
                                 headers={"Authorization": "Bearer " + access})).status_code == 403
    assert not read_fixture.snapshot()["effects"]
    assert not insert_fixture.snapshot()["effects"]


@pytest.mark.asyncio
@pytest.mark.parametrize("change", [
    {"iss": "https://wrong-issuer.local"},
    {"sub": "spiffe://fielddesk.test/rogue"},
    {"aud": ["wrong-audience"]},
    {"exp": 1_699_999_999},
])
async def test_svid_claims_are_checked(tmp_path, change):
    app, _, _, svid = harness(tmp_path)
    async with client_for(app) as client:
        assert (await exchange(client, svid(**change))).status_code == 401


@pytest.mark.asyncio
async def test_wrong_task_signature_kid_and_missing_bearer_denied(tmp_path):
    app, _, _, svid = harness(tmp_path)
    async with client_for(app) as client:
        assert (await exchange(client, svid(), task_id="task-beta")).status_code == 401
        assert (await exchange(client, svid().rsplit(".", 1)[0] + "." + b64(b"invalid"))).status_code == 401
        assert (await exchange(client, sign_svid(ec.generate_private_key(ec.SECP256R1()),
                          {"iss": "https://spire-oidc.local", "sub": "spiffe://fielddesk.test/agent",
                           "aud": "mock-wif", "iat": 1_700_000_000, "exp": 1_700_000_300},
                           kid="other-key"))).status_code == 401
        assert (await client.get("/tickets/ticket-alpha")).status_code == 401


@pytest.mark.asyncio
async def test_expiry_and_trusted_revocation_cut_off_issued_access(tmp_path):
    app, _, now, svid = harness(tmp_path)
    async with client_for(app) as client:
        access = (await exchange(client, svid())).json()["access_token"]
        now[0] += 61
        assert (await client.get("/tickets/ticket-alpha",
                                 headers={"Authorization": "Bearer " + access})).status_code == 401
        access = (await exchange(client, svid())).json()["access_token"]
        app.state.broker.revoke_grant()
        assert (await client.get("/tickets/ticket-alpha",
                                 headers={"Authorization": "Bearer " + access})).status_code == 401
        assert (await exchange(client, svid())).status_code == 401


@pytest.mark.asyncio
async def test_rs256_svid_from_spire_jwks_is_accepted(tmp_path):
    app, _, _, svid = harness(tmp_path, algorithm="RS256")
    async with client_for(app) as client:
        assert (await exchange(client, svid())).status_code == 200


def test_jwks_endpoint_must_be_https_keys(tmp_path):
    for bad_url in ("http://spire.local/keys", "https://spire.local/other", "https://x@spire.local/keys",
                    "https://other-spire.local/keys"):
        settings = mock_api.Settings("https://spire.local", bad_url, "spiffe://fielddesk.test/agent",
                                     str(tmp_path / "ca.pem"))
        with pytest.raises(ValueError, match="SPIRE_JWKS_URL"):
            settings.validate()


@pytest.mark.asyncio
async def test_persistent_evidence_keeps_decisions_without_credentials_or_canary(tmp_path):
    app, fixture, _, svid = harness(tmp_path / "identity")
    settings = app.state.broker.settings
    settings = mock_api.Settings(settings.spire_issuer, settings.spire_jwks_url,
                                 settings.spiffe_agent_id, settings.tls_ca_file,
                                 lab_state_dir=str(tmp_path / "evidence"))
    own_app = mock_api.create_app(settings, None, app.state.broker.jwks_fetcher,
                                  lambda: 1_700_000_000.0, synthetic_opa_decision)
    async with client_for(own_app) as client:
        access = (await exchange(client, svid())).json()["access_token"]
        assert (await client.get("/tickets/ticket-beta",
                                 headers={"Authorization": "Bearer " + access})).status_code == 403
    evidence = own_app.state.evidence_dir
    assert evidence and evidence.is_dir()
    assert (evidence / "fixture.sqlite").is_file()
    assert evidence.stat().st_mode & 0o777 == 0o700
    assert all((evidence / name).stat().st_mode & 0o777 == 0o600
               for name in ("fixture.sqlite", "manifest.json", "events.jsonl"))
    manifest = json.loads((evidence / "manifest.json").read_text())
    assert manifest["grant_source"] == "synthetic_controller"
    events = (evidence / "events.jsonl").read_text()
    assert "read_denied_policy" in events
    assert access not in events
    assert own_app.state.broker.fixture.canary() not in events
    assert own_app.state.broker.fixture.canary() not in json.dumps(manifest)
