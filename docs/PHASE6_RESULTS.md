# Phase 6 — thử runbook v1.0 và cải tiến v1.1, 15/11/2026

## Kết luận

**Đã thực hiện review, chạy phần khả dụng an toàn của v1.0 trên Linux và tạo
Runbook v1.1. Chưa nghiệm thu toàn bộ Phase 6.** Lượt clean restore/main drill mới,
PowerShell Windows 10 và lượt độc lập của Minh Quân còn **NOT TESTED**.
Blocker hiện tại là tài nguyên cloud: chỉ còn khoảng 132 MiB trống; clean gate
FAIL trước khi dừng nguồn/tạo target. Không xóa volume/snapshot để chạy tiếp.

Đây là thao tác Codex trên Linux/cloud, không phải biên bản hai thành viên đã
thực hiện hoặc giảng viên đã nghiệm thu. Giờ trong raw evidence là UTC; lượt
control bắt đầu 02:56 UTC (09:56 UTC+7), 15/11/2026.

Review: [Phase 0–5](reviews/PHASE0_5_REVIEW_2026-11-15.md).
Runbook: [v1.1](../THESIS/runbook/Runbook_v1.1.md).
DOCX v1.0 gốc giữ nguyên SHA-256; phần không phù hợp được ghi lỗi, không thực thi.

## Nhánh và nguồn thực thi

Base `068e1f4f70f75a9246889ce320a2c28b258bb92e`, nhánh riêng
`codex/group08-phase6-runbook-20261115`; phụ thuộc PR #6/Phase 5, chưa merge main.

- Commit `3a71b307f386da6c5025327bf6be8cab8d007690`: preflight, local-input guard,
  uncertain HTTP 201 fix; là source của các real control/gate ban đầu.
- Commit `de7b2ad3f4158f89f478bc6ccd729913532dff51`: resource hardening sau review,
  không dùng credit host như dung lượng Docker VM đã được giải phóng. Gate/unit
  chạy lại ở `post-review-*`; không sửa timing của control đã chạy trước đó.

Mã app/backup/metrics cốt lõi, Compose, SQL schema/seed và raw evidence Phase 1–5
không bị thay đổi để làm phép thử PASS. Nhánh main khi kiểm tra vẫn ở Phase 2;
PR #5/#6 vẫn draft/open. PR Phase 6 cũng để review, không tự merge.

## Những bước v1.0 đã thử và lỗi ghi nhận

`v1.0-safe-checks.json` ghi đúng command, exit code và cách thích nghi Linux:
Compose config/ps/logs, HTTP health, DB/version/table count và app grants. Truy
vấn MySQL đọc secret từ file trong container, không hiển thị password; không gọi
nguyên lệnh PowerShell nhập mật khẩu tương tác rồi nhận là Windows PASS.

V1.0 §9.1 được kiểm bằng `runtime_phase1.py`: restart nguồn, kiểm dữ liệu còn,
dừng DB → health/API 503, start DB → HTTP 200. Script chỉ đối chiếu API window;
Phase 6 kiểm thêm hash/schema **toàn bảng** ở hai đầu, tránh kết luận từ 100 dòng.
Đây là control persistence/khả dụng, không là phục hồi bằng Restic.

Không chạy v1.0 §9.2: còn BACKUP_DIR placeholder, restore cùng nguồn/DB tạm và
COUNT làm đối chiếu; các điểm này FAIL review so với yêu cầu clean restore. Không
bật general log hoặc tìm thao tác phá bảng cho bài dừng service. Xem F601 và
changelog cuối v1.1; bản gốc được giữ làm lịch sử.

## Bảng nghiệm thu thực tế

| Hạng mục | Bằng chứng | Trạng thái | Hạn chế/việc tiếp theo |
|---|---|---|---|
| Đọc/review code và v1.0 | Review F601–F612; SHA DOCX trong safe checks | PASS phạm vi review | Không là full CVE/image audit hoặc đối chiếu Sheet mới |
| V1.0 dùng nguyên trạng cho clean recovery | §4, §9.2, §10, §11 trong DOCX | FAIL review | Dùng v1.1, không chạy đoạn import nguồn |
| Các bước v1.0 chỉ đọc | `v1.0-safe-checks.json`, 9 command exit 0, HTTP 200/108 | PASS Linux | Lệnh native Windows NOT TESTED |
| Chặn khi thiếu tài nguyên | `clean-gate-*`, `release-gate-*`, `post-review-release-*`: exit 1, source_touched=false, target_created=false | PASS của negative guard | Resource requirement vẫn FAIL |
| Đủ tài nguyên cho clean target mới | Host free 138,743,808 B; VFS estimate 2,136,002,336 B; credit vẫn thiếu | FAIL | Tăng disk/chuyển lab đã chuẩn bị, chạy clean gate lại |
| Gate web-only | `web-gate-*`, `post-review-web-*` | PASS Linux | Không cấp phép restore/backup tool container mới |
| Dừng/start web đối chứng | `web-rehearsal-result.json`, raw events, return_source_status=PASS | PASS Linux | RPO N/A; không có snapshot recovery |
| V1.0 §9.1 DB-stop/start và restart | `v1.0-db-control.txt`, exit 0, health/API 503 rồi health 200 | PASS Linux | Không suy ra clean restore hoặc RPO=0 |
| Full source trước/sau controls | `inventory-before.json`, `inventory-after.json`: schema/hash/108 dòng bằng nhau | PASS | Không thêm đơn; không dùng COUNT/API window thay hash |
| Candidate SQL copy bị sửa | `local-corrupt-copy.json`: SHA mismatch, original unchanged, import_attempted=false | PASS local artifact thật | Dùng artifact đã extract từ trước; không phải Restic readback mới |
| Full reject-corrupt qua Restic mới | Không tạo tool container vì thiếu disk | NOT TESTED | Bằng chứng Phase 4 cũ vẫn riêng, không chuyển thành PASS hôm nay |
| Clean restore/import/schema/API-write target/restart target mới | Không tạo target trong Phase 6 | NOT TESTED | Historical Phase 3/4 Linux PASS không thay lần chạy mới |
| SQL import bị gián đoạn thật | Chưa chạy | NOT TESTED | Unit nonzero-exit không thay fault injection thật |
| ACK response hỏng, không retry | `recovery-before-fix.txt` và `recovery-final-unit.txt` | PASS unit sau fix | Dùng mock, chưa inject response-loss trên MySQL thật; API chưa idempotent |
| Regression | Recovery 27, metrics 21, backup 14, app 14 | PASS, 76 tests | Unit/mock/fixture, không phải 76 lượt phục hồi thật |
| Tái xuất CSV lịch sử | `historical-export-20261115/` và output manifest | PASS | 4 case cũ, không phải dữ liệu/đo main trial mới |
| Giữ bằng chứng/dữ liệu | `inventory-after.json`: 5 volume tên cũ, 4 encrypted snapshot file hash không đổi, DOCX không đổi | PASS | Inventory/hash không là Restic check mới hoặc chống mất host |
| Kết thúc/cleanup | Web control return_source_status=PASS; final gate source_touched=false; nguồn HTTP 200/108 | PASS Linux | Chưa inject cleanup failure thật; guard unit không thay bài lỗi Windows |
| Windows 10 / PowerShell / Task Scheduler | Chưa có transcript máy Windows | NOT TESTED | Đa Minh chạy, Minh Quân đọc/ghi độc lập |
| Mục tiêu RTO/RPO, exact RPO | Nhóm chưa chọn target; chỉ có send/ACK bounds lịch sử | NOT TESTED | Không tự đặt SLA hoặc timestamp commit |

Control web mới có observed interval **5.050724009 s**, tính từ raw monotonic của
chính control này. Không thay observed main RTO **54.198351197 s** ngày 10/11 và
không coi web control là một main repeat. Phép thử DB-stop/start ở v1.0 không
được gán số đo clean restore.

Tái xuất giữ đúng bốn case: main, web-only, corrupt candidate, FAILED restore.
SQL/metadata hiện có được verify SHA lại, không import hoặc đọc DB target. Không
truyền proof retained-DB cũ để nhận là hậu kiểm DB mới hôm nay; các trường fresh
Restic/retained DB của lần tái xuất này là NOT TESTED. Mục tiêu vẫn để trống.

## Lệnh đã chạy

Các lệnh dưới đây **đã chạy trên Linux**, không phải thiết kế:

```bash
python3 -B -m unittest discover -s SOURCE/tests -p test_recovery.py -v
python3 -B -m unittest discover -s SOURCE/tests -p test_backup.py -v
python3 -B -m unittest discover -s SOURCE/tests -p test_metrics.py -v
docker compose exec -T web python -m unittest discover -s /tests -p test_app.py -v
python3 -B SOURCE/recovery/controller.py preflight --run-id p3-p6-gate-20261115
python3 -B SOURCE/recovery/controller.py preflight --run-id p3-p6-gate-release-20261115 --release-source-containers
python3 -B SOURCE/recovery/controller.py preflight --run-id p4-p6-gate-web-20261115 --preflight-scope web-control
python3 -B SOURCE/recovery/controller.py web-outage --run-id p4-p6-web-20261115 --return-source
python3 -B SOURCE/tests/runtime_phase1.py
python3 -B SOURCE/metrics/export_metrics.py --artifact-root work/recovery --output-dir docs/evidence/phase6/historical-export-20261115
python3 -B SOURCE/recovery/controller.py preflight --run-id p4-p6-final-web-20261115 --preflight-scope web-control
python3 -B SOURCE/recovery/controller.py preflight --run-id p3-p6-postreview-20261115 --release-source-containers
python3 -B SOURCE/recovery/controller.py preflight --run-id p4-p6-postreview-20261115 --preflight-scope web-control
```

Không lặp lại nguyên run ID/output directory: các workflow cố ý từ chối reuse.
Lệnh PowerShell dự kiến chạy thật nằm trong Runbook v1.1, không gắn PASS Linux
cho chúng. Local copy check chỉ dùng verifier Phase 2 và candidate riêng trong
work; chứng cứ chỉ chứa digest/status, không commit SQL/secret.

Lỗi thử nghiệm được giữ: tests mới trước fix ACK có 1 failure/3 errors; một lượt
fixture mới thiếu thuộc tính mock được ghi ở `recovery-fixture-failed.txt`, sau
khi sửa fixture suite PASS. Discover mọi suite trực tiếp trên host từng lỗi
thiếu PyMySQL; chạy lại từng suite đúng runtime như bảng trên, không báo lệnh
discover lỗi đó đã PASS. Không cài thêm dependency hoặc rebuild image trong cửa
sổ disk gần đầy này.

## File tạo/chỉnh sửa

| File | Lý do |
|---|---|
| `SOURCE/recovery/controller.py` | Preflight hai scope, input guard, ghi resources/state, validate ACK 201 malformed |
| `SOURCE/recovery/run_lab.ps1` | Expose action preflight và scope cho workflow Windows |
| `SOURCE/tests/test_recovery.py` | 7 test mới, positive/negative ACK, secret, low-space và Docker-capacity guard |
| `THESIS/runbook/Runbook_v1.1.md` | Lệnh/đường dẫn thật, acceptance/abort/evidence, metric và phạm vi hiện hành |
| `docs/reviews/PHASE0_5_REVIEW_2026-11-15.md` | Finding, tái hiện, fix tối thiểu, owner/effort/dependency |
| `docs/PHASE6_RESULTS.md`, `docs/evidence/phase6/` | Kết quả thật, cả FAIL/NOT TESTED; inventory, source/version/test/command logs |
| README, recovery/tests README, lab_config và addendum runbook | Trỏ v1.1 và bỏ thông tin trạng thái lỗi thời |
| `SOURCE/config/lab_config.example`, `SOFT/README.md`, `SETUP/installation/install_guide.md` | Đồng bộ đường dẫn backup/script hiện tại, dependency Python host Phase 3–6 và hướng dẫn runbook |
| `.gitattributes` | Giữ nguyên trailing space thật trong output unittest failure, không sửa raw log cho qua whitespace check |

## Việc còn lại theo thứ tự phụ thuộc

1. **Đa Minh:** mở rộng dung lượng cloud/Docker Desktop hoặc chuẩn bị lab khác có
   đủ disk; giữ kho/secret gốc, chạy clean preflight. Không dùng xóa DB/target/snapshot
   làm cách cấp chỗ. Nếu đổi máy, bản sao khác ổ/host cần kiểm chứng, không chỉ copy
   thư mục rồi gọi là độc lập.
2. **Đa Minh thao tác, Minh Quân ghi:** trên Windows 10 thật, theo v1.1 từ preflight
   → backup receipt mới → restore cổng 8081 → đọc/schema/all rows/grants → probe →
   restart → return-source. Lưu transcript không secret, Git/Docker/Python versions,
   exit code và nguyên raw result. Tiêu chí từng bước trong v1.1.
3. **Minh Quân:** chạy độc lập theo tài liệu, ghi bước sai/khó hiểu và đối chiếu
   v1.0→v1.1; hai người review biên bản. Chưa có dữ liệu để ký PASS thay thành viên.
4. Sau Phase 3 Windows PASS và gate mới PASS, mới chạy full Phase 4 drill trên
   Windows. Khi thêm trial, đăng ký corpus/pin mới trước CSV tổng hợp, giữ raw cũ.
5. Trước mở retry/schedule/copy độc lập hoặc demo cuối, xử lý finding tương ứng:
   API idempotency, legacy backup cleanup/log/concurrency, Flask patch/rebuild,
   rồi test đúng profile. Các mục này chưa được đóng bởi control không retry.
6. Phase 7 đồng bộ hồ sơ/nhật ký/slide từ số liệu có thật. Chưa có target RTO/RPO
   thì chỉ báo quan sát, không đặt mục tiêu sau khi xem kết quả.

Không thiếu quyền phê duyệt cho các bước an toàn ở lượt này; phần chưa chạy bị
giới hạn bởi tài nguyên và chưa có môi trường Windows, không phải do chờ merge.
