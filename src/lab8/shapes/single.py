"""Shape B — one ReAct agent. Student work.

Use `lab8.runtime.run_react` with max_steps=8. `decide` may pick a read tool.
It must not call `issue_refund`. After the loop, the host validates the quote
and is the only writer.

A decide() that trusts ticket text over the order row will fail hidden claims
where the customer overstates the delay or cites a superseded clause.

Per-order cap: an order may already have been refunded by an earlier claim.
The read tool `lookup_refund_history` shows how much. The host still enforces
the cap, so pass the full quote to `durability.issue_refund`, not a net amount.

Caps: stop at 8 steps. Count model calls in the Budget so cost stays comparable.

Trace contract v1 (docs/contracts.md): return a trace_path to a JSON file written in this run,
{"run_id": <same run_id>, "events": [...]}, on every return path including early
ones. `lab8.trace.Trace` does this; your own tracer is fine if it matches.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from lab8.db import connect
from lab8.durability import InjectedCrash, issue_refund
from lab8.mock_llm import complete
from lab8.runtime import run_react
from lab8.schemas import Budget, RunResult, make_run_id
from lab8.shapes.common import finish
from lab8.tools import get_claim_view, tool_cost
from lab8.trace import Trace

SHAPE = "single"
MAX_STEPS = 8


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    # Mở DB một lần, luôn đóng trong finally (Windows sẽ khóa file .sqlite nếu quên).
    conn = connect(store_path)
    try:
        return _run(conn, claim_id, seed=seed, crash_at=crash_at)
    finally:
        conn.close()


def _run(conn: sqlite3.Connection, claim_id: str, *, seed: int, crash_at: str | None) -> RunResult:
    budget = Budget()
    run_id = make_run_id(SHAPE, claim_id, seed)
    trace = Trace(run_id)

    # Hàm phụ: mọi nhánh return đều đi qua finish() để có trace + đọc ledger thật.
    def done(status: str, proposal_amount: int, error_reason: str | None) -> RunResult:
        trace.add("decision", {"status": status, "proposal_amount": int(proposal_amount), "reason": error_reason})
        return finish(
            conn,
            shape=SHAPE,
            claim_id=claim_id,
            seed=seed,
            status=status,
            proposal_amount=proposal_amount,
            budget=budget,
            trace=trace,
            error_reason=error_reason,
        )

    # ── TRƯỚC vòng lặp ────────────────────────────────────────────────
    # 1. Đọc claim qua read tool (chỉ trả claim_id, principal_id, order_id, ticket;
    #    KHÔNG có parent_secret / raw_headers).
    claim = get_claim_view(conn, claim_id)
    budget.add_tool(tool_cost())

    # Trace chỉ ghi field an toàn. Không ghi ticket thô: đó là dữ liệu người dùng,
    # có thể chứa injection hoặc thông tin cá nhân.
    trace.add(
        "claim",
        {"claim_id": claim_id, "found": bool(claim.get("found")), "has_order_id": bool(claim.get("order_id"))},
    )

    # 2. Claim không tồn tại → failed, amount 0, không ghi ledger.
    if not claim.get("found"):
        return done("failed", 0, "unknown_claim")

    # 3. Thiếu order_id → needs_info. Không đoán mã đơn từ câu chữ trong ticket.
    if not claim.get("order_id"):
        return done("needs_info", 0, "missing_order_id")

    # ── GIỮA vòng lặp: run_react + decide ─────────────────────────────
    principal_id = claim["principal_id"]
    order_id = claim["order_id"]

    # run_react chỉ đưa cho decide kết quả của tool VỪA gọi (last_tool/last_result),
    # không giữ lịch sử. Nên decide tự nhớ những gì đã đọc trong `memory`.
    memory: dict[str, Any] = {"step": 0, "order": None, "history": None, "policy_count": None}

    def decide(seen: dict[str, Any]) -> dict[str, Any]:
        memory["step"] += 1
        last_tool = seen.get("last_tool")
        last_result = seen.get("last_result") or {}

        # Mỗi lần "suy nghĩ" là một lời gọi model → đếm vào Budget qua MockLLM.
        # Prompt chỉ chứa trạng thái nội bộ, không chứa ticket hay dữ liệu cá nhân.
        complete(budget, seed=seed, purpose="react", prompt=f"step={memory['step']};last={last_tool}")

        # 1) Ghi nhớ kết quả của tool vừa chạy.
        if last_tool == "lookup_order":
            trace.add("react_step", {"step": memory["step"], "tool": last_tool, "visible": bool(last_result.get("visible")), "reason": last_result.get("reason")})
            if not last_result.get("visible"):
                # Không thấy đơn hoặc không sở hữu đơn → dừng, không đọc thêm gì.
                return {"final": {"kind": "escalated", "reason": last_result.get("reason")}}
            # order đã qua allowlist ORDER_FIELDS của tools.lookup_order (không SĐT, địa chỉ).
            memory["order"] = dict(last_result["order"])
        elif last_tool == "lookup_refund_history":
            memory["history"] = {
                "refund_count": int(last_result.get("refund_count", 0)),
                "refunded_vnd": int(last_result.get("refunded_vnd", 0)),
            }
            trace.add("react_step", {"step": memory["step"], "tool": last_tool, **memory["history"]})
        elif last_tool == "lookup_policy":
            policies = last_result.get("policies") or []
            memory["policy_count"] = len(policies)
            trace.add("react_step", {"step": memory["step"], "tool": last_tool, "as_of": last_result.get("as_of"), "policy_ids": [p.get("policy_id") for p in policies]})
        elif last_tool == "compute_compensation":
            # Tiền do code (compensation.quote) tính trên order row từ DB, không do model.
            quote = {
                "amount_vnd": int(last_result.get("amount_vnd", 0)),
                "reason": last_result.get("reason"),
                "clause_ids": list(last_result.get("clause_ids") or []),
            }
            trace.add("react_step", {"step": memory["step"], "tool": last_tool, **quote})
            return {"final": {"kind": "quote", **quote}}

        # 2) Chọn tool tiếp theo dựa trên những gì còn thiếu.
        if memory["order"] is None:
            return {"tool": "lookup_order", "args": {"order_id": order_id, "principal_id": principal_id}}
        if memory["history"] is None:
            return {"tool": "lookup_refund_history", "args": {"order_id": order_id, "principal_id": principal_id}}
        if memory["policy_count"] is None:
            return {"tool": "lookup_policy", "args": {}}
        # Dùng delay_days của order row, KHÔNG dùng số ngày khách ghi trong ticket.
        return {"tool": "compute_compensation", "args": {"order": memory["order"]}}

    try:
        loop = run_react(
            conn,
            budget,
            observation={"claim": {"claim_id": claim_id, "order_id": order_id}},
            decide=decide,
            max_steps=MAX_STEPS,
        )
    except Exception as exc:  # ToolRejected hoặc lỗi bất ngờ: run_claim không được ném exception.
        trace.add("react_error", {"error": type(exc).__name__})
        return done("failed", 0, f"react_error:{type(exc).__name__}")

    final = loop["final"]
    trace.add("react_stop", {"stopped": loop["stopped"], "steps": memory["step"]})

    if loop["stopped"] == "step_cap":
        return done("failed", 0, "step_cap")

    # ── SAU vòng lặp: final → status / issue_refund → finish ──────────
    # 1. Không thấy đơn hoặc principal không sở hữu đơn → escalated, không ghi gì.
    if final.get("kind") == "escalated":
        complete(budget, seed=seed, purpose="draft", prompt="escalated")
        return done("escalated", 0, final.get("reason"))

    if final.get("kind") != "quote":
        return done("failed", 0, "no_quote")

    quote = int(final["amount_vnd"])

    # 2. Quote = 0 (trễ < 3 ngày, đơn hủy, phí 0, policy cũ...) → denied, KHÔNG gọi issue_refund.
    if quote <= 0:
        complete(budget, seed=seed, purpose="draft", prompt="denied")
        return done("denied", 0, final.get("reason"))

    # 3. Quote > 0 → luôn đưa cho host. Truyền QUOTE ĐẦY ĐỦ: host tự kiểm approval,
    #    tự cap theo approved/paid và tự trừ phần đơn đã được hoàn bởi claim khác.
    #    Nếu host từ chối, chính host ghi audit policy_denied (shape tự từ chối thì không có audit).
    trace.add("issue_refund", {"proposed_vnd": quote})
    try:
        outcome = issue_refund(conn, claim_id, quote, crash_at=crash_at)  # CP3: truyền crash_at
    except InjectedCrash:
        # CP3: KHÔNG nuốt crash. Chỉ flush trace rồi ném tiếp để test thấy crash thật.
        trace.add("crash", {"at": crash_at})
        trace.write()
        raise

    trace.add(
        "host_outcome",
        {
            "ok": bool(outcome["ok"]),
            "reason": outcome["reason"],
            "conflict": bool(outcome["conflict"]),
            "committed_vnd": int(outcome["effect"]["amount_vnd"]) if outcome.get("effect") else 0,
        },
    )
    complete(budget, seed=seed, purpose="draft", prompt=f"proposal={quote}")

    if not outcome["ok"]:
        # conflict: gọi lại với số khác số đã commit → failed, giữ dòng cũ.
        # còn lại (approval hỏng, approval của claim khác, đơn đã hoàn đủ) → denied.
        status = "failed" if outcome["conflict"] else "denied"
        return done(status, quote, outcome["reason"])

    # proposal_amount là quote đầy đủ, KHÔNG phải số host đã ghi (T14: 150000 vs ledger 120000).
    return done("resolved", quote, None)
