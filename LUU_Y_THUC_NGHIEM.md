# Các lưu ý trước và trong thực nghiệm — Nhóm 08

Cập nhật 17/11/2026 (UTC+7). [Báo cáo các phase](BAO_CAO_CAC_PHASE.md) ghi kết quả;
[HUONGDAN](HUONGDAN.md) là đầu mối lệnh chạy. Bản này tập hợp cấu hình, điều kiện
GO/NO-GO, finding và giới hạn còn mở; không tạo thêm một runbook song song.

## 1. Cấu hình và đường dẫn thật

| Thành phần | Giá trị |
|---|---|
| Compose nguồn | project group08-lab; services db, web |
| DB/bảng/engine | MySQL 8.4.7; lab_config.orders; InnoDB |
| Sáu cột | id, customer_alias, product_name, quantity, unit_price_vnd, created_at_utc |
| Quyền app | group08_app@%; SELECT/INSERT chỉ orders |
| Web | 127.0.0.1:8080 → container 8000; đọc WEB_PORT cục bộ nếu đã đổi |
| DB port | 3306 nội bộ; không publish host |
| Network | db trên lab internal; web trên lab + frontend bridge |
| Volume nguồn | group08-lab_db_data → /var/lib/mysql; là DB đang dùng, không phải backup |
| Secret host | secrets/db_root_password.txt, db_app_password.txt, db_backup_password.txt, restic_password.txt |
| Kho Restic | backups/restic host → /data/restic của service backup |
| Artifact backup | backups/runs/<p2-id>/payload/database.sql và metadata.json |
| Manifest/receipt/log | backups/runs/<p2-id>/manifest.json, result.json, restic.log |
| Target | group08-restore-<run-id>; volume <project>_restore_data, network riêng |
| Secret target | secrets/restore/<run-id>/root.txt, app.txt; giữ bản gốc |
| Evidence run | work/recovery/<run-id>/events.jsonl, result.json, acknowledgements.json, evidence-manifest.json |
| Session Windows | work/sessions/<session-id>/powershell.txt và CSV ghi chép |
| Evidence công bố | docs/evidence; không bao gồm SQL plaintext/secret |

Alias chỉ LAB-..., sản phẩm Notebook/Pen/Folder, số lượng 1–100 và giá nguyên VND.
Clone mới không tạo Docker daemon/volume mới. Init nay từ chối khi phát hiện
`group08-lab_db_data` hoặc container nguồn cũ mà checkout chưa có config; tìm
secret gốc, không tạo password mới hoặc xóa volume. Guard mới chưa chạy native
Windows. Trước thao tác lifecycle phải kiểm đúng local Docker Desktop context;
controller chưa cưỡng chế allowlist daemon. HUONGDAN có các lệnh kiểm chỉ đọc.

100 seed chỉ áp dụng volume rỗng lần đầu. Smoke test/POST thêm dòng thật trong
lab; không reset seed. Mạng frontend không chặn outbound Internet; chưa air-gap.

## 2. Các điều kiện bắt buộc

1. Đúng nhánh/commit có recovery Guided và exporter --trial-dir. Source Guided
   phải khớp byte Git, kể cả LF/CRLF; dừng trước mutation nếu không khớp. Không
   reset/force checkout để mất thay đổi; lưu và review thay đổi trước.
2. Windows 10, Docker Desktop Linux containers, Compose v2 hỗ trợ --wait,
   Python host >=3.10, Git. PowerShell native/Task Scheduler/Office cần bằng chứng
   riêng. Unit trong container hoặc LibreOffice/Linux không cấp Windows PASS.
3. Giữ .env/secret gốc khi đã có volume. Init không đổi mật khẩu MySQL đã có.
   Mất password Restic thì tìm bản gốc, không reset kho. Không in secret/inspect
   environment, đặt password trong argv, quay màn hình secret hoặc commit SQL.
4. Nguồn healthy, app grants đúng và chỉ một người điều khiển. Không POST/DDL,
   client ghi, scheduler hoặc backup khác trong cửa sổ baseline/diễn tập. Khóa
   controller chỉ chặn controller cùng host/user/daemon, chưa chặn công cụ ngoài.
5. Host và filesystem Docker cùng đủ chỗ. Clean preflight PASS trước restore;
   web-control gate chỉ cấp đối chứng web. Tăng disk/chọn lab đủ tài nguyên nếu
   FAIL; không xóa DB volume, snapshot hoặc prune để cố vượt gate.
6. Chỉ full snapshot ID 64 hex + digest tin cậy, không latest. Receipt và SHA
   hợp lệ trước import; target phải mới, schema zero table, không seed/source mount.
7. Readiness SELECT 1 không phụ thuộc orders. Mọi lỗi SQL import phải FAIL,
   không --force, không import lại target dở. Dump orders không chứa user/grants,
   controller tạo lại app role và kiểm SELECT/INSERT.
8. Đối chiếu schema và mọi dòng bằng baseline nhất quán; API newest 100 và COUNT
   chỉ hỗ trợ kiểm, không thay toàn bộ nội dung. Đọc trước probe; probe riêng;
   restart vẫn giữ base/probe; cleanup/stable health/URL phải được xác nhận.

Baseline mới capture toàn bảng trước/sau dump khi web dừng, đã drain transaction,
không admin writer/DDL; được nhúng metadata và hash/readback cùng SQL. Chuẩn
orders-jsonl-v1 sắp ID tăng, sáu cột, exact integer/UTF-8/LF/UTC microsecond.
Snapshot cũ thiếu baseline có thể kiểm byte, nhưng không dùng target vừa restore
làm baseline độc lập để nghiệm thu nghiệp vụ. Nguồn còn tin cậy thì tạo backup mới;
không còn nguồn/baseline thì ghi giới hạn NOT TESTED.

## 3. Finding cần biết

| ID | Vị trí | Xác nhận/phạm vi | Xử lý và điều kiện đóng |
|---|---|---|---|
| F01 | SOURCE/app/app.py, static/app.js | OPEN: chưa idempotency/unique business request; retry sau mất ACK có thể trùng. Chưa có real retry benchmark | Profile hiện tại tuần tự, không retry. Trước mở retry cần key unique, payload match/replay, test lost response/concurrent duplicate; Đa Minh, khoảng 2–4 giờ + migration/test |
| F02 | SOURCE/backup/backup.ps1, backup.sh, backup.py | OPEN: đường dẫn script DB tạm chung, cleanup có thể không làm overall FAIL, một số Restic action thiếu log đích | Chỉ Setup tuần tự khi cần; backup thực nghiệm dùng recovery controller. Trước concurrency/Scheduler: staging theo run, exit cleanup/log đủ; Đa Minh, khoảng 2–3 giờ + Windows |
| F03 | SOURCE/app/requirements.txt, Dockerfile | OPEN theo review trước: Flask 3.1.2; advisory GHSA-68rp-wp8r-4726, bản vá được ghi là 3.1.3. App không dùng session/no-store chỉ giảm phạm vi | Xác minh advisory hiện tại rồi nâng pin/rebuild, app unit + HTTP/recovery smoke; chưa gọi đã vá vì chỉ đổi tài liệu |
| F04 | SOURCE/metrics/verify_retained.py | OPEN: stop nguồn trước resource gate; source_unchanged chỉ so health/count | Không dùng action này trong workflow hiện tại. Nếu mở lại: gate trước stop, full baseline hai đầu, regression cùng count khác nội dung + integration đủ tài nguyên; Đa Minh 1–2 giờ + lab |
| F05 | SOURCE/recovery/controller.py validate_source | Giới hạn: restore/drill đòi nguồn running/healthy lúc bắt đầu | Dùng scripted drill có chuẩn bị. Incident nguồn hỏng từ trước cần thiết kế guard/ownership/quiescence riêng và test; không bỏ gate hoặc import vào source |
| F06 | Kho/secret/journal trên host | Giới hạn: chưa có storage độc lập, append-only/immutable hoặc host/repo-loss test | Chỉ kiểm mất kho khi đã có bản sao ở thiết bị/vị trí độc lập được verify. Khác thư mục trên cùng ổ chưa đủ |
| F07 | run_lab.ps1, start_session.ps1, register_daily_backup.ps1 | NOT TESTED native Windows; lập lịch chưa là bằng chứng task thực sự chạy | Theo HUONGDAN lưu transcript/exit/result trên máy nhóm. Scheduler để sau F02 và kiểm LastTaskResult cùng run mới |
| F08 | Prototype verifier nhánh starter | Finding cũ root-symlink/JSON-list chưa đóng trên nhánh này | Pipeline dùng backup.py scope hai file đã có test. Nếu dùng lại prototype phải patch/test riêng |

Đã sửa có regression theo phạm vi: ACK 201 malformed/exact-int → uncertain,
secret presence/format guards, direct restore/drill kiểm cả host và Docker trước
POST/stop, và exporter từng run. Các test này là mock/fixture; chưa thay restore
thật trên mã mới nhất. File/dòng cũ phụ thuộc commit; dùng tên hàm để tìm mã hiện tại.

## 4. Đọc số đo và trạng thái đúng

| Đại lượng | Định nghĩa |
|---|---|
| T0 | FAULT_REQUESTED ngay trước gửi lệnh stop DB; web control dùng stop web |
| Tready automated-v1 | SERVICE_VERIFIED sau dữ liệu/API/probe/restart/cleanup/stable health; comparison ACK chốt sau ready |
| Tready guided-v2 | Sau comparison ACK, WEB_OK của Minh Quân, recheck dữ liệu/API và stable health |
| RTO | (Tready_ns − T0_ns)/1e9, cùng observer; return-source sau trial nằm ngoài |
| Phát hiện | FAULT_DETECTED − T0; một khoảng phát hiện script, không tự coi là MTTD trung bình/IDS |
| Cô lập | N/A nếu chưa định nghĩa và kiểm chứng hành động cô lập riêng; stop lab không tự thay cô lập tài khoản/mạng |
| Backup age | T0 − SNAPSHOT_VERIFIED; khác thời điểm capture/commit |
| Bounded recovery lag | [T0 − ACK, T0 − first-send] của request cuối phục hồi, khi tuần tự/recovered prefix/không duplicate |
| Dữ liệu chưa phục hồi | ACK trước T0 không có trên snapshot target; tách probe, duplicate và uncertain |
| Exact RPO / đạt target | NOT TESTED khi thiếu commit timestamp độc lập hoặc mục tiêu chưa được chọn |

Không dùng created_at_utc làm bằng chứng commit độc lập. Không đặt target sau
khi đã thấy số đo. Không trộn guided-v2/automated-v1 hoặc web-only/main để tính
trung bình. Chỉ một main Linux, không suy ra thống kê từ bốn dòng CSV.

PASS kỹ thuật phục hồi khác đạt mục tiêu RTO/RPO. FAIL/ABORTED sau fault chưa
ready là censored, không gán RTO=0 hoặc dùng thời điểm abort làm ready. Corrupt
check không outage → RTO/RPO N/A; Phase 3 không incident T0 → RTO N/A. Negative
test PASS có thể đi kèm candidate integrity FAIL dự kiến.

## 5. Hủy, lỗi và bằng chứng

Mất ACK/201 sai/interrupt giữa POST là uncertain: dừng profile đo, giữ send/error,
không retry. Điều tra chỉ đọc theo alias/ID/toàn bảng; alias chưa unique nên không
tự suy ra đúng một commit. SIGKILL/mất điện có thể thiếu TRIAL_ENDED/seal; ghi
lượt không hoàn tất, không tự điền sự kiện để exporter chấp nhận.

Giữ run ID/target dở để điều tra, dùng ID/target mới sau đó. Khóa còn sau SIGKILL
phải kiểm process/PID trước xử lý. Kiểm `status` riêng `return_source_status`;
trial PASS nhưng return-source FAILED vẫn là lỗi vận hành, chưa chạy tiếp.

Chỉ dừng target có label owner đúng run. Nếu khôi phục shell, dùng secret/cổng
gốc của target để nhả URL trước bật nguồn. Không tự import SQL vào nguồn. Quy trình
phục hồi shell từng bước ở HUONGDAN; nếu thiếu chỗ để trả nguồn, ghi lỗi tài nguyên.

Seal cục bộ chỉ băm allowlist, không chữ ký hoặc storage độc lập. Review/pin Git
receipt, manifest và raw đã che phù hợp; SQL/secret giữ ngoài Git. Bản chia sẻ
đã che phải là bản riêng, không sửa raw rồi băm lại để làm PASS. Manifest lịch sử
tham chiếu source tại đúng commit cũ; source hiện nay thay đổi không được sửa proof cũ.

Lượt mới có dataset_evidence_version=1 lưu hai JSONL canonical tương ứng toàn
bộ baseline trước tail/probe. Export kiểm SHA/row count/capture events và đối
chiếu ACK membership với capture target; không chỉ tin summary. Không chỉnh
JSONL bằng Excel hoặc trộn probe/tail vào baseline. Không suy ra fresh DB/Restic
PASS từ việc đọc sidecar; lượt cũ thiếu sidecar giữ NOT TESTED. JSONL vẫn cần
review dữ liệu giả trước công bố. Thứ tự cột là id/customer_alias/product_name/
quantity/unit_price_vnd/created_at_utc.

Export --trial-dir đọc SQL byte nếu artifact private còn, thiếu thì fresh artifact
NOT TESTED. Nó không chạy Restic/DB mới. Đọc lại proof cũ không tạo fresh PASS.
Proof Phase 5 nguồn unchanged chỉ health/count; full hash nguồn hai đầu có riêng
ở Phase 6. Tái xuất CSV không tạo performance trial.

## 6. Phạm vi bảo vệ và hồ sơ

Lab chứng minh phục hồi sau tác động mất khả dụng và từ chối đầu vào sai SHA.
Chưa chứng minh phát hiện/ngăn ransomware, giải mã tệp, mất cả host, mất quyền
quản trị, kho chính bị sửa hoặc backup cách ly. Bốn tình huống mở rộng trong
Sheets chờ xác nhận; không điền PASS bằng kịch bản khác tên.

DOCX v1.0 của Minh Quân còn các bước cũ không phù hợp, giữ làm lịch sử. Lệnh chạy
hiện tại chỉ lấy từ HUONGDAN. Đóng băng v1.0 trước lượt đầu bằng commit/hash;
Minh Quân cập nhật v1.1 dựa trên lỗi/khó khăn thật, ghi trợ giúp đã nhận và retest
run ID. Không có lỗi thì ghi đúng, không tạo lỗi giả hoặc ký thay thành viên.

Giữ video đầy đủ; bản demo 3–5 phút phải chú thích tua/cắt, không lấy thời lượng
video biên tập làm RTO. Cập nhật số liệu trong nguồn Word/PPTX/Sheet rồi đối chiếu
CSV/manifest. Mở kiểm font/bảng/Notes trên Office Windows; render Linux chưa thay
bước đó. Chỉ share folder hồ sơ đã review, không cả secrets/backup/work.

## 7. Công cụ và tài liệu tham khảo

Thực nghiệm dùng Docker, Git, PowerShell, Python host >=3.10, MySQL/Restic trong
image. OBS và Office dùng quay/trình bày; VS Code là editor tùy chọn. Không cần
VPS/SSH, systemctl/ufw/nginx cho lab Docker Desktop hiện tại.

Phiên bản và giấy phép cụ thể: [danh mục phần mềm](SOFT/README.md).
Restic chính thức: [backup v0.18.1](https://github.com/restic/restic/blob/v0.18.1/doc/040_backup.rst),
[working with repos](https://github.com/restic/restic/blob/v0.18.1/doc/045_working_with_repos.rst).
Compose tham khảo [docker/awesome-compose](https://github.com/docker/awesome-compose/tree/master/nginx-flask-mysql).
Chỉ tham khảo thiết kế/API/tài liệu; không sao chép nguyên dự án. rest-server,
Kopia, pgBackRest/MinIO là tham khảo, chưa dùng để tạo bằng chứng lab này.
