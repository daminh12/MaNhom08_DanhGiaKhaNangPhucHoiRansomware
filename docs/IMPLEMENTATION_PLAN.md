# Implementation plan — De tai 08

**Trang thai:** phase 0 + SHA-256 verifier prototype. Docker/Web/DB/Restic/Runbook drill: NOT TESTED.
**Nguon:** tab planning, Do luong RPO & RTO, Danh sach Minh chung, Bien ban Dien tap & Runbook trong Google Sheets cua nhom.
**Thoi gian:** 6 tuan; 2 thanh vien (Da Minh, Minh Quan).

## Tieu chi nghiem thu bat buoc
| ID | Yeu cau | Minh chung | Hien trang |
|---|---|---|---|
| AC01 | Ung dung Web + DB gia chay tren lab cach ly | Compose logs, browser, DB rows | NOT TESTED |
| AC02 | Sao luu du lieu nhat quan, co snapshot va thoi diem | Restic snapshot ID, DB dump log | NOT TESTED |
| AC03 | Ban sao luu thu hai co phan quyen / vi tri tach biet | Cau hinh che bi mat va khoi phuc thu | NOT TESTED |
| AC04 | Mo phong dich vu khong kha dung KHONG dung ma doc | Event log + mo ta kich ban | NOT TESTED |
| AC05 | Khoi phuc vao moi truong sach, ung dung duoc xac minh | Probe, doi chieu DB, hash | NOT TESTED |
| AC06 | Do RTO va recovery point lag theo timestamp | Bang Google Sheets + CSV + log | NOT TESTED |
| AC07 | Runbook v1.0 va v1.1, co ghi nhan sua doi | Bien ban thao tac doc lap | NOT TESTED |
| AC08 | Video 3-5 phut, bao cao, slide, tai lieu nguon | Danh sach Minh chung | NOT TESTED |
| AC09 | Kiem chung SHA-256 cho du lieu gia | Unit test + CLI manifest/verify | PASS (local pre-PR) |

## Workflow 6 tuan
1. **Week 1 — Grounding / setup:** lock scope, Docker Compose, Flask + MySQL; ghi cach chay tren Win11, screenshot config.
2. **Week 2 — Baseline:** du lieu 100-500 ban ghi gia; dump nhat quan; baseline hashes; Restic snapshot.
3. **Week 3 — Restore clean:** khoi phuc snapshot vao DB/container doc lap; kiem tra so row, key, SHA-256 cua dump/moc du lieu.
4. **Week 4 — Dry run 1:** benign outage (application availability toggle), A ghi thoi gian, B chi doc Runbook 1.0.
5. **Week 5 — Improvement:** log loi, Runbook 1.1, tai dien tap 3 lan; so sanh RTO/RPO va ket qua verify.
6. **Week 6 — Delivery:** CSV, hinh, chart, video, paper/slides, checklist va PR review.

## Kich ban lab
- S01: web service unavailable (mock state), restore healthy deployment from clean copy.
- S02: operator access unavailable (tabletop, recovery through separate role).
- S03: backup candidate marked invalid by verification; reject it without modifying backups.
- S04: primary repository unavailable (simulated disconnect); use independent copy.

## Thu thap so lieu (khong duoc gia)
- t0: thoi diem bat dau gian doan duoc event log ghi.
- t1: thoi diem endpoint /health va truy van du lieu hoat dong tro lai, hash/record checks PASS.
- RTO observed = t1 - t0. Khong tinh rieng thoi gian chay lenh restore la RTO.
- Recovery point lag = incident timestamp - timestamp cua ban ghi cuoi duoc phuc hoi;
  ghi rieng so records bi mat va thong tin snapshot. So sanh voi RPO muc tieu.
- Ghi 3 lan lap lai neu co the; khong lam tron hoac dien so lieu truoc khi chay.
- Danh gia ket qua hash cua dung snapshot tuong ung, khong nham voi du lieu moi nhat.

## Referenced source code
- https://github.com/restic/restic — encrypted backups, snapshots, restore and check.
- https://github.com/restic/rest-server — independent append-only REST repository (advanced).
- https://github.com/docker/awesome-compose — multi-service development examples.
- https://github.com/kopia/kopia — alternative backup GUI/CLI, not mandatory.
- https://github.com/pgbackrest/pgbackrest — PostgreSQL-specific alternative, not needed for MySQL.
- https://csrc.nist.gov/pubs/sp/800/61/r3/final — incident-response guidance (2025).
- https://csrc.nist.gov/pubs/sp/1800/11/final — recovering data integrity after ransomware incidents.

## Cau hoi nghiem thu giang vien co the hoi
1. Sao luu va phuc hoi khac nhau the nao? Co bao dam restore duoc khong?
2. Khoi phuc dung snapshot nhung mat ban ghi moi nhat thi co dat RPO?
3. Tai sao SHA-256 PASS chua du de khang dinh ung dung hoat dong?
4. Nguoi restore co the lam theo Runbook ma khong can nho quy trinh khong?
5. Ban sao luu doc lap co thuc su tach quyen / tach noi luu tru?
6. Gioi han cua mo phong lanh tinh so voi ransomware ngoai doi?
