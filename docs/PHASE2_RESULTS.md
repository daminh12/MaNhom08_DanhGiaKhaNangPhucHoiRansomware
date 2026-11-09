# Phase 2 — Backup MySQL nhất quán + Restic, ngày 09/11/2026

## Kết luận và phạm vi

**PASS trên Linux/cloud** cho workflow backup `lab_config.orders`: dump
transaction InnoDB, manifest SHA-256, snapshot Restic 0.18.1, kiểm tra đọc toàn
bộ repository và đối chiếu byte đọc lại từ đúng snapshot. Có hai run thành công
và đầy đủ log; đầu vào hỏng không tạo trạng thái PASS hoặc snapshot mới.

**Windows 10 / PowerShell / Task Scheduler: NOT TESTED trực tiếp.** Có hướng dẫn
và script để nhóm chạy trên máy demo; chưa khẳng định lịch hàng ngày đã chạy.
**Restore SQL vào DB sạch và xác minh ứng dụng: NOT TESTED**, thuộc Phase 3.
Không có số đo RTO/RPO thực tế trong hồ sơ này.

Nhánh `codex/group08-phase2-backup-20261109` tách từ main
`f6653eeb7db55ff73889d2f8c0ccb4b2d5834603`, sau khi nhóm đã merge PR #3 và cập
nhật Runbook sang Docker. Không sửa DOCX của Minh Quân. Gửi PR để review,
không tự merge main.

## File tạo/chỉnh sửa và cách chạy

| File/nhóm | Thay đổi |
|---|---|
| `compose.backup.yaml` | Service backup explicit overlay/profile, không mạng hoặc Docker socket, user riêng, cap-drop/read-only, volume backup tách khỏi web/DB |
| `SOURCE/backup/Dockerfile`, `backup.py` | Binary Restic chính thức, Python stdlib, manifest an toàn, failure gates, snapshot/check/readback |
| `SOURCE/backup/db_dump.sh` | Role backup SELECT-only, kiểm tra InnoDB, dump `.part` → SQL hoàn tất, metadata UTC, dọn credential tạm |
| `SOURCE/backup/backup.ps1`, `backup.sh` | Điều phối DB exec/cp và service backup; không chuyển SQL qua redirection PowerShell |
| `SOURCE/backup/register_daily_backup.ps1` | Tùy chọn đăng ký task mỗi ngày theo giờ máy Windows, không ghi đè task có sẵn |
| `.gitattributes`, `.gitignore` | Shell LF trên Windows; bỏ qua artifact/kho thật trong `backups/` |
| README, SOFT, SETUP/environment, tests README, config example | Hướng dẫn đường dẫn/lệnh/thành phần và giới hạn thật |
| `SOURCE/tests/test_backup.py`, `integration_backup.py` | Unit và kiểm chứng repository thực; fixture lỗi riêng |
| `docs/evidence/phase2/` | Metadata môi trường, log thực, manifest/kết quả, fingerprint mã nguồn |

Trên Windows 10, lab Phase 1 đang healthy, tại repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Setup
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Backup
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Snapshots
docker compose -f compose.yaml -f compose.backup.yaml run --rm --no-deps --entrypoint python backup -m unittest discover -s /tests -p test_backup.py -v
```

Hướng dẫn đầy đủ: [SOURCE/backup/README.md](../SOURCE/backup/README.md).
Lệnh verify dùng `-Action Verify -RunId <run_id_thật>`; lịch hàng ngày là lựa chọn
riêng sau khi backup thủ công PASS. Setup không thay credential hoặc reset kho.

Trên Linux đã chạy thực tế:

```bash
docker build -t group08-lab-backup SOURCE/backup
PHASE2_SKIP_BUILD=1 sh SOURCE/backup/backup.sh setup
sh SOURCE/backup/backup.sh backup
python3 -m unittest discover -s SOURCE/tests -p test_backup.py -v
docker compose -f compose.yaml -f compose.backup.yaml run --rm --no-deps --entrypoint python backup -m unittest discover -s /tests -p test_backup.py -v
python3 SOURCE/tests/integration_backup.py
sh SOURCE/backup/backup.sh snapshots
```

`PHASE2_SKIP_BUILD=1` chỉ để test dùng image đã build; hướng dẫn Linux thông
thường không cần biến này. Không cài package bổ sung hoặc secret vào image.

## Đường dẫn và phân quyền đã chốt

- Database `lab_config`, table `orders`, InnoDB, schema + data; dump không chứa
  triggers/routines/events, MySQL users/grants hoặc mọi bảng khác nếu phát sinh.
- User backup `group08_backup`@`%`: chỉ SELECT trên `lab_config.orders`; user
  ứng dụng vẫn SELECT/INSERT, không có DROP/ALTER/DELETE.
- Kho mã hóa trên host: `<REPO_DIR>/backups/restic/`; trong backup là `/data/restic`.
- SQL từng run: `<REPO_DIR>/backups/runs/<run_id>/payload/database.sql`.
- Metadata nằm cạnh SQL; `manifest.json`, `result.json`, `restic.log` nằm ở thư
  mục run. Manifest ngoài payload để tránh tự băm chính nó.
- Secret mới nằm dưới `secrets/`; credential backup chỉ chép tạm vào DB cho
  provisioning/dump rồi dọn. Service backup chỉ nhận Restic password, không có
  DB credential. Web không được mount bất kỳ kho/artifact backup nào.

Restic đọc payload đã dump, không đọc nóng `/var/lib/mysql`. InnoDB consistent
read đến từ `--single-transaction`; không DDL trong cửa sổ dump. Header/footer
và SHA chỉ kiểm tra hoàn tất/byte, chưa thay thế kiểm tra import SQL/DB ở Phase 3.

## Hai run thành công

| Run | Snapshot ID đầy đủ | Dòng giả trong dump | Kết quả |
|---|---|---|---|
| `p2-20261109T135131Z-742a4652976a` | `5044d86ed493778891581971975300df590c94f17245707f566bab14bc852581` | 103 | PASS |
| `p2-20261109T135429Z-99fc676302c1` | `7589d7b35dd8b5e1393d0e0f344615d4a28e0592a24a09d200167563f1ef367f` | 104 | PASS |

Giữa hai run đã thêm một đơn hàng tổng hợp `LAB-PHASE2` qua API (HTTP 201).
Số dòng trên là phép đếm các tuple với alias LAB- trong SQL fixture của lab,
không phải số dòng đã xác minh sau import vào DB mới. Bộ dữ liệu có 100 seed và
các đơn thử Phase 1; không sửa/xóa dữ liệu để ép số đo về 100.

Mốc dump bắt đầu/kết thúc, full snapshot ID, manifest digest và thời điểm verify
có trong `successful-runs.json`. Hai timestamp dump có độ phân giải một giây;
cùng giây không có nghĩa thời gian xử lý bằng 0. Không diễn giải thành RTO hay
thời điểm commit chính xác để tính RPO.

## Test case, điều kiện đạt và bằng chứng

| Kiểm tra | Điều kiện đạt | Kết quả / bằng chứng trong `evidence/phase2/` |
|---|---|---|
| Unit backup trên host và trong image | 14 test được phát hiện, không skip | PASS, `unit.txt`, `container-unit.txt` |
| Manifest đầu vào | Từ chối symlink cả root, JSON không phải object, path traversal/trùng, size/hash sai, file rỗng/thiếu/thừa | PASS, unit suite |
| Failure gates | Restic exit khác 0 (gồm exit 3), repo check hoặc readback lỗi không PASS | PASS, unit suite |
| Provision role, setup lặp | SELECT-only; setup không đổi secret/reset repo | PASS, `grants-and-count.txt`, `setup-final.txt` |
| Dump + snapshot thật | Dump exit 0, manifest hợp lệ, có snapshot ID | PASS 2 run, `backup-first.txt`, `backup-second-success.txt`, `successful-runs.json` |
| Restic check toàn kho | `check --read-data` không lỗi | PASS, log từng run |
| Snapshot readback | SQL/metadata đọc lại khớp size/SHA; manifest trong snapshot khớp baseline | PASS, log từng run |
| Verify run đã PASS | Check lại đúng snapshot theo full ID | PASS, `integration.json` |
| Init kho đã có/re-run ID đã có | Fail, không ghi đè | PASS, `integration.json` |
| Dump fixture bị cắt cụt | Fail trước gọi Restic, result FAILED/snapshot_id null | PASS, `integration.json` |
| Password file thiếu | Fail closed | PASS, `integration.json` |
| Không sinh snapshot từ phép thử âm | Danh sách snapshot trước/sau giữ nguyên 2 ID | PASS, `integration.json`, `snapshots.json` |
| Regression ứng dụng | 14 unit test app PASS, health 200/104 đơn sau khởi động lại web | PASS, `app-regression.txt`, `final-health.json` |
| PowerShell và Task Scheduler | Nhóm chạy thật trên Windows 10 | NOT TESTED |
| Restore DB sạch / app phục hồi | Import và kiểm tra DB/API trong môi trường mới | NOT TESTED, Phase 3 |
| Bản sao độc lập/air-gap/append-only | Khác quyền/vị trí, có thử phục hồi khi kho chính mất | NOT TESTED, chưa triển khai |

Hai run FAILED cũng được giữ trong `failed-runs.json`: một lần không tạo được
container do hết dung lượng cloud, một fixture cố ý thiếu footer. Log cũ của lần
hết dung lượng ghi phase `dump_or_copy` do controller lúc đó chưa tách bước
launch; lỗi thực tế xảy ra khi tạo container, sau dump/copy. Controller hiện tại
đã tách `backup_container` để các lần sau ghi chính xác hơn. Không đổi run cũ
thành PASS hoặc chạy lại cùng ID.

## Sự cố môi trường và giới hạn

Cloud chỉ có khoảng 8 GB và Docker VFS sao chép nhiều lớp. Đã gặp hết dung lượng
khi tạo container. Khắc phục bằng cache/image build thử có thể tạo lại, tối ưu
Dockerfile thành một COPY ở final stage, và chạy từng container kiểm thử tuần tự.
Đã sửa user backup để file repository thuộc UID/GID host, tránh root-owned files
khi controller kiểm tra trạng thái kho. Kho tạo thử ban đầu được chỉnh ownership
trong cloud; không xóa snapshot hoặc volume DB.

Backup đầu tiên PASS khi web đang online. Các test container sau và backup thứ
hai tạm dừng riêng web để đủ dung lượng; cuối phiên đã tạo lại web, health 200.
Đây là hạn chế môi trường kiểm thử, không phải bước bắt buộc của workflow backup,
không phải diễn tập sự cố và không được dùng làm số đo RTO/RPO. Chưa có stress
test concurrent writes/DDL; điều kiện không DDL vẫn phải được giữ.

Kho cùng host chưa đáp ứng bản sao thứ hai độc lập/offsite hoặc chống mất host.
Dump staging trên host còn plaintext. Người có quyền host/Docker có thể sửa cả
repository và baseline; SHA-256 tự nó không chứng minh nguồn đáng tin cậy.
Chưa bật retention/prune tự động để tránh xóa nhầm snapshot; chưa đo tăng trưởng
dung lượng dài hạn. Script lịch có nhưng chưa có bằng chứng chạy hàng ngày.

Module manifest Phase 2 có scope cố định và test riêng; không sửa prototype
verifier trên nhánh starter và không xóa hai finding trong audit Phase 0.
Trước nghiệm thu restore, nhóm cần thống nhất verifier dùng chính thức và xử lý
finding tương ứng qua PR riêng nếu tiếp tục dùng prototype cũ.

Metadata phiên bản và fingerprint source ở `environment.json` và
`source-sha256.json`. Không commit SQL thật, mật khẩu hoặc toàn bộ kho Restic.
Tài liệu tham khảo CLI chính thức theo tag v0.18.1 được ghi trong SOFT/README.
