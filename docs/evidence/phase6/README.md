# Evidence Phase 6 — 15/11/2026

Kết luận theo hạng mục: `docs/PHASE6_RESULTS.md`. Raw timestamps UTC;
operator là Codex/Linux cloud, không gán vai thực thi cho hai thành viên.

| Nhóm file | Ý nghĩa |
|---|---|
| `v1.0-safe-checks.json` | DOCX SHA và lệnh v1.0 chỉ đọc được thích nghi Linux; ghi bước bị bỏ và lý do |
| `clean-gate-*`, `release-gate-*`, `gate-commands.json` | Clean recovery NO-GO vì disk, cả hai không dừng nguồn/tạo target |
| `web-gate-*`, `final-gate-*` | Preflight scope web-control PASS trước/sau rehearsal |
| `web-rehearsal-*`, `rehearsal-commands.json` | Web-only control thật, raw observer events và return-source |
| `v1.0-db-control.txt` | Script có sẵn chạy DB-stop/start, source restart/persistence; không là Restic restore |
| `inventory-before/after.json` | Full source baseline hai đầu, hash 4 encrypted snapshot files, tên 5 volume, v1.0 DOCX không đổi |
| `local-corrupt-copy.json` | Candidate mới trong work bị SHA từ chối; artifact extract có sẵn, không fresh Restic |
| `historical-export-20261115/`, `export-console.txt` | Tái xuất corpus lịch sử, không đo main trial mới; fresh artifact hash riêng với DB/Restic NOT TESTED |
| `recovery-before-fix.txt` | Mock reproducer thật trước fix HTTP 201: giữ failures/errors |
| `recovery-fixture-failed.txt` | Lỗi mock fixture trong lúc viết test, không phải lỗi DB; đã sửa fixture |
| `recovery-unit.txt`, `recovery-final-unit.txt`, `metrics-final-unit.txt` | 27 recovery / 21 metrics tests; final sau resource hardening |
| `app-regression.txt`, `backup-regression.txt`, `metrics-regression.txt`, `regression-commands.json` | Suite đúng runtime; app/backup source không đổi; mock/fixture không thay integration |
| `environment.json` | Môi trường control tại commit 3a71b30; actual installed dependency versions |
| `post-review-*` | Unit/gate tại de7b2ad sau resource hardening; không sửa log/timing control trước đó |
| `verification.json`, `manifest.json` | Hậu kiểm evidence, Git/source pins và SHA output; manifest không tự hash chính nó |

Chưa có full restore mới, fresh Restic readback, Windows native hoặc lượt chạy
độc lập của Minh Quân. Không copy SQL plaintext, secret hay full rows vào bundle.
Trong log unit có fixture timestamp/row/error giả; không dùng chúng làm số đo.
