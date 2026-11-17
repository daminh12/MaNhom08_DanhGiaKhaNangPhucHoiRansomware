# Báo cáo các phase — Nhóm 08

Cập nhật 17/11/2026 (UTC+7). Đề tài: **Đánh giá khả năng phục hồi trước sự cố
mã hóa tống tiền bằng mô phỏng an toàn**. Thành viên: Đa Minh, Minh Quân.

Tài liệu này tổng hợp kết quả, nhật ký và truy vết yêu cầu. Đọc
[các lưu ý](LUU_Y_THUC_NGHIEM.md) trước khi làm theo
[hướng dẫn thực nghiệm](HUONGDAN.md). PASS luôn gắn với môi trường và lượt chạy.
Các kiểm tra Linux/cloud có hỗ trợ tự động chưa là xác nhận hai thành viên đã
thực hành Windows. Không có số liệu hoặc chữ ký được tạo thay người thực hiện.

## 1. Hiện trạng và phạm vi

| Phase | Nội dung | Kết luận dựa trên bằng chứng |
|---|---|---|
| 0 | Kiểm kê, review cấu trúc và verifier SHA-256 | Đã review; prototype cũ còn finding, không dùng cho pipeline hiện hành. Nghiệm thu nguyên trạng prototype: NOT TESTED trên nhánh này |
| 1 | Flask/MySQL, đơn hàng giả, health, quyền và persistence | PASS phạm vi Linux; Windows NOT TESTED |
| 2 | Dump nhất quán, manifest, Restic/check/readback | PASS các backup Linux đã ghi; script backup cũ còn finding |
| 3 | Restore vào stack sạch, toàn bảng/schema, quyền, API và restart | PASS lượt Linux ngày 10/11; có cả lần FAILED được giữ. Windows và restore trên mã mới nhất NOT TESTED |
| 4 | DB unavailable → clean restore; web-only; SQL copy hỏng | PASS ba phép thử Linux đã ghi; một main trial, chưa có Windows |
| 5 | Tính RTO/lag, kiểm toàn vẹn, xuất CSV | PASS tái lập corpus đã pin; exact RPO và đạt mục tiêu NOT TESTED |
| 6 | Review/chạy phần phù hợp của runbook v1.0, soạn v1.1 | PASS một phần trên Linux; nghiệm thu đầy đủ và Minh Quân thực hành Windows NOT TESTED |
| 7 | Review cuối, Word/PPTX và kiểm artifact | PASS kiểm tài liệu trên Linux; native Office/Windows và nghiệm thu toàn dự án NOT TESTED |
| Bổ sung Windows | Guided, exporter từng run, session, dataset và biểu mẫu | 116 unit PASS ngày 17/11; preflight Linux từ chối thiếu disk. Guided phục hồi thật, hai người và video NOT TESTED |

**Quyết định:** sẵn sàng review hồ sơ và chuẩn bị thực hành Windows. Chỉ chạy
diễn tập chính sau Phase 3 Windows và clean preflight trên máy đó PASS. Chưa kết
luận toàn bộ dự án hoàn thành hoặc đạt mục tiêu RTO/RPO; nhóm chưa chọn mục tiêu.

Kiến trúc đã triển khai: Docker Compose, Flask 3.1.2/Gunicorn/PyMySQL, MySQL
8.4.7, bảng InnoDB `lab_config.orders`, mysqldump, Restic 0.18.1, SHA-256 và
observer Python host. Có cùng luồng backup/restore cho các phase; không dùng mã
độc hoặc phá bảng để tạo sự cố. Dừng service DB chỉ mô phỏng mất khả dụng.

## 2. Phase 0 — kiểm kê và lựa chọn verifier

Đã đọc README, Compose, mã app/backup/recovery/metrics, tests, các DOCX và các
báo cáo trước khi tổng hợp. Nhánh thực thi không có AGENTS hoặc bộ prompt/plan
AI được theo dõi. Không suy đoán nội dung file/nhánh chưa đọc.

Prototype SHA-256 ở nhánh starter từng có lỗi root symlink và đầu vào JSON list;
không dùng nó làm điều kiện nghiệm thu hiện tại. Module `SOURCE/backup/backup.py`
có scope hai file cố định, guard symlink/path/manifest/dump và unit riêng.
Prototype không tự được coi là đã sửa bởi module mới.

## 3. Phase 1 — web và DB giả

Mã: `compose.yaml`, `SOURCE/app/`, `SOURCE/database/`,
`SETUP/installation/init_lab.ps1`, các test app/runtime/smoke.

| Kiểm chứng | Kết quả | Bằng chứng |
|---|---|---|
| DB/schema/seed mới | MySQL 8.4.7, InnoDB, 100 dòng trước lần ghi đầu | [Schema và quyền](docs/evidence/phase1/seed-and-grants.txt) |
| Health/HTTP/ghi và đầu vào sai | PASS Linux; lỗi DB trả 503, không lộ secret | [Runtime](docs/evidence/phase1/runtime-results.txt), [unit](docs/evidence/phase1/unit-final.txt) |
| Restart giữ dữ liệu | PASS Linux, dùng volume nguồn cũ | [Runtime](docs/evidence/phase1/runtime-results.txt) |
| Desktop/mobile và thêm đơn | PASS Chromium/Linux; count có tăng do thao tác thật | [Browser](docs/evidence/phase1/browser-results.json), [desktop](docs/evidence/phase1/desktop.png), [mobile](docs/evidence/phase1/mobile.png) |

App chỉ SELECT/INSERT trên orders; DB không publish port host. Web localhost
dùng thêm bridge frontend, chưa là air-gap. Seed chỉ nạp khi volume rỗng; không
xóa dữ liệu để làm số dòng quay về 100. Môi trường/image digest ghi tại
[environment](docs/evidence/phase1/environment.json).

## 4. Phase 2 — backup nhất quán và SHA-256

Mã: `compose.backup.yaml`, `SOURCE/backup/` và `test_backup.py`.
Dump orders bằng single-transaction/quick/skip-lock-tables, không copy nóng volume.
Payload gồm SQL + metadata; manifest ngoài payload; Restic phải backup/check/
readback thành công trước result PASS. Dump không bao gồm user/grants.

| Run đã chạy | Snapshot đầy đủ | Dữ liệu và kết quả |
|---|---|---|
| p2-20261109T135131Z-742a4652976a | `5044d86ed493778891581971975300df590c94f17245707f566bab14bc852581` | 103 dòng, backup/check/readback PASS |
| p2-20261109T135429Z-99fc676302c1 | `7589d7b35dd8b5e1393d0e0f344615d4a28e0592a24a09d200167563f1ef367f` | 104 dòng, backup/check/readback PASS |

Bằng chứng: [successful runs](docs/evidence/phase2/successful-runs.json),
[integration](docs/evidence/phase2/integration.json),
[snapshot inventory](docs/evidence/phase2/snapshots.json),
[failed runs](docs/evidence/phase2/failed-runs.json),
[14 unit](docs/evidence/phase2/unit.txt).
Dump/copy lỗi và dump cắt cụt có result FAILED được giữ, không tạo snapshot PASS.
Backup PASS chưa chứng minh restore PASS. Legacy PS/SH còn lỗi staging/cleanup/
log; lịch Task Scheduler chưa có chứng cứ Windows.

## 5. Phase 3 — phục hồi vào môi trường sạch

Mã: `compose.restore.yaml`, `compose.recovery-tools.yaml`, `SOURCE/recovery/`.
Luồng: full snapshot/digest → Restic extract/check → SHA/metadata → target mới →
SELECT 1 → schema rỗng → import → user/grants → schema/toàn bảng → API đọc →
probe riêng → restart → cleanup/stable health. Không mount volume nguồn/seed.

Snapshot baseline ngày 10/11:
`42e4948c0d191d32afcd81fb0bca95fa83982f1d0f7162a4c3d6422ff8dc8b9c`;
manifest digest `f27cdaccf18416bd7533af3decbad4015076af3ce563994978013f6d0aeec225`.

| Kiểm tra | Kết quả / bằng chứng |
|---|---|
| Baseline nguồn độc lập, dump/check/readback | PASS: [baseline result](docs/evidence/phase3/baseline-result.json), [events](docs/evidence/phase3/baseline-events.jsonl) |
| Lần đầu p3-clean-20261110 | FAILED ở schema compare: [result](docs/evidence/phase3/first-failed-result.json), [chẩn đoán](docs/evidence/phase3/diagnostic-schema.json) |
| Lần mới p3-clean-v2-20261110 | PASS Linux: [result](docs/evidence/phase3/clean-result.json), [events](docs/evidence/phase3/clean-events.jsonl) |
| Kết quả clean run | 104 dòng nền + 1 probe riêng = 105 trên target; grants/API/restart PASS; nguồn về healthy/104 |
| Run/target đã tồn tại | Từ chối: [existing run](docs/evidence/phase3/existing-run-refused.txt), [guard Docker](docs/evidence/phase3/post-review-guard.json) |
| Snapshot cũ thiếu baseline | Từ chối nghiệm thu đầy đủ: [result](docs/evidence/phase3/legacy-refused-result.json) |
| Import SQL bị gián đoạn thật | NOT TESTED; nonzero-exit được kiểm bằng mock |

Lỗi schema ban đầu do MySQL bổ sung CHARACTER SET dư thừa. Chỉ chuẩn hóa khi
charset khớp bảng và vẫn giữ collation; sửa/test rồi dùng run/volume mới. Không
ghi lại FAILED thành PASS. Guard sau integration có kiểm riêng; không hồi tố
source fingerprint của lượt cũ.

## 6. Phase 4 — các kịch bản đã chạy

Main run `p4-main-20261110`, snapshot
`23a5aa61e65808bcae3680900a5f708f7c42ef1af64ef28ca5f2a842b36f6f78`,
manifest digest `eb7311dea5acca507f14b5d821c7d7599e3899833bf8d487aa07d53e4e9cd65b`.

Nguồn 104 dòng → canary có ACK → baseline/snapshot 105 dòng → ba tail ACK →
dừng DB, health 503 → restore stack sạch tại URL 8080. Target có 105 nền + 1 probe;
nguồn trả về 108 sau trial. Một checkpoint phục hồi, ba tail ACK chưa phục hồi,
duplicate = 0, uncertain = 0 trong profile tuần tự không retry.

| Kịch bản | Trạng thái | Bằng chứng |
|---|---|---|
| DB unavailable → clean restore | PASS Linux, một main trial | [Result](docs/evidence/phase4/main-result.json), [events](docs/evidence/phase4/main-events.jsonl), [ACK](docs/evidence/phase4/acknowledgements.json) |
| Dừng riêng web | PASS; khoảng 4.918264275 s, không restore snapshot | [Result](docs/evidence/phase4/web-control-result.json) |
| Sửa SQL copy trong work | PASS của negative test; từ chối trước import, không outage | [Result](docs/evidence/phase4/corrupt-result.json), [events](docs/evidence/phase4/corrupt-events.jsonl) |
| Mất host/kho từ bản sao độc lập | NOT TESTED | Chưa có storage độc lập |

Profile cloud dùng `--release-source-containers` để gỡ container đã dừng sau khi
lưu log; giữ volume nguồn/target và snapshot. Đây là điều kiện vận hành riêng,
không phải kiểm chứng giữ nguyên container hoặc mất host.

## 7. Phase 5 — số đo và kiểm toàn vẹn

[CSV chính thức](docs/evidence/phase5/export-20261110/metrics.csv) có bốn case:
main, web-only, corrupt và restore đầu FAILED. Không phải bốn main trials.

| Đại lượng của main trial | Giá trị quan sát |
|---|---|
| RTO | 54.198351197 s |
| Phát hiện | 1.986393601 s; một khoảng phát hiện của script |
| Backup age từ SNAPSHOT_VERIFIED | 0.091588006 s |
| Import SQL | 0.133908284 s |
| Tuổi commit cuối phục hồi từ send/ACK | 10.518407983–10.532435583 s; không phải exact RPO |
| ACK chưa phục hồi | 3/4 yêu cầu trong tập diễn tập; probe không thuộc tập này |
| Exact RPO / đạt mục tiêu | NOT TESTED |

Tính từ monotonic của cùng observer và đối chiếu summary; không lấy created_at
làm timestamp commit. Historical automated run chốt comparison ACK sau ready
396,797 ns. Không nói RTO lịch sử chứa bước chốt đó; `guided-v2` có thứ tự mới.

Hậu kiểm thực tế có timestamp riêng: [retained integrity](docs/evidence/phase5/retained-integrity.json),
[readback](docs/evidence/phase5/restic-readback.txt),
[events](docs/evidence/phase5/integrity-events.jsonl).
Restic check/readback PASS; target 105 nền + 1 probe, schema/toàn bảng/grants/
membership khớp. Không import lại hoặc tạo đơn trong hậu kiểm. `source_unchanged`
ở proof này chỉ so health/count, chưa so toàn bộ dữ liệu nguồn hai đầu.

Input corpus pin `258ebc8b7bddb7b5fd4ce9562a37889bf1c2a36a`;
source thực thi integration đối chiếu fingerprint tại
`dde61a2241de9bfd2b9f8138433b60f63d140cdd`. Re-export không tạo performance sample.

## 8. Phase 6 — runbook và lỗi ghi nhận

Ngày 15/11 review DOCX v1.0: còn placeholder backup, import tại nguồn/DB tạm,
COUNT-only và công thức RPO theo tuổi backup. Không chạy đoạn import nguồn đó.
Giữ DOCX gốc, soạn v1.1 với target sạch, checkpoint và xử lý lỗi.

Các bước chỉ đọc, DB-stop/start/restart và web control đã chạy trên Linux.
Toàn bảng/schema nguồn trước/sau controls bằng nhau, 108 dòng. Web control mới
5.050724009 s, không thay main RTO. SQL copy cục bộ bị từ chối bằng SHA; dùng
artifact đã trích xuất trước, chưa là Restic readback mới.

Preflight clean FAIL trước stop/target: free 138,743,808 B tại gate, ước lượng VFS
cần 2,136,002,336 B. Credit container cũng chưa đủ. Giữ 5 volume và 4 encrypted
snapshot file hash; không xóa dữ liệu để có chỗ.

Bằng chứng: [safe checks](docs/evidence/phase6/v1.0-safe-checks.json),
[DB control](docs/evidence/phase6/v1.0-db-control.txt),
[web result](docs/evidence/phase6/web-rehearsal-result.json),
[inventory trước](docs/evidence/phase6/inventory-before.json),
[sau](docs/evidence/phase6/inventory-after.json),
[gate](docs/evidence/phase6/post-review-release-result.json),
[verification](docs/evidence/phase6/verification.json).
76 unit PASS ở phase này; HTTP 201 malformed được sửa và kiểm bằng mock.
Clean restore mới, PowerShell/Task Scheduler và Minh Quân thực hành: NOT TESTED.

## 9. Phase 7 — hồ sơ và review cuối

Đã xuất [báo cáo Word](THESIS/BaoCao_Nhom08.docx) 17 trang render,
[PPTX](THESIS/ThuyetTrinh_Nhom08.pptx) 15 slide có Notes và runbook v1.1 Word
11 trang. Nguồn bài báo cáo nằm ở `THESIS/REPORT_GROUP08.md`, nguồn slide ở
`THESIS/reporting/slides.json`. DOCX dàn ý và runbook v1.0 của nhóm được giữ.

Review sửa direct restore/drill để kiểm host và Docker capacity trước POST/stop.
78 unit PASS tại commit `5d6c8328b621c5cc3e8d08d4a303da3d8bb3d686`.
Không có restore mới sau patch. Kiểm ZIP/XML, Notes, render/content/metric PASS
bằng LibreOffice/Linux; native Office NOT TESTED.
Bằng chứng: [QA](docs/evidence/phase7/artifact-qa.json),
[verification](docs/evidence/phase7/verification.json),
[test commands](docs/evidence/phase7/test-commands.json).

## 10. Bổ sung để nhóm thực hành Windows

Code commit `01396dd6b7efd5e1b84d78b963b0299f2b39982a` thêm `-Guided`,
`--trial-dir`, session helper và seal theo allowlist. `guided-v2` giữ một observer,
chờ Đa Minh INJECT, Minh Quân RECOVER/WEB_OK; tính cả bàn giao trong RTO. Có kiểm
source Git/LF, abort/uncertain và recheck toàn bảng sau chờ xem URL.

| Kiểm chứng ngày 16/11 | Kết quả và nguồn |
|---|---|
| Recovery/metrics/backup/app | 38 + 36 + 14 + 14 = **102 unit PASS**; [test commands](docs/evidence/windows-tooling-20261116/tests.json) |
| Guided/live exporter fixtures | PASS bằng mock/FixtureOS, không là Windows hoặc restore thật |
| Preflight Linux thật | FAILED vì thiếu disk, source_touched=false, target_created=false; [proof](docs/evidence/windows-tooling-20261116/read-only-verification.json) |
| Export run mới | PASS thao tác; giữ FAILED/N/A trong [CSV](docs/evidence/windows-tooling-20261116/gate-export/metrics.csv), không tạo RTO mới |
| Tài liệu thực hành Word/slide | 10 trang/7 slide, kiểm LibreOffice/Linux; [QA](docs/evidence/windows-tooling-20261116/artifact-qa.json) |
| Windows, Guided hai người, video, retest v1.1 | NOT TESTED |

## 11. Truy vết yêu cầu và việc còn lại

| Yêu cầu | Bằng chứng / tình trạng | Người phụ trách bước tiếp |
|---|---|---|
| Flask/MySQL, seed, quyền, health/persistence | Phase 1 Linux PASS | Đa Minh kiểm Windows, Minh Quân đối chiếu |
| Backup nhất quán + full snapshot + SHA | Phase 2/3 Linux PASS | Đa Minh tạo receipt mới trên máy Windows |
| Target sạch, không nguồn/seed, import/grants | Phase 3 Linux PASS | Minh Quân thực hành Windows, Đa Minh quan sát |
| Schema/toàn bảng/API/probe/restart | Phase 3/4 Linux PASS | Minh Quân xác minh trước/giữa/sau probe |
| Corrupt/unsafe target từ chối, log lỗi/cleanup | Có test thật theo phạm vi và unit; chưa mọi lỗi runtime | Đa Minh lưu negative tests và exit code |
| Tài nguyên phục hồi mới | Cloud FAIL gate | Đa Minh chuẩn bị đủ host/Docker disk |
| Runbook khớp lệnh, bàn giao, URL phục vụ | Mã Guided và hướng dẫn có; Windows NOT TESTED | Minh Quân làm theo HUONGDAN, Đa Minh ghi trợ giúp/lỗi |
| Metric/CSV run mới | Unit và export gate FAILED thật PASS thao tác | Đa Minh export đúng run; hai người đối chiếu |
| v1.0 → lỗi thật → v1.1 → retest | Chưa có lượt độc lập Windows | Minh Quân sửa theo quan sát, giữ v1.0 trong Git |
| Biên bản bàn giấy, video, Sheets links | Chưa có bằng chứng đầy đủ của hai người | Cả hai thực hiện, không ký thay |
| Word/PPTX và truy xuất số liệu | Artifact Linux PASS; Windows Office NOT TESTED | Minh Quân cập nhật sau thực hành, mở kiểm trên máy nộp |
| Exact RPO, target RTO/RPO, storage độc lập | NOT TESTED | Chỉ bổ sung khi có yêu cầu, mục tiêu và môi trường phù hợp |

Yêu cầu ngoài MVP trong [Google Sheets](https://docs.google.com/spreadsheets/d/1akuMwhM-N3BXN0V8xOcPl2OdIb3PAh_oW5JUYyJivjI/edit):
mất máy chủ, mất tài khoản quản trị, backup trực tuyến bị sửa, bản sao cách ly còn
nguyên. Chưa xác nhận cả bốn bắt buộc; đều NOT TESTED theo đúng nghĩa đó. DB-stop
không thay host-loss, SQL copy hỏng không thay repo bị sửa, thư mục cùng ổ không
thay storage độc lập. Điều kiện và giới hạn chi tiết nằm ở LUU_Y_THUC_NGHIEM.

## 12. Quy ước cập nhật sau mỗi lượt

Mỗi entry mới ghi ngày UTC (trình bày địa phương UTC+7 nếu cần), OS/build/tool,
Git commit, người thao tác/quan sát, run ID, snapshot/digest, lệnh/exit code, loại
test, kết quả và link raw. Giữ FAILED và ảnh gốc. Chỉ cập nhật PASS khi đã kiểm
chính lượt đó; unit/mock không là restore thật, Linux không là Windows.

Các báo cáo phase, review, nhật ký/phân công và kế hoạch Windows rời trước đây
được hợp nhất trong ba tài liệu gốc ngày 16/11. Hướng dẫn module/runbook Markdown
trùng được đưa vào HUONGDAN; finding đưa vào LUU_Y. Lịch sử đầy đủ còn trong Git
tại `a304b9ee843191119d801de789366a4fd2b2816e`. Bằng chứng gốc, mã nguồn và các bản
Office/PDF lịch sử giữ nguyên; đường dẫn cũ trong artifact lịch sử phải đọc theo
commit đó. Khi thực hành dùng HUONGDAN hiện hành, không tìm lệnh ở báo cáo cũ.

Kiểm tra đợt hợp nhất: loại 34 Markdown trùng/trống, đối chiếu 213 file mã nguồn,
evidence và artifact lịch sử giữ nguyên byte; không còn link Markdown hỏng hoặc
tham chiếu tài liệu bị xóa trong các nguồn đang dùng. Chạy `python3 -B -m unittest
discover -s SOURCE/tests -p 'test_*metrics.py' -v`: 36 tests PASS. Hai builder
chạy thành công trong thư mục tạm, bốn output DOCX/PPTX kiểm ZIP/XML PASS; không
ghi đè binary lịch sử. Đây là kiểm tài liệu/tái lập, không là restore, kiểm layout
mới hoặc nghiệm thu Windows. Các README/manifest trong evidence giữ nguyên theo
commit lịch sử của chính chúng, không sửa lại để khớp cấu trúc tài liệu mới.


## 13. Chuẩn bị buổi thực hành ngày 17/11/2026

Code commit `f3b6ca5d06ceb33c54d43bf4172487452b4decc1` bổ sung guard init:
phát hiện volume/container nguồn cũ trước khi tạo credential, không ghi đè dữ
liệu. Guard mới được kiểm thứ tự tĩnh và giữ nguyên byte phần sinh config;
chạy init native Windows vẫn NOT TESTED.

Backup/restore mới lưu `source-dataset.jsonl`/`restored-dataset.jsonl` ngoài
payload Restic, trước tail/probe. Seal theo allowlist; exporter đối chiếu byte
SHA, toàn bộ baseline, capture events/thứ tự và ACK membership từ dataset target.
CSV có dataset_evidence_status, hai hash và row count. Lượt cũ thiếu sidecar giữ
NOT TESTED, không tạo bổ sung. Đây là capture cục bộ, không là fresh DB recheck,
chữ ký hoặc storage độc lập. Restore end-to-end trên code mới vẫn NOT TESTED.

| Kiểm chứng thật ngày 17/11 | Kết quả | Bằng chứng |
|---|---|---|
| Recovery/metrics/backup/app | 41 + 47 + 14 + 14 = **116 unit PASS**, không skip trong môi trường này | [Commands và metadata](docs/evidence/windows-preparation-20261117/tests.json), cùng các log unit |
| New sealed dataset fixtures | PASS: tất cả rows, event binding, sai byte/phase/membership bị từ chối | [Metrics log](docs/evidence/windows-preparation-20261117/metrics-tests.txt); dữ liệu/chronology fixture, không là restore thật |
| Clean preflight Linux thật | FAILED do thiếu host disk; source_touched=false, target_created=false | [Result](docs/evidence/windows-preparation-20261117/p3-windows-prep-gate-20261117/result.json) |
| Source trước/sau gate | Full schema/row hash, health và container lifecycle giữ nguyên | [Read-only proof](docs/evidence/windows-preparation-20261117/read-only-verification.json) |
| Export đúng gate mới | Exit 0; giữ trial FAILED, không sinh RTO giả | [CSV](docs/evidence/windows-preparation-20261117/gate-export/metrics.csv) |
| Build hướng dẫn bản mới trong work tạm | DOCX/PPTX build và ZIP/XML PASS, không kiểm layout/native Office | [Smoke](docs/evidence/windows-preparation-20261117/guide-smoke.json) |
| Giữ hồ sơ cũ | 177 file evidence/Office/ảnh giữ nguyên byte so với be0a0d7 | [Preservation](docs/evidence/windows-preparation-20261117/preservation.json) |
| Native Windows/Guided hai người/video/retest | **NOT TESTED** | Nhóm thực hiện theo HUONGDAN, lưu raw và biên bản thật |

HUONGDAN v1.0 được mở rộng theo ba buổi để giảm tải: lấy đúng branch/daemon,
file đầu tiên, setup mới/cũ, sổ run qua các bước, Phase 3 trước main, cách mở lại
terminal, video và đóng gói năm minh chứng. Các lệnh PowerShell/đóng gói đã đối
chiếu tên file/cú pháp tĩnh, chưa có bằng chứng chạy Windows; không đổi nhãn thành
v1.1 trước buổi Minh Quân thực hành và vòng ghi lỗi/cải tiến/retest thật.
