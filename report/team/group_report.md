# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: Nhom171126
- Thành viên: xem `TEAM.md`
- Commit chốt (trùng `report/team/decision_adr.md`):

## 2. Mục tiêu và cách tiếp cận

Nhóm hiểu bài toán thế nào, chia việc ra sao, thứ tự làm bốn shape.
- Hiểu đề bài là cần xây dựng hệ thống xử lý yêu cầu hoàn phí vận chuyển và bồi thường hàng hỏng cho LogiX-VN. Hệ thống cần có khả năng xác minh được quyền sở hữu đơn, đối chiếu dữ liệu và policy để đề xuất tính toán số tiền cần hoàn, sau đó các lý do và mức hoàn sẽ được kiểm tra approval và thực hiện hoàn tiền. Nhóm cần khai thác 3 kiến trúc là workflow, single agent và orchestrator và so sánh với swarm làm baseline. Mục tiêu là xác định ra phương pháp có độ chính xác ổn định và chi phí phù hợp.
- Phân chia công việc:  

| Thành viên | Phần việc phụ trách | File liên quan |
| --- | --- | --- |
| Phạm Ngọc Long | Triển khai workflow, kiểm thử crash/resume tại các điểm crash | `src/lab8/shapes/workflow.py`; `src\tests\test_workflow_crash_resume.py` |
| Lê Bá Nguyên | Triển khai single agent, kiểm thử bỏ qua số ngày trễ trong ticke | `src/lab8/shapes/single.py`; `src/tests/test_single_shape.py` |
| Trần Trọng Đạt | Triển khai orchestrator, kiểm thử thiếu approval | `src/lab8/shapes/orchestrator.py`; `src/tests/test_orchestrator.py` |

## 3. Giải pháp

Mô tả ba shape nhóm viết (workflow, single, orchestrator): mỗi shape đọc gì, quyết định gì, gọi host ra sao. Chỉ rõ ranh giới code / model (tham khảo [docs/architecture.md](../../docs/architecture.md)), cách handoff được sanitize và trace ghi những event nào.

| Nội dung | Workflow | Single agent | Orchestrator |
| --- | --- | --- | --- |
| Cách điều phối | Luồng Python cố định: đọc claim → kiểm mã đơn → tra đơn và quyền sở hữu → tính quote → quote dương thì gọi host → trả kết quả; dừng sớm nếu thiếu thông tin hoặc không đủ điều kiện | Đọc claim → kiểm mã đơn → vòng ReAct: code chọn tool đọc → nhận kết quả → cập nhật trạng thái → chọn bước tiếp theo, tối đa 8 bước → nhận quote → gọi host nếu quote dương → trả kết quả | Đọc claim → kiểm mã đơn → tạo handoff với nhiệm vụ và tool cố định → investigator lần lượt tra đơn, đọc policy và tính quote → orchestrator kiểm kết quả → gọi host nếu quote dương → trả kết quả |
| Dữ liệu và tool sử dụng | Đọc claim, tra đơn, tính quote | Đọc claim, tra đơn, lịch sử refund, policy và tính quote | Đọc claim; investigator tra đơn, policy và tính quote |
| Vai trò của model | Không áp dụng LLM | MockLLM mô phỏng bước ReAct và soạn phản hồi; code chọn tool | Không áp dụng LLM |
| Cách tính quote | Gọi trực tiếp `compute_compensation` | Gọi `compute_compensation` trong vòng ReAct | Investigator gọi `compute_compensation` |
| Kiểm approval và ghi refund | Gửi quote đầy đủ vào `issue_refund`; host kiểm approval và trần tiền | Code gọi host sau vòng ReAct với quote đầy đủ | Orchestrator gọi host với quote đầy đủ; investigator không ghi tiền |
| Phân quyền và handoff | Kiểm principal qua tool; không dùng handoff | Runtime chặn tool ghi; không dùng handoff | `make_handoff` lọc allowlist, gọi `sanitize`; chỉ cấp tool đọc |
| Retry và crash/resume | Truyền `crash_at`; ghi trace crash rồi ném lại exception | Truyền `crash_at`; ghi trace crash rồi ném lại exception | Truyền `crash_at`, không nuốt exception; host chống hoàn trùng |
| Trace và bảo vệ dữ liệu | Ghi `decision`, `crash`; không dump claim/order | Ghi claim chọn lọc, bước ReAct, kết quả host và quyết định | Ghi handoff đã sanitize, investigator, quote, refund và decision; không ghi secret/PII |
| Kết quả trả về | Dùng `finish()` tạo `RunResult` theo contract | Dùng `finish()`; lỗi hoặc vượt bước → `failed` | Dùng `finish()` tạo `RunResult` theo contract |
| Giới hạn của giải pháp | Luồng cố định | Tool do code chọn, chưa có model suy luận chọn tool | Tool cố định; chưa điều phối động hoặc chạy song song |


## 4. Kết quả

Bảng so sánh 4 shape trên bộ public (từ `src/reports/benchmark.json`): pass rate, pass^5, seed min–max, variance, cost/success, mean/p95 steps. Kèm crash safety (`src/reports/crash.json`) và, nếu có, kết quả tự kiểm trên `student_drop/`.

Số liệu từ [benchmark.json](../../src/reports/benchmark.json), gồm 14 claim × 5 seed (`11,22,33,44,55`), 70 trial cho mỗi shape. Chi phí là VND mô phỏng, làm tròn hai chữ số thập phân.

| Shape | Trial pass | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean steps | P95 steps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Workflow | 70/70 | 100% | 100% | 100%–100% | 0 | 27,86 | 1,00 | 1 |
| Single agent | 70/70 | 100% | 100% | 100%–100% | 0 | 47,84 | 7,71 | 9 |
| Orchestrator | 70/70 | 100% | 100% | 100%–100% | 0 | 46,43 | 4,36 | 5 |
| Swarm | 69/70 | 98,57% | 92,86% | 92,86%–100% | 0,00081633 | 49,57 | 2,80 | 3 |

Quyết định kiến trúc và lý do: xem `report/team/decision_adr.md`. Phiếu nghiên cứu và ablation: xem `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

Lỗi gặp phải (kèm lệnh, output hoặc ảnh chụp) và cách nhóm xử lý.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

## 7. Hạn chế và hướng cải thiện

MockLLM không phải model sản xuất; latency là `unavailable`. Nêu thêm giới hạn của nhóm và điều kiện làm kết luận thay đổi.

| Hạn chế | Hướng cải thiện |
| --- | --- |
| Orchestrator trong benchmark chưa dùng model, chủ yếu thể hiện phân quyền | Bổ sung planner và kiểm thử khả năng kiểm soát hành vi model |
| Single chọn tool bằng code; MockLLM chưa phản ánh suy luận của LLM thật | Đánh giá thêm khả năng chọn tool và lỗi model trong nghiên cứu tiếp theo |
| Chỉ đánh giá 14 claim public trên 5 seed | Mở rộng tình huống biên và kiểm chứng trên hidden |
| Chi phí mô phỏng, chưa đo latency; steps phụ thuộc trace | Chuẩn hóa trace và đo lại trong môi trường thực tế |
| Investigator chạy tuần tự; chưa tách riêng tác động của topology | Ablation từng yếu tố, thử song song các việc đọc độc lập |

Đánh giá lại lựa chọn kiến trúc khi thay đổi task, model, giá hoặc yêu cầu latency. Ablation trong [research_card.md](research_card.md) mới khảo sát bật/tắt lời gọi MockLLM ở bước ReAct.

## 8. Tài liệu tham khảo

Nguồn nghiên cứu được nhóm ghi trong [research_card.md](research_card.md):

- Bogavelli, Subramani, Sharma (ServiceNow). *AgentArch: A Benchmark for Evaluating Agent Architectures in Enterprise Workflows*. AACL-IJCNLP 2026; arXiv:2509.10769 (v1: 09/2025, v2: 01/2026). [Bài nghiên cứu](https://arxiv.org/abs/2509.10769).
