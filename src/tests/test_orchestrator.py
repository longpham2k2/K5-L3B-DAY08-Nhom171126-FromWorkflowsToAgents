import json
from pathlib import Path
from tempfile import TemporaryDirectory

from lab8.db import connect, init_store
from lab8.durability import committed_audit_count, get_refund
from lab8.shapes.orchestrator import run_claim
from tests.conftest import CLAIMS, WORLD


def test_orchestrator_denies_approval(monkeypatch):
    with TemporaryDirectory(prefix="orchestrator-no-approval-") as directory:
        store = Path(directory) / "session.sqlite"
        init_store(store, WORLD, CLAIMS).close()

        with monkeypatch.context() as session:
            session.chdir(directory)
            conn = connect(store)

            try:
                conn.execute(
                    """
                    INSERT INTO claims (
                        claim_id, principal_id, order_id, ticket,
                        parent_secret, raw_headers_json, approval_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        "C-NOAPPROVAL",
                        "P-100",
                        "O-107",
                        "no approval",
                        "CANARY_SECRET_PARENT_X",
                        "{}",
                        None,
                    ),
                )
                conn.commit()

                before = conn.execute(
                    "SELECT COUNT(*) FROM refund_ledger"
                ).fetchone()[0]

                result = run_claim(
                    "C-NOAPPROVAL",
                    seed=1234,
                    store_path=str(store),
                )

                # Kiểm tra denied approval
                assert result.status == "denied"
                assert result.error_reason == "missing_approval"
                assert result.proposal_amount == 35000
                assert result.refund_effects == []
                assert result.committed_audit_count == 0
                assert get_refund(conn, "C-NOAPPROVAL") is None
                assert committed_audit_count(conn, "C-NOAPPROVAL") == 0

                after = conn.execute(
                    "SELECT COUNT(*) FROM refund_ledger"
                ).fetchone()[0]
                # Kiểm tra tổng số dòng ledger không tăng
                assert after == before

                denials = conn.execute(
                    "SELECT details_json FROM audit_events "
                    "WHERE claim_id = ? AND event_type = 'policy_denied'",
                    ("C-NOAPPROVAL",),
                ).fetchall()

                # Kiểm tra ghi lý do từ chối là 'missing_approval'
                assert any(
                    json.loads(row[0])["reason"] == "missing_approval"
                    for row in denials
                )

                trace_path = Path(result.trace_path).resolve()
                expected_directory = (Path(directory) / "traces").resolve()

                assert trace_path.parent == expected_directory

                trace = json.loads(
                    trace_path.read_text(encoding="utf-8")
                )
                assert trace["run_id"] == result.run_id
            finally:
                conn.close()

    # Đảm bảo không thêm vào DB public 
    # File DB tạm thời đã được xóa
    assert not store.exists()

    # File trace tạm thời đã được xóa
    assert not trace_path.exists()