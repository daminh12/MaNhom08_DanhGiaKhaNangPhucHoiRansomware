# Phase 5 — số đo, toàn vẹn và CSV, 10/11/2026

## Điều kiện chuyển phase

Review Phase 0–4: `docs/reviews/PHASE0_4_REVIEW_2026-11-10.md`. R01 được sửa và
20 unit recovery PASS trước khi phân tích. **GO scoped Linux evidence processing**;
không đồng nghĩa mọi finding đã đóng hoặc nghiệm thu Windows. PR Phase 5 dựa trên
PR #5 chưa merge, không tự merge main. Người dùng xác nhận chưa chốt RTO/RPO
mục tiêu; chỉ xuất quan sát thực tế, giữ mục tiêu trống/NOT TESTED.

## Kết quả thật

Xuất bốn dòng trong `docs/evidence/phase5/export-20261110/metrics.csv`:

| Scenario | Run status | Observed RTO (s) | Khoảng tuổi commit cuối phục hồi (s) | Đơn ACK chưa phục hồi |
|---|---|---|---|---|
| Main DB unavailable → clean restore | PASS | 54.198351197 | 10.518407983–10.532435583 | 3/4 yêu cầu ACK; checkpoint trước snapshot phục hồi |
| Web-only control | PASS | 4.918264275 | N/A | N/A |
| Corrupt SQL candidate | PASS của negative test | N/A | N/A | N/A |
| Phase 3 first restore attempt | FAILED, giữ nguyên | N/A (không có incident T0) | N/A | N/A |

Main: backup age từ lúc SNAPSHOT_VERIFIED **0.091588006 s**, import SQL
**0.133908284 s**. Hai số này không phải RTO và không phải khoảng commit lag.
Khoảng send/ACK không được ghi thành exact RPO. Ba tail orders thiếu đúng phạm vi
snapshot, zero duplicate và zero uncertain trong profile đã chạy; không suy ra
không mất dữ liệu cho profile khác. Probe sau restore được ghi riêng, không tính
vào dataset snapshot hay yêu cầu chưa phục hồi.

RTO/MTTD tính lại từ monotonic raw events, kiểm chéo summary đến 1 ns, không dùng
ready UTC trừ fault UTC hoặc created_at_utc. Kiểm thứ tự import/data/API/probe/
restart/stable health; loại return-source sau trial khỏi RTO. Không tạo thêm
performance sample, không lấy control/negative/FAILED làm ba lần lặp main.

## Hậu kiểm thực tế Phase 5

Chạy `verify_retained.py` trên volume target của main trial, không import lại:

- Local receipt/hash khớp bằng chứng Git đã pin.
- Restic `check --read-data` và readback đúng full snapshot PASS; inventory vẫn
  đủ 4 snapshot, gồm hai snapshot Phase 2 cũ, baseline Phase 3 và main Phase 4.
- Target volume có đúng owner/name; dữ liệu đọc lại có **105 dòng nền + 1 probe**,
  hash toàn bảng loại probe và schema vẫn khớp baseline; grants SELECT/INSERT.
- Membership đọc từ DB target xác nhận checkpoint có, ba tail requests không có.
- Nguồn trước/sau đều healthy/108; không tạo thêm order, không xóa volume/snapshot.
- Dùng profile giải phóng stopped containers vì cloud chỉ còn ~138 MB. Khoảng
  downtime phục vụ kiểm chứng này không được đưa vào sample RTO Phase 4.

Proof có timestamp riêng: `retained-integrity.json`, `integrity-events.jsonl`,
`restic-readback.txt`, `snapshot-list.txt`, environment và source fingerprints.
File SQL private ở work chỉ đọc để kiểm SHA; không commit SQL hoặc credential.

## Lệnh đã chạy

```bash
python3 -B -m unittest discover -s SOURCE/tests -p test_recovery.py -v
python3 -B -m unittest discover -s SOURCE/tests -p test_metrics.py -v
python3 -B SOURCE/metrics/verify_retained.py --verification-id p3-phase5-verify-20261110 --output docs/evidence/phase5/retained-integrity.json --release-source-containers
python3 -B SOURCE/metrics/export_metrics.py --artifact-root work/recovery --verification docs/evidence/phase5/retained-integrity.json --output-dir docs/evidence/phase5/export-20261110
```

Output cũ ở lần xuất ban đầu được giữ dưới `work/phase5-first-export-20261110`;
lần xuất chính thức bổ sung full processor/helper hashes. Không ghi đè một output
đã tồn tại và không coi hai lần xuất cùng dữ liệu là hai trial.

## File, test và bằng chứng

| Thành phần | Kiểm chứng | Trạng thái |
|---|---|---|
| Review/ACK guard | Uniqueness, integer clock, send≤ACK≤fault, profile không overlap | PASS, 20 unit recovery |
| Exporter/evidence reader | Git pin, duplicate/nonfinite JSON, event identity/order, truncation, summary mismatch, stable gates, target identity | PASS, 21 unit metrics |
| CSV | BOM/comma/LF, exact decimal strings, blank N/A, failed row retained, formula neutralization, không overwrite | PASS, unit và export thật |
| Artifact integrity | SHA SQL/metadata/manifest đọc lại, metadata binds dump, corrupt copy vẫn bị reject | PASS, `export-20261110/integrity.json` |
| Restic/retained DB | Fresh readback + current target schema/all rows/probe/grants, source returned unchanged | PASS, `retained-integrity.json` |
| Input/output provenance | Pin evidence `258ebc8...`; execution source `dde61a2...`; processor/helper và output SHA | PASS, export manifest |
| App/backup regression | Dùng suite hiện có, DB mock/temporary fixtures | Xem log regression trong evidence Phase 5 |
| Windows/PowerShell | Chạy lab/observer trên Windows thật | NOT TESTED |
| Mục tiêu RTO/RPO | Chưa được nhóm chọn | NOT TESTED |
| Exact RPO, independent storage, 3 main trials, real lost-ACK retry | Chưa có bằng chứng tương ứng | NOT TESTED |

Regression chạy lại trong phiên này: app 14/14, backup 14/14 PASS. Tổng 69 unit
test (20 recovery + 21 metrics + 14 backup + 14 app), không skip trong môi trường
có private artifact; không gộp số unit thành bằng chứng 69 lần phục hồi thật.

## Hạn chế và việc tiếp theo

Chỉ một main trial scripted trên Linux/VFS với image cached; không có confidence
interval hoặc tuyên bố SLA. Journal cùng host phù hợp DB-stop, không chứng minh
mất host thật. Phase 0 prototype, backup entrypoint cũ, Flask advisory và API
idempotency còn finding theo review; không dùng chúng để giả đóng điều kiện mới.

Phase 6: Minh Quân chạy độc lập theo runbook, sửa v1.1 từ lỗi thật. Khi có thêm
nguồn lực/mục tiêu, chạy thêm trial mới và Windows với cùng định nghĩa; không
chép một log thành ba mẫu. Sheet chưa được cập nhật tự động. Hướng dẫn chi tiết:
`SOURCE/metrics/README.md`.
