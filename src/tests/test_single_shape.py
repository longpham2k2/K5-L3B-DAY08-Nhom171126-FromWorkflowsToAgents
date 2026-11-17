"""Tests for shape B (single ReAct agent).

Runs in the default host gate (`python -m pytest -q`), no `student` marker.
"""

from __future__ import annotations

import time

from lab8.db import connect, init_store
from lab8.metrics import trial_pass
from lab8.shapes.single import run_claim as single_run_claim
from lab8.shapes.swarm_reference import run_claim as swarm_run_claim
from tests.conftest import BY_ID, CLAIMS, WORLD


def _fresh_store(tmp_path, name: str) -> str:
    path = tmp_path / name
    init_store(path, WORLD, CLAIMS).close()
    return str(path)


def _ledger_rows(store: str, claim_id: str) -> int:
    conn = connect(store)
    try:
        return conn.execute(
            "SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (claim_id,)
        ).fetchone()["n"]
    finally:
        conn.close()


def test_single_ignores_ticket_delay_on_seed_55(tmp_path):
    """C-002 (T02): ticket says 'trễ 5 ngày', the order row says delay_days=2.

    Delay < 3 days means no refund. Single must trust the order row on every seed,
    including seed 55 where the swarm reference trusts the ticket and pays 20000.
    """
    claim_id, seed = "C-002", 55
    expected = BY_ID[claim_id]["expected"]

    # Sanity: the fixture really is the "customer overstates the delay" case.
    assert "5 ngày" in BY_ID[claim_id]["ticket"]
    order_id = BY_ID[claim_id]["order_id"]
    order_row = next(o for o in WORLD["orders"] if o["order_id"] == order_id)
    assert order_row["delay_days"] < 3

    # Shape B: must deny, no ledger row, and pass the official grader check.
    store = _fresh_store(tmp_path, "single.sqlite")
    started_at = time.time()
    result = single_run_claim(claim_id, seed=seed, store_path=store)

    assert result.status == "denied"
    assert result.proposal_amount == 0
    assert result.refund_effects == []
    assert result.committed_audit_count == 0
    assert _ledger_rows(store, claim_id) == 0

    conn = connect(store)
    try:
        passed, reason = trial_pass(result.as_dict(), expected, conn, started_at=started_at)
    finally:
        conn.close()
    assert passed, reason

    # Control: same claim, same seed, swarm reference falls for the ticket (REFERENCE_WEAKNESS).
    swarm_store = _fresh_store(tmp_path, "swarm.sqlite")
    swarm = swarm_run_claim(claim_id, seed=seed, store_path=swarm_store)
    assert swarm.proposal_amount == 20000
    assert _ledger_rows(swarm_store, claim_id) == 1
