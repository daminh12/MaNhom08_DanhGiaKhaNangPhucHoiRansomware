# Kết quả triển khai công cụ thực hành Windows — 16/11/2026

Nhánh `codex/group08-windows-rehearsal-20261116`, dựa trên Phase 7 `7b4091f`.
Mã được kiểm thử tại commit `01396dd6b7efd5e1b84d78b963b0299f2b39982a`.
Đây là bổ sung để hai thành viên thực hành; không phải chứng nhận đã chạy trên
Windows hoặc đã hoàn tất toàn bộ đề tài.

## Thay đổi

- Guided yêu cầu terminal tương tác và byte mã thực thi khớp Git (kể cả LF/CRLF).
  Đa Minh INJECT, Minh Quân RECOVER/WEB_OK; giữ một monotonic observer. RTO
  guided-v2 gồm bàn giao, comparison ACK, URL, recheck toàn bảng và stable health.
  Automated-v1 và mọi raw evidence lịch sử giữ nguyên định nghĩa.
- Ctrl+C/EOF ghi ABORTED; nếu ngắt trong POST thì ghi uncertain, không retry.
  Sai xác nhận, resource gate FAIL hoặc dữ liệu đổi khi chờ không được ready.
- Run mới có result schema 2 và evidence manifest theo allowlist, không SQL/
  secret. Exporter --trial-dir xác minh seal/source Git/snapshot/baseline/timeline,
  xuất CSV/JSON/manifest đúng run; FAIL/ABORTED không gán RTO thành công bằng 0.
- Session PowerShell tạo transcript và CSV mẫu; Runbook Windows v1.0 có lệnh
  thật, phân công theo Sheets. v1.1 chỉ là DRAFT chờ quan sát/retest thực tế.
- Xuất Word runbook 10 trang và 7 slide hướng dẫn riêng; không thay báo cáo
  Word/PPTX kết quả Linux. Các file lịch sử được kiểm byte với base commit.

## Bằng chứng và kết luận

Thư mục [evidence](evidence/windows-tooling-20261116/):

| Kiểm tra | Kết quả | Phạm vi/bằng chứng |
|---|---|---|
| Recovery | PASS, 38 unit | recovery-tests.txt; 29 cũ + 9 Guided/mock, không Docker outage |
| Metrics | PASS, 36 unit | metrics-tests.txt; 21 cũ + 15 fixture mới, Git/mock/FixtureOS không là Windows |
| Backup | PASS, 14 unit | backup-tests.txt; verifier/Restic mock |
| App | PASS, 14 unit | app-tests.txt; chạy suite trong container hiện có, DB mock |
| Tổng | **102 unit PASS** | tests.json ghi command, timestamp và code commit; không skip tại máy này |
| Preflight Linux thật | **FAIL yêu cầu dung lượng** | p3-windows-tooling-gate-20261116; guard từ chối đúng trước mutation |
| Export run mới thật | PASS thao tác export | gate-export; CSV giữ trial FAILED, RTO/RPO N/A; không phải trial phục hồi |
| Hệ thống sau kiểm tra | PASS phạm vi chỉ đọc | read-only-verification.json: source_touched=false, target_created=false; health/count 108, tên 5 volume và hash 4 snapshot file không đổi |
| Bảo toàn lịch sử | PASS, 148 file không đổi | preservation.json; gồm evidence và 6 Office file cũ; scan giá trị secret đã biết không thấy trong phần thay đổi |
| Artifact mới | PASS kiểm ZIP/XML và render Linux | artifact-qa.json: Word 10 trang, PPTX 7 slide có Notes, không trang rỗng/text vượt trang; xem PDF preview |
| PowerShell/Windows 10 | **NOT TESTED** | Không có PowerShell/Windows runtime trong môi trường này |
| Guided phục hồi thật, hai người và video | **NOT TESTED** | Không chạy outage/restore mới khi cloud thiếu dung lượng; không giả thao tác người thật |
| Native Microsoft Office | **NOT TESTED** | LibreOffice/Linux không thay chứng cứ Office Windows |

Inventory trước/sau không chứng minh toàn bộ nội dung DB nguồn bất biến; chỉ
health/count, tên volume và encrypted snapshot file hashes được so hai đầu.
Preflight có capture baseline toàn bảng, nhưng không gọi đó là so baseline hai đầu.
Export đọc bằng chứng và hash file, không chạy Restic/DB hậu kiểm mới.

## Cách bắt đầu trên máy nhóm

Mở [Runbook Windows v1.0](../THESIS/runbook/windows/Runbook_Windows_v1.0.md)
hoặc [bản Word](../THESIS/runbook/windows/Runbook_Windows_v1.0.docx).
Tại repo root trên đúng nhánh:

```powershell
. .\SOURCE\recovery\start_session.ps1
```

Làm từng checkpoint: gate → backup → Phase 3 Windows → đối chứng → Guided →
--trial-dir export → ghi lỗi/sửa v1.1 → retest/video → cập nhật Sheets/hồ sơ.
Không copy chạy hết một lượt; một lỗi native phải dừng bước phụ thuộc.

## Blocker và giới hạn còn lại

Cloud còn khoảng 120 MiB; không chạy target mới hoặc xóa dữ liệu để giải phóng.
Nhóm cần tài nguyên Windows đủ và một lượt Minh Quân thực hành thật. CSV/Sheet,
biên bản ký, video và báo cáo số đo Windows chỉ được hoàn thiện từ lượt đó.
Sheet chưa được ghi số đo mới vì chưa có Windows trial; mẫu và mapping đã chuẩn bị.

Không thay đổi scope bốn tình huống mở rộng chưa được giảng viên xác nhận. API
idempotency, legacy backup concurrency/cleanup/log, Flask advisory, verify_retained
gate muộn và storage độc lập vẫn mở. Profile này chỉ tuần tự, không retry, không
Scheduler, không verify_retained. Exact RPO và đạt mục tiêu vẫn NOT TESTED.
Manifest cục bộ không có chữ ký; cần review/pin bằng chứng, không tuyên bố immutable.

Quyết định: GO cho review mã/tài liệu và chuẩn bị Windows; chỉ diễn tập sau các
gate trên máy đó PASS. Chưa nghiệm thu toàn bộ Phase 6/Windows hoặc toàn dự án.
