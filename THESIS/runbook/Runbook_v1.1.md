# Runbook v1.1 — phục hồi lab Docker và diễn tập lành tính

Ngày cập nhật: 15/11/2026 (UTC+7). Nhóm 08: Đa Minh / Minh Quân.
Trạng thái: bản cải tiến để review; phạm vi đã chạy ghi tại
[kết quả Phase 6](../../docs/PHASE6_RESULTS.md). Chưa nghiệm thu Windows 10 hoặc
lượt chạy độc lập của Minh Quân. Không coi tài liệu này là bằng chứng đã chạy.

`Runbook_v1.0.docx` được giữ nguyên làm đầu vào review. Với workflow hiện tại,
dùng bản v1.1 này thay phần placeholder/restore tại chỗ trong v1.0. Các “pha”
PICERL trong DOCX khác với Phase 0–7 của kế hoạch dự án.

## 1. Phạm vi và vai trò

Chỉ lab Docker với đơn hàng tổng hợp `LAB-...`. Kịch bản chính dừng service DB,
khôi phục snapshot sang stack sạch rồi xác minh tại URL phục vụ. Đây là phép thử
khả năng phục hồi sau mất khả dụng, không mô phỏng hành vi mã độc hoặc chứng minh
phát hiện/ngăn chặn ransomware. Không xóa bảng, volume, snapshot hoặc reset kho.

Workflow này bắt đầu khi nguồn còn healthy để controller tự tạo sự cố có kiểm
soát. `restore` hiện cũng yêu cầu nguồn running/healthy ở bước đầu; chưa có mode
cho sự cố nguồn đã hỏng từ trước. Với trường hợp đó, giữ bằng chứng và ghi giới
hạn này; không nhập vào source hoặc bỏ gate để giả lập hoàn thành runbook.

Đa Minh đề xuất làm người thao tác; Minh Quân đọc từng bước, ghi giờ/lệnh/exit code,
phân loại lỗi và review kết quả. Phân công này chưa phải xác nhận hai thành viên
đã thực hiện. Một lượt do Codex chạy trên cloud không thay lượt chạy độc lập đó.

| Thành phần | Giá trị thực thi |
|---|---|
| Nguồn | Compose project `group08-lab`, services `db`, `web` |
| DB / bảng / engine | MySQL 8.4.7 / `lab_config.orders` / InnoDB |
| URL nguồn | `http://127.0.0.1:8080/`; đọc `WEB_PORT` nếu đã đổi |
| Volume nguồn | `group08-lab_db_data` → `/var/lib/mysql` |
| Kho backup host / container | `backups/restic` / `/data/restic` |
| Artifact host | `backups/runs/<p2-id>/payload/{database.sql,metadata.json}` |
| Manifest / receipt | `backups/runs/<p2-id>/{manifest.json,result.json}` |
| Secret host | `secrets/db_root_password.txt`, `db_app_password.txt`, `db_backup_password.txt`, `restic_password.txt` |
| Target | Project `group08-restore-<run-id>`; volume `<project>_restore_data`; network riêng |
| Secret target | `secrets/restore/<run-id>/{root.txt,app.txt}`; không commit |
| Journal / kết quả | `work/recovery/<run-id>/{events.jsonl,result.json}` |

DB không publish port host. Kho/password/journal vẫn cùng host, chưa chịu được
mất host hoặc mất kho chính. Thư mục khác trên cùng ổ đĩa không là bản sao độc lập.

## 2. Chuẩn bị và điều kiện dừng

1. Dùng nhánh chứa Phase 3–6 đã review, ghi `git status --short --branch` và
   `git rev-parse HEAD`; main có thể chưa chứa các PR này. Giữ mọi thay đổi sẵn có.
2. Windows 10: Docker Desktop Linux containers, Compose v2, Python host 3.10+,
   Git. Chạy tại repository root. Host Python không cần cài Flask/PyMySQL để dùng
   controller; unit ứng dụng chạy trong container có dependency.
3. Dùng `.env`/secret gốc của lab đang có. Không chạy init để tạo mật khẩu mới
   cho volume cũ. Phase 1/2 Setup phải hoàn thành trước backup/restore.
4. Cả hai service healthy. Chỉ một người điều khiển; không có POST khác, SQL/DDL,
   backup cũ hoặc Task Scheduler trong cửa sổ baseline/diễn tập. Khóa controller
   không khóa các entrypoint cũ hoặc client khác.
5. Kiểm tra dung lượng host **và filesystem trong Docker**. Ước lượng preflight
   là ngưỡng vận hành, không phải bảo đảm đủ mọi tải. Cần chỗ cho target mới,
   staging, log và trả nguồn về hoạt động. Không xóa dữ liệu để vượt qua gate.
6. Không bật MySQL general log chỉ để đo thời gian. Dùng observer UTC + monotonic
   và nhật ký send/ACK. Không tìm sự kiện xóa bảng cho kịch bản dừng service.

Một lỗi native command phải dừng bước phụ thuộc. PowerShell 5.1 không tự biến
exit code khác 0 thành exception chỉ nhờ `$ErrorActionPreference='Stop'`.
Nạp các helper sau trong phiên PowerShell dùng cho lượt chạy:

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    & $Exe @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Lệnh $Exe thất bại, exit=$LASTEXITCODE" }
}
function Invoke-Recovery {
    param([string[]]$LabArgs)
    Invoke-Checked -Exe 'powershell.exe' -Arguments (@(
        '-NoProfile', '-ExecutionPolicy', 'Bypass',
        '-File', '.\SOURCE\recovery\run_lab.ps1'
    ) + $LabArgs)
}
Invoke-Checked -Exe 'py' -Arguments @('-3','--version')
Invoke-Checked -Exe 'docker' -Arguments @('compose','config','--quiet')
Invoke-Checked -Exe 'docker' -Arguments @('compose','ps')
Invoke-RestMethod http://127.0.0.1:8080/health
```

Helper và launcher có mã nguồn, nhưng lệnh PowerShell trong bản này vẫn là
**NOT TESTED trên Windows** cho đến khi có transcript từ máy Windows thật.

## 3. Preflight trước mỗi cửa sổ thử

Lệnh `preflight` đã được triển khai trong Phase 6. Nó chỉ đọc trạng thái lab,
schema/toàn bảng, đối chiếu cửa sổ API, quyền, sự hiện diện/format secret và
dung lượng host/Docker; không dừng service, backup, import hoặc tạo target.
Không mở file secret cho giảng viên xem. Secret đúng format không chứng minh
password Restic đúng hoặc snapshot nguyên vẹn; các bước backup/archive sẽ kiểm.

Gate cho phục hồi sạch/diễn tập chính:

```powershell
$gate = 'p3-gate-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gate)
Get-Content "work/recovery/$gate/result.json" -Raw | ConvertFrom-Json
```

Chỉ tiếp tục phục hồi nếu exit 0, `status=PASS`, `preflight.scope=clean-recovery`.
Nếu FAIL, ghi lỗi, giữ result/journal và dừng nhánh phục hồi. Không tái dùng run ID.

Một gate riêng cho đối chứng web, yêu cầu dự trữ 64 MiB cho bằng chứng nhưng
không cấp phép tạo DB mới:

```powershell
$gateWeb = 'p4-gate-web-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateWeb,'-PreflightScope','web-control')
```

Cloud VFS có tùy chọn rõ ràng `-ReleaseSourceContainers` (Linux:
`--release-source-containers`) trong clean gate và action restore/drill. Chỉ dùng
khi đã chọn profile lưu log, dừng và gỡ **container đã dừng**, giữ mọi volume.
Ước lượng credit chỉ dùng cho host, không được coi là dung lượng đã thu hồi trong
filesystem Docker/VM; gate vẫn yêu cầu số đo Docker hiện tại đủ ngưỡng. Gate này
cố ý thận trọng, có thể NO-GO dù một phương án dọn container sau đó sẽ đủ chỗ.
Kiểm lại trước tạo target; không mặc định dùng tùy chọn này trên Windows.

## 4. Backup mới và lựa chọn snapshot

Chỉ chạy phần này sau clean gate PASS:

```powershell
$backup = 'p3-backup-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','backup','-RunId',$backup)
$r = Get-Content "work/recovery/$backup/backup-receipt.json" -Raw | ConvertFrom-Json
if ($r.status -ne 'PASS' -or $r.snapshot_id -notmatch '^[a-f0-9]{64}$' -or
    $r.manifest_sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Receipt chưa đủ điều kiện' }
$r | Select-Object run_id,snapshot_id,manifest_sha256
```

Controller dừng web, xác nhận không còn transaction InnoDB, capture toàn bảng
trước/sau mysqldump single-transaction và buộc hai baseline bằng nhau. Không có
admin writer/DDL là điều kiện vận hành bắt buộc. Baseline nằm trong metadata của
run mới và được ràng buộc SHA-256 với SQL; manifest vẫn đúng hai file Phase 2.
Lưu full snapshot ID, manifest digest, receipt và Git commit vào hồ sơ đã review.

Snapshot cũ thiếu baseline: có thể kiểm tra byte theo Phase 2; không nghiệm thu
schema/nghiệp vụ đầy đủ bằng baseline tự lấy từ target vừa restore. Tạo backup
mới nếu nguồn tin cậy còn sẵn sàng; nếu không, ghi hạn chế **NOT TESTED**.

## 5. Phase 3 — phục hồi vào stack sạch

```powershell
$restore = 'p3-restore-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','restore','-RunId',$restore,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,
    '-ManifestSha256',$r.manifest_sha256,'-Port','8081','-ReturnSource')
Get-Content "work/recovery/$restore/result.json" -Raw | ConvertFrom-Json
```

Không chọn `latest`, ID rút gọn hoặc target cũ. Controller đọc lại snapshot qua
Restic/check, kiểm digest manifest và SHA-256 **trước import**. Target phải có
volume/network/project riêng, không mount volume nguồn/seed; MySQL readiness bằng
SELECT 1 khi chưa có orders; schema lab_config phải zero table trước import.

SQL import không dùng `--force`; exit khác 0 làm lượt FAIL. Dump chỉ có schema/data
orders nên controller tạo lại `group08_app` chỉ SELECT/INSERT. Kiểm schema và hash
**mọi dòng** theo ID, sau đó API đọc, rồi đúng một probe ghi riêng; restart và
kiểm lại base/probe; cleanup SQL staging và ba mẫu health liên tiếp mới đạt ready.

API chỉ trả tối đa 100 dòng mới nhất, không dùng API/COUNT để thay full-table hash.
Không cập nhật baseline từ target để làm PASS. `-ReturnSource` giữ target volume,
trả nguồn về sau trial; đây là thao tác vận hành sau phép thử.

## 6. Phase 4 — ba kịch bản riêng

Đối chứng dừng riêng web, sau gate web PASS:

```powershell
$web = 'p4-web-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','web-outage','-RunId',$web,'-ReturnSource')
```

Phải quan sát URL unavailable, web trở lại, full dataset/schema không đổi.
Trang `/` có thể trả 200 khi DB dừng; dùng `/health`/API và quan sát UI để phân loại.
Đối chứng không có restore snapshot, nên RPO N/A.

Đầu vào SQL hỏng, sau clean gate và receipt hợp lệ:

```powershell
$corrupt = 'p4-corrupt-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','reject-corrupt','-RunId',$corrupt,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,'-ManifestSha256',$r.manifest_sha256)
```

Chỉ sửa một bản SQL copy trong work; giữ manifest/snapshot gốc. Candidate phải bị
từ chối trước import; negative test PASS đi cùng integrity FAIL dự kiến của copy.
Không có outage nên RTO/RPO N/A. Không coi kiểm tra copy cục bộ là Restic readback
mới; nếu chỉ chạy copy check vì thiếu tài nguyên, ghi đúng phạm vi đó.

Diễn tập chính: chỉ sau Phase 3 PASS trên môi trường đang dùng và clean gate mới
PASS. Lượt Linux lịch sử không cấp Windows PASS:

```powershell
$main = 'p4-main-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Recovery -LabArgs @('-Action','drill','-RunId',$main,
    '-Port','8080','-PostOrders','3','-ReturnSource')
```

Port phải bằng WEB_PORT nguồn. Controller ACK canary trước snapshot mới, ACK ba
đơn sau snapshot, drain mọi request rồi dừng DB; `/health` phải 503. Restore sang
stack sạch, đưa target web về đúng URL nguồn và kiểm tra Docker binding.
Đối chiếu ACK đã/chưa phục hồi, duplicate, uncertain; probe target không thuộc
tập nghiệp vụ. Không đọc lại volume nguồn để cứu tail orders.

Không retry POST. HTTP 201 thiếu/sai nội dung hoặc mất phản hồi là **uncertain**;
dừng profile đo, giữ REQUEST_SENT/REQUEST_UNCERTAIN và điều tra bằng truy vấn DB
toàn bảng theo alias/ID. Alias chưa unique trong DB nên không tự suy ra đúng một
lần commit. Nếu Ctrl+C/SIGKILL sau send mà chưa có ACK hợp lệ, cũng coi kết quả
write chưa rõ. Không dùng created_at_utc như bằng chứng độc lập thời điểm commit.

## 7. Thời gian, toàn vẹn và CSV Phase 5

Ở kịch bản chính: T0 = FAULT_REQUESTED, ngay trước gửi lệnh stop. Tready = SERVICE_VERIFIED sau
schema/toàn bảng, quyền, URL/API đọc/ghi, restart, cleanup và stable health. Dùng
monotonic_ns cùng observer: observed RTO = (Tready − T0)/1e9. Return-source diễn
ra sau TRIAL_ENDED, không nằm trong RTO. Hủy/thất bại trước ready không có RTO
thành công; ghi NOT TESTED/censored, không gán 0.

Giữ riêng backup age từ SNAPSHOT_VERIFIED, khoảng tuổi commit cuối phục hồi
[T0−ACK, T0−first-send] khi profile tuần tự/prefix hợp lệ, số ACK chưa phục hồi,
duplicate và uncertain. Không gọi backup age là RPO thực tế chính xác. Nhóm chưa
chốt RTO/RPO mục tiêu: target result **NOT TESTED**, không suy ra đạt SLA.

Tái xuất CSV của corpus lịch sử đã pin, không gây outage:

```powershell
$export = 'work/metrics-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','SOURCE/metrics/export_metrics.py',
    '--output-dir',$export)
Import-Csv "$export/metrics.csv" | Format-Table scenario,trial_status,observed_rto_seconds
```

Exporter hiện chỉ đọc bốn case lịch sử tại Git ref cố định, không tự đọc trial mới
ở phần 6. CSV này không phải số đo lượt vừa diễn tập. Không có private artifact
thì fresh artifact check giữ NOT TESTED. Khi còn đủ artifact và proof hậu kiểm,
xem [metrics README](../../SOURCE/metrics/README.md) để kiểm tra thêm; proof cũ luôn
giữ timestamp cũ. Một lần tái xuất không là một trial mới.

## 8. Kết thúc, hủy và giữ bằng chứng

1. Ghi người thao tác, môi trường, Git commit/hash source, lệnh/exit code, run ID,
   snapshot/digest, các bước PASS/FAIL/NOT TESTED và lỗi cleanup/return-source.
2. Giữ nguyên `events.jsonl`, `result.json`, ACK và mọi target dở/volume. Không
   sửa FAILED thành PASS, không nhập lại vào target dở. Dùng run ID và target mới
   sau điều tra. Khóa còn sau SIGKILL phải kiểm tra PID/process trước xử lý riêng.
3. Đọc `return_source_status` riêng với `status`. Kể cả trial PASS, return-source
   FAILED vẫn là lỗi vận hành, exit khác 0; không bắt đầu trial tiếp theo.
4. Nếu shell/return-source lỗi, lưu log trước. Chỉ dừng target đã xác minh owner
   `com.docker.compose.project` đúng run của mình. Với Compose target phải đặt
   `RESTORE_SECRET_DIR` tới secret **gốc** của run và `RESTORE_WEB_PORT` đúng cổng;
   không tạo lại secret. Sau khi target đã nhả URL, bật nguồn bằng:

```powershell
Invoke-Checked -Exe 'docker' -Arguments @('compose','up','-d','--no-build',
    '--wait','--wait-timeout','180','db','web')
Invoke-RestMethod http://127.0.0.1:8080/health
```

5. Nếu thiếu chỗ để trả nguồn, dừng và ghi sự cố tài nguyên; không xóa volume,
   snapshot hoặc chạy prune. Quy trình gỡ stopped containers cần đúng ownership
   và profile đã review. Không tiếp tục nhập SQL bằng lệnh thủ công vào DB nguồn.
6. Chỉ đưa log/receipt/manifest/hash đã kiểm tra vào evidence. Không commit SQL
   plaintext, toàn bảng, secret, Docker inspect environment hoặc ảnh chứa password.
   Giữ raw artifact gốc; khi cần che thông tin, tạo bản đã che riêng có ghi nguồn.

## 9. Tiêu chí nghiệm thu v1.1

| Hạng mục | Điều kiện |
|---|---|
| Chuẩn bị | Preflight đúng scope PASS, nguồn healthy và không writer ngoài |
| Restore | Full snapshot/digest rõ; fresh target, no seed/source mount; import exit 0 |
| Dữ liệu | Schema/full-table hash khớp baseline trước probe và sau restart |
| Ứng dụng | Grants đúng, API đọc/ghi, URL do target sở hữu, health ổn định |
| Lỗi/hủy | Corrupt/unsafe target bị chặn, FAIL/uncertain/cleanup được giữ rõ |
| Thời gian | Raw events đủ, định nghĩa RTO/lag không đổi, không fake target/SLA |
| Kết thúc | Bằng chứng được giữ, mọi volume/snapshot nguyên vẹn, nguồn healthy |
| Windows / độc lập | Transcript Windows thật và Minh Quân chạy theo v1.1, ghi lỗi và ký review |

Runbook được cải tiến không đồng nghĩa toàn bộ bảng đã PASS. Kết quả từng lượt,
blocker và test chưa chạy phải đọc trong `docs/PHASE6_RESULTS.md`.

## 10. Thay đổi từ v1.0

| V1.0 DOCX | V1.1 và lý do |
|---|---|
| §4/§9.2 placeholder BACKUP_DIR, khung dump tạm | Đường dẫn Phase 2 thật, full Restic receipt, baseline/digest |
| §9.1 start DB là “recovery” | Tách persistence/web control với clean snapshot restore |
| §9.2 import trong nguồn và DB tạm cùng stack | Volume/network/project độc lập, no seed, không reuse target |
| §10 chỉ count/UI/quyền | Schema/toàn bảng, read-before-write, probe riêng, restart và URL |
| §11 RPO=T0−backup; RTO chọn T3 hoặc T4 | Tready cố định gồm xác minh; backup age/commit-lag/ACK tách riêng |
| §4/§5 bật general log/tìm destructive SQL | Observer log cho kịch bản dừng service; không thêm trạng thái SQL |
| Chưa có gate tài nguyên/exit/uncertain | Preflight theo scope, kiểm exit native, không retry khi outcome chưa rõ |
| Chưa có xử lý hủy/return-source cụ thể | Giữ evidence/target dở, lỗi cleanup riêng, hậu kiểm nguồn healthy |
