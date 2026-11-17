"""Shape C — orchestrator plus read-only investigators. Student work.

1. Build a handoff with `lab8.handoff.make_handoff`. Allowed tools are read-only.
   Never put parent_secret, raw headers, or the full claim row into facts.
2. `lab8.runtime.run_readonly_investigators` runs those tools.
3. The orchestrator quotes from the investigator's order view and calls
   `durability.issue_refund`. Investigators have no write registry.
   Pass the full quote; the host subtracts earlier refunds on the same order.
   `lookup_refund_history` is a read-only tool you may hand to an investigator.
4. Trace the sanitized handoff, not the parent context.

An LLM summary of the parent context is not a sanitizer. Use the allowlist.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

from lab8.db import connect
from lab8.durability import issue_refund
from lab8.handoff import make_handoff
from lab8.runtime import run_readonly_investigators
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    budget = Budget()
    trace = Trace(make_run_id("orchestrator", claim_id, seed))
    conn = connect(store_path)
    try:
        budget.add_tool(tool_cost())
        claim = get_claim_view(conn, claim_id)
        proposal = 0
        if not claim["found"]:
            status, reason = "failed", "unknown_claim"
        elif not claim.get("order_id"):
            status, reason = "needs_info", "missing_order_id"
        else:
            handoff = make_handoff(
                request_id=trace.run_id,
                claim_id=claim_id,
                task="check_applicable_policy",
                facts={},
                allowed_tools=["lookup_order", "lookup_policy", "compute_compensation"],
            )
            trace.add("handoff", handoff)
            investigated = run_readonly_investigators(
                conn, budget, handoff, principal_id=claim["principal_id"]
            )
            order_view = investigated["tools"]["lookup_order"]
            trace.add("investigator", {"lookup_order": order_view})
            if not order_view["visible"]:
                status, reason = "escalated", order_view["reason"]
            else:
                quote = investigated["tools"]["compute_compensation"]
                proposal = int(quote["amount_vnd"])
                trace.add("quote", quote)
                if proposal <= 0:
                    status, reason = "denied", quote.get("reason")
                else:
                    outcome = issue_refund(conn, claim_id, proposal, crash_at=crash_at)
                    trace.add("refund", outcome)
                    if outcome["ok"]:
                        status, reason = "resolved", None
                    else:
                        status = "failed" if outcome["conflict"] else "denied"
                        reason = outcome["reason"]

        trace.add("decision", {"status": status, "reason": reason})
        return finish(
            conn,
            shape="orchestrator",
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal,
            budget=budget,
            trace=trace,
            error_reason=reason,
        )
    finally:
        conn.close()
