# Runbook Windows v1.0 — Đa Minh gây sự cố, Minh Quân phục hồi

Ngày soạn: 16/11/2026 (UTC+7). Trạng thái: **chờ thực hành Windows 10**.
Đây là v1.0 của đợt Windows, dựa trên Runbook Docker v1.1 ngày 15/11.
Không đổi tên hoặc ghi đè các DOCX v1.0/v1.1 lịch sử. Không coi việc có tài liệu
hoặc unit test là đã thực hành. Đóng băng commit tài liệu trước lượt đầu.

## 1. Phạm vi, vai trò và điều kiện

- Đa Minh chuẩn bị, nhập INJECT, ghi thời gian/lỗi và quan sát; Minh Quân chỉ
  theo runbook này để nhập RECOVER và WEB_OK. Mọi trợ giúp phải ghi vào biên bản.
- Lab: Windows 10, Docker Desktop Linux containers, Compose v2, Python host
  3.10+, Git. PowerShell 5.1; mở tại repo root chứa compose.yaml. Không cần SSH,
  thuê VPS hoặc cài MySQL trực tiếp trên Windows. VS Code chỉ là editor.
- MySQL 8.4.7, `lab_config.orders`, InnoDB, dữ liệu giả. Web 127.0.0.1:8080;
  port 8081 dành cho Phase 3. Nếu đã đổi WEB_PORT, dùng giá trị đó cho source URL
  và main drill; chọn port Phase 3 khác, trống. Không in toàn bộ .env/secret.
- Source volume `group08-lab_db_data`. Backup host `backups/restic`, trong
  công cụ `/data/restic`. Secret tại `secrets/`; không đưa vào transcript/video.
- Target `group08-restore-<run-id>` có network/volume riêng, không seed/mount
  nguồn. Không nhập SQL vào nguồn, xóa bảng/volume/snapshot hoặc reset kho.
- Nguồn phải healthy khi bắt đầu; đây là diễn tập có chuẩn bị, chưa hỗ trợ
  nguồn đã hỏng từ trước. Backup/password/journal cùng host, chưa là offsite.
- Chỉ controller này ghi đơn trong cửa sổ thử. Không chạy Task Scheduler,
  backup PS/SH cũ, POST khác hoặc SQL/DDL ngoài. Không retry POST uncertain.
- Đủ dung lượng host và Docker VM. Preflight FAIL thì dừng nhánh phục hồi,
  tăng dung lượng hoặc chuẩn bị máy phù hợp; không xóa dữ liệu để vượt gate.

## 2. Chuẩn bị một lần và mở hồ sơ

Nếu lab chưa từng được khởi tạo, làm theo `SETUP/installation/install_guide.md`
và Setup trong `SOURCE/backup/README.md`, tuần tự và kiểm exit code. Nếu đã có
volume/secret, giữ nguyên; không chạy init để tạo password mới cho volume cũ.
Mọi image phải chuẩn bị trước đo, không tải/build trong cửa sổ diễn tập.

Trong PowerShell tại repo root, **dot-source** helper (có dấu chấm đầu):

```powershell
. .\SOURCE\recovery\start_session.ps1
```

Helper tạo `$sessionDir`, bắt đầu transcript, sao chép các CSV mẫu và cung cấp
`Invoke-Checked`, `Invoke-Recovery`, `New-LabRunId`. Nó chỉ kiểm phiên bản công cụ;
không khởi động/dừng lab và không tự cấp preflight PASS. Nếu helper báo lỗi,
giữ transcript, xử lý trước bước tiếp. Kiểm git branch/commit, Docker `linux`,
Compose v2, Python >=3.10. Commit các file thực thi trước Guided.

Ghi tên người thao tác/quan sát, OS build, commit và phiên bản runbook vào CSV.
Mọi khối dưới có thể làm thay đổi lab; không copy chạy cả tài liệu một lượt.

## 3. Gate và backup mốc 0 — Đa Minh

```powershell
Invoke-Checked -Exe 'docker' -Arguments @('compose','config','--quiet')
Invoke-Checked -Exe 'docker' -Arguments @('compose','ps')
Invoke-RestMethod http://127.0.0.1:8080/health
$gate = New-LabRunId -Phase p3 -Label gate
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gate)
Get-Content "work/recovery/$gate/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
```

[ ] Exit 0, status PASS, scope clean-recovery; đọc số đo host và Docker.
Nếu FAIL: ghi nguyên nhân vào biên bản, không tiếp tục backup/restore/drill.

```powershell
$backup = New-LabRunId -Phase p3 -Label backup
Invoke-Recovery -LabArgs @('-Action','backup','-RunId',$backup)
$r = Get-Content "work/recovery/$backup/backup-receipt.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if ($r.status -ne 'PASS' -or $r.snapshot_id -notmatch '^[a-f0-9]{64}$' -or
    $r.manifest_sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Invalid backup receipt' }
$r | Select-Object run_id,snapshot_id,manifest_sha256
```

[ ] Giữ receipt, full snapshot ID, digest, baseline và log check/readback.
Không dùng latest/ID rút gọn. Nguồn được dừng web để baseline/dump nhất quán;
backup mốc 0 không là mẫu RTO. Snapshot cũ thiếu baseline không đủ nghiệm thu.

## 4. Phase 3 Windows — Minh Quân thực hiện, Đa Minh quan sát

```powershell
$restore = New-LabRunId -Phase p3 -Label restore
Invoke-Recovery -LabArgs @('-Action','restore','-RunId',$restore,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,
    '-ManifestSha256',$r.manifest_sha256,'-Port','8081','-ReturnSource')
Get-Content "work/recovery/$restore/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
```

[ ] Project/network/volume target mới, không seed/source mount.
[ ] Manifest/SHA trước import, import exit 0, grants SELECT/INSERT.
[ ] Schema/toàn bảng khớp, API đọc trước probe, probe riêng, restart giữ dữ liệu.
[ ] status và return_source_status cùng PASS, nguồn trở lại healthy.

API chỉ trả tối đa 100 dòng; không dùng cửa sổ này hoặc COUNT thay full hash.
Đừng đánh giá lỗi vì count không còn 100: mỗi smoke/probe có thể thêm đơn giả.
Phase 3 này không có FAULT_REQUESTED nên không báo RTO diễn tập.

## 5. Đối chứng — chạy riêng, ghi riêng

Web-only, không phục hồi snapshot và không đo RPO:

```powershell
$gateWeb = New-LabRunId -Phase p4 -Label gate-web
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateWeb,'-PreflightScope','web-control')
$web = New-LabRunId -Phase p4 -Label web
Invoke-Recovery -LabArgs @('-Action','web-outage','-RunId',$web,'-ReturnSource')
```

SQL copy hỏng, không outage và không import:

```powershell
$corrupt = New-LabRunId -Phase p4 -Label corrupt
Invoke-Recovery -LabArgs @('-Action','reject-corrupt','-RunId',$corrupt,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,'-ManifestSha256',$r.manifest_sha256)
```

[ ] Web mất khả dụng rồi trở lại, toàn dữ liệu/schema không đổi.
[ ] Copy SQL bị từ chối trước import; snapshot gốc không đổi.
Negative test PASS đi cùng candidate integrity FAIL dự kiến; RTO/RPO N/A.

## 6. Diễn tập hai người — giữ một terminal/observer suốt lượt

Chỉ chạy sau Phase 3 Windows PASS. Chạy clean preflight mới và kiểm lại dung
lượng; bật OBS trước fault, không mở secret. Không dùng vòng lặp tạo trial.

```powershell
$gateMain = New-LabRunId -Phase p3 -Label gate-main
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateMain)
$main = New-LabRunId -Phase p4 -Label main
Invoke-Recovery -LabArgs @('-Action','drill','-RunId',$main,
    '-Port','8080','-PostOrders','3','-Guided','-ReturnSource')
```

Controller chuẩn bị một canary ACK trước snapshot mới và ba ACK sau snapshot.
Ba lệnh sau nhập **ở prompt của controller**, không phải lệnh PowerShell.
Dùng nguyên run ID đang hiển thị; không nhập ký tự `< >` và không pipe câu trả lời.

| Ai | Prompt cần nhập | Thực hiện và ghi nhận |
|---|---|---|
| Đa Minh | `INJECT <run-id>` | Xác nhận bắt đầu; controller ghi T0 rồi stop DB và xác nhận 503 |
| Minh Quân | `RECOVER <run-id>` | Đọc runbook rồi yêu cầu restore vào stack sạch; thời gian chờ nằm trong RTO |
| Minh Quân | `WEB_OK <run-id>` | Chỉ nhập sau khi mở URL nguồn, xem dữ liệu trên UI và lưu ảnh/video; không tạo thêm đơn |

Controller thực hiện các lệnh Docker/Restic/import theo runbook. Đây là phục hồi
có tự động hóa, không phải gõ tay từng SQL. Xác nhận tên vai trò không là xác thực
danh tính; transcript/video/biên bản ghi ai thực sự thao tác và trợ giúp đã nhận.

Sau WEB_OK, controller kiểm lại dữ liệu/API và ba health mẫu cách nhau >=1 giây,
ghi SERVICE_VERIFIED/TRIAL_ENDED rồi mới trả nguồn. Không đợi xem target sau khi
ReturnSource hoàn tất: lúc đó URL lại phục vụ nguồn. Ảnh target chụp trước WEB_OK.

```powershell
Get-Content "work/recovery/$main/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
Invoke-RestMethod http://127.0.0.1:8080/health
```

[ ] status PASS; integrity/schema/grants/api_read_write/persistence PASS.
[ ] Một checkpoint phục hồi, ba tail ACK chưa phục hồi, duplicate/uncertain = 0
trong profile này; probe không thuộc tập ACK nghiệp vụ.
[ ] return_source_status PASS; nếu FAILED, ghi lỗi vận hành riêng và chưa chạy tiếp.

## 7. Đo lường và xuất CSV mới

```powershell
$export = "work/metrics-$main"
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','SOURCE/metrics/export_metrics.py',
    '--trial-dir',"work/recovery/$main",'--output-dir',$export)
Import-Csv "$export/metrics.csv" -Encoding UTF8 |
    Format-Table run_id,trial_status,measurement_version,observed_rto_seconds,unrecovered_acknowledged_requests
```

Output phải là thư mục mới; mỗi run xuất riêng. Dùng lệnh này cho `$restore`,
`$web`, `$corrupt` hoặc gate bằng cách thay trial-dir/output-dir. Không có
`--trial-dir` thì exporter vẫn tái xuất corpus Linux cũ, không là lượt vừa chạy.

Định nghĩa `guided-v2`: RTO = (SERVICE_VERIFIED − FAULT_REQUESTED)/1e9, gồm
bàn giao, xác minh toàn dữ liệu, đối chiếu ACK, xác nhận URL và ổn định health.
`automated-v1` giữ định nghĩa lịch sử: comparison ACK sau SERVICE_VERIFIED.
Không gộp hai phiên bản để tính trung bình hoặc chứng minh runbook nhanh hơn.

Giữ riêng backup age, bounds tuổi commit cuối từ send/ACK, đơn chưa phục hồi,
duplicate và uncertain. Không dùng created_at_utc làm commit evidence; không gọi
backup age/bounds là exact RPO. Nhóm chưa chốt target: target result NOT TESTED.
FAIL/ABORTED sau fault không có RTO thành công: censored, không gán 0.

`evidence-manifest.json` băm các file an toàn, không chứa SQL/secret. Hash cục bộ
không phải chữ ký hoặc bằng chứng lưu trữ độc lập; hai người review và pin Git
bản này cùng các input đã che phù hợp trước khi chia sẻ. Không chỉnh raw rồi
băm lại để làm PASS. Export chỉ kiểm byte SQL nếu artifact private còn tồn tại;
không chạy Restic hoặc DB mới, không được ghi fresh Restic/DB PASS.

## 8. Lỗi, hủy và bảo toàn

- Sai xác nhận thì dừng bước phụ thuộc, ghi FAILED. Ctrl+C hoặc EOF ghi ABORTED;
  ReturnSource được thử khi nguồn đã bị tác động. SIGKILL/mất điện có thể thiếu
  seal/TRIAL_ENDED: ghi lượt chưa hoàn tất, không tự tạo sự kiện còn thiếu.
- HTTP 201 sai payload hoặc mất phản hồi là uncertain, không retry. Giữ send/
  ACK/error và điều tra chỉ đọc; alias không unique nên không suy ra commit một lần.
- Giữ mọi target dở, volume, snapshot và run ID. Sau điều tra dùng run/target mới.
- Nếu return-source lỗi hoặc shell mất, lưu log trước; theo §8 của Runbook Docker
  v1.1 để xác minh owner, dừng đúng target và nhả port. Không chạy nguồn khi target
  còn chiếm URL. Giữ secret gốc của target và không xóa volume/snapshot/prune.
- Không dùng `verify_retained.py` trong buổi này: finding gate tài nguyên muộn
  chưa được sửa. Hậu kiểm của restore hiện tại đã có schema/full hash/restart.

## 9. Ghi lỗi, cải tiến và nộp

Đa Minh điền Biên_bản_Diễn_tập_Runbook.csv trong `$sessionDir`. Minh Quân tạo
v1.1 dựa trên lỗi/điểm khó dùng thực tế, ghi bảng thay đổi và run retest. Không có
lỗi runtime thì ghi đúng như vậy; không tạo lỗi giả. Chạy lại bằng run ID mới,
cùng protocol guided-v2 và ghi khác biệt máy/tải/cache/dữ liệu.

Xuất Đo_lường_RPO_RTO.csv; cập nhật đúng tên kịch bản trong Sheets, giữ bốn
tình huống mở rộng là NOT TESTED khi chưa chạy. Cô lập không được đo riêng thì
N/A. Tỷ lệ file phải có mẫu số, ví dụ hai payload file; không thay tỷ lệ đơn.
Ghi biên bản bàn giấy riêng về quyết định phát hiện/cô lập/bảo toàn/phục hồi.

Quay bản đầy đủ và bản demo 3–5 phút; chú thích mọi tua/cắt, không lấy độ dài
video biên tập làm RTO. Cập nhật nguồn Word/PPTX và số đo được pin trước build;
builder lịch sử không tự nhận run mới. Mở kiểm native Office trên máy trình bày.
Chỉ chia sẻ cấu hình/log đã che, CSV, report, slide, runbook và video; không chia
sẻ secrets hoặc SQL plaintext. Kiểm quyền link bằng cửa sổ chưa đăng nhập.

```powershell
Stop-Transcript
```

[ ] Hai thành viên ghi tên/ngày review thật. [ ] Link hoạt động. [ ] Số liệu có
nguồn. [ ] NOT TESTED/FAIL còn hiển thị. [ ] Không auto-merge PR hoặc ký thay.
