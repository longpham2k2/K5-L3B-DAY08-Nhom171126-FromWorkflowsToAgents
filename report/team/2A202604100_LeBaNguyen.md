# Báo cáo cá nhân — 2A202604100_LeBaNguyen

## 1. Thông tin thành viên

- Họ tên: Lê Bá Nguyên
- MSSV: 2A202604100
- Email: 26ai.nguyenlb2@vinuni.edu.vn
- GitHub: lbNGuyen06

## 2. Phần việc phụ trách

Shape B `single` (một agent ReAct): file `src/lab8/shapes/single.py`, gồm cả phần CP2 (luồng xử lý claim) và CP3 (truyền `crash_at`, để `InjectedCrash` đi qua). Kèm một test riêng cho shape này trong `src/tests/test_single_shape.py`.

## 3. Đóng góp cụ thể

**Commit chính:** `1175413` — `feat(single): implement shape B ReAct agent (CP2 + CP3)` (nhánh `feat/single-shape`).

**Cấu trúc shape `single`:**

| Phần | Việc làm |
| --- | --- |
| Trước vòng lặp | Đọc claim bằng read tool `get_claim_view` (không đọc SQL trực tiếp nên không chạm `parent_secret`). Claim không tồn tại → `failed` / `unknown_claim`. Thiếu `order_id` → `needs_info`, không đoán mã đơn từ ticket |
| Vòng lặp | `runtime.run_react` với `max_steps=8`. `decide()` chọn lần lượt `lookup_order` → `lookup_refund_history` → `lookup_policy` → `compute_compensation`, rồi trả `final`. Không thấy đơn hoặc không sở hữu → dừng sớm, `escalated` |
| Sau vòng lặp | Quote = 0 → `denied`, không gọi host. Quote > 0 → `durability.issue_refund(conn, claim_id, quote, crash_at=crash_at)`. Kết quả host → `resolved` / `denied` / `failed` (conflict). `proposal_amount` luôn là quote đầy đủ |

**Quyết định kỹ thuật:**

1. **`decide()` có bộ nhớ riêng.** `run_react` chỉ đưa cho `decide` kết quả tool vừa gọi, không giữ lịch sử, nên `decide` lưu order, refund history, policy vào một dict `memory`.
2. **Không tin ticket.** `compute_compensation` nhận order row lấy từ DB. Ticket không đi vào `decide` hay prompt của MockLLM. Nhờ đó T02 ở seed 55 vẫn `denied` (swarm trả 20.000).
3. **Tiền do code, ghi do host.** Model chỉ chọn tool đọc; số tiền do `compensation.quote` tính; chỉ code sau vòng lặp gọi `issue_refund`.
4. **Truyền quote đầy đủ.** Không tự trừ phần đơn đã được hoàn; host tự trừ. T14: quote 150.000, ledger 120.000.
5. **Quote > 0 luôn đưa cho host,** kể cả khi biết có thể bị từ chối, để host ghi audit `policy_denied` (T07, T13).
6. **Đếm chi phí trung thực.** Mỗi lần `decide` gọi `mock_llm.complete(purpose="react")` một lần, cộng một lần `draft` cuối. Một claim bình thường: 6 model call, 5 tool call.
7. **Trace tối thiểu.** Chỉ ghi `claim_id`, `found`, `has_order_id`, tên tool, `visible`/`reason`, số tiền đã hoàn, mã policy, quote, kết quả host. Không ghi ticket, claim row hay order row thô.
8. **`run_claim` không ném lỗi** (trừ `InjectedCrash`): lỗi trong vòng lặp → `failed` / `react_error:<loại>`; hết 8 bước → `failed` / `step_cap`.

**Test đã thêm:** `tests/test_single_shape.py::test_single_ignores_ticket_delay_on_seed_55` — C-002 (ticket ghi trễ 5 ngày, order ghi 2 ngày) ở seed 55: `single` phải `denied`, không có dòng ledger, qua `metrics.trial_pass`; đối chứng swarm cùng claim cùng seed trả 20.000. Test nằm trong cổng host (không gắn marker `student`).

## 4. Bằng chứng

- Commit: `1175413` trên nhánh `feat/single-shape`.
- Ma trận student của shape `single`:
  `python -m pytest -q -m student -o addopts= -k "not workflow and not orchestrator and not swarm"` → `62 passed, 240 deselected`.
- Cổng host: `python -m pytest -q` → `55 passed, 248 deselected` (54 ban đầu + 1 test mới).
- Crash thủ công trên C-012:
  `python -m lab8.run --shape single --claim-id C-012 --seed 11 --db data/crash1.sqlite --crash-at after_effect_before_checkpoint` → `{"crashed": true, "at": "after_effect_before_checkpoint"}`; chạy lại không có `--crash-at` trên cùng DB → `status: resolved`, ledger 1 dòng 35.000, `committed_audit_count: 1`.
- Quét `traces/R-single-*` tìm `CANARY`, `Bearer`, phone, address: không có kết quả.
- Lưu ý: `python -m lab8.crash_test` chỉ chạy shape swarm (`src/lab8/crash_test.py`), nên bằng chứng crash của `single` là test T12 và lần chạy thủ công ở trên.

## 5. Công cụ AI đã dùng

- **Claude Code (Claude, Anthropic)** trong VS Code: đọc tài liệu đề bài và code host để tóm tắt yêu cầu, giải thích các thành phần (`run_react`, MockLLM, `issue_refund`, quote), viết `single.py` theo từng phần (trước / giữa / sau vòng lặp) và viết test `test_single_shape.py`.
- **Cách tự kiểm tra:**
  - Làm từng phần một và chạy thử sau mỗi phần: phần trước vòng lặp kiểm trên C-999 / C-004; phần giữa in bảng quote của 14 claim ở seed 55 so với `expected.proposal_amount` trong `data/public_claims.jsonl`; phần sau chạy ma trận student.
  - Chạy ma trận student (62/62), cổng host (55/55), crash thủ công trên C-012, quét trace tìm secret.
  - Đối chiếu code với `docs/business_rules.md` và `docs/contracts.md` (quote đầy đủ, không gọi host khi quote = 0, không bắt `InjectedCrash`).
  - Kiểm tra test mới thực sự phân biệt được: cùng claim, cùng seed thì swarm sai còn `single` đúng.

## 6. Tự đánh giá

<!-- Tự viết phần này: mức độ hiểu, điều làm tốt, điều còn hạn chế. RULES.md không cho dùng AI viết phần tự đánh giá. -->

...
