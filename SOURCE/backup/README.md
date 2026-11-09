# Phase 2 — Sao lưu nhất quán bảng orders bằng Restic

Phạm vi hiện tại: schema + dữ liệu của `lab_config.orders` (InnoDB), không gồm
user/grants MySQL, triggers, routines, events hoặc bảng mới phát sinh. Chưa
khôi phục DB vào môi trường sạch; đó là Phase 3. Chỉ dùng dữ liệu giả trong lab.

## Chuẩn bị trên Windows 10

Mở PowerShell tại repository root, Docker Desktop dùng Linux containers. Lab
Phase 1 phải đang healthy; giữ nguyên `.env`, secret và volume DB đã có.

```powershell
docker compose ps
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Setup
```

Setup tạo thêm `secrets/db_backup_password.txt` và `secrets/restic_password.txt`
nếu chưa có. Không ghi đè mật khẩu hoặc khởi tạo lại kho đang tồn tại. Nếu
kho tồn tại mà mất file password, phải tìm lại password gốc. Setup cấp user
`group08_backup`@`%` chỉ SELECT trên `lab_config.orders`, thông qua một lần dùng
root secret trong container DB. User ứng dụng vẫn chỉ SELECT/INSERT; backup
không dùng tài khoản web hoặc lưu root credential vào image/kho Restic.

Service backup không có mạng, chạy UID/GID 1000 mặc định, read-only rootfs,
drop capabilities; chỉ có volume backup và Restic password. Không có Docker
socket, network DB hoặc root/app/backup-DB secret trong service này. Trên Linux,
script lấy UID/GID host; nếu tự gọi Compose, có thể đặt `BACKUP_UID/BACKUP_GID`
trong `.env`. Windows Docker Desktop dùng bind-mount của Desktop; cần kiểm
tra quyền ghi và secret trên máy nhóm bằng checklist chạy thật.

## Tạo backup mốc 0 và các lần sau

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Backup
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Snapshots
```

Lần đầu PASS có thể chọn làm mốc 0 và lưu lại run_id/snapshot_id. Mỗi lần tạo
ID UTC + random mới, không ghi đè các run cũ. Không chạy Setup/Backup đồng thời
trên cùng lab: bước chép script vào DB dùng một đường dẫn chung; task hàng ngày
đã đặt IgnoreNew nhưng thao tác thủ công vẫn cần được điều phối. Workflow:

1. Chép script và credential tạm vào container DB; tạo client config chỉ đọc
   bởi root. Credential không truyền qua argv hoặc in ra log.
2. Xác nhận bảng InnoDB và chạy `mysqldump --single-transaction --quick
   --skip-lock-tables --no-tablespaces --set-gtid-purged=OFF --skip-triggers`.
   Không DDL trong lúc dump. Chỉ INSERT từ ứng dụng có thể tiếp tục; transaction
   cung cấp consistent read cho InnoDB. Không chép nóng `/var/lib/mysql`.
3. SQL được ghi `.part` trong DB; chỉ đổi tên sau exit 0. Dùng `docker compose cp`
   lấy byte nguyên vẹn, tránh `>`/Out-File của PowerShell 5.1 đổi encoding SQL.
   Ghi hai mốc UTC bắt đầu/kết thúc dump; chúng là cửa sổ thu thập, không phải
   timestamp commit chính xác hoặc RPO thực tế.
4. Kiểm tra header/footer, scope metadata; tạo manifest SHA-256 cho SQL và
   metadata. Manifest nằm ngoài payload để không tự băm chính nó.
5. Restic backup đúng payload + manifest, lấy full snapshot ID; mọi mã thoát khác
   0, kể cả partial backup exit 3, đều fail.
6. `restic check --read-data`; đọc lại từng file bằng `restic dump <snapshot_id>`
   vào thư mục tạm và đối chiếu SHA-256 cùng manifest đã lưu. Kiểm tra lại payload
   gốc không đổi. Chỉ sau đó ghi `result.json` status PASS.
7. Dọn credential/client config/SQL staging trong DB. Artifact trên host và
   snapshot vẫn giữ nguyên. Dọn tạm thất bại cần xem log, không xóa volume DB.

Snapshot này chứa SQL đã dump cùng metadata/manifest. Restic snapshot không phải
snapshot VM hoặc snapshot vật lý của MySQL. Kiểm tra byte thành công chưa chứng
minh SQL nhập vào DB sạch chạy được hoặc ứng dụng phục hồi; Phase 3 sẽ kiểm tra.

## Đường dẫn lab thật

| Đối tượng | Host, tính từ repository root | Trong container |
|---|---|---|
| Kho Restic mã hóa | `backups/restic/` | `/data/restic/` của backup |
| Dump của một run | `backups/runs/<run_id>/payload/database.sql` | `/data/runs/<run_id>/payload/database.sql` |
| Metadata | `backups/runs/<run_id>/payload/metadata.json` | cùng đường dẫn dưới `/data` |
| Baseline SHA-256 | `backups/runs/<run_id>/manifest.json` | ngoài payload |
| Kết quả tin cậy | `backups/runs/<run_id>/result.json` | status, full snapshot ID, manifest digest, mốc UTC |
| Log Restic | `backups/runs/<run_id>/restic.log` | lệnh, output, mã thoát; không chứa SQL/password |
| Staging trong DB | không dùng làm backup | `/tmp/group08-<run_id>/`, được dọn sau copy |

`backups/` và `secrets/` được Git bỏ qua. Dump staging trên host là plaintext;
không upload toàn thư mục backup vào repo/Drive. App/web không được mount kho
này. Người có quyền host/Docker vẫn có thể can thiệp cả kho và baseline; cần
lưu bản sao tin cậy/thiết bị tách biệt ở bước thiết kế storage sau.

## Kiểm chứng lại một snapshot theo run

```powershell
$run = 'p2-THAY-BANG-RUN-ID-THAT'
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Verify -RunId $run
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Check
```

`Verify` dùng đúng snapshot ID và baseline digest của run đã PASS; không chọn
`latest` mơ hồ. `Check` đọc kiểm tra toàn bộ kho. Script không có thao tác prune,
forget, xóa snapshot, xóa volume hoặc reset repository. Một run thất bại không
được chạy lại cùng ID. Nếu `.processing` còn sau khi bị ngắt, giữ để điều tra;
tạo run mới, không tự xóa marker để hợp thức hóa kết quả.

## Lịch backup hàng ngày trên máy Windows

Sau khi Setup và Backup thủ công PASS, tùy chọn đăng ký task lúc 18:00 theo giờ
máy Windows đang cấu hình:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\register_daily_backup.ps1 -At '18:00'
Get-ScheduledTask -TaskName Group08-Lab-Backup
Get-ScheduledTaskInfo -TaskName Group08-Lab-Backup
```

Task chạy bằng user đang đăng nhập; Docker Desktop/lab cần sẵn sàng. Không lưu
mật khẩu Windows, không tự ghi đè task đã có. `StartWhenAvailable` không bảo đảm
có backup khi máy tắt hoặc user đăng xuất. Cần kiểm tra LastTaskResult và result
của run mới; lịch được cấu hình không phải bằng chứng đã chạy hàng ngày.
Script Task Scheduler và PowerShell chưa được chạy trực tiếp trên Windows 10
trong môi trường cloud; nhóm cần ghi minh chứng riêng.

## Linux và kiểm thử

Linux có Python3 host và Docker Compose:

```bash
sh SOURCE/backup/backup.sh setup
sh SOURCE/backup/backup.sh backup
sh SOURCE/backup/backup.sh snapshots
sh SOURCE/backup/backup.sh verify p2-THAY-BANG-RUN-ID-THAT
```

Unit/integration tests và điều kiện đạt xem `SOURCE/tests/README.md`. Không chạy
nhiều one-off container đồng thời khi cloud dùng VFS với dung lượng thấp. Trong
phiên test này, backup đầu tiên chạy cùng web; các lần sau có tạm dừng riêng web
để đủ ổ đĩa, rồi đã khởi động lại. Đây không phải phép đo downtime/RTO.

## Lỗi và giới hạn

- DB chưa chạy/credential sai/không còn InnoDB/SQL copy thiếu: fail, không tạo
  snapshot được công nhận. Kiểm tra `docker compose ps`, console và result.
- Password Restic sai hoặc mất: không reset kho. Khôi phục đúng secret gốc.
- DDL hoặc đổi schema trong lúc dump có thể phá điều kiện nhất quán; app role
  không có DDL, admin phải tránh thay schema trong cửa sổ backup. Bảng mới phải
  được đưa vào scope và test riêng, không được coi đã được backup tự động.
- Kho này cùng host với DB; chưa có bản sao offsite, append-only, immutable hay
  air-gap. Chưa đáp ứng kiểm chứng mất host/storage hoặc AC03 bản sao độc lập.
- Chưa có restore DB sạch, RTO/RPO thực tế hoặc diễn tập Runbook độc lập.

Tham khảo Restic chính thức (BSD-2-Clause), tag v0.18.1: `doc/040_backup.rst`,
`doc/045_working_with_repos.rst`. Chỉ tham khảo CLI/thiết kế, không sao chép dự án.
