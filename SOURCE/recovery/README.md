# Phục hồi sạch và diễn tập lành tính — Phase 3/4

Chỉ dùng lab Docker `group08-lab`, MySQL 8.4.7, `lab_config.orders`, dữ liệu
`LAB-...`. Không có thao tác xóa volume, reset kho, xóa snapshot, mã hóa tống tiền
hoặc gây sự cố bằng xóa bảng. SQL dump có DDL chuẩn do mysqldump sinh ra; chỉ import
vào schema mới đã được xác nhận chưa có bảng. Dump mới thêm `--skip-add-drop-table`;
không thay đổi dump/snapshot cũ. Không import vào DB nguồn.

## Điều kiện và phạm vi

- Phase 1 và Setup backup Phase 2 đã chạy; hai service healthy. Kho, secret và
  các image `mysql:8.4.7`, `group08-lab-web`, `group08-lab-backup` đã có.
- Observer cần **Python 3.10+ trên host**, Docker CLI và Compose v2. Đây là
  dependency mới của Phase 3/4; các workflow Phase 1/2 vẫn không cần Python host.
- Windows 10: `py -3 --version`, `docker version`, `docker compose version`.
  PowerShell launcher có nhưng chỉ được công nhận Windows PASS khi nhóm chạy thật.
- Chỉ một người điều khiển lab. Không chạy script backup cũ/Task Scheduler, DDL
  hoặc công cụ ghi khác trong cửa sổ baseline/diễn tập. Khóa controller bảo vệ
  những lần chạy controller này trên cùng host/user/daemon, không bảo vệ script cũ.
- Đủ dung lượng trong Docker và host. Kiểm tra dung lượng host không thay thế
  kiểm tra dung lượng VM/VHD của Docker Desktop. Kho cùng host chưa phải offsite.

## Tương thích Phase 2 và baseline

Giữ manifest v1 gồm `database.sql`, `metadata.json`. Baseline độc lập được
capture từ nguồn trong lúc web dừng, xác nhận không còn InnoDB transaction,
đối chiếu toàn bộ dữ liệu trước/sau dump rồi **nhúng trong metadata của run mới**.
SHA-256 của metadata và SQL vẫn do module Phase 2 tạo và đọc lại từ Restic.
Baseline được ràng buộc thêm với SHA-256 SQL, không tự băm chính nó.

Không sửa snapshot/manifest lịch sử. Snapshot cũ thiếu business baseline vẫn
verify byte bằng Phase 2 được, nhưng không được nghiệm thu restore đầy đủ bằng
workflow này. Cần tạo backup mới; không lấy target vừa restore làm baseline nguồn.

Chuẩn hóa `orders-jsonl-v1`: sáu cột theo ID tăng dần, số nguyên chính xác,
UTF-8 JSON compact + LF, timestamp UTC microsecond. So sánh toàn bảng, không LIMIT.
Schema giữ kiểu, PK, CHECK, collation và engine; bỏ bộ đếm AUTO_INCREMENT và
`CHARACTER SET` dư thừa chỉ khi bằng charset bảng và vẫn giữ COLLATE tường minh.

## Chạy Windows 10

Tại repository root, sau khi Python/Docker sẵn sàng:

```powershell
$id = 'p3-backup-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action backup -RunId $id
```

Đọc `work/recovery/<id>/backup-receipt.json`, đối chiếu và giữ full snapshot ID,
run ID backup cùng manifest digest ở hồ sơ đáng tin cậy. Không chọn `latest`.

```powershell
$r = Get-Content "work/recovery/$id/backup-receipt.json" -Raw | ConvertFrom-Json
$restore = 'p3-restore-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action restore -RunId $restore -BackupId $r.run_id -SnapshotId $r.snapshot_id -ManifestSha256 $r.manifest_sha256 -Port 8081 -ReturnSource
```

Restore dừng DB và web nguồn, trích xuất lại từ Restic, dựng project/volume mới,
readiness bằng SELECT 1, import, cấp SELECT/INSERT, kiểm schema/all rows, kiểm API,
thêm đúng một probe rồi restart và kiểm lại. `ReturnSource` thực hiện **sau** khi
kết thúc phép thử: lưu log, dừng/gỡ container target, giữ volume target và bật lại
nguồn. Đây là trả lab về trạng thái vận hành, không được tính vào thời gian phục hồi.

### Cloud VFS thiếu dung lượng

Tùy chọn `-ReleaseSourceContainers` / `--release-source-containers` chỉ dành cho
lab cần giải phóng root filesystem container. Sau khi lưu log và dừng hai service,
controller gỡ **container đã dừng**, giữ volume nguồn. Không có `rm -v` hay `down -v`.
Ghi hành động và thời gian này vào journal. Bản sao sạch luôn dùng volume mới.
Không dùng tùy chọn này để tuyên bố đã kiểm thử giữ nguyên container nguồn.

## Phase 4 — các kịch bản

Web-only control (không khôi phục snapshot, không suy ra RPO):

```powershell
$trial = 'p4-web-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action web-outage -RunId $trial
```

SQL candidate hỏng: chỉ sửa bản sao dưới work, giữ nguyên snapshot và manifest;
không gọi import và không gây outage, RTO/RPO không áp dụng:

```powershell
$trial = 'p4-corrupt-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action reject-corrupt -RunId $trial -BackupId $r.run_id -SnapshotId $r.snapshot_id -ManifestSha256 $r.manifest_sha256
```

Main drill (port phải bằng WEB_PORT của nguồn, thường 8080):

```powershell
$trial = 'p4-main-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action drill -RunId $trial -Port 8080 -PostOrders 3 -ReturnSource
```

Main drill: gửi một canary có ACK trước backup, capture baseline + snapshot đã
verify, gửi PostOrders đơn có ACK, không retry, không request in-flight, rồi dừng
DB. Bằng chứng phải có health 503. Dừng web nguồn, restore stack mới về URL nguồn,
đối chiếu ACK đã/chưa phục hồi, duplicate, full baseline, API, probe và restart.
Đơn thử phục hồi luôn ghi riêng; hash base sau probe phải vẫn khớp baseline cũ.

Linux tương đương: `python3 -B SOURCE/recovery/controller.py <action> --run-id ...`;
`--backup-id`, `--snapshot-id`, `--manifest-sha256`, `--port`, `--post-orders`,
`--release-source-containers`, `--return-source` tương ứng các tham số PowerShell.

## Bằng chứng, metric và xử lý lỗi

`work/recovery/<run>/events.jsonl` được flush/fsync mỗi sự kiện: UTC và monotonic
observer, lệnh/mã thoát, send/ACK/uncertain, fault, import, verification và return.
`result.json` là kết quả run; `acknowledgements.json` của main drill ghi từng request.
SQL plaintext và secret không được commit. Baseline chỉ lưu hash/schema/count.

T0 = ngay trước gửi lệnh stop DB (web-only: stop web). Tready = kết thúc xác minh
data, API đọc/ghi, restart, cleanup SQL và ba lần health liên tiếp cách một giây.
Main drill chỉ ghi Tready khi URL nguồn thuộc web target đã kiểm tra Docker binding.
Thời gian release container/cutover/import/validation đều nằm trong observed RTO.
Thời gian return-source sau trial không nằm trong RTO. Không có mục tiêu RTO/RPO
định lượng được cấu hình: PASS kỹ thuật không phải đạt SLA.

Thiếu đơn sau snapshot là mất dữ liệu quan sát theo tập ACK, không phải sai hash
snapshot. Độ tuổi commit cuối được phục hồi chỉ được báo thành khoảng [T0-ACK,
T0-first-send] từ observer khi recovered requests là prefix và không duplicate.
Không dùng created_at_utc làm thời điểm commit hoặc tự gán RPO=0.

Mọi lỗi/KeyboardInterrupt làm run FAILED/ABORTED; kết quả write không rõ không
retry. Không tái sử dụng run, project/volume cũ để import; giữ dữ liệu dở để điều tra.
Không tự xóa khóa còn lại sau SIGKILL: xác minh process đã hết và điều tra riêng.
`ReturnSource` là tùy chọn hậu kiểm, lỗi của nó được ghi riêng và exit khác 0.
Trong lỗi tài nguyên nghiêm trọng, không xóa volume/snapshot để cố chạy tiếp.

Windows, mất kho/host và bản sao độc lập chỉ được PASS khi có bằng chứng riêng.
Kịch bản mất kho chính chưa triển khai vì chưa có storage độc lập. Các finding
retry API, controller backup cũ và Flask advisory chưa được đóng bởi PR này.
