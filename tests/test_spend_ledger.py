"""Spend admission tests use no provider, credentials, or model execution."""
from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from red_blue_field.spend_ledger import (
    MODEL, PILOT_ID, SpendBlocked, SpendConflict, SpendError,
    SpendLedger, SpendLimitExceeded,
)


@pytest.fixture
def ledger(tmp_path):
    return SpendLedger(tmp_path / "spend.sqlite3")


def reserve(ledger, n=0, run="episode-1", **kwargs):
    return ledger.reserve(run, f"job-{n}", f"request-{n}", 12_000, **kwargs)


def settle(ledger, row, **kwargs):
    return ledger.settle(row["id"], row["request_id"], 1_000, 100, **kwargs)


def test_exact_reservation_and_usage_reconciliation_survive_reopen(ledger):
    row = reserve(ledger)
    assert row["is_new"] is True
    assert row["reserved_nano_usd"] == 18_000_000
    assert row["reserved_usd"] == "0.018"
    assert ledger.snapshot()["reserved_nano_usd"] == 18_000_000
    ledger.mark_submitted(row["id"])
    finished = settle(ledger, row, response_id="response-1")
    assert finished["cost_nano_usd"] == 1_200_000
    assert finished["cost_usd"] == "0.0012"
    # Cached input is deliberately not discounted by this conservative ledger.
    reopened = SpendLedger(ledger.path)
    assert reopened.snapshot("episode-1")["episode"]["spent_usd"] == "0.0012"
    assert reopened.snapshot()["reserved_nano_usd"] == 0


def test_pilot_counts_normal_episodes_and_technical_smoke_together(ledger):
    for episode in range(4):
        for call in range(4):
            row = reserve(ledger, episode * 4 + call, run=f"episode-{episode}")
            ledger.mark_submitted(row["id"])
            ledger.settle(row["id"], row["request_id"], 12_000, 2_000)
    for call in range(4):
        row = reserve(ledger, 16 + call, run="technical-smoke", smoke=True)
        ledger.mark_submitted(row["id"])
        ledger.settle(row["id"], row["request_id"], 12_000, 2_000)
    state = ledger.snapshot()
    assert state["requests"] == 20
    assert state["episodes"] == 4
    assert state["spent_nano_usd"] == 360_000_000
    assert state["remaining_nano_usd"] == 640_000_000
    with pytest.raises(SpendLimitExceeded):
        reserve(ledger, 20, run="another-smoke", smoke=True)
    with pytest.raises(SpendLimitExceeded):
        ledger.register_episode("episode-five")
    assert SpendLedger(ledger.path).snapshot()["requests"] == 20


def test_concurrent_admission_cannot_reserve_the_same_episode_slots_twice(ledger):
    def attempt(n):
        try:
            return reserve(SpendLedger(ledger.path), n)
        except SpendLimitExceeded:
            return None
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(attempt, range(24)))
    admitted = [r for r in results if r]
    assert len(admitted) == 4
    assert len({r["id"] for r in admitted}) == 4
    assert ledger.snapshot()["reserved_nano_usd"] == 72_000_000


def test_identical_claim_is_idempotent_but_submission_permission_is_one_shot(ledger):
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims = list(pool.map(lambda _: reserve(SpendLedger(ledger.path)), range(16)))
    assert len({r["id"] for r in claims}) == 1
    assert sum(r["is_new"] for r in claims) == 1
    row = claims[0]
    ledger.mark_submitted(row["id"])
    with pytest.raises(SpendConflict):
        ledger.mark_submitted(row["id"])
    assert ledger.snapshot()["requests"] == 1


def test_two_workers_cannot_submit_concurrently_even_for_different_episodes(ledger):
    first, second = reserve(ledger, 0), reserve(ledger, 1, run="episode-2")
    ledger.mark_submitted(first["id"])
    with pytest.raises(SpendConflict):
        ledger.mark_submitted(second["id"])
    settle(ledger, first)
    ledger.mark_submitted(second["id"])
    assert ledger.snapshot()["requests"] == 2


def test_reusing_a_job_or_request_id_cannot_change_the_reserved_input(ledger):
    row = reserve(ledger)
    with pytest.raises(SpendConflict):
        ledger.reserve("episode-1", "job-0", "request-0", 11_999)
    with pytest.raises(SpendConflict):
        ledger.reserve("episode-1", "new-job", "request-0", 12_000)
    with pytest.raises(SpendConflict):
        ledger.reserve("another-episode", "job-0", "request-0", 12_000)
    assert reserve(ledger)["id"] == row["id"]
    assert ledger.snapshot()["requests"] == 1


def test_unknown_charge_holds_money_and_blocks_new_work_after_restart(ledger):
    row = reserve(ledger)
    ledger.mark_submitted(row["id"])
    ledger.mark_unknown(row["id"], "timeout")
    reopened = SpendLedger(ledger.path)
    state = reopened.snapshot()
    assert state["blocked"] is True
    assert state["reserved_nano_usd"] == 18_000_000
    with pytest.raises(SpendBlocked):
        reserve(reopened, 1)
    with pytest.raises(SpendBlocked):
        reopened.register_episode("another-episode")
    with pytest.raises(SpendConflict):
        settle(reopened, row)


@pytest.mark.parametrize("changed", [
    {"model": "different-model"}, {"service_tier": "flex"},
    {"request_id": "another-request"}, {"input_tokens": 12_001},
    {"output_tokens": 2_001},
])
def test_invalid_receipt_does_not_release_the_reservation(ledger, changed):
    row = reserve(ledger)
    ledger.mark_submitted(row["id"])
    receipt = dict(request_id=row["request_id"], input_tokens=1_000, output_tokens=100)
    receipt.update(changed)
    with pytest.raises(SpendConflict):
        ledger.settle(row["id"], **receipt)
    state = SpendLedger(ledger.path).snapshot()
    assert state["blocked"] is True
    assert state["spent_nano_usd"] == 0
    assert state["reserved_nano_usd"] == 18_000_000


@pytest.mark.parametrize("invalid", [-1, True, 1.5, None])
def test_malformed_usage_blocks_and_holds_the_reservation(ledger, invalid):
    row = reserve(ledger)
    ledger.mark_submitted(row["id"])
    with pytest.raises(SpendConflict):
        ledger.settle(row["id"], row["request_id"], invalid, 100)
    assert ledger.snapshot()["blocked"] is True
    assert ledger.snapshot()["reserved_nano_usd"] == 18_000_000


def test_receipt_replay_does_not_double_bill_and_changed_replay_blocks(ledger):
    row = reserve(ledger)
    ledger.mark_submitted(row["id"])
    assert settle(ledger, row)["is_new"] is True
    assert settle(ledger, row)["is_new"] is False
    assert ledger.snapshot()["spent_nano_usd"] == 1_200_000
    with pytest.raises(SpendConflict):
        ledger.settle(row["id"], row["request_id"], 1_000, 101)
    assert ledger.snapshot()["blocked"] is True
    assert ledger.snapshot()["spent_nano_usd"] == 1_200_000


def test_known_usage_with_incomplete_output_still_blocks_further_calls(ledger):
    row = reserve(ledger)
    ledger.mark_submitted(row["id"])
    settle(ledger, row)
    ledger.mark_unknown(row["id"], "incomplete_response")
    assert ledger.snapshot()["blocked"] is True
    assert ledger.snapshot()["spent_nano_usd"] == 1_200_000
    assert ledger.snapshot()["reserved_nano_usd"] == 0


def test_only_proven_unsubmitted_work_can_release_allowance(ledger):
    row = reserve(ledger)
    assert ledger.cancel_before_submit(row["id"])["status"] == "cancelled"
    assert ledger.snapshot()["requests"] == 0
    assert ledger.snapshot()["reserved_nano_usd"] == 0
    with pytest.raises(SpendConflict):
        ledger.mark_submitted(row["id"])
    row = reserve(ledger, 1)
    ledger.mark_submitted(row["id"])
    assert ledger.cancel_before_submit(row["id"])["status"] == "unknown"
    assert ledger.snapshot()["blocked"] is True
    assert ledger.snapshot()["reserved_nano_usd"] == 18_000_000


def test_startup_recovery_keeps_unknown_submissions_and_never_retries(ledger):
    unsubmitted, submitted = reserve(ledger, 0), reserve(ledger, 1)
    ledger.mark_submitted(submitted["id"])
    reopened = SpendLedger(ledger.path)
    assert reopened.recover_pending() == {"cancelled_unsubmitted": 1, "unknown_submitted": 1}
    assert reopened.snapshot()["requests"] == 1
    assert reopened.snapshot()["reserved_nano_usd"] == 18_000_000
    assert reopened.snapshot()["blocked"] is True
    assert reopened.recover_pending() == {"cancelled_unsubmitted": 0, "unknown_submitted": 0}
    assert reopened.cancel_before_submit(unsubmitted["id"])["status"] == "cancelled"


def test_existing_episode_classification_and_pilot_cannot_reset(ledger):
    ledger.register_episode("episode-1")
    with pytest.raises(SpendConflict):
        ledger.register_episode("episode-1", smoke=True)
    with pytest.raises(SpendConflict):
        SpendLedger(ledger.path, pilot_id="fresh-budget")
    with sqlite3.connect(ledger.path) as db:
        db.execute("UPDATE s02_spend_pilots SET policy='different' WHERE id=?", (PILOT_ID,))
    with pytest.raises(SpendConflict):
        SpendLedger(ledger.path)


@pytest.mark.parametrize("count", [-1, 12_001, 1.0, True])
def test_invalid_input_bounds_are_denied_before_admission(ledger, count):
    with pytest.raises(SpendError):
        ledger.reserve("episode-1", "job-1", "request-1", count)
    assert ledger.snapshot()["requests"] == 0


def test_out_of_policy_request_is_denied_without_call_or_account_block(ledger):
    with pytest.raises(SpendConflict):
        reserve(ledger, model="another-model")
    with pytest.raises(SpendConflict):
        reserve(ledger, service_tier="flex")
    with pytest.raises(SpendError):
        reserve(ledger, max_output_tokens=2_001)
    assert ledger.snapshot()["requests"] == 0
    assert ledger.snapshot()["blocked"] is False


def test_provider_error_text_is_not_persisted(ledger):
    row = reserve(ledger)
    ledger.mark_submitted(row["id"])
    ledger.mark_unknown(row["id"], "synthetic-secret-must-not-be-logged")
    assert ledger.snapshot()["reason"] == "provider_result_uncertain"
    assert b"synthetic-secret-must-not-be-logged" not in ledger.path.read_bytes()
