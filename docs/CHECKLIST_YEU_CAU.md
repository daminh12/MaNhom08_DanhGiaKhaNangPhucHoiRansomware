# Checklist và truy vết yêu cầu — Nhóm 08

Cập nhật 15/11/2026. Bảng dưới phản ánh bằng chứng đã có trong repository, không
phải biên bản nghiệm thu của giảng viên. PASS chỉ áp dụng phạm vi ghi trong bảng;
code/script có sẵn không tự tạo bằng chứng chạy thật. Bằng chứng Linux không thay
Windows 10. Chưa có RTO/RPO mục tiêu do nhóm phê duyệt.

| ID | Yêu cầu / điều kiện đạt | File thực thi / hồ sơ | Bằng chứng và trạng thái |
|---|---|---|---|
| R01 | Audit cấu trúc, giữ nguyên tài liệu/mã nhóm | `docs/reviews/PHASE0_5_REVIEW_2026-11-15.md` | PASS phạm vi review đã ghi; AGENTS/plan/prompts nêu ở master prompt chưa có trên nhánh thực thi; không tự suy đoán nội dung |
| R02 | Compose, Flask, MySQL và dữ liệu giả | `compose.yaml`, `SOURCE/app/`, `SOURCE/database/` | PASS Linux: [Phase 1](PHASE1_RESULTS.md); Windows NOT TESTED |
| R03 | Health truy vấn DB; DB unavailable phải 503 | `SOURCE/app/app.py`, `SOURCE/tests/runtime_phase1.py` | PASS Linux: [runtime](evidence/phase1/runtime-results.txt), [control Phase 6](evidence/phase6/v1.0-db-control.txt) |
| R04 | Quyền ứng dụng chỉ SELECT/INSERT, DB không publish port | `SOURCE/database/03_privileges.sql`, `compose.yaml` | PASS Linux: [grants](evidence/phase1/seed-and-grants.txt), [runtime](evidence/phase1/runtime-results.txt) |
| R05 | Dump orders nhất quán, không copy nóng volume MySQL | `SOURCE/backup/db_dump.sh`, recovery controller | PASS Linux: [Phase 2](PHASE2_RESULTS.md), [baseline Phase 3](evidence/phase3/baseline-result.json); phải ngừng writer/DDL theo runbook |
| R06 | Snapshot Restic có full ID; check và readback | `SOURCE/backup/backup.py`, `SOURCE/recovery/archive.py` | PASS Linux lịch sử: [hai backup](evidence/phase2/successful-runs.json), [hậu kiểm Phase 5](evidence/phase5/retained-integrity.json) |
| R07 | Manifest/SHA-256 kiểm trước import | `SOURCE/backup/backup.py`, `SOURCE/recovery/archive.py` | PASS phạm vi đã chạy: [corrupt guard](evidence/phase4/corrupt-result.json), [copy check Phase 6](evidence/phase6/local-corrupt-copy.json); copy check không là Restic readback mới |
| R08 | Restore vào project/network/volume sạch, không seed/mount nguồn | `compose.restore.yaml`, recovery controller | PASS Linux lịch sử: [clean events](evidence/phase3/clean-events.jsonl), [clean result](evidence/phase3/clean-result.json) |
| R09 | Readiness không phụ thuộc orders; import exit 0; tạo lại app role | `compose.restore.yaml`, `SOURCE/recovery/controller.py` | PASS Linux: [clean result](evidence/phase3/clean-result.json), [target grants](evidence/phase3/target-grants.txt); SQL interruption thật NOT TESTED |
| R10 | Schema và toàn bảng khớp baseline; API đọc trước probe; restart giữ dữ liệu | `SOURCE/recovery/common.py`, controller | PASS Linux: [clean result](evidence/phase3/clean-result.json), [main events](evidence/phase4/main-events.jsonl); API LIMIT 100 không thay full-table hash |
| R11 | Từ chối target dở/đã tồn tại | Recovery guard và `test_recovery.py` | PASS các case đã thử: [existing run](evidence/phase3/existing-run-refused.txt), [Docker guard](evidence/phase3/post-review-guard.json); không suy ra mọi lỗi import đã thử thật |
| R12 | Diễn tập DB dừng lành tính, restore tại URL phục vụ | `SOURCE/recovery/controller.py drill` | PASS một main trial Linux: [main result](evidence/phase4/main-result.json); không malware, không phá bảng; Windows NOT TESTED |
| R13 | ACK độc lập, không retry; tách missing/duplicate/uncertain | Controller/common; `acknowledgements.json` | PASS profile tuần tự đã chạy: 1 checkpoint phục hồi, 3 ACK chưa phục hồi, 0 duplicate, 0 uncertain; real lost-ACK/retry NOT TESTED |
| R14 | RTO từ fault requested đến validation và URL ready | `SOURCE/metrics/` | PASS tính lại corpus: [CSV Phase 5](evidence/phase5/export-20261110/metrics.csv); 54.198351197 s là một mẫu quan sát, không SLA |
| R15 | Tách backup age, commit-lag bounds, số đơn thiếu và RPO objective | `SOURCE/metrics/README.md` | PASS phương pháp xuất hiện tại; exact RPO/target attainment NOT TESTED, không dùng created_at_utc làm commit evidence |
| R16 | Log/CSV giữ FAIL và N/A, có hash/provenance | Metrics exporter; evidence theo phase | PASS corpus lịch sử: [manifest Phase 5](evidence/phase5/export-20261110/manifest.json), [replay Phase 6](evidence/phase6/historical-export-20261115/manifest.json) |
| R17 | Chạy v1.0, ghi lỗi, cải tiến v1.1 | [Runbook v1.1](../THESIS/runbook/Runbook_v1.1.md), [Phase 6](PHASE6_RESULTS.md) | PASS phần review/control Linux; nghiệm thu Phase 6 đầy đủ NOT TESTED vì thiếu disk, Windows và lượt Minh Quân độc lập |
| R18 | Đủ tài nguyên cho restore mới | `controller.py preflight` | FAIL tại kiểm tra Phase 6: [gate](evidence/phase6/post-review-release-result.json); guard từ chối trước mutation. Không xóa volume/snapshot để cấp chỗ |
| R19 | Workflow PowerShell/Windows 10 thực sự chạy | `SOURCE/recovery/run_lab.ps1`, backup PS/Scheduler | NOT TESTED native Windows; cần transcript, version, exit code và kết quả riêng |
| R20 | Bản sao độc lập cho mất host/kho chính | Thiết bị/vị trí độc lập chưa có bằng chứng | NOT TESTED; kho/password/journal hiện cùng host, không tuyên bố 3-2-1/offsite/immutable đã đạt |
| R21 | Báo cáo và slide truy được về evidence | `THESIS/REPORT_GROUP08.md`, `BaoCao_Nhom08.docx`, `SLIDES_GROUP08.md`, `ThuyetTrinh_Nhom08.pptx` | PASS kiểm artifact: Word 17 trang, 15 slide có Notes, ZIP/XML/render và metric agreement; xem `docs/evidence/phase7/artifact-qa.json`. Native Microsoft Office/Windows và nghiệm thu dự án đầy đủ NOT TESTED |

Các finding còn mở: API idempotency, entrypoint backup cũ dùng script chung/cleanup
và log chưa đầy đủ, Flask 3.1.2 chưa nâng bản vá, cùng host và giới hạn controller
bắt đầu từ nguồn healthy. Chi tiết/owner/điều kiện đóng nằm trong review Phase 6.
Không đổi trạng thái các mục này thành PASS vì đã có báo cáo Word hoặc slide.
