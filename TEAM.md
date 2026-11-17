# Team

## Thông tin nhóm

- Tên nhóm: Nhóm 171126
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/longpham2k2/K5-L3B-DAY08-Nhom171126-FromWorkflowsToAgents
    - Nhánh main
    - Commit: 8f13c9b

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Phạm Ngọc Long | 2A202604111 | 26ai.longpn@vinuni.edu.vn | longpham2k2 | Nhóm trưởng; shape A workflow; tích hợp; durability/crash; ADR |
|   2 | Trần Trọng Đạt | 2A202604030 | 26ai.dattt5@vinuni.edu.vn | dtr-uep | Shape C orchestrator; handoff và trace an toàn; báo cáo nhóm |
|   3 | Lê Bá Nguyên | 2A202604100 | 26ai.nguyenlb2@vinuni.edu.vn | lbNGuyen06 | Shape B single (ReAct); benchmark; research card |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Phạm Ngọc Long | Shape A workflow, tích hợp, durability/crash, ADR | `c93495c` feat(workflow): implement workflow shape and run crash test | `src/tests/test_workflow_crash_resume.py::test_workflow_crash_then_resume_pays_once` |
| Lê Bá Nguyên | Shape B single (ReAct), benchmark, research card | `1175413` feat(single): implement shape B ReAct agent (CP2 + CP3) | `src/tests/test_single_shape.py::test_single_ignores_ticket_delay_on_seed_55` |
| Trần Trọng Đạt | Shape C orchestrator, handoff, báo cáo nhóm | `9ec4fe1` feat(orchestrator): thêm orchestrator điều phối investigator | `src/tests/test_orchestrator.py::test_orchestrator_denies_approval` |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## MSSV_HoTen

### Phần việc phụ trách

-

### Đóng góp cụ thể

-

### Bằng chứng

-
