"""Workflow survives a crash at every crash point: resume -> exactly one refund."""
from __future__ import annotations

import pytest

from lab8.db import connect, init_store
from lab8.durability import InjectedCrash
from lab8.shapes.workflow import run_claim
from tests.conftest import  BY_ID, CLAIMS, WORLD

CLAIM = "C-012"   # same claim as T12; it resolves with a refund


@pytest.mark.parametrize("crash_at", ["before_effect", "after_effect_before_checkpoint", "after_checkpoint"])   # all three points
def test_workflow_crash_then_resume_pays_once(tmp_path, crash_at):
    store = tmp_path / f"wf-crash-{crash_at}.sqlite"
    init_store(store, WORLD, CLAIMS).close()

    expected = BY_ID[CLAIM]["expected"]

    # 1. first run must crash
    with pytest.raises(InjectedCrash):
        run_claim(CLAIM, seed=11, store_path=str(store), crash_at=crash_at)

    # 2. resume (no crash_at)
    result = run_claim(CLAIM, seed=11, store_path=str(store))
    assert result.status == expected["status"]
    assert result.committed_audit_count == expected["audit_refund_committed"]
    assert result.refund_effects[0]["amount_vnd"] == expected["refund_vnd"]

    # 3. ledger
    conn = connect(store)
    try:
        n = conn.execute("SELECT COUNT(*) AS n FROM refund_ledger WHERE claim_id = ?", (CLAIM,)).fetchone()["n"]
    finally:
        conn.close()
    assert n == 1
