"""External cryptographic signing and verification for sealed evidence bundles."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from .evidence import atomic_json, canonical, now, verify_export


def generate_keypair(private_path: Path, public_path: Path, signer_id: str = "human:auditor") -> dict:
    """Generate an Ed25519 keypair for external evidence signing."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    private_path.parent.mkdir(parents=True, exist_ok=True)
    public_path.parent.mkdir(parents=True, exist_ok=True)
    import os
    fd = os.open(private_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as handle:
        handle.write(priv_bytes.hex() + "\n")
    key_id = "ed25519:" + hashlib.sha256(pub_bytes).hexdigest()[:16]
    pub_doc = {
        "schema_version": "0.1.0",
        "key_id": key_id,
        "algorithm": "ed25519",
        "signer_id": signer_id,
        "public_key_hex": pub_bytes.hex(),
        "created_at": now(),
    }
    atomic_json(public_path, pub_doc)
    return pub_doc


def sign_export(root: Path, private_key_hex: str, signer_id: str = "human:auditor") -> dict:
    """Verify a sealed episode directory and attach a detached Ed25519 signature.json."""
    if not signer_id.startswith("human:") or signer_id == "human:operator":
        raise ValueError("External evidence signing requires a distinct human signer identity (e.g. human:auditor-1)")
    verify_export(root)
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    raw_priv = bytes.fromhex(private_key_hex.strip())
    if len(raw_priv) != 32:
        raise ValueError("Ed25519 private key must be 32 raw bytes (64 hex chars)")
    private_key = Ed25519PrivateKey.from_private_bytes(raw_priv)
    pub_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    key_id = "ed25519:" + hashlib.sha256(pub_bytes).hexdigest()[:16]
    signed_at = now()
    payload = {
        "schema_version": "0.1.0",
        "run_id": manifest["run_id"],
        "code_commit": manifest["code_commit"],
        "manifest_sha256": manifest_sha256,
        "scope_sha256": manifest["scope_sha256"],
        "last_event_hash": manifest["last_event_hash"],
        "signer_id": signer_id,
        "key_id": key_id,
        "algorithm": "ed25519",
        "signed_at": signed_at,
    }
    signature = private_key.sign(canonical(payload)).hex()
    envelope = {
        **payload,
        "public_key_hex": pub_bytes.hex(),
        "signature_hex": signature,
    }
    atomic_json(root / "signature.json", envelope)
    return envelope


def verify_signature(
    root: Path,
    public_key_hex: str | None = None,
    expected_signer: str | None = None,
) -> dict:
    """Verify both the export bundle and its detached Ed25519 signature.json."""
    base = verify_export(root)
    sig_path = root / "signature.json"
    if not sig_path.is_file() or sig_path.is_symlink():
        raise ValueError("Missing signature.json in export directory")
    envelope = json.loads(sig_path.read_text())
    manifest_bytes = (root / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()

    if envelope.get("run_id") != manifest["run_id"]:
        raise ValueError("Signature run_id mismatch")
    if envelope.get("manifest_sha256") != manifest_sha256:
        raise ValueError("Signature manifest_sha256 mismatch")
    if envelope.get("scope_sha256") != manifest["scope_sha256"]:
        raise ValueError("Signature scope_sha256 mismatch")
    if envelope.get("last_event_hash") != manifest["last_event_hash"]:
        raise ValueError("Signature last_event_hash mismatch")
    signer_id = envelope.get("signer_id", "")
    if not signer_id.startswith("human:") or signer_id == "human:operator":
        raise ValueError("Signature signer_id must be a distinct external human identity")
    if expected_signer and signer_id != expected_signer:
        raise ValueError(f"Expected signer {expected_signer}, got {signer_id}")

    pub_hex = public_key_hex or envelope.get("public_key_hex", "")
    if public_key_hex and envelope.get("public_key_hex") and public_key_hex.strip() != envelope["public_key_hex"]:
        raise ValueError("Pinned public key does not match signature envelope public key")
    raw_pub = bytes.fromhex(pub_hex.strip())
    if len(raw_pub) != 32:
        raise ValueError("Invalid Ed25519 public key length")
    expected_key_id = "ed25519:" + hashlib.sha256(raw_pub).hexdigest()[:16]
    if envelope.get("key_id") != expected_key_id:
        raise ValueError("Signature key_id fingerprint mismatch")

    payload = {
        k: envelope[k]
        for k in [
            "schema_version",
            "run_id",
            "code_commit",
            "manifest_sha256",
            "scope_sha256",
            "last_event_hash",
            "signer_id",
            "key_id",
            "algorithm",
            "signed_at",
        ]
    }
    public_key = Ed25519PublicKey.from_public_bytes(raw_pub)
    try:
        public_key.verify(bytes.fromhex(envelope["signature_hex"]), canonical(payload))
    except (InvalidSignature, ValueError) as exc:
        raise ValueError("Invalid Ed25519 evidence signature") from exc

    return {
        **base,
        "signed": True,
        "signer_id": signer_id,
        "key_id": expected_key_id,
        "manifest_sha256": manifest_sha256,
    }
