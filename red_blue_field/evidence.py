from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

from .config import resources


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def atomic_json(path: Path, body: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w") as handle:
        json.dump(body, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


class Contracts:
    def __init__(self):
        self.schemas = {}
        registry = Registry()
        for path in (resources() / "schemas").glob("*.json"):
            value = json.loads(path.read_text())
            Draft202012Validator.check_schema(value)
            value["$id"] = "https://red-blue-field.invalid/schemas/" + path.name
            registry = registry.with_resource(value["$id"], Resource.from_contents(value))
            self.schemas[path.name] = value
        self.registry = registry

    def validate(self, name: str, body: object) -> None:
        Draft202012Validator(self.schemas[name + ".schema.json"], registry=self.registry,
                             format_checker=FormatChecker()).validate(body)


class Collector:
    @classmethod
    def archived(cls, root: Path, contracts: Contracts):
        manifest = json.loads((root / 'manifest.json').read_text())
        value = cls.__new__(cls)
        value.root, value.run_id, value.record_kind = root, manifest['run_id'], manifest['record_kind']
        value.contracts, value.lock, value.failed = contracts, threading.RLock(), False
        value.events = [json.loads(line) for line in (root / 'events.jsonl').read_text().splitlines()]
        value.artifacts = {a['path']: a['kind'] for a in manifest['artifacts']}
        value.trace_id = value.events[0]['trace_id']
        value.root_span = value.events[0]['span_id']
        # Existing evidence must pass verification before any human annotation can reseal it.
        verify_export(root)
        return value

    def __init__(self, root: Path, run_id: str, record_kind: str, contracts: Contracts):
        self.root, self.run_id, self.record_kind = root, run_id, record_kind
        self.contracts = contracts
        self.lock = threading.RLock()
        self.failed = False
        self.trace_id = uuid.uuid4().hex
        self.root_span = uuid.uuid4().hex[:16]
        self.events: list[dict] = []
        self.root.mkdir(parents=True, exist_ok=False, mode=0o700)
        self.artifacts: dict[str, str] = {}

    def event(self, actor: str, event_type: str, payload: dict, refs: list[str] | None = None) -> dict:
        with self.lock:
            if self.failed:
                raise OSError("Collector unavailable; no further actions allowed")
            stamp = now()
            event = dict(schema_version="0.2.0", record_kind=self.record_kind,
                         run_id=self.run_id, episode_id=self.run_id + "-episode", event_id=uuid.uuid4().hex,
                         sequence=len(self.events), occurred_at=stamp, received_at=stamp,
                         trace_id=self.trace_id, span_id=uuid.uuid4().hex[:16], parent_span_id=self.root_span,
                         actor=actor, event_type=event_type, visibility=["audit"], payload=payload,
                         artifact_refs=refs or [], prev_event_hash=self.events[-1]["event_hash"] if self.events else None)
            if not self.events:
                event["span_id"], event["parent_span_id"] = self.root_span, None
            event["event_hash"] = digest(event)
            self.contracts.validate("event", event)
            try:
                with (self.root / "events.jsonl").open("ab") as handle:
                    handle.write(canonical(event) + b"\n")
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError:
                self.failed = True
                raise
            self.events.append(event)
            self.artifacts["events.jsonl"] = "events"
            return event

    def json(self, name: str, body: object, kind: str = "other") -> str:
        with self.lock:
            path = self.path(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                atomic_json(path, body)
            except OSError:
                self.failed = True
                raise
            self.artifacts[name] = kind
        return name

    def jsonl(self, name: str, bodies: list[dict], kind: str = "other") -> str:
        with self.lock:
            path = self.path(name)
            tmp = path.with_suffix(".tmp")
            try:
                with tmp.open('wb') as handle:
                    handle.write(b"".join(canonical(x) + b"\n" for x in bodies))
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp, path)
            except OSError:
                self.failed = True
                raise
            self.artifacts[name] = kind
        return name

    def path(self, name: str) -> Path:
        if not name or Path(name).is_absolute() or ".." in Path(name).parts:
            raise ValueError("Invalid artifact reference")
        path = self.root / name
        if path.resolve().is_relative_to(self.root.resolve()) and not path.is_symlink():
            return path
        raise ValueError("Artifact outside episode")

    def seal(self, manifest: dict) -> None:
        with self.lock:
            manifest["last_event_hash"] = self.events[-1]["event_hash"] if self.events else None
            manifest["artifacts"] = [dict(path=n, sha256=hashlib.sha256(self.path(n).read_bytes()).hexdigest(), kind=k)
                                     for n, k in sorted(self.artifacts.items()) if n != "manifest.json"]
            self.contracts.validate("manifest", manifest)
            try:
                atomic_json(self.root / "manifest.json", manifest)
            except OSError:
                self.failed = True
                raise


def verify_export(root: Path) -> dict:
    contracts = Contracts()
    manifest = json.loads((root / "manifest.json").read_text())
    contracts.validate("manifest", manifest)
    artifacts = {a["path"]: a for a in manifest["artifacts"]}
    if len(artifacts) != len(manifest['artifacts']) or manifest['scope_ref'] not in artifacts or 'events.jsonl' not in artifacts:
        raise ValueError('Manifest requires unique, sealed scope and event artifacts')
    for name, item in artifacts.items():
        path = root / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Unsafe artifact path")
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Artifact hash mismatch: " + name)
    scope = json.loads((root / manifest["scope_ref"]).read_text())
    contracts.validate("scope", scope)
    if hashlib.sha256((root / manifest["scope_ref"]).read_bytes()).hexdigest() != manifest["scope_sha256"]:
        raise ValueError("Scope hash mismatch")
    event_ids, spans, last = set(), set(), None
    events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    for i, event in enumerate(events):
        contracts.validate("event", event)
        body = {k: v for k, v in event.items() if k != "event_hash"}
        if event["sequence"] != i or event["prev_event_hash"] != last or digest(body) != event["event_hash"]:
            raise ValueError("Event chain mismatch")
        if event["run_id"] != manifest["run_id"] or event["record_kind"] != manifest["record_kind"]:
            raise ValueError("Event origin mismatch")
        if event['event_id'] in event_ids or event['span_id'] in spans or any(ref not in artifacts for ref in event['artifact_refs']):
            raise ValueError('Duplicate identity or unsealed event evidence')
        event_ids.add(event["event_id"])
        spans.add(event["span_id"])
        last = event["event_hash"]
    if last != manifest["last_event_hash"] or any(e["parent_span_id"] and e["parent_span_id"] not in spans for e in events):
        raise ValueError("Manifest seal or span linkage mismatch")
    for filename, schema in [("episodes.jsonl", "episode"), ("hypotheses.jsonl", "hypothesis"), ("findings.jsonl", "finding")]:
        path = root / filename
        if not path.exists():
            continue
        records = [json.loads(line) for line in path.read_text().splitlines()]
        ids = {x.get("hypothesis_id") for x in records}
        by_id = {x.get('hypothesis_id'): x for x in records}
        for item in records:
            contracts.validate(schema, item)
            if item["run_id"] != manifest["run_id"]:
                raise ValueError("Record origin mismatch")
            if schema == "episode" and (not set(item["evidence_event_ids"]) <= event_ids or item["study_context"] != manifest["study_context"]):
                raise ValueError("Verdict context or evidence mismatch")
            if schema == "hypothesis" and (not set(item["parent_ids"]) <= ids or item["hypothesis_id"] in item["parent_ids"]):
                raise ValueError("Hypothesis parent mismatch")
            if schema == 'hypothesis':
                if any(by_id[p]['depth'] + 1 != item['depth'] for p in item['parent_ids']) or (not item['parent_ids'] and item['depth'] != 0):
                    raise ValueError('Hypothesis depth or ancestry mismatch')
                if any(ref not in artifacts for ref in item['evidence_refs']) or item['proposed_test_ref'] not in artifacts:
                    raise ValueError('Unsealed hypothesis evidence')
            if schema == 'episode' and any(ref not in artifacts for ref in [item['state_before_ref'], item['state_after_ref'], *item['effect_assessment']['evidence_refs']]):
                raise ValueError('Unsealed verdict evidence')
            if schema == "finding" and item["finder_id"] == item["verifier_id"]:
                raise ValueError("Finder and verifier must differ")
    if 'coverage-ledger.json' in artifacts:
        contracts.validate('coverage-ledger', json.loads((root / 'coverage-ledger.json').read_text()))
    return {"valid": True, "events": len(events), "artifacts": len(artifacts), "run_id": manifest["run_id"]}
