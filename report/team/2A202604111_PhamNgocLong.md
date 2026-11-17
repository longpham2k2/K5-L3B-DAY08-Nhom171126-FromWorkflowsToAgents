# Báo cáo cá nhân — 2A202604111_PhamNgocLong

## 1. Thông tin thành viên

- Họ tên: Phạm Ngọc Long
- MSSV: 2A202604111
- Email: 26ai.longpn@vinuni.edu.vn
- GitHub: longpham2k2

## 2. Phần việc phụ trách

- Nhóm trưởng, phụ trách tích hợp (merge PR của các thành viên, chạy `check_submission`).
- Shape A `workflow`: `src/lab8/shapes/workflow.py`.
- Durability và crash: test crash/resume của workflow, crash suite `src/reports/crash.json`.
- Quyết định kiến trúc: `report/team/decision_adr.md`.

## 3. Đóng góp cụ thể

**Commit chính**

| Commit | Nội dung |
| --- | --- |
| [`c93495c`](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/c93495c) | `feat(workflow)`: cài shape workflow và chạy crash suite |
| [`70a3354`](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/70a3354) | `test(workflow)`: crash ở mọi điểm rồi resume vẫn chỉ hoàn một lần |
| [`7006965`](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/7006965) | Bản nháp báo cáo cá nhân |

**Test đã thêm:** `src/tests/test_workflow_crash_resume.py::test_workflow_crash_then_resume_pays_once`, chạy trong cổng host (không gắn marker `student`). Test được parametrize theo cả ba điểm crash (`before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`). Mỗi case kiểm: lần chạy đầu ném `InjectedCrash`; lần resume trả `resolved`, đúng 1 audit `refund_committed`, số tiền bằng `expected.refund_vnd` (35.000 VND), và đúng 1 dòng ledger. T12 có sẵn chỉ phủ điểm `after_effect_before_checkpoint`.

**Quyết định kỹ thuật trong workflow:**
- Tiền do code tính bằng `compute_compensation` từ order row. Workflow không đọc số ngày trễ trong ticket, nên không mắc lỗi của swarm ở C-002 seed 55.
- Truyền **quote đầy đủ** vào `durability.issue_refund`. Host tự trừ phần đơn đã được hoàn; nếu shape tự trừ trước thì host trừ lần nữa và T14 fail.
- Khi host từ chối (T13), `proposal_amount` vẫn là quote đầy đủ, status `denied`; xung đột số tiền trả `failed`.
- Truyền `crash_at` vào `issue_refund`. Khi `InjectedCrash` xảy ra thì ghi trace rồi raise lại, không nuốt lỗi, để host resume đúng.
- Trace chỉ ghi `status`, `reason` và điểm crash; không ghi ticket, order row, `parent_secret` hay `raw_headers`.
- Không gọi MockLLM: workflow có 0 model call, các bước cố định.
- Đếm `budget.add_tool(tool_cost())` sau mỗi tool call (claim, order, compensation) để so cost công bằng với các shape khác.

## 4. Bằng chứng

- Ma trận student: `python -m pytest -q -m student -o addopts= -k workflow` ra 62 passed.
- Cổng host: `python -m pytest -q` xanh, có cả test crash/resume của tôi (3 case pass).
- Mutation check: xóa dòng `raise` trong `except InjectedCrash` của workflow thì cả 3 case của `test_workflow_crash_then_resume_pays_once` và T12 đều fail (`UnboundLocalError`). Trả lại dòng `raise` thì pass. Test thực sự bắt được lỗi nuốt crash.
- Crash suite: `src/reports/crash.json` cho `crash_safety` = `20/20`. Lưu ý: crash suite này chạy host với swarm; độ an toàn crash của workflow được chứng minh bằng T11, T12 và test của tôi.
- Benchmark public (`src/reports/benchmark.json`, 14 claim × 5 seed): workflow pass rate 1.0, pass^5 1.0, variance 0.0, cost per success 27.86 VND (mô phỏng), mean model calls 0.
- Run id dẫn chứng: `R-workflow-C-002-s55` pass, trong khi `R-swarm-C-002-s55` fail trên cùng claim, cùng seed.
- Hidden self-check (`src/reports/hidden_selfcheck.json`, 200 trial): workflow 0 `error`, 0 `leak_suspect`.
- Rà trace: 0/262 trace workflow trong `src/traces/` chứa `CANARY_SECRET`.

## 5. Công cụ AI đã dùng

- Công cụ: Claude Code trong VS Code.
- Dùng vào việc gì:
  - Đọc hiểu đề bài, giải thích khái niệm (budget và cost, idempotency, `crash_at`, seed min-max, cách đọc `benchmark.json`).
  - Gợi ý khung code cho workflow: import, cấu trúc `run_claim`/`_run` với `try/finally`, helper `done()` và bước 1. Tôi tự viết các bước 2–5.
  - Review code và chỉ ra lỗi: truyền nhầm status vào `done("failed")`, hard-code reason thay vì dùng `view["reason"]`, gọi dict bằng `()` thay vì `[]`, truyền reason vào vị trí tham số `proposal`, thiếu `proposal_amount` ở nhánh `resolved`.
  - Gợi ý khung test crash/resume (tôi điền phần assert và câu SQL) và cách làm mutation check.
  - Gợi ý cách diễn đạt một số đoạn trong ADR và soạn các phần mang tính thủ tục của báo cáo này (mục 2–5). Mục 6 tôi tự viết.
- Kiểm tra kết quả như thế nào: chạy pytest sau mỗi thay đổi và đọc lỗi; đối chiếu với `swarm_reference.py`, `docs/business_rules.md` và `docs/contracts.md`; tự làm mutation check cho test; đối chiếu mọi số liệu trong ADR và báo cáo với `benchmark.json`, `hidden_selfcheck.json`, `crash.json` và trace thật. Không dùng AI để bịa số liệu, run id hay commit.

## 6. Tự đánh giá
- Tôi đã học được: Tầm quan trọng của ghi trace trong các bước, vì nó hoạt động như một ranh giới bảo mật cho luồng. Mỗi lần gọi tool (bao gồm cả truy vấn DB) cũng được tính là cost. Tầm quan trọng của idempotency, ngay cả khi thử lại sau crash.
- Tôi đã gặp khó khăn gì: Tôi đã gặp khó khăn trong việc đọc hiểu các APIs đề bài cho và đọc hiểu error log để fix. Ngoài ra, các concept trong bài như cost, crash_at hay seed cũng khiến tôi mất thời gian tìm hiểu. Khi tôi thử sửa shape để kiếm chứng test, tôi đã bỏ cả cụm try catch nên exception vẫn được ném ra và test vẫn pass bình thường, trong khi tôi chỉ cần bỏ raise để nuốt lỗi.
- Tôi có thể cải thiện gì: Tôi có thể chạy test lẻ (-k ... -x) thay vì cả bộ và bối rối khi không biết lỗi ở đâu. Tôi nên viết test sau khi hoàn thành từng bước trong shape để check ngay, không đợi đến cuối. Tôi cũng nên đọc swarm_reference.py kĩ hơn để hiểu về các API trước khi viết code.