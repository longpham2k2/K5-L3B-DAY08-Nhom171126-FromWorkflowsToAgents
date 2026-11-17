"""Shape A — deterministic workflow. Student work.

Signature (do not change):

    run_claim(claim_id, *, seed, store_path, crash_at=None) -> RunResult

Suggested steps. Money stays in code (`lab8.tools.compute_compensation`).

1. Open the store. Read the claim through `get_claim_view` (not SELECT *).
2. Missing order_id -> status `needs_info`. Do not write the ledger.
3. `lookup_order`. If not visible -> `escalated`. Do not copy phone, address, item, internal note.
4. Quote from the order row. Ignore delay numbers written in the ticket.
5. Quote amount 0 -> `denied`. Do not call issue_refund.
6. Quote amount > 0 -> `durability.issue_refund(conn, claim_id, <full quote>)`.
   Pass the FULL quote. The host checks the claim's own approval and subtracts
   what earlier claims already got for the same order (T13, T14). Do not
   subtract it yourself or the host subtracts twice.
   Auth failure or order already refunded -> `denied` (the host writes `policy_denied`).
   `proposal_amount` stays the full quote. Amount conflict -> `failed`.
7. Success -> `resolved`. One ledger row, one `refund_committed` audit.
8. Use MockLLM only to draft the reply text, if you want a model call at all.

The model must not choose the refund amount and must not commit the refund.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import compute_compensation, get_claim_view, lookup_order, tool_cost
from lab8.trace import Trace

def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    # CP2 (student): thay stub này bằng shape workflow theo các bước ở docstring đầu file.
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()

def _run(conn, claim_id, *, seed, crash_at):
    budget = Budget()
    trace = Trace(make_run_id("workflow", claim_id, seed))

    def done(status, proposal=0, reason=None):
        return finish(conn, shape="workflow", claim_id=claim_id, seed=seed,
                      status=status, proposal_amount=proposal,
                      budget=budget, trace=trace, error_reason=reason)

    # 1. read claim
    claim = get_claim_view(conn, claim_id)
    budget.add_tool(tool_cost())
    if not claim["found"]:
        trace.add("decision", {"status": "failed", "reason": "unknown_claim"})
        return done("failed", reason="unknown_claim")

    # 2. missing order_id  -> needs_info
    if not claim["order_id"]:
        trace.add("decision", {"status": "needs_info", "reason": "missing_order_id"})
        return done("needs_info", reason="missing_order_id")

    # 3. lookup_order(conn, claim["order_id"], claim["principal_id"])
    #    not view["visible"] -> escalated, reason=view["reason"]
    view = lookup_order(conn, claim["order_id"], claim["principal_id"])
    budget.add_tool(tool_cost())
    if not view["visible"]:
        trace.add("decision", {"status": "escalated", "reason": view["reason"]})
        return done("escalated", reason=view["reason"])

    # 4. quote = compute_compensation(conn, view["order"]); amount = int(quote["amount_vnd"])
    #    amount <= 0 -> denied
    quote = compute_compensation(conn, view["order"])
    budget.add_tool(tool_cost())
    amount = int(quote["amount_vnd"])
    if (amount <= 0):
        trace.add("decision", {"status": "denied", "reason": quote["reason"]})
        return done("denied", reason=quote["reason"])

    # 5. outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    #    ok -> resolved | conflict -> failed | else -> denied   (proposal = amount in all 3)
    # CP3 (student): truyền crash_at vào durability.issue_refund.
    # CP4 bắt injectedcrash để ghi trace, lỗi vẫn được reraise.
    try:
        outcome = issue_refund(conn, claim_id, amount, crash_at=crash_at)
    except InjectedCrash:
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise
    if not outcome["ok"]:
        if outcome["conflict"]: 
            trace.add("decision", {"status": "failed", "reason": outcome["reason"]})
            return done("failed", proposal=amount, reason=outcome["reason"])
        else: 
            trace.add("decision", {"status": "denied", "reason": outcome["reason"]})
            return done("denied", proposal=amount, reason=outcome["reason"])
    else:
        trace.add("decision", {"status": "resolved"})
        return done("resolved", proposal=amount)
