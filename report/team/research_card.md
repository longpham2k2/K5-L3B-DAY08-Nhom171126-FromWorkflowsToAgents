# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R3 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Bogavelli, Subramani, Sharma (ServiceNow), *AgentArch: A Benchmark for Evaluating Agent Architectures in Enterprise Workflows*, AACL-IJCNLP 2026; arXiv 2509.10769 (v1 09/2025, v2 01/2026), https://arxiv.org/abs/2509.10769 . Loại bằng chứng: benchmark thực nghiệm có kiểm soát |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Trên 18 cấu hình (orchestration, kiểu prompt agent ReAct vs function calling, memory, thinking tool), kiến trúc tốt nhất phụ thuộc vào model ("model-specific architectural preferences"), không có kiến trúc phù hợp mọi trường hợp; function calling nhìn chung tốt hơn ReAct ở đa số model (ngoại lệ LLaMA 3.3 70B) |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | 6 LLM thật qua API (GPT-4.1, GPT-4o, GPT-4.1-mini, o3-mini, Claude Sonnet 4, LLaMA 3.3 70B); 2 workflow doanh nghiệp (xin nghỉ phép, định tuyến yêu cầu khách hàng); tool là mock trả kết quả cố định; pass@1 trên k = 8 lần thử. Không nói gì về MockLLM deterministic hay task claim hoàn phí |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Tắt vòng ReAct của shape `single` (model không chọn bước, thứ tự tool cố định trong code): pass rate, pass^5, seed variance KHÔNG đổi (task tuần tự, đường đi đúng là cố định); cost/success GIẢM, và dự đoán phần lớn khoảng chênh ~20 VND giữa `single` (47,84) và `workflow` (27,86) trong `reports/benchmark.json` là do ReAct |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: MockLLM, 5 read tool cùng thứ tự, `compute_compensation`, host `issue_refund`, cách ghi trace, 14 claim public, seed 11/22/33/44/55, `config/pricing.yaml`, evaluator `lab8.metrics`, SQLite mới cho mỗi trial. Biến duy nhất thay đổi: có/không gọi MockLLM ở mỗi bước `decide` (`single` vs `single_fixed` = `src/bonus/single_fixed.py`, gọi `single._run(react_model=False)`). `workflow` chạy kèm chỉ để tham chiếu, không phải một nhánh của ablation |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến của vòng ReAct: không dừng kịp → hết 8 bước (`step_cap`), hoặc decide tin số ngày trong ticket (T02 seed 55). Đo bằng pass rate, pass^5, seed variance và `reasons` trong report; chi phí đo bằng cost/success và mean_model_calls |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn, trong `src/`):
  `python -m lab8.benchmark --shapes workflow,single,single_fixed --extra-shape single_fixed=bonus.single_fixed:run_claim --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_r3_react.json`
- Run id / file report: `src/reports/ablation_r3_react.json` (210 trial = 3 shape × 14 claim × 5 seed). Run id theo mẫu `R-<shape>-<claim>-s<seed>`, ví dụ `R-single-C-014-s11` và `R-single_fixed-C-014-s11`.
- Kết quả so với hypothesis: **đúng một phần, sai ở phần quan trọng.**

  | Shape | pass | pass^5 | variance | cost/success (VND) | mean model calls | mean tool calls | mean steps |
  | --- | --- | --- | --- | --- | --- | --- | --- |
  | `single` (ReAct bật) | 1,000 | 1,000 | 0 | 47,84 | 5,36 | 4,50 | 7,71 |
  | `single_fixed` (ReAct tắt) | 1,000 | 1,000 | 0 | 45,86 | 0,93 | 4,50 | 7,71 |
  | `workflow` (tham chiếu) | 1,000 | 1,000 | 0 | 27,86 | 0 | 2,79 | 1,00 |

  - Đúng: pass rate, pass^5, variance không đổi. 70/70 trial của hai biến thể có cùng `status`, cùng số tool call, cùng số step; không có trial nào `step_cap`.
  - Sai: tắt ReAct chỉ giảm cost/success 1,98 VND (−4,1%), dù bỏ được ~4,4 lời gọi model mỗi trial. Khoảng chênh `single` − `workflow` là 19,99 VND, trong đó ReAct chỉ chiếm ~10% (1,98); ~90% (18,0) đến từ 1,71 tool call đọc thêm mỗi trial (`lookup_refund_history`, `lookup_policy`, 10 VND/lần) và lời gọi soạn thư.
  - `mean steps` không đổi vì metric này đếm event trong trace, mà hai biến thể ghi cùng event; vì vậy không nên dùng steps để so độ phức tạp giữa các shape có cách ghi trace khác nhau.
  - Kết luận trong phạm vi lab: với task tuần tự này, ReAct không tăng độ đúng; chi phí của nó nhỏ dưới bảng giá mô phỏng. Điều này nhất quán với nhận định của AgentArch rằng ReAct không phải lựa chọn mặc định tốt hơn, nhưng không kiểm chứng được phần "phụ thuộc model" vì lab chỉ có một MockLLM.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`. MockLLM tính token theo độ dài prompt; prompt của bước ReAct rất ngắn (`step=..;last=..`) nên chi phí ReAct ở đây gần như chắc chắn thấp hơn với LLM thật (prompt chứa lịch sử và kết quả tool). MockLLM deterministic và `decide` là code cố định, nên lab không đo được loại lỗi ReAct mà paper thấy (hallucination, chọn sai tool, phụ thuộc model). Chỉ 14 claim public.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
