# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 8f13c9b
- Run id dẫn chứng: R-workflow-C-002-s55 (đối chứng R-swarm-C-002-s55 fail cùng claim, cùng seed)
- Pass rate / pass^5 / seed min-max / variance: 1.0 / 1.0 / 1.0-1.0 / 0.0
- Cost per success (mô phỏng, VND): 27.86 
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0 (public: 0/62 trace workflow chứa CANARY_SECRET; ma trận student pass các case approval)

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Viết 1 đoạn. So cùng corpus và cùng seed, không so với một lần chạy lẻ.

Theo bảng benchmark, có thể thấy cả workflow, single và orchestrator đều có pass và pass^5 là 100%. Vì vậy cần so sánh dựa trên chi phí và số lần gọi model. Workflow có 0 model call (= orchestrator) và chi phí 27.86 < 46.43 < 47.84 < 49.57, là thấp hơn khoảng 40% - 44% so với các shape khác. Ngoài ra, cần xét đến workflow cũng là các bước fixed, ít tự động hơn, ít rủi ro model call hơn. Lựa chọn vừa đảm bảo tính chính xác, lại tiết kiệm chi phí ở trong điều kiện này (14 claim x 5 seed) là workflow.

## Có đáng đổi lấy multi-agent không

Nếu pass nhỉnh hơn mà cost và variance cao hơn, nhóm giữ hay đổi? Điều kiện nào làm quyết định đảo lại?

Trên bộ public, single và orchestrator đạt pass và pass^5 1.0, bằng workflow, còn swarm chỉ đạt 0.986 và 0.929. Nghĩa là khoản chi phí cao hơn (+67–78%) không đem lại thêm độ chính xác nào. Kể cả khi một shape multi-agent có pass nhỉnh hơn nhưng cost và variance cao hơn, nhóm vẫn giữ workflow: sai sót ở đây là hoàn sai tiền cho khách, khó sửa và tốn kém, nên phải ưu tiên tính đúng đắn và khả năng đoán trước (phương sai thấp) trước, chi phí xét sau.
Điều kiện có thể khiến nhóm đổi ý: claim chỉ có thông tin ở dạng free-text mà luật cố định không phân loại được, hoặc chính sách phức tạp, thay đổi thường xuyên, khó cập nhật vào code. Khi chuyển sang LLM thật, pass, chi phí và phương sai của các shape đều có thể thay đổi nên phải đo lại. Với bộ hidden 40 claim, nếu grader của giảng viên cho thấy pass rate của workflow dưới ngưỡng 0.75 trong khi single hoặc orchestrator vượt ngưỡng, nhóm sẽ xem xét lại.

Nhóm chọn shape từ benchmark public, sau đó tự kiểm trên `student_drop/` (`src/reports/hidden_selfcheck.json`, 40 claim × 5 seed = 200 trial mỗi shape). Cả ba shape đều có 0 trial `error`, 0 trial `leak_suspect`, và trả cùng status ở cả 200 trial (95 denied, 90 resolved, 10 escalated, 5 needs_info). Workflow vẫn rẻ nhất: tổng chi phí mô phỏng 5.800 VND so với 9.700 (orchestrator) và 10.103,5 (single). Vì vậy nhóm giữ quyết định.

## Trace và bằng chứng

Trace của nhóm ghi những event nào? Field nào cố ý **không** ghi, và vì sao? Nếu trace nằm ngoài chỗ scanner quét được, đội security chứng minh thế nào là hệ thống không lộ secret?
- Trace của workflow chỉ có hai loại event: `decision` (payload `status`, kèm `reason` ở các nhánh có lý do), ghi ở mọi nhánh return; và `crash` (payload `at`), ghi khi `InjectedCrash` xảy ra, trước khi raise lại để host resume. `proposal_amount` nằm trong `RunResult`, không nằm trong trace.
- Trace cố ý không ghi: từ order là `phone`, `address`, `internal_note`, `item_name`, `principal_id`, `carrier`; từ claim là `ticket`, `parent_secret`, `raw_headers` (chứa header `Authorization: Bearer CANARY_SECRET_...`). Trace cũng không ghi nguyên order row hay ticket. Lý do: trace là ranh giới bảo mật, không phải tiện ích debug. Ticket là dữ liệu người dùng nhập, có thể chứa secret hoặc câu injection; phone, address, item_name là thông tin cá nhân có thể truy ra khách hàng.
- Bảo đảm này đến từ code, không đến từ việc scan. `workflow.py` có đúng 8 lời gọi `trace.add`, và mỗi lời gọi chỉ ghi `status`, `reason` hoặc `at`. Vì vậy reviewer có thể đọc code để kiểm, không cần tin vào scanner. Bằng chứng thêm: 0/262 trace workflow trong `src/traces/` (62 public + 200 hidden self-check) chứa `CANARY_SECRET`, và 0/200 trial `leak_suspect` trong `hidden_selfcheck.json`.


## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
- MockLLM không phải model thật, nên cost và phương sai là số mô phỏng, chưa phản ánh chi phí và hành vi thực tế.
- Latency là `unavailable`, nên không so sánh được tốc độ giữa các shape.
- Bộ public chỉ có 14 claim, và cả ba shape của nhóm đều đạt pass và pass^5 1.0, nên benchmark không phân biệt được các shape về độ chính xác. Quyết định dựa chủ yếu vào chi phí và mức tự chủ.
- Hidden self-check không có nhãn. Ba shape trả cùng status không chứng minh là đúng, vì cả ba dùng chung lõi tất định (`compute_compensation` và cổng host) nên có thể sai giống nhau. Kết quả chính thức do grader của giảng viên chấm.
- Số secret leak / approval bypass trên bộ hidden do giảng viên đo. Nhóm chỉ có bằng chứng trên bộ public và self-check.
- Trace của workflow rất gọn: nhánh `resolved` không ghi số tiền hay clause, nên khó audit một khoản hoàn chỉ từ trace.
