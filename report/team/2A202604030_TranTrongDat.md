# Báo cáo cá nhân — MSSV_HoTen

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Trần Trọng Đạt
- MSSV: 2A202604030
- Email: 26ai.dattt@vinuni.edu.vn
- GitHub: dtr-uep

## 2. Phần việc phụ trách

- Shape, module hoặc phần báo cáo bạn phụ trách.
- Shape: Ochestrator  

## 3. Đóng góp cụ thể

Commit chính (hash), test đã thêm hoặc sửa, quyết định kỹ thuật bạn đưa ra.
- Orchestrator: [9ec4fe1](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/9ec4fe1aa5d31bbccafdefb889f134c8744076ae)
- Test approval: [d8971ce](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/d8971cef152834a182f8fa19c9c14ea3a331ceda)
- Test đã thêm: test_orchestrator.test_orchestrator_denies_approval


## 4. Bằng chứng

Link commit, tên test, run id hoặc trích đoạn report liên quan.
- Triển khai orchestrator: [9ec4fe1](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/9ec4fe1aa5d31bbccafdefb889f134c8744076ae)
- Test thiếu approval: [d8971ce](https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/d8971cef152834a182f8fa19c9c14ea3a331ceda)
- Tên test: [test_orchestrator_denies_approval](../../src/tests/test_orchestrator.py)


## 5. Công cụ AI đã dùng

Công cụ, dùng vào việc gì, và bạn đã tự kiểm tra kết quả thế nào (xem [RULES.md](../../RULES.md)).

- Sử dụng codex: dùng để gợi ý code, giải thích trước qua đề bài, cho đường dẫn đến các file cần đọc.
- Đọc nghiệp vụ, suy ra flow và cho AI kiểm chứng, chọn loại test và yêu cầu AI sửa code để test không tạo dữ liệu mới mà làm việc trên file tạm thời.

## 6. Tự đánh giá
- Đã hiểu workflow, và agent trong nghiệp vụ, ochestrator hiện chưa áp dụng LLM, chỉ hiểu được cách giới hạn quyền giữa ochestrator và investigator. 
- Workflow cho thấy là lựa chọn tốt nhất vì có đầu ra ổn định và chi phí rẻ cho thấy phương pháp đơn giản này tuy ít linh hoạt hơn nhưng vẫn hiệu quả.
