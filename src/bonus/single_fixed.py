"""Ablation R3 (research card): shape `single` with the ReAct model call turned off.

Same claim reads, same 5 read tools in the same order, same trace events, same
host write path and same draft call as `lab8.shapes.single`. The ONLY change:
`decide` does not call MockLLM at each step, so the tool order is fixed by code.

Run next to the four shapes:
    python -m lab8.benchmark --shapes workflow,single --extra-shape single_fixed=bonus.single_fixed:run_claim ...
"""

from __future__ import annotations

from lab8.db import connect
from lab8.schemas import RunResult
from lab8.shapes import single

SHAPE = "single_fixed"


def run_claim(
    claim_id: str,
    *,
    seed: int,
    store_path: str,
    crash_at: str | None = None,
) -> RunResult:
    conn = connect(store_path)
    try:
        return single._run(conn, claim_id, seed=seed, crash_at=crash_at, shape=SHAPE, react_model=False)
    finally:
        conn.close()
