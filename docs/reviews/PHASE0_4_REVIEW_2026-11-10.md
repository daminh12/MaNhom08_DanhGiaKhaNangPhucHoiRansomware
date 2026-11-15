# Review Phase 0–4 trước Phase 5 — 10/11/2026

## Quyết định

**GO có giới hạn cho Phase 5 phân tích bằng chứng Linux/cloud đã có**, sau khi
sửa R01 và chạy 20 unit recovery PASS. Không GO cho nghiệm thu Windows, benchmark
retry/concurrent writes hoặc mất host/kho độc lập. Người dùng xác nhận **chưa chốt
RTO/RPO mục tiêu; chỉ xuất số đo thực tế**, nên kết luận đạt mục tiêu là NOT TESTED.

Review base `258ebc8b7bddb7b5fd4ce9562a37889bf1c2a36a` (PR #5 draft); main vẫn
`37addd7`/Phase 2. PR #1/#2 starter/audit chưa merge. Không tự merge bất kỳ PR nào.
Nhánh mới `codex/group08-phase5-metrics-20261110`, dựa trên nhánh Phase 4.

## Findings và cách xử lý

| ID | Mức/phạm vi | Bằng chứng | Kết luận và hành động |
|---|---|---|---|
| R01 | High, tính đúng metric | `SOURCE/recovery/common.py:99` trước fix chấp nhận ACK sau fault, thứ tự sai/ID trùng và có thể tính lag âm | **FIXED**: kiểm integer clock, uniqueness, row identity và profile tuần tự trước fault; 20 unit PASS, 4 ACK thực đáp ứng validation. Chặn Phase 5 đến khi sửa |
| R02 | Medium, provenance | `main-result.json` có số tổng hợp nhưng raw events/ACK mới là nguồn tính toán; source đã harden sau integration | Exporter phải pin input theo Git ref, tính lại từ monotonic events, kiểm summary, ghi execution source `dde61a2` và processor source riêng; không sửa log cũ |
| R03 | Medium, integrity scope | Target đã giữ volume nhưng container đã gỡ; Phase 4 chỉ là bằng chứng tại thời điểm trial | Phase 5 phải phân biệt byte check hiện tại, readback Restic hiện tại và DB verification lịch sử/hiện tại. Kiểm target chỉ đọc nghiệp vụ, không import lại, không tạo thêm mẫu RTO |
| R04 | Medium, resource | Cloud chỉ còn ~138 MB, Docker VFS; failed/success target volumes đều giữ | Không chạy thêm benchmark/volume mới. Chỉ dùng profile giải phóng stopped containers đã có nếu kiểm lại target; luôn trả nguồn về healthy, không xóa volume/snapshot |
| R05 | Medium, retry app | `SOURCE/app/app.py:139`, probe mock cũ có 2 commit khi lost ACK + retry | **OPEN**, không cho phép kết luận profile retry. Trial đã chạy tuần tự, không retry, uncertain=0 nên không chặn phân tích mẫu đó |
| R06 | Medium, backup cũ | `backup.ps1:15,43,70`, `backup.sh:10,49`, `backup.py:104,191,204`: shared script, cleanup unchecked/suppressed, một số action không lưu log | **OPEN** ở entrypoint cũ. Controller Phase 3/4 dùng script theo run, journal cleanup và log snapshot/extract. Không chạy entrypoint cũ đồng thời; không đánh dấu finding đã đóng |
| R07 | Low hiện tại, dependency | Flask vẫn 3.1.2; GHSA-68rp-wp8r-4726 LOW, fixed 3.1.3; app không dùng session và no-store | **OPEN**, patch dependency riêng trước demo cuối. Không có full CVE/image scan trong review này |
| R08 | Medium, Windows/evidence | PS launcher cần Python host mới; chưa chạy Windows 10/Task Scheduler | **NOT TESTED**; Linux không thay Windows. Không chặn exporter đọc dữ liệu Linux |
| R09 | Medium, storage | Restic/password/source cùng host; không có secondary storage độc lập | **NOT TESTED** kịch bản mất host/kho chính; không chặn single-host outage đã chạy |
| R10 | Process/scope | Prototype verifier Phase 0 có 2 lỗi trên nhánh draft; AGENTS/plan chưa ở main | Không dùng prototype đó làm verifier Phase 5. Dùng manifest Phase 2 và canonical baseline Phase 3; không merge prototype để giả đóng finding |
| R11 | Evidence/method | Một main trial; restore-return source là bước sau trial, baseline/data probe không được trộn | Không tạo 3 mẫu từ một log, không đưa post-trial return vào RTO, không gọi tuổi backup là RPO, không lấy created_at_utc làm commit time |
| R12 | Portability, pin/hash | Windows autocrlf có thể thay byte JSON/JSONL dù nội dung nhìn giống | `.gitattributes` giữ LF cho evidence JSON/JSONL/CSV; check-attr đúng LF. Không tự sửa input để qua pin và không coi đây là Windows runtime PASS |

## Đối chiếu theo phase

- Phase 0: audit thực hiện; finding prototype chưa sửa nhưng không ở execution path.
- Phase 1: 16 fingerprint source khớp evidence, app source không đổi; dữ liệu hiện
  108 đơn fake, health 200. Không ép về 100 hoặc xóa đơn để làm đẹp kết quả.
- Phase 2: chỉ `db_dump.sh` thay đổi có chủ đích thêm skip-add-drop-table. Manifest
  vẫn v1, metadata mở rộng baseline của run mới; snapshot cũ không bị viết lại.
- Phase 3: real restore schema/all rows/grants/API/restart PASS Linux; run FAILED
  trước charset normalization vẫn giữ. Partial SQL interruption thực NOT TESTED.
- Phase 4: web control/main/corrupt guard có raw events; fingerprint của cả Phase
  3/4 khớp commit execution `dde61a2241de9bfd2b9f8138433b60f63d140cdd`.
  Hardening sau integration có bằng chứng guard riêng, không hồi tố timing.

## Điều kiện đầu ra Phase 5

RTO/MTTD tính từ raw monotonic; tách backup age, khoảng lag từ send/ACK, số yêu
cầu chưa phục hồi, duplicate, uncertain và mục tiêu chưa chốt. CSV phải giữ NULL
cho N/A/NOT TESTED, giữ run FAILED, kiểm pin/hash/schema/timeline và không ghi đè
output cũ. Dữ liệu mock chỉ dùng test, không đưa vào CSV thực nghiệm.

Đầu ra Phase 5 đã thực hiện sau gate: 21 unit metric PASS, fresh Restic/readback,
SQL đọc lại target 105 nền + 1 probe, source trở lại healthy/108 và đủ 4 snapshot.
Xuất 4 dòng có giữ FAILED/N/A; không phát sinh performance trial mới. Chi tiết và
hash manifest ở `docs/PHASE5_RESULTS.md` và `docs/evidence/phase5/`.
