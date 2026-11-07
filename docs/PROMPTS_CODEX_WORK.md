# Codex + Work end-to-end prompts — Group 08

## P0 — Start in Codex Ask/Plan mode (read-only)
Ban la ky su an toan thong tin, lap trinh vien Python va mentor do an. Doc README.md, AGENTS.md, docs/IMPLEMENTATION_PLAN.md, Google Sheets cua nhom (neu co quyen doc) va toan bo file trong repo. Kiem ke file 0-byte, code da ton tai, cac rui ro ve scope. Lap requirement traceability table (requirement -> source -> module -> test -> evidence). Chi de xuat ke hoach, chua sua file. Dung rubric minh hoa neu khong co rubric chinh thuc. Khong tu tao du lieu do luong.

## P1 — Python baseline (Codex Code mode)
Kiem tra module SOURCE/verification/verify_hashes.py, thuc thi python -m unittest discover -s SOURCE/tests -v. Cho test voi du lieu gia SOURCE/data/synthetic. Dam bao manifest nam ngoai dataset; phat hien file modified/missing/unexpected va tu choi symlink/path traversal. Neu co bug, de xuat PR nho, bao cao test.

## P2 — Docker Web + Database
Tao Docker Compose cho Flask + MySQL chi truy cap localhost, dung database gia. Them /health de kiem tra DB va API hien thi danh sach du lieu gia. Khong hard-code secrets; dung .env.example. Viet smoke tests va huong dan Windows 11. Khong exposure port ra public internet. Acceptance: docker compose up va tests PASS.

## P3 — Backup / restore
Thiet ke quy trinh dump DB nhat quan va sao luu bang Restic. Dung 2 noi luu tru tach biet cho local backup va ban sao thu hai neu kha thi. Restore sang volume + DB sach, khong ghi de nguon. Ghi snapshot ID, timestamp UTC, backup/restore logs. Co script chay lai va tests. Thong bao neu Restic chua cai va danh dau NOT TESTED.

## P4 — Benign incident drill
Tao che do mock outage tuong tac voi app lab (flag health check), khong xoa bang hay ma hoa tep. Log thoi diem kich hoat mock outage, detect, isolate, restore, verify. Khoi phuc tu snapshot hop le va thao tac theo Runbook. Test trong lab cach ly.

## P5 — Metrics + repeated trials
Do RTO tu outage den khi endpoint /health va kiem chung du lieu PASS. Tinh recovery point lag tu timestamps cua du lieu duoc khoi phuc; ghi data loss count rieng. Tao CSV co scenario, run_id, UTC timestamps, snapshot_id, actual_rto_seconds, recovery_point_lag_seconds, recovered_files_percent, integrity_result, notes. Chay 3 trials neu co the; tuyet doi khong fabricating metrics.

## P6 — Runbook and review
Tu event logs viet Runbook 1.0 cho nguoi thuc hien khong can doc source code. Minh Quan dien tap khac nguoi phat trien, ghi loi tung buoc, sua thanh 1.1. Rerun and compare, luu evidence. Review bao mat secrets/paths va code changes.

## P7 — Work: academic + report
Su dung Google Sheets https://docs.google.com/spreadsheets/d/1akuMwhM-N3BXN0V8xOcPl2OdIb3PAh_oW5JUYyJivjI/edit
va GitHub https://github.com/daminh12/MaNhom08_DanhGiaKhaNangPhucHoiRansomware.
Doc NIST SP 800-61r3 va SP 1800-11. Dua tren log, manifest, screenshots, CSV CO THAT: doi chieu traceability, ghi bao cao va slide, tao runbook final, cross-check references; dung NOT TESTED cho noi chua co bang chung. KHONG dien thay so lieu hay danh gia.

## Working rule for every task
Truoc khi sua: liet ke files se sua va acceptance criteria. Sau khi sua: noi ro diff, commands actually run, outputs, commands not run, residual risks. Branch/PR rieng, KHONG merge vao main khong review.
