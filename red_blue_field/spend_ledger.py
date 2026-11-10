"""Persistent admission control for the approved, bounded S02 pilot.

Amounts are integer nano-USD estimates at the frozen rate card, not receipts or
account-wide billing guarantees. No provider request belongs in this module.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path


MODEL = "gpt-5.4-mini-2026-03-17"
PILOT_ID = "s02-pilot"
MAX_INPUT_TOKENS = 12_000
MAX_OUTPUT_TOKENS = 2_000
MAX_EPISODES = 4
MAX_EPISODE_REQUESTS = 4
MAX_PILOT_REQUESTS = 20
MAX_SMOKE_REQUESTS = 4
PILOT_CAP_NANO_USD = 1_000_000_000
EPISODE_CAP_NANO_USD = 200_000_000
INPUT_NANO_USD_PER_TOKEN = 750
OUTPUT_NANO_USD_PER_TOKEN = 4_500

_POLICY = json.dumps({
    "model": MODEL, "tier": "default", "input": MAX_INPUT_TOKENS,
    "output": MAX_OUTPUT_TOKENS, "episodes": MAX_EPISODES,
    "episode_requests": MAX_EPISODE_REQUESTS, "pilot_requests": MAX_PILOT_REQUESTS,
    "smoke_requests": MAX_SMOKE_REQUESTS, "pilot_cap": PILOT_CAP_NANO_USD,
    "episode_cap": EPISODE_CAP_NANO_USD, "input_rate": INPUT_NANO_USD_PER_TOKEN,
    "output_rate": OUTPUT_NANO_USD_PER_TOKEN,
}, sort_keys=True, separators=(",", ":"))


class SpendError(ValueError):
    pass


class SpendLimitExceeded(SpendError):
    pass


class SpendConflict(SpendError):
    pass


class SpendBlocked(SpendError):
    pass


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 256 or any(ord(c) < 32 for c in value):
        raise SpendError("Invalid ledger identifier")
    return value


def _tokens(value: int, maximum: int | None = None) -> int:
    if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
        raise SpendError("Token count is outside the approved bounds")
    return value


def _usd(value: int) -> str:
    return format(Decimal(value) / Decimal(1_000_000_000), "f")


class SpendLedger:
    """One immutable pilot policy, shared safely by processes using one DB path.

    ``reserve`` is idempotent, but ``mark_submitted`` is a one-shot capability:
    call it immediately before returning permission to contact the provider.
    Ordinary receipts cannot unblock an unknown charge. Reconciliation requires
    a separate owner decision rather than an automatic retry/release.
    """

    def __init__(self, path: Path | str, pilot_id: str = PILOT_ID):
        if pilot_id != PILOT_ID:
            raise SpendConflict("The approved pilot identifier cannot be changed")
        self.path, self.pilot_id = Path(path), pilot_id
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS s02_spend_pilots (
                    id TEXT PRIMARY KEY, policy TEXT NOT NULL,
                    blocked INTEGER NOT NULL DEFAULT 0, reason TEXT
                );
                CREATE TABLE IF NOT EXISTS s02_spend_episodes (
                    pilot_id TEXT NOT NULL, run_id TEXT NOT NULL,
                    smoke INTEGER NOT NULL,
                    PRIMARY KEY(pilot_id, run_id)
                );
                CREATE TABLE IF NOT EXISTS s02_spend_requests (
                    id TEXT PRIMARY KEY, pilot_id TEXT NOT NULL, run_id TEXT NOT NULL,
                    job_id TEXT NOT NULL, request_id TEXT NOT NULL,
                    model TEXT NOT NULL, tier TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL, output_limit INTEGER NOT NULL,
                    reserved_nano_usd INTEGER NOT NULL, cost_nano_usd INTEGER,
                    status TEXT NOT NULL, receipt_hash TEXT, reason TEXT,
                    UNIQUE(pilot_id, job_id), UNIQUE(pilot_id, request_id)
                );
            """)
        with self._transaction() as db:
            db.execute("INSERT OR IGNORE INTO s02_spend_pilots(id,policy) VALUES (?,?)", (pilot_id, _POLICY))
            if db.execute("SELECT policy FROM s02_spend_pilots WHERE id=?", (pilot_id,)).fetchone()[0] != _POLICY:
                raise SpendConflict("Stored pilot policy differs; owner review is required")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def _transaction(self):
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                yield db
                db.execute("COMMIT")
            except BaseException:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise

    def _active(self, db):
        row = db.execute("SELECT blocked FROM s02_spend_pilots WHERE id=?", (self.pilot_id,)).fetchone()
        if row[0]:
            raise SpendBlocked("Pilot blocked pending owner reconciliation")

    def _episode(self, db, run_id: str, smoke: bool):
        row = db.execute("SELECT smoke FROM s02_spend_episodes WHERE pilot_id=? AND run_id=?",
                         (self.pilot_id, run_id)).fetchone()
        if row:
            if row[0] != int(smoke):
                raise SpendConflict("Episode classification cannot be changed")
            return
        count = db.execute("SELECT COUNT(*) FROM s02_spend_episodes WHERE pilot_id=? AND smoke=?",
                           (self.pilot_id, int(smoke))).fetchone()[0]
        if count >= (MAX_SMOKE_REQUESTS if smoke else MAX_EPISODES):
            raise SpendLimitExceeded("Approved episode slots exhausted")
        db.execute("INSERT INTO s02_spend_episodes VALUES (?,?,?)", (self.pilot_id, run_id, int(smoke)))

    def register_episode(self, run_id: str, smoke: bool = False) -> dict:
        _identifier(run_id)
        if type(smoke) is not bool:
            raise SpendError("Smoke classification must be boolean")
        with self._transaction() as db:
            self._active(db)
            self._episode(db, run_id, smoke)
        return self.snapshot(run_id)

    def _totals(self, db, run_id: str | None = None) -> dict:
        clause, params = "pilot_id=?", [self.pilot_id]
        if run_id is not None:
            clause += " AND run_id=?"
            params.append(run_id)
        row = db.execute(f"""SELECT
            COUNT(CASE WHEN status != 'cancelled' THEN 1 END) AS requests,
            COALESCE(SUM(CASE WHEN status='settled' THEN cost_nano_usd ELSE 0 END),0) AS spent,
            COALESCE(SUM(CASE WHEN status IN ('reserved','submitted','unknown') THEN reserved_nano_usd ELSE 0 END),0) AS pending
            FROM s02_spend_requests WHERE {clause}""", params).fetchone()
        return dict(requests=row["requests"], spent_nano_usd=row["spent"], reserved_nano_usd=row["pending"])

    @staticmethod
    def _record(row, *, is_new: bool = False) -> dict:
        result = dict(row)
        result["is_new"] = is_new
        result["reservation_id"] = result["id"]
        result["reserved_usd"] = _usd(result["reserved_nano_usd"])
        result["cost_usd"] = None if result["cost_nano_usd"] is None else _usd(result["cost_nano_usd"])
        return result

    def _request(self, db, reservation_id: str):
        row = db.execute("SELECT * FROM s02_spend_requests WHERE pilot_id=? AND id=?",
                         (self.pilot_id, _identifier(reservation_id))).fetchone()
        if row is None:
            raise SpendConflict("Unknown spend reservation")
        return row

    def reserve(self, run_id: str, job_id: str, request_id: str, input_tokens: int,
                max_output_tokens: int = MAX_OUTPUT_TOKENS, model: str = MODEL,
                service_tier: str = "default", smoke: bool = False) -> dict:
        for value in (run_id, job_id, request_id):
            _identifier(value)
        _tokens(input_tokens, MAX_INPUT_TOKENS)
        _tokens(max_output_tokens, MAX_OUTPUT_TOKENS)
        if max_output_tokens == 0 or type(smoke) is not bool:
            raise SpendError("Invalid request bounds")
        if model != MODEL or service_tier != "default":
            raise SpendConflict("Request does not use the approved model and processing tier")
        worst = input_tokens * INPUT_NANO_USD_PER_TOKEN + max_output_tokens * OUTPUT_NANO_USD_PER_TOKEN
        with self._transaction() as db:
            prior = db.execute("SELECT * FROM s02_spend_requests WHERE pilot_id=? AND (job_id=? OR request_id=?)",
                               (self.pilot_id, job_id, request_id)).fetchone()
            if prior:
                expected = (run_id, job_id, request_id, model, service_tier, input_tokens, max_output_tokens)
                actual = tuple(prior[k] for k in ("run_id", "job_id", "request_id", "model", "tier", "input_tokens", "output_limit"))
                if actual != expected:
                    raise SpendConflict("Idempotency identifier reused for another request")
                self._episode(db, run_id, smoke)
                return self._record(prior)
            self._active(db)
            self._episode(db, run_id, smoke)
            pilot, episode = self._totals(db), self._totals(db, run_id)
            if pilot["requests"] >= MAX_PILOT_REQUESTS or episode["requests"] >= MAX_EPISODE_REQUESTS:
                raise SpendLimitExceeded("Approved request count exhausted")
            if smoke:
                count = db.execute("""SELECT COUNT(*) FROM s02_spend_requests r
                    JOIN s02_spend_episodes e ON e.pilot_id=r.pilot_id AND e.run_id=r.run_id
                    WHERE r.pilot_id=? AND e.smoke=1 AND r.status!='cancelled'""", (self.pilot_id,)).fetchone()[0]
                if count >= MAX_SMOKE_REQUESTS:
                    raise SpendLimitExceeded("Technical smoke allowance exhausted")
            if (pilot["spent_nano_usd"] + pilot["reserved_nano_usd"] + worst > PILOT_CAP_NANO_USD
                    or episode["spent_nano_usd"] + episode["reserved_nano_usd"] + worst > EPISODE_CAP_NANO_USD):
                raise SpendLimitExceeded("Insufficient approved monetary allowance")
            reservation_id = uuid.uuid4().hex
            db.execute("""INSERT INTO s02_spend_requests
                (id,pilot_id,run_id,job_id,request_id,model,tier,input_tokens,output_limit,reserved_nano_usd,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,'reserved')""",
                       (reservation_id, self.pilot_id, run_id, job_id, request_id, model, service_tier,
                        input_tokens, max_output_tokens, worst))
            return self._record(self._request(db, reservation_id), is_new=True)

    def mark_submitted(self, reservation_id: str) -> dict:
        with self._transaction() as db:
            self._active(db)
            row = self._request(db, reservation_id)
            if row["status"] != "reserved":
                raise SpendConflict("Provider submission permission was already consumed or closed")
            other = db.execute("SELECT 1 FROM s02_spend_requests WHERE pilot_id=? AND status='submitted' AND id!=?",
                               (self.pilot_id, reservation_id)).fetchone()
            if other:
                raise SpendConflict("Another provider request is awaiting reconciliation")
            db.execute("UPDATE s02_spend_requests SET status='submitted' WHERE id=?", (reservation_id,))
            return self._record(self._request(db, reservation_id), is_new=True)

    def _unknown(self, db, row, reason: str):
        if row["status"] != "settled":
            db.execute("UPDATE s02_spend_requests SET status='unknown',reason=? WHERE id=?", (reason, row["id"]))
        db.execute("UPDATE s02_spend_pilots SET blocked=1,reason=? WHERE id=?", (reason, self.pilot_id))

    def mark_unknown(self, reservation_id: str, reason: str = "provider_result_uncertain") -> dict:
        # Never retain caller/provider error text, even if it resembles an ID.
        reasons = {"provider_result_uncertain", "provider_error", "worker_error", "worker_failed",
                   "invalid_result", "malformed_output", "incomplete_response", "model_mismatch",
                   "tier_mismatch", "usage_missing", "timeout", "stopped_after_submit",
                   "restart_after_submit", "cancellation_after_submit"}
        category = reason if isinstance(reason, str) and reason in reasons else "provider_result_uncertain"
        with self._transaction() as db:
            row = self._request(db, reservation_id)
            if row["status"] == "cancelled":
                raise SpendConflict("A proven unsubmitted cancellation cannot become a provider receipt")
            self._unknown(db, row, category)
            return self._record(self._request(db, reservation_id))

    def settle(self, reservation_id: str, request_id: str, input_tokens: int, output_tokens: int,
               model: str = MODEL, service_tier: str = "default", response_id: str | None = None) -> dict:
        invalid = False
        try:
            _identifier(request_id)
            _tokens(input_tokens, MAX_INPUT_TOKENS)
            _tokens(output_tokens, MAX_OUTPUT_TOKENS)
            _identifier(model)
            _identifier(service_tier)
            if response_id is not None:
                _identifier(response_id)
        except SpendError:
            invalid = True
        fingerprint = None
        if not invalid:
            receipt = dict(request_id=request_id, input_tokens=input_tokens, output_tokens=output_tokens,
                           model=model, service_tier=service_tier, response_id=response_id)
            fingerprint = hashlib.sha256(json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        failure = None
        with self._transaction() as db:
            row = self._request(db, reservation_id)
            if invalid:
                self._unknown(db, row, "malformed_receipt")
                failure = SpendConflict("Usage receipt is invalid; pilot blocked")
            elif row["status"] == "settled" and row["receipt_hash"] == fingerprint:
                return self._record(row)
            elif row["status"] == "settled":
                self._unknown(db, row, "divergent_receipt")
                failure = SpendConflict("Conflicting settlement receipt; pilot blocked")
            elif row["status"] != "submitted":
                raise SpendConflict("Only a submitted request can settle; unknown charges require owner reconciliation")
            elif (request_id != row["request_id"] or model != row["model"] or service_tier != row["tier"]
                  or input_tokens > row["input_tokens"] or output_tokens > row["output_limit"]):
                self._unknown(db, row, "receipt_outside_reservation")
                failure = SpendConflict("Receipt differs from reserved request; pilot blocked")
            else:
                cost = input_tokens * INPUT_NANO_USD_PER_TOKEN + output_tokens * OUTPUT_NANO_USD_PER_TOKEN
                db.execute("""UPDATE s02_spend_requests SET status='settled',cost_nano_usd=?,receipt_hash=?
                    WHERE id=?""", (cost, fingerprint, reservation_id))
                result = self._record(self._request(db, reservation_id), is_new=True)
        if failure:
            raise failure
        return result

    def cancel_before_submit(self, reservation_id: str, reason: str = "cancelled_before_submit") -> dict:
        with self._transaction() as db:
            row = self._request(db, reservation_id)
            if row["status"] == "cancelled":
                return self._record(row)
            if row["status"] != "reserved":
                self._unknown(db, row, "cancellation_after_submit")
                result = self._record(self._request(db, reservation_id))
            else:
                db.execute("UPDATE s02_spend_requests SET status='cancelled',reason=? WHERE id=?",
                           ("cancelled_before_submit", reservation_id))
                result = self._record(self._request(db, reservation_id))
        return result

    def recover_pending(self) -> dict:
        """Call once during coordinator startup, before accepting target work."""
        with self._transaction() as db:
            pending = db.execute("SELECT * FROM s02_spend_requests WHERE pilot_id=? AND status IN ('reserved','submitted')",
                                 (self.pilot_id,)).fetchall()
            cancelled = unknown = 0
            for row in pending:
                if row["status"] == "reserved":
                    db.execute("UPDATE s02_spend_requests SET status='cancelled',reason='startup_before_submit' WHERE id=?", (row["id"],))
                    cancelled += 1
                else:
                    self._unknown(db, row, "restart_after_submit")
                    unknown += 1
        return {"cancelled_unsubmitted": cancelled, "unknown_submitted": unknown}

    def snapshot(self, run_id: str | None = None) -> dict:
        if run_id is not None:
            _identifier(run_id)
        with self._connect() as db:
            pilot = db.execute("SELECT blocked,reason FROM s02_spend_pilots WHERE id=?", (self.pilot_id,)).fetchone()
            totals = self._totals(db)
            episodes = db.execute("SELECT smoke,COUNT(*) AS count FROM s02_spend_episodes WHERE pilot_id=? GROUP BY smoke",
                                  (self.pilot_id,)).fetchall()
            result = {"pilot_id": self.pilot_id, "model": MODEL, "service_tier": "default",
                      "blocked": bool(pilot["blocked"]), "reason": pilot["reason"], **totals,
                      "spent_usd": _usd(totals["spent_nano_usd"]),
                      "reserved_usd": _usd(totals["reserved_nano_usd"]),
                      "cap_nano_usd": PILOT_CAP_NANO_USD,
                      "remaining_nano_usd": PILOT_CAP_NANO_USD - totals["spent_nano_usd"] - totals["reserved_nano_usd"],
                      "episodes": sum(r["count"] for r in episodes if not r["smoke"]),
                      "smoke_episodes": sum(r["count"] for r in episodes if r["smoke"]),
                      "max_requests": MAX_PILOT_REQUESTS, "max_episodes": MAX_EPISODES}
            if run_id is not None:
                episode = self._totals(db, run_id)
                result["episode"] = {"run_id": run_id, **episode, "cap_nano_usd": EPISODE_CAP_NANO_USD,
                                     "spent_usd": _usd(episode["spent_nano_usd"]),
                                     "reserved_usd": _usd(episode["reserved_nano_usd"]),
                                     "max_requests": MAX_EPISODE_REQUESTS}
            return result
