# Review Phase 0–5 trước Phase 6 — 15/11/2026

## Phạm vi và quyết định

Review base `068e1f4f70f75a9246889ce320a2c28b258bb92e`, nhánh mới
`codex/group08-phase6-runbook-20261115`. Đã đọc README, Compose, app/JS/dependencies,
backup/dump/PS/shell/scheduler, recovery/metrics, các suite test, báo cáo Phase 1–5,
Runbook v1.0 DOCX và addendum. DOCX được trích văn bản để đối chiếu, không sửa gốc.
Không có AGENTS.md, docs/IMPLEMENTATION_PLAN.md hoặc docs/PROMPTS_CODEX_WORK.md
trên checkout này; không suy đoán nội dung các nhánh khác. Không đọc/cập nhật Sheet
trong lượt này và không gọi đây là review tuân thủ toàn bộ Sheet.

Main vẫn `37addd7` (Phase 2); PR #5/#6 vẫn draft/open tại lúc kiểm tra. PR Phase 6
phụ thuộc nhánh Phase 5; không tự merge hoặc thay nhánh của các PR trước.

**GO** cho review, bước v1.0 chỉ đọc, đối chứng dịch vụ trên lab hiện tại và tái
xuất corpus lịch sử. **NO-GO** cho lượt clean restore/main drill mới: host/Docker
chỉ còn khoảng 132 MiB, không đạt resource gate. Bằng chứng Phase 3/4 Linux cũ
vẫn được giữ nhưng không biến lượt Phase 6 chưa chạy thành PASS. Windows và lượt
độc lập Minh Quân: **NOT TESTED**.

## Finding và xử lý

Dòng dưới đây là ở mã nguồn sau patch Phase 6; DOCX dùng số đoạn P vì không có
dòng text ổn định. “Xác nhận code” không có nghĩa đã tái hiện lỗi trên DB thật.

| ID / mức | Vị trí và bằng chứng | Phân loại / tái hiện | Sửa tối thiểu / điều kiện đạt | Phụ trách, công sức, phụ thuộc |
|---|---|---|---|---|
| F601 / High, chất lượng runbook | `Runbook_v1.0.docx` §4 P87–90, §9.2 P140–159; `v1.0-safe-checks.json` pin SHA DOCX | Xác nhận tài liệu: placeholder BACKUP_DIR, import vào nguồn/DB tạm cùng stack, không phải clean restore. Không chạy các bước đó | Giữ v1.0, viết v1.1 với đường dẫn/receipt thật và target độc lập. Nghiệm thu: reviewer đi hết workflow sạch trên môi trường đích; hiện NOT TESTED lượt mới | Minh Quân review, Đa Minh kiểm lệnh; 1–2 giờ tài liệu, cần disk/Windows cho rehearsal đầy đủ |
| F602 / High, tính đúng ACK | `SOURCE/recovery/controller.py:394`, `SOURCE/tests/test_recovery.py:79`; `recovery-before-fix.txt` | **Đã tái hiện bằng mock**: 201 thiếu order gây KeyError/TypeError mà không REQUEST_UNCERTAIN; bool ID có thể được ACK. 22 tests trước fix: 1 failure/3 errors | **FIXED**: kiểm canonical row/kiểu exact int/payload; ghi uncertain, dừng không retry. 27 unit cuối PASS; HTTP lỗi dạng này trên DB thật NOT TESTED | Đa Minh; đã xử lý, không thay schema/API idempotency |
| F603 / High, tài nguyên | `SOURCE/recovery/controller.py:357`; `clean-gate-result.json`, `release-gate-result.json`, `environment.json` | **Xác nhận thật**: free 138,743,808 B lúc gate; ước lượng VFS cần 2,136,002,336 B. Credit stopped containers 1,867,566,880 B vẫn thiếu. Hai gate exit 1, source_touched/target_created=false | Chặn trước outage/target; thêm preflight đọc host và Docker. Không dùng credit host làm free space giả của Docker VM. Mở rộng disk hoặc dùng lab khác đã chuẩn bị; clean gate phải PASS trước restore mới | Đa Minh chuẩn bị storage, Minh Quân ghi gate; 30–90 phút môi trường + 30–60 phút rehearsal; không xóa volume/snapshot |
| F604 / Medium, chuẩn bị | `SOURCE/recovery/controller.py:176`, `:184`, `:199`; `run_lab.ps1:1` | Trước đây chưa kiểm secret/kho đầy đủ trước mutation; xác nhận code, không tái hiện bằng cách bỏ secret thật | **FIXED theo phạm vi**: presence/format/symlink guard trước action cần kho; preflight đọc full source/API/grants/disk. Restore không đòi secret của dump account. Unit fixture và real gates PASS; password đúng/Restic integrity vẫn do archive kiểm | Đa Minh; đã xử lý; Windows launcher NOT TESTED |
| F605 / Medium, retry | `SOURCE/app/app.py:111`, `:147`; `SOURCE/app/static/app.js:66` | Xác nhận code không có idempotency key/unique business request. Mất ACK rồi người dùng retry có nguy cơ thêm hai row; real lost-ACK retry chưa chạy lại | **OPEN**, không dùng retry trong diễn tập. Nếu thêm profile retry: key unique + đối chiếu payload và replay cùng kết quả; test lost response/concurrent duplicate phải chỉ một logical commit | Đa Minh; 2–4 giờ + DB migration/test; chưa chặn profile tuần tự không retry |
| F606 / Medium, backup cũ | `SOURCE/backup/backup.ps1:15,43,70`, `backup.sh:10,49`, `backup.py:104,191,204` | Xác nhận code: script DB tạm chung; cleanup chưa kiểm/suppressed; init/snapshots/check thiếu log đích. Không chạy concurrency/cleanup fault trên DB thật hôm nay | **OPEN**; v1.1 dùng recovery controller có staging theo run và kiểm cleanup. Trước schedule/concurrency: staging riêng, lỗi cleanup giữ primary + overall nonzero, log cho mọi Restic action; test mock native exit và Windows thật | Đa Minh code / Minh Quân Scheduler; 2–3 giờ code/test + Windows; không chạy entrypoint cũ song song |
| F607 / Low hiện tại, dependency | `SOURCE/app/requirements.txt:6`; `environment.json` xác nhận Flask installed 3.1.2 | Chưa cập nhật. Advisory GHSA-68rp-wp8r-4726 đã đánh giá ở review Phase 5; app không dùng session, response no-store. Không có CVE/image scan mới trong lượt này | **OPEN**; nâng bản vá tương thích (advisory cũ ghi fixed 3.1.3), rebuild image, app tests + HTTP/recovery smoke. Chưa sửa pin mà để image cũ giả đã cập nhật | Đa Minh; 30–60 phút + image rebuild; cần disk trước |
| F608 / Medium, portability/storage | `SOURCE/recovery/run_lab.ps1`, `SOURCE/backup/register_daily_backup.ps1`, `compose.backup.yaml` | Windows/Task Scheduler chưa có transcript thật; backup/password/observer cùng host. Không có bản sao độc lập | **NOT TESTED** các kịch bản Windows, host-loss/repo-loss. Giữ giới hạn trong runbook; chạy Windows thật và chỉ thử mất kho khi có bản sao ở vị trí/thiết bị độc lập | Hai thành viên; 1–2 giờ Windows, storage phụ thuộc thiết bị; không chặn đối chứng Linux |
| F609 / Medium, phạm vi metric | `SOURCE/metrics/evidence.py:16,18`; `export_metrics.py:128` | Xác nhận exporter có registry bốn case lịch sử/pin Git cố định; không tự nhận các trial Phase 6 mới | Không gọi CSV tái xuất là trial mới. Với dataset mới, cần workflow đăng ký evidence/pin đã review và test trước khi tổng hợp. **Chấp nhận phạm vi hiện tại** | Đa Minh + Minh Quân đối chiếu; 1–2 giờ nếu mở rộng corpus, để sau khi có trial mới |
| F610 / Medium, phạm vi recovery | `SOURCE/recovery/controller.py:162`, `:531` | Xác nhận `restore` vẫn yêu cầu nguồn running/healthy lúc bắt đầu; phù hợp drill scripted từ nguồn khỏe, không là entrypoint cho sự cố nguồn đã hỏng ngoài drill | Ghi rõ v1.1 là runbook diễn tập có chuẩn bị. Không hướng dẫn import thủ công vào source để vượt gate. Nếu mở rộng incident recovery thật: thiết kế source-unavailable guard/ownership/quiescence riêng và test âm | Hai thành viên; scope hiện tại chấp nhận, ngoài mục tiêu rehearsal scripted hôm nay |
| F611 / Medium, hồ sơ | Các file AGENTS/plan/prompts nêu trên thiếu; `docs/NHAT_KY_THUC_NGHIEM.md`, `KICH_BAN_DEMO.md`, `PHAN_CONG_CONG_VIEC.md`, `THESIS/runbook/Runbook_template.md` đều 0 B | Xác nhận filesystem. Báo cáo/evidence theo phase có nội dung, nhưng các file đầu mối chưa nối lại | Không tự tạo lịch sử nhóm hoặc nội dung file thiếu. Phase 6 tạo review/runbook/results riêng; Phase 7 nhóm đồng bộ nhật ký/báo cáo/phân công từ evidence thật | Minh Quân, Đa Minh đối chiếu; 1–2 giờ tài liệu, không chặn control test |
| F612 / Low, lệnh test | `SOURCE/tests/README.md:11,101` | Thử discover toàn bộ trên host lỗi import PyMySQL. Đây là thiếu dependency host của lệnh đó, không phải app unit FAIL trong image | Dùng pattern và runtime đúng README: app trong web container, backup/recovery/metrics stdlib theo suite. 14+14+27+21 = 76 tests PASS; không ghi broad discovery thành PASS | Đa Minh; đã sửa cách chạy/ghi nhận; không cài thêm dependency host để che lệnh sai |

## Đối chiếu Phase 0–5

| Phase | Bằng chứng hiện có | Kết luận review |
|---|---|---|
| 0 | Prototype/audit chưa trong main/nhánh Phase 5; report cũ ghi symlink/JSON-list finding | Không dùng prototype làm verifier hiện hành; chưa đóng finding bằng code mới không liên quan |
| 1 | App/Compose thực; HTTP healthy 108, app unit 14; DB-stop/restart control Phase 6 | PASS phạm vi Linux đã chạy; LIMIT 100 là API window, không full baseline |
| 2 | Bốn file snapshot giữ nguyên, artifacts hiện có verify SHA; backup unit 14 | Backup cũ không tự chứng minh restore; entrypoint/schedule findings còn mở |
| 3 | Clean restore schema/data/grants/API/restart trong evidence cũ; có cả FAILED thật | Historical Linux PASS còn giá trị; clean restore mới Phase 6 NOT TESTED vì disk |
| 4 | Main/control/corrupt raw events cũ, thêm web control mới và local corrupt copy check | Không dùng dừng/start nguồn hoặc copy check làm bằng chứng clean restore mới |
| 5 | 21 metrics unit, tái xuất bốn case từ raw pin, SHA input/output | Tái lập số cũ PASS; chưa target/exact commit RPO/ba main trials |

## Giới hạn review

Đây là review kỹ thuật và rehearsal có giới hạn tài nguyên, không là pentest,
full dependency/image audit, kiểm chứng anti-ransomware hay diễn tập mất host.
Patch ACK được kiểm bằng mock và regression; các control chạy thật không gây lost
ACK. Source code thực thi control/gates ban đầu là `3a71b30`; resource hardening
sau đó là `de7b2ad` và được kiểm lại bằng gate/unit riêng, không sửa timing cũ.
Chi tiết lệnh và trạng thái nghiệm thu ở `docs/PHASE6_RESULTS.md`.
