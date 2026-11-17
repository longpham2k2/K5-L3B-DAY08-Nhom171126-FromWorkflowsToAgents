# Báo cáo cá nhân — 2A202604111_PhamNgocLong

## 1. Thông tin thành viên

- Họ tên: Phạm Ngọc Long
- MSSV: 2A202604111
- Email: 26ai.longpn@vinuni.edu.vn
- GitHub: longpham2k2

## 2. Phần việc phụ trách

Shape, module hoặc phần báo cáo bạn phụ trách.
- Shape A `workflow`: File src/lab8/shapes/workflow.py
- Crash check: File src/reports/crash.json

## 3. Đóng góp cụ thể

Commit chính (hash), test đã thêm hoặc sửa, quyết định kỹ thuật bạn đưa ra.
c93495c2f51ba7340d4acba866b36419be9f803f - Viết workflow
...

## 4. Bằng chứng

Link commit, tên test, run id hoặc trích đoạn report liên quan.
https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents/commit/c93495c
...

## 5. Công cụ AI đã dùng

Công cụ, dùng vào việc gì, và bạn đã tự kiểm tra kết quả thế nào (xem [RULES.md](../../RULES.md)).
- Công cụ: Claude Code trong VS Code.
- Dùng vào việc gì: Đọc hiểu bài tập, gợi ý code, review lại code và chỉ ra các lỗi sai. Tôi thường truyền nhầm status vào done("status"), truyền nhầm hard-code reason thay vì sử dụng kết quả trả ra của các method. Nhờ Claude chỉ ra các lỗi đó nên code tôi mới hoàn thiện.
- Kiểm tra kết quả như thế nào: Sau khi được AI gợi ý cấu trúc tổng quan, tôi thực hiện code từng bước trong Shape, tự chạy test để kiểm chứng kết quả và chỉ nhờ Claude giải thích khi không tìm ra vấn đề.

## 6. Tự đánh giá
- Tôi đã học được: Tầm quan trọng của ghi trace trong các bước. Mỗi lần gọi tool (bao gồm cả truy vấn DB) cũng được tính là cost. Tầm quan trọng của idempotency, ngay cả khi thử lại sau crash.
- Tôi đã gặp khó khăn gì: 
- Tôi có thể cải thiện gì:
