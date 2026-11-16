# Nhóm 08 — Phục hồi sau sự cố mất khả dụng bằng mô phỏng an toàn

Đề tài: Đánh giá khả năng phục hồi trước sự cố mã hóa tống tiền bằng mô phỏng an toàn.
Thành viên: Đa Minh, Minh Quân. Máy thực hành: Windows 10, Docker Desktop.

Ba tài liệu chính, đọc theo nhu cầu:

| Tài liệu | Nội dung |
|---|---|
| [Báo cáo các phase](BAO_CAO_CAC_PHASE.md) | Phase 0–7, kết quả/bằng chứng, PASS/FAIL/NOT TESTED và việc còn thiếu |
| [Các lưu ý thực nghiệm](LUU_Y_THUC_NGHIEM.md) | Đường dẫn thật, gate, finding, định nghĩa RTO/RPO và giới hạn |
| [Hướng dẫn thực nghiệm](HUONGDAN.md) | Chuẩn bị Windows, lệnh từng bước, bàn giao hai người, CSV, retest và hồ sơ |

Stack: Docker Compose, Flask, MySQL 8.4.7 (`lab_config.orders`), mysqldump,
Restic và SHA-256. Chỉ dùng đơn hàng giả; kịch bản chính dừng service DB.

Mã và bằng chứng Linux đã có; Windows, Guided hai người, video và retest vẫn
NOT TESTED. Chưa chọn mục tiêu RTO/RPO. Có code hoặc tài liệu chưa đủ nghiệm thu.

Mở PowerShell tại repository root, làm từng checkpoint trong HUONGDAN:

```powershell
. .\SOURCE\recovery\start_session.ps1
```

| Thư mục | Nội dung giữ trong repo |
|---|---|
| SETUP | Script khởi tạo lab |
| SOURCE | Mã ứng dụng, backup/recovery/metrics và test |
| docs/evidence | Log, JSON/CSV, hash và ảnh kiểm thử gốc, gồm cả FAIL |
| docs/templates/windows | CSV mẫu biên bản, minh chứng và thay đổi runbook |
| THESIS | Word/PPTX, nguồn nội dung, công cụ build và PDF lịch sử |
| SOFT | Phiên bản công cụ, nguồn và giấy phép |

Báo cáo Word/PPTX và runbook cũ trong THESIS được giữ làm hồ sơ; lệnh hiện hành
lấy từ HUONGDAN. Tài liệu phase/review/hướng dẫn rời trước đây đã được hợp nhất;
lịch sử xem trong Git. Không xóa volume/snapshot hoặc tự merge các PR.
