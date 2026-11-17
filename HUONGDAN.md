# Hướng dẫn chạy thực nghiệm — Nhóm 08

Phiên bản thực hành Windows **v1.0**, cập nhật 17/11/2026 (UTC+7).
Đọc [các lưu ý](LUU_Y_THUC_NGHIEM.md) trước khi thao tác.
[Báo cáo các phase](BAO_CAO_CAC_PHASE.md) là nơi xem kết quả đã có.

Đây là đầu mối lệnh hiện hành thay cho các hướng dẫn module/runbook Markdown
trùng trước đây. Mã các lệnh đã tồn tại; PowerShell/Windows, Guided hai người và
video vẫn **NOT TESTED** cho đến khi nhóm thực hành. Làm từng bước, không copy
chạy cả tài liệu một lượt. Một bước FAIL dừng các bước phụ thuộc.

## 0. Bắt đầu khi nhóm đang quá tải

Chia làm ba buổi; không cần hoàn thành mọi artifact trong một buổi:

1. Đa Minh chuẩn bị máy và chạy đến backup (mục 2–5); Minh Quân làm Phase 3
   (mục 6). Kết thúc buổi khi nguồn healthy, receipt và kết quả đã lưu.
2. Khi Phase 3 Windows đạt, hai người cùng chạy đối chứng và Guided (mục 7–8),
   xuất số đo (mục 9), ghi lỗi thật. Không vừa sửa code vừa đo.
3. Cải tiến runbook và retest (mục 10), quay video, cập nhật Word/PPTX/Sheets và
   đóng gói năm minh chứng (mục 12). Giữ cả lượt thất bại và lượt chạy lại.

Nếu buổi đầu chỉ đến Phase 3 PASS thì đã có một kết quả thực hành hữu ích;
không bắt buộc cố làm luôn Phase 4 khi mệt hoặc thiếu disk. Trước lúc nghỉ, ghi
đường dẫn `run-sheet.json`, kiểm nguồn healthy, dừng transcript và giữ evidence.

Chuẩn bị Docker Desktop đang chạy ở **Linux containers**, Git for Windows,
Python >=3.10 có launcher `py` (khuyên 3.12/3.13), trình duyệt. Docker Compose
v2 phải hỗ trợ `--wait`. Khi quay/nộp mới cần OBS và Word/PowerPoint. Không cần
cài MySQL, Restic hoặc Flask trực tiếp trên Windows; lab dùng container.

Mở **Windows PowerShell**, chạy tại repository root; không dùng CMD, terminal
trong container hoặc cửa sổ Git Bash để copy các khối PowerShell bên dưới.
Không mặc định phải chạy bằng Administrator. Không nhập dòng nhắc `PS C:\...>`.
Các biến `$...` thuộc cùng một cửa sổ; giữ cửa sổ đó mở trong một lượt.

Nguồn cài: [Git for Windows](https://git-scm.com/downloads/win),
[Python cho Windows](https://www.python.org/downloads/windows/),
[Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/),
[OBS](https://obsproject.com/download). Với Python, bật launcher `py` và tùy chọn
PATH nếu installer cung cấp; mở lại PowerShell sau cài đặt. Windows 10 phải đáp
ứng điều kiện phiên bản của Docker Desktop đang dùng; không nâng/hạ Docker giữa
lượt đo. Máy đã chạy Docker tốt không cần cài lại Docker.

Nếu Docker/Python/Git chưa cài, hoàn thành phần cài đặt chính thức trước khi
chạy script. Kiểm nhanh `git --version`, `py -3 --version`, `docker version`;
Docker phải có cả Client và Server. Đừng tiếp tục nếu Server báo không kết nối.

## 1. Vai trò, lộ trình và hồ sơ

| Thứ tự | Đa Minh | Minh Quân | Điều kiện chuyển bước |
|---|---|---|---|
| Chuẩn bị | Lab/công cụ/dung lượng, mở transcript | Kiểm tài liệu/commit | Công cụ đúng và nguồn healthy |
| Phase 2 | Tạo backup mốc 0, giữ receipt | Đối chiếu full ID/digest | Clean gate và backup PASS |
| Phase 3 | Quan sát, ghi lệnh/lỗi | Restore theo tài liệu, kiểm kết quả | Windows restore và return-source PASS |
| Đối chứng | Web-only và corrupt copy | Đối chiếu phạm vi/N/A | Mỗi scenario có result riêng |
| Phase 4 | INJECT, quan sát/ghi nhận | RECOVER và WEB_OK theo tài liệu | Guided có đủ raw/checkpoints |
| Phase 5 | Export CSV, kiểm công thức | Đối chiếu báo cáo/Sheet | Đúng run/version, không thiếu bằng chứng |
| Phase 6 | Ghi khó khăn, trợ giúp và lỗi thật | Sửa v1.1, chạy lại bằng run mới | Có changelog và retest thật |
| Phase 7 | Video, biểu đồ, kiểm link | Word/PPTX, native Office | Hồ sơ khớp CSV, hai người review |

Buổi đầu chuẩn bị và Phase 3; buổi tiếp theo diễn tập/ghi lỗi; sau đó sửa và
retest/quay video; cuối cùng hoàn thiện hồ sơ. Thời gian phụ thuộc gate, không
chứng nhận nhóm đã hoàn thành. Hỏi giảng viên phạm vi bốn tình huống mở rộng;
trong lúc chưa xác nhận vẫn chuẩn bị MVP, giữ các tình huống đó NOT TESTED.

Giữ mỗi run tại `work/recovery/<run-id>`; hồ sơ buổi tại `work/sessions/<session>`.
CSV mẫu được copy từ [docs/templates/windows](docs/templates/windows).
Ghi người thao tác/quan sát thật, OS, commit, phiên bản tài liệu, lệnh/exit,
expected/observed, status, lỗi và link bằng chứng. Raw timestamp UTC, khi trình
bày có thể đổi UTC+7; thời lượng chính dùng monotonic cùng observer.

## 2. Chọn đúng mã và mở phiên PowerShell

### 2.1. Chọn một trong hai cách lấy repo

**Máy chưa có checkout/lab:** lấy đầy đủ lịch sử, không tải ZIP hoặc shallow clone.
Chạy từng dòng; dừng ngay nếu clone lỗi. Thư mục đích phải chưa tồn tại.

```powershell
New-Item -ItemType Directory -Force C:\Labs | Out-Null
Set-Location C:\Labs
git clone --branch nhom08/thuc-hanh-tung-buoc-20261117 https://github.com/daminh12/MaNhom08_DanhGiaKhaNangPhucHoiRansomware.git Nhom08
Set-Location C:\Labs\Nhom08
```

**Đã có lab:** mở đúng checkout cũ đang giữ `.env` và `secrets/`. Kiểm
`git status --short --branch`; lưu/review công việc chưa commit trước khi đổi nhánh.
Chỉ khi working tree sạch mới dùng:

```powershell
git fetch origin
git switch nhom08/thuc-hanh-tung-buoc-20261117
git pull --ff-only
```

Kiểm exit code sau từng lệnh Git. Nếu switch không được, dừng xử lý xung đột;
không reset/force/checkout đè. Clone mới trên cùng máy **vẫn thấy volume Docker
cũ**, không phải lab sạch. Không copy password từ nguồn không rõ.

### 2.2. File đầu tiên cần chạy

Mở PowerShell ở **repository root**, nơi có compose.yaml. Dùng nhánh đã review
chứa `-Guided` và `--trial-dir`, không mặc định main đã tích hợp các PR.

```powershell
git status --short --branch
git rev-parse HEAD
. .\SOURCE\recovery\start_session.ps1
```

Dòng chạy script có **hai dấu chấm cách nhau một khoảng trắng** để nạp hàm
vào phiên hiện tại. Không thay bằng `&` hoặc mở script trong một process con.
Nếu policy PowerShell chặn script, chạy dòng sau rồi dot-source lại:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
. .\SOURCE\recovery\start_session.ps1
```

Policy tổ chức nếu có cần được xử lý trên máy nhóm; không sửa policy toàn máy.
Kiểm đã nạp hàm và ghi lại đường dẫn hồ sơ buổi:

```powershell
Get-Command Invoke-Recovery,Invoke-Checked,New-LabRunId
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
Get-TimeZone
Get-PSDrive -PSProvider FileSystem | Select-Object Name,Used,Free,Root
$sessionDir
```

### 2.3. Chọn đúng Docker daemon, cổng và ghi sổ lượt chạy

Trước mọi lệnh khởi tạo/start/stop, xác nhận đây là Docker Desktop **của máy lab**:

```powershell
Invoke-Checked -Exe 'docker' -Arguments @('context','show')
Invoke-Checked -Exe 'docker' -Arguments @('context','inspect','--format','{{.Endpoints.docker.Host}}')
Invoke-Checked -Exe 'docker' -Arguments @('info','--format','{{.OSType}}')
Invoke-Checked -Exe 'docker' -Arguments @('info','--format','{{.ID}}')
if ($env:DOCKER_HOST -or $env:DOCKER_CONTEXT) { throw 'Docker override is set: confirm the approved daemon before continuing' }
```

Trên PowerShell trực tiếp ở Windows, endpoint Docker Desktop thường là `npipe:`
và OSType phải là `linux`. Nếu thấy `ssh:`/`tcp:`/máy khác hoặc biến override,
dừng để xác nhận daemon; không tự xóa biến rồi chạy tiếp. Đây là bước xác nhận
của người thao tác, chưa phải daemon allowlist được cưỡng chế trong controller.

Helper tạo `$sessionDir`, bắt đầu transcript và nạp `Invoke-Checked`,
`Invoke-Recovery`, `New-LabRunId`. Kiểm Docker server kết nối, OSType linux,
Compose v2 hỗ trợ --wait, Python >=3.10. Helper không dừng/bật lab và không tự
cấp clean preflight PASS. Không ghi secret vào lệnh, log hoặc video.

Đặt cổng phù hợp cấu hình đang dùng; nếu WEB_PORT khác mặc định, sửa số ở đây:

```powershell
$sourcePort = 8080
$restorePort = 8081
$sourceUrl = "http://127.0.0.1:$sourcePort"
```

Lưu những biến cần dùng qua các bước vào hồ sơ không chứa password:

```powershell
$bookPath = Join-Path $sessionDir 'run-sheet.json'
$book = [ordered]@{
    repo_root = (Get-Location).Path
    code_commit = (git rev-parse HEAD).Trim()
    session_dir = $sessionDir
    source_port = $sourcePort
    restore_port = $restorePort
    backup_run = ''; backup_receipt = ''; restore_run = ''
    web_run = ''; corrupt_run = ''; main_run = ''; metrics_dir = ''; runs = @()
    runbook_version = ''; runbook_copy = ''
    transcript_files = @((Join-Path $sessionDir 'powershell.txt'))
}
function Save-RunSheet {
    $book | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $bookPath -Encoding UTF8
}
function Remember-LabRun {
    param([string]$Action,[string]$RunId,[int]$Port = 0)
    $book.runs = @($book.runs) + [pscustomobject]@{
        action = $Action; run_id = $RunId; port = $Port
        noted_at_utc = [DateTime]::UtcNow.ToString('o')
    }
    Save-RunSheet
}
Save-RunSheet
$bookPath
```

Ghi run ID **trước** khi gọi controller để kể cả lượt lỗi vẫn tìm được hồ sơ.
Đây là sổ tham chiếu, không thay `result/events` và không cấp phép dùng lại target dở.

Chuẩn bị khoảng 10–20 GB trống để có chỗ cho image, nhiều target được giữ và
video; đây là khuyến nghị dự phòng, không phải dung lượng đã đo hoặc ngưỡng
nghiệm thu cố định. Kiểm cả ổ Windows chứa repo và disk/VM của Docker Desktop
trong Settings → Resources. Preflight đo lại host/Docker; host còn trống không
bảo đảm Docker VM còn trống. Khi gate FAIL không thử lặp restore để mong qua.

Cổng target Phase 3 phải khác cổng nguồn và đang trống. Không thay .env/secret
hoặc rebuild giữa lượt đo. Guided yêu cầu file source đã commit và đúng byte Git;
nếu từ chối vì CRLF/thay đổi chưa commit, lưu/review thay đổi, chuẩn bị checkout LF
phù hợp trước lượt mới. Không reset để mất công việc và không sửa fingerprint.

## 3. Chuẩn bị lab và backup tool — trước thực nghiệm

### 3.1. Chỉ đối với lab mới hoàn toàn

Kiểm trước khi chạy init:

```powershell
Test-Path .env
Test-Path secrets
Invoke-Checked -Exe 'docker' -Arguments @('volume','ls','--filter','name=group08-lab_db_data')
Invoke-Checked -Exe 'docker' -Arguments @('ps','-a','--filter','label=com.docker.compose.project=group08-lab')
```

- Không có config/secret và không có Docker resources nguồn: chạy init bên dưới.
- Đã có lab cùng config/secret gốc: **bỏ qua init**, sang mục 3.2.
- Có volume/container nguồn nhưng mất config/secret: **DỪNG**, tìm bản gốc; clone
  mới và password mới không mở được DB cũ. Init nay từ chối trường hợp này trước
  khi tạo file. Không xóa volume để lách guard. Trạng thái tạo dở cần điều tra.

```powershell
Invoke-Checked -Exe 'powershell.exe' -Arguments @(
    '-NoProfile','-ExecutionPolicy','Bypass','-File','.\SETUP\installation\init_lab.ps1'
)
```

### 3.2. Khởi động và kiểm nguồn

Build/tải image trong phần chuẩn bị, chưa tính vào RTO diễn tập:

```powershell
Invoke-Checked -Exe 'docker' -Arguments @('compose','config','--quiet')
Invoke-Checked -Exe 'docker' -Arguments @('compose','up','-d','--build','--wait','--wait-timeout','180')
Invoke-Checked -Exe 'docker' -Arguments @('compose','ps')
Invoke-RestMethod "$sourceUrl/health"
Start-Process "$sourceUrl/"
```

Đạt khi web/db healthy, health 200/status ok/database ok và UI có đơn giả.
Chỉ volume mới, trước ghi lần đầu, mới kỳ vọng đúng 100 dòng. DB không publish
host; web phải bind localhost. `/` có thể 200 khi DB lỗi, dùng `/health`/API để xét.

### 3.3. Setup backup tool nếu chưa chuẩn bị Phase 2

```powershell
Invoke-Checked -Exe 'powershell.exe' -Arguments @(
    '-NoProfile','-ExecutionPolicy','Bypass','-File','.\SOURCE\backup\backup.ps1','-Action','Setup'
)
```

Setup tạo image backup, cấp role SELECT-only và init kho mới hoặc check kho đã
có. Chạy tuần tự khi nguồn healthy, không backup khác/Scheduler đồng thời.
Giữ credential/kho đã có; mất password kho thì dừng tìm bản gốc. Legacy Setup còn
finding cleanup/log trong LUU_Y; console không lỗi chưa thay backup/restore PASS.

## 4. Kiểm tra lab trước khi đo

Unit app dùng DB mock; smoke gọi HTTP thật và **thêm một đơn giả**. Chỉ chạy trong
chuẩn bị, không trong cửa sổ snapshot/diễn tập:

```powershell
Invoke-Checked -Exe 'docker' -Arguments @('compose','exec','-T','web','python','-B',
    '-m','unittest','discover','-s','/tests','-p','test_app.py','-v')
Invoke-Checked -Exe 'docker' -Arguments @('compose','exec','-T','web','python','-B','/tests/smoke_phase1.py')
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','-m','unittest','discover',
    '-s','SOURCE/tests','-p','test_backup.py','-v')
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','-m','unittest','discover',
    '-s','SOURCE/tests','-p','test_*recovery.py','-v')
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','-m','unittest','discover',
    '-s','SOURCE/tests','-p','test_*metrics.py','-v')
```

Điều kiện: có test được phát hiện, exit 0; ghi số PASS/skip thật. Clone không có
SQL private có thể SKIP một test metrics, không ghi toàn suite không skip.
Không discover toàn bộ app suite trên Python host thiếu dependencies rồi gọi là
lỗi DB. App chạy đúng image; backup/recovery/metrics dùng host stdlib.

Control runtime tùy chọn (restart nguồn, dừng DB → 503, bật lại), ngoài lượt đo:

```powershell
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','SOURCE/tests/runtime_phase1.py','--base-url',$sourceUrl)
```

Control này không là restore từ snapshot. Nó kiểm API window; kiểm toàn bảng
cho nghiệm thu phục hồi nằm trong controller/preflight. Nếu control lỗi, giữ log,
kiểm nguồn trở lại healthy trước tiếp tục. Mỗi lần smoke có thể tăng số dòng.

## 5. Clean preflight và backup mốc 0

```powershell
$gate = New-LabRunId -Phase p3 -Label gate
Remember-LabRun -Action preflight -RunId $gate
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gate)
$g = Get-Content "work/recovery/$gate/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if ($g.status -ne 'PASS' -or $g.preflight.scope -ne 'clean-recovery') { throw 'NO-GO: clean gate failed' }
$g.preflight
```

Preflight chỉ đọc source/schema/toàn bảng/API/quyền/secret presence/format và
dung lượng host/Docker. Không thay Restic/password/readback; chúng được kiểm khi
backup/archive. Gate FAIL: ghi lỗi, dừng nhánh phục hồi, không dùng lại run ID.
Không lấy gate Linux hoặc web-control để cấp PASS cho clean Windows.

```powershell
$backup = New-LabRunId -Phase p3 -Label backup
$book.backup_run = $backup
Remember-LabRun -Action backup -RunId $backup
Invoke-Recovery -LabArgs @('-Action','backup','-RunId',$backup)
$r = Get-Content "work/recovery/$backup/backup-receipt.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if ($r.status -ne 'PASS' -or $r.snapshot_id -notmatch '^[a-f0-9]{64}$' -or
    $r.manifest_sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Invalid backup receipt' }
$book.backup_receipt = (Resolve-Path "work/recovery/$backup/backup-receipt.json").Path
Save-RunSheet
$r | Select-Object run_id,snapshot_id,manifest_sha256
```

Controller dừng web, kiểm drained transactions, capture toàn bảng trước/sau dump
và buộc khớp; metadata baseline được hash/readback cùng SQL. Không admin writer/
DDL là điều kiện bắt buộc. Giữ receipt/full snapshot/digest/Git commit/baseline.
Không dùng latest hoặc ID/số liệu Linux cũ trên kho mới ở Windows.
Mỗi lệnh controller có thể im lặng trong lúc Docker/Restic chạy; giữ cửa sổ và
đợi kết thúc hoặc prompt, không nhấn Ctrl+C chỉ vì chưa thấy output. Có thể mở
PowerShell thứ hai ở repo để xem `Get-Content "work/recovery/<run-id-thật>/events.jsonl"
-Tail 8 -Wait`; không nhập lệnh theo dõi vào cửa sổ đang chờ Guided.

## 6. Phase 3 — Minh Quân phục hồi sạch

Đa Minh quan sát/ghi lại. Lệnh này tạm dừng nguồn; target dùng cổng riêng. Không
có incident T0 nên chưa là mẫu RTO diễn tập:

```powershell
$restore = New-LabRunId -Phase p3 -Label restore
$book.restore_run = $restore
Remember-LabRun -Action restore -RunId $restore -Port $restorePort
Invoke-Recovery -LabArgs @('-Action','restore','-RunId',$restore,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,
    '-ManifestSha256',$r.manifest_sha256,'-Port',"$restorePort",'-ReturnSource')
$restored = Get-Content "work/recovery/$restore/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$restored | Select-Object status,integrity,schema,grants,api_read_write,persistence,return_source_status
Invoke-RestMethod "$sourceUrl/health"
```

Nghiệm thu từng mục bằng result/events, không chỉ dòng PASS cuối:

- Project/network/volume mới, không seed hoặc mount DB nguồn; target chưa có.
- Full snapshot/digest đúng; manifest/SHA kiểm trước import; SELECT 1 readiness,
  schema zero table; SQL import exit 0; tạo lại app role chỉ SELECT/INSERT.
- Schema/hash mọi dòng khớp baseline; API đọc trước một probe, probe tách riêng.
- Restart target giữ base/probe, cleanup và ba health samples đạt; nguồn trả lại
  healthy, `status` và `return_source_status` PASS.

ReturnSource chạy sau trial, dừng/gỡ target containers nhưng **giữ volume**. Nếu
cần hình target cho lần Phase 3, chuẩn bị workflow quan sát riêng đã review;
đừng chụp URL nguồn sau return rồi gọi là ảnh target. Main Guided có điểm WEB_OK
để xem/chụp target trước return. Phase 3 Windows chưa PASS thì chưa chạy main.

Kiểm tự động các cờ nghiệm thu, đồng thời giữ log để đối chiếu phạm vi:

```powershell
foreach ($field in @('status','integrity','schema','grants','api_read_write','persistence','return_source_status')) {
    if ($restored.$field -ne 'PASS') { throw "NO-GO Phase 3: $field is not PASS" }
}
$beforeHash = (Get-FileHash "work/recovery/$backup/source-dataset.jsonl" -Algorithm SHA256).Hash.ToLowerInvariant()
$afterHash = (Get-FileHash "work/recovery/$restore/restored-dataset.jsonl" -Algorithm SHA256).Hash.ToLowerInvariant()
if ($beforeHash -ne $afterHash) { throw 'Baseline dataset SHA256 differs' }
[pscustomobject]@{source_sha256=$beforeHash; restored_sha256=$afterHash}
```

Hai JSONL chứa **tất cả** hàng baseline theo thứ tự ID, trước probe ghi mới;
không chỉ 100 dòng API. Mỗi dòng là một mảng theo thứ tự `id, customer_alias,
product_name, quantity, unit_price_vnd, created_at_utc` (xem hợp đồng trong common.py).
SQL/schema vẫn được kiểm riêng. Giữ byte JSONL nguyên vẹn, không mở rồi lưu lại
bằng Excel/editor; đổi LF/encoding sẽ đổi hash. Đây là đơn giả, vẫn chỉ share
sau review. File nằm ngoài payload Restic hai tệp, không sửa snapshot lịch sử.
Hash trùng chỉ chứng minh byte dữ liệu baseline trùng, không chứng minh không
có mã độc hoặc kho sao lưu độc lập. Các lượt cũ thiếu JSONL giữ NOT TESTED.

## 7. Phase 4 — hai đối chứng riêng

### 7.1. Dừng riêng web

```powershell
$gateWeb = New-LabRunId -Phase p4 -Label gate-web
Remember-LabRun -Action preflight-web -RunId $gateWeb
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateWeb,'-PreflightScope','web-control')
$web = New-LabRunId -Phase p4 -Label web
$book.web_run = $web
Remember-LabRun -Action web-outage -RunId $web -Port $sourcePort
Invoke-Recovery -LabArgs @('-Action','web-outage','-RunId',$web,'-ReturnSource')
Get-Content "work/recovery/$web/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
```

Đạt khi quan sát web unavailable rồi hoạt động, schema/toàn bảng không đổi và
return-source PASS. Không restore snapshot, RPO N/A; không tính thành main repeat.

### 7.2. SQL copy hỏng bị từ chối

Dùng receipt bước 5. Nếu vừa thay đổi tài nguyên hoặc buổi thực hành đã chuyển
sang ngày khác, chạy lại clean preflight như mục 5 với run ID mới trước bước này:

```powershell
$corrupt = New-LabRunId -Phase p4 -Label corrupt
$book.corrupt_run = $corrupt
Remember-LabRun -Action reject-corrupt -RunId $corrupt
Invoke-Recovery -LabArgs @('-Action','reject-corrupt','-RunId',$corrupt,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,'-ManifestSha256',$r.manifest_sha256)
Get-Content "work/recovery/$corrupt/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
```

Chỉ sửa bản SQL copy trong work, giữ manifest/snapshot gốc. Expected:
`rejection=PASS`, `import_attempted=false`. Candidate integrity FAIL dự kiến,
negative test PASS; không outage nên RTO/RPO N/A. Thiếu disk không chạy được
Restic extract thì ghi NOT TESTED, không lấy local-copy check thay lượt đầy đủ.

## 8. Main Guided — diễn tập hai người

Trước buổi diễn tập bàn giấy, chốt người quyết định là ai, kênh liên hệ và ai có
quyền bấm INJECT/RECOVER. Đa Minh ghi trạng thái Docker/health và thời gian vào
transcript trước fault; controller ghi journal/ID container/volume trong run.
Không chụp toàn `docker inspect` chứa environment/secret metadata để công bố.
Đây là bảo toàn log cho lab, chưa phải acquisition RAM/ảnh đĩa forensics hoặc
chuỗi bàn giao chứng cứ đã được ký. Trên sự cố thật cần quy trình IR riêng để
cân bằng dữ liệu volatile, cô lập và bảo toàn; không format hay restore đè nguồn.

Đóng băng commit/hash **HUONGDAN v1.0** và biên bản trước lượt đầu. Minh Quân chỉ
nhìn bản đã đóng băng; mọi hỗ trợ hoặc sai sót phải ghi. Bật OBS trước fault;
không mở secret. Giữ một terminal/observer suốt ba xác nhận, không pipe đáp án.
Lưu đúng bản tài liệu mà Minh Quân sẽ sử dụng; không sửa nó trong lúc đo:

```powershell
$runbookVersion = '1.0' # Lan retest sau cai tien that: doi thanh '1.1'.
$runbookCopy = Join-Path $sessionDir ("HUONGDAN-v$runbookVersion-used.md")
if (Test-Path -LiteralPath $runbookCopy) {
    if ((Get-FileHash $runbookCopy -Algorithm SHA256).Hash -ne
        (Get-FileHash .\HUONGDAN.md -Algorithm SHA256).Hash) { throw 'Frozen runbook differs; use the correct new version, never overwrite it' }
} else {
    Copy-Item .\HUONGDAN.md -Destination $runbookCopy
    Get-FileHash $runbookCopy -Algorithm SHA256 |
        Export-Csv (Join-Path $sessionDir "runbook-v$runbookVersion-sha256.csv") -NoTypeInformation -Encoding UTF8
}
$book.runbook_version = $runbookVersion
$book.runbook_copy = $runbookCopy
Save-RunSheet
git rev-parse HEAD
```

```powershell
$gateMain = New-LabRunId -Phase p3 -Label gate-main
Remember-LabRun -Action preflight -RunId $gateMain
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateMain)
$main = New-LabRunId -Phase p4 -Label main
$book.main_run = $main
Remember-LabRun -Action drill -RunId $main -Port $sourcePort
Invoke-Recovery -LabArgs @('-Action','drill','-RunId',$main,
    '-Port',"$sourcePort",'-PostOrders','3','-Guided','-ReturnSource')
```

Trong phần chuẩn bị snapshot, controller tạm dừng web để capture nhất quán;
đoạn này nằm trước fault T0, phải ghi riêng nếu báo cáo tổng downtime. Không gọi
backup này là online không gián đoạn hoặc dùng RTO chính để che downtime chuẩn bị.

Controller chuẩn bị checkpoint có ACK trước snapshot mới, ba ACK sau snapshot,
drain requests và guard target. Nhập các chuỗi sau **ở ô xác nhận controller**,
không phải lệnh PowerShell. Thay `<run-id>` bằng ID đang hiển thị, không nhập dấu < >:

| Ai | Chuỗi nhập | Điều kiện/ý nghĩa |
|---|---|---|
| Đa Minh | INJECT <run-id> | Bắt đầu lỗi có kiểm soát; controller ghi T0, stop DB, xác nhận 503 |
| Minh Quân | RECOVER <run-id> | Đọc runbook rồi yêu cầu phục hồi sạch; thời gian đọc/chờ nằm trong RTO |
| Minh Quân | WEB_OK <run-id> | Mở URL nguồn, quan sát UI đọc dữ liệu và lưu ảnh/video trước khi xác nhận; không POST thêm |

Controller thực hiện Docker/Restic/import và kiểm chứng; đây là runbook có tự
động hóa hỗ trợ. Tên role trong prompt không xác thực danh tính người nhập;
video/transcript/biên bản ghi người thật. Không nói hai người tự gõ từng SQL nếu
controller thực hiện. Sai xác nhận thì dừng bước phụ thuộc, không tự nhập lại.

Sau restore, comparison ACK phải đạt; sau WEB_OK controller recheck toàn bảng/
schema/API và stable health rồi mới SERVICE_VERIFIED/TRIAL_ENDED. Sau đó trả
nguồn về; URL sau return là source. Kiểm kết quả:

```powershell
$trial = Get-Content "work/recovery/$main/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$trial | Select-Object status,measurement_version,observed_rto_seconds,return_source_status
$trial.request_comparison
Invoke-RestMethod "$sourceUrl/health"
```

Main tạo **snapshot và receipt riêng** bên trong lượt; không lấy receipt mốc 0
để mô tả snapshot main. Nếu baseline main có N dòng, DB nguồn sau ba tail có
N+3, còn target sau probe có N+1. Probe là kiểm ghi riêng, không là đơn phục hồi.
Trước WEB_OK, URL phục vụ đang trỏ target; sau ReturnSource nó lại trỏ nguồn.

Expected profile: checkpoint phục hồi, ba tail ACK chưa phục hồi, duplicate/
uncertain = 0; base data/schema/grants/API/persistence PASS, probe riêng. Thiếu
ba tail đơn đúng snapshot khác sai SHA. Hủy/thất bại giữ kết quả thật và target dở.

## 9. Phase 5 — xuất đúng lượt và kiểm số đo

Chỉ đọc evidence của lượt mới, không gây outage:

```powershell
$export = "work/metrics-$main"
$book.metrics_dir = $export
Save-RunSheet
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','SOURCE/metrics/export_metrics.py',
    '--trial-dir',"work/recovery/$main",'--output-dir',$export)
Import-Csv "$export/metrics.csv" -Encoding UTF8 |
    Format-Table run_id,trial_status,measurement_version,observed_rto_seconds,unrecovered_acknowledged_requests
```

Có thể thay `$main` bằng `$restore`, `$web`, `$corrupt` hoặc gate để xuất riêng.
Output phải mới, ngoài thư mục input. Giữ `result/events`, seal, ACK, receipt,
manifest/metadata/verified/observed baseline theo allowlist; đừng đổi tên thư mục
run hoặc sửa raw. Commit source thực thi cần có trong clone để kiểm fingerprints.

Với main mới, `dataset_evidence_status` phải PASS, hai cột
`source_dataset_sha256` và `restored_dataset_sha256` phải giống nhau, và
`dataset_row_count` là N trước tail/probe. Export từ chối sidecar thiếu/sai byte;
không tự bổ sung file cho lượt cũ. `integrity.json` ghi rõ phạm vi dataset.

Output: `metrics.csv` và `Đo_lường_RPO_RTO.csv` cùng số liệu UTF-8 BOM/comma/LF,
`metrics.json`, `integrity.json`, `manifest.json`. Excel nếu mở sai cột: Data →
From Text/CSV → UTF-8/Comma. Một file export là một run, không phải trial mới.

Đối chiếu T0/ready từ events và measurement_version, full ID/digest, số base/probe,
ACK phục hồi/thiếu/duplicate/uncertain. RTO từ monotonic; backup age, khoảng tuổi
commit send/ACK và số đơn thiếu ghi riêng. Exact RPO/đạt mục tiêu NOT TESTED;
cô lập N/A nếu chưa đo riêng. FAIL/ABORTED sau fault là censored, không zero.

### Tái xuất lịch sử để tham khảo

```powershell
$historical = 'work/metrics-history-' + [guid]::NewGuid().ToString('N').Substring(0,12)
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','SOURCE/metrics/export_metrics.py',
    '--output-dir',$historical)
```

Không `--trial-dir` là bốn case Linux cũ, không số đo Windows vừa chạy. Không dùng
`--verification`/`--artifact-root` lịch sử cùng `--trial-dir`. Clone thiếu SQL
private ghi fresh artifact NOT TESTED. Export không chạy Restic/DB mới; không
gọi proof cũ là fresh check. Giữ mã commit corpus có đầy đủ Git objects.

Trên Linux đã chuẩn bị lab tương ứng, dùng Python trực tiếp thay launcher
PowerShell, cùng action/run ID và gate; không chạy lệnh Linux trong PowerShell:

```bash
python3 -B SOURCE/recovery/controller.py --help
python3 -B SOURCE/metrics/export_metrics.py --help
```

Ví dụ chuyển tham số: `-Action preflight` → `controller.py preflight`, `-RunId`
→ `--run-id`, `-Guided` → `--guided`, `-ReturnSource` → `--return-source`. Guided
vẫn đòi terminal tương tác. Tùy chọn cloud `--release-source-containers` chỉ dùng
khi đã review profile lưu log/gỡ container đã dừng; giữ volume và snapshot, không
mặc định áp dụng trên Windows. Không dùng credit host để giả dung lượng Docker VM.

## 10. Phase 6 — ghi lỗi, sửa v1.1 và chạy lại

Đa Minh điền `Biên_bản_Diễn_tập_Runbook.csv` và `Thay_đổi_Runbook.csv` trong
`$sessionDir`: bước, giờ, lệnh/exit, quan sát, lỗi/khó hiểu, trợ giúp và link.
Ghi biên bản bàn giấy riêng về phát hiện/cô lập/bảo toàn/phục hồi/xác nhận.

Minh Quân sửa **chính HUONGDAN** lên v1.1 từ quan sát thực tế, giữ v1.0 qua commit/
hash và changelog. Không tạo file DRAFT trống thứ tư, không tạo lỗi hoặc chữ ký
giả. Chưa có lỗi runtime thì ghi đúng các quan sát có thật. Chạy lại bằng run ID/
target mới, giữ guided-v2 và ghi khác biệt máy/tải/cache/dữ liệu/hỗ trợ.
Cách chạy lại: lặp mục 8 với `$runbookVersion = '1.1'`, gate mới và main ID mới;
lặp mục 9 để có thư mục CSV mới. Mục 8 tự tạo ID, không gõ lại ID cũ. Sổ runs
vẫn giữ lượt trước dù `$main` chuyển sang lượt retest. Không ghi đè bản v1.0 đã
đóng băng; đối chiếu hai run và điền `retest_run_id` trong CSV thay đổi.

Mỗi lượt dùng preflight mới. Không gộp automated-v1 với guided-v2 hoặc gọi hai
mẫu là bằng chứng chắc chắn v1.1 nhanh hơn. Hai người review kết quả retest rồi
mới đánh dấu các mục Windows tương ứng PASS.

## 11. Lỗi, hủy và trả nguồn

### 11.1. Mở lại terminal sau khi kết thúc một lượt

Chỉ dùng cách này để đọc hồ sơ/xuất số đo hoặc tiếp tục **bước mới**. Không dùng
để chạy lại import trong target dở. Vào đúng checkout rồi mở transcript mới:

```powershell
. .\SOURCE\recovery\start_session.ps1
$newSessionDir = $sessionDir
$bookPath = Read-Host 'Nhap duong dan day du run-sheet.json cua buoi truoc'
$book = Get-Content -LiteralPath $bookPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ((Get-Location).Path -ne $book.repo_root) { throw 'Wrong original checkout' }
if ((git rev-parse HEAD).Trim() -ne $book.code_commit) { throw 'Code changed: review before continuing' }
$sessionDir = $book.session_dir
$sourcePort = [int]$book.source_port
$restorePort = [int]$book.restore_port
$sourceUrl = "http://127.0.0.1:$sourcePort"
$backup = $book.backup_run
$restore = $book.restore_run
$main = $book.main_run
$export = $book.metrics_dir
$book.transcript_files = @($book.transcript_files) + (Join-Path $newSessionDir 'powershell.txt')
if ($book.backup_receipt) {
    $r = Get-Content -LiteralPath $book.backup_receipt -Raw -Encoding UTF8 | ConvertFrom-Json
}
```

Nạp lại hai hàm `Save-RunSheet` và `Remember-LabRun` ở mục 2.3, **không chạy lại
khối khởi tạo `$book = [ordered]...`** làm mất danh sách cũ. Gọi `Save-RunSheet`
sau khi nạp lại hàm để lưu đường dẫn transcript mới. `$newSessionDir` là
nơi có transcript mới; ghi đường dẫn này vào biên bản. Kiểm lại Docker context,
nguồn healthy và gate trước bước phục hồi mới. Không lấy `$r` cũ làm receipt main.

### 11.2. Hủy và xử lý lỗi


Ctrl+C/EOF tạo ABORTED và thử ReturnSource nếu nguồn đã bị tác động. Nếu mất shell/
SIGKILL, giữ bằng chứng thiếu, không tự tạo seal/TRIAL_ENDED. Uncertain POST:
không retry; điều tra chỉ đọc. Target dở giữ nguyên, không nhập lại. Không xóa
khóa còn lại khi chưa kiểm process/PID.

Nếu `return_source_status=FAILED`, lưu result/events/log và kiểm đúng project của
run; chưa chạy trial khác. Khi result còn đầy đủ, quy trình nhả URL thủ công sau
trial như sau (trong phiên có helper):

```powershell
# Nếu đã mở shell mới, điền run ID thật từ hồ sơ thay cho biến $main.
$failedRun = $main
if ($failedRun -notmatch '^p[34]-[a-z0-9-]{1,40}$') { throw 'Invalid run ID' }
$failed = Get-Content "work/recovery/$failedRun/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
$targetProject = "group08-restore-$failedRun"
if ($failed.target_project -ne $targetProject) { throw 'Target identity mismatch' }
Invoke-Checked -Exe 'docker' -Arguments @('ps','-a','--filter',
    "label=com.docker.compose.project=$targetProject",'--format','{{.Names}} {{.Status}}')
```

Đối chiếu tên/label với run của mình; tuyệt đối không chọn project group08-lab
cho bước dừng target. Nếu target_created=true, nhả port bằng đúng cấu hình gốc:

```powershell
$env:RESTORE_SECRET_DIR = (Resolve-Path "secrets/restore/$failedRun").Path.Replace('\','/')
# Lấy port đã ghi khi bắt đầu đúng lượt, không mặc định 8080 cho mọi target.
$recorded = @($book.runs | Where-Object { $_.run_id -eq $failedRun })
if ($recorded.Count -ne 1 -or [int]$recorded[0].port -lt 1) { throw 'Unknown original target port; inspect original inputs first' }
$env:RESTORE_WEB_PORT = [string]$recorded[0].port
Invoke-Checked -Exe 'docker' -Arguments @('compose','-p',$targetProject,
    '-f','compose.restore.yaml','logs','--no-color','--timestamps')
Invoke-Checked -Exe 'docker' -Arguments @('compose','-p',$targetProject,
    '-f','compose.restore.yaml','stop','web','db')
```

Nếu target chưa được tạo thì bỏ bước dừng target. Khi URL đã được nhả và còn đủ
tài nguyên, bật nguồn; không build trong xử lý này:

```powershell
Invoke-Checked -Exe 'docker' -Arguments @('compose','up','-d','--no-build',
    '--wait','--wait-timeout','180','db','web')
Invoke-RestMethod "$sourceUrl/health"
```

Không có result/secret gốc hoặc owner không rõ: dừng điều tra, không đoán target
hoặc tạo password mới. Dung lượng không đủ trả nguồn thì ghi lỗi tài nguyên;
không xóa volume/snapshot/prune. Không dùng `verify_retained.py` trong workflow
này vì còn finding resource gate muộn.

## 12. Phase 7 — cập nhật Sheets, video và hồ sơ nộp

| Đầu ra | Ai | Việc cần làm |
|---|---|---|
| Đo_lường_RPO_RTO.csv | Đa Minh, Minh Quân kiểm | Lấy từ --trial-dir; giữ run/version/OS/commit/status và link raw |
| Biên bản diễn tập và thay đổi runbook | Đa Minh ghi, Minh Quân xác nhận | Ghi lỗi/giúp đỡ thật; quyết định, changelog và retest |
| Danh_sách_Minh_chứng.csv | Cả hai | Cấu hình đã che, baseline/hash, log, bàn giấy, video, reviewer |
| Tab đo lường | Đa Minh | Thêm tên scenario thật; bốn kịch bản mở rộng chưa chạy giữ NOT TESTED |
| Tab biên bản | Minh Quân | Phát hiện/cô lập/bảo toàn/phục hồi/xác nhận, kênh, người quyết định, lỗi/cải tiến |
| Word/PPTX | Minh Quân | Cập nhật nguồn, CSV/biểu đồ đúng run, ảnh/video thật; mở kiểm native Office |
| Folder nộp | Đa Minh | Kiểm link bằng cửa sổ chưa đăng nhập; chỉ share hồ sơ đã review |

Tỷ lệ tệp đúng phải nêu mẫu số SQL/metadata, không thay tỷ lệ đơn trước sự cố.
Chưa có mục tiêu thì không vẽ đường mục tiêu hoặc kết luận đạt SLA. Giữ mọi FAIL/
NOT TESTED/N/A phù hợp. Đừng gán Linux/cloud là ảnh/thao tác Windows của nhóm.

### 12.1. Điền hồ sơ nào và như thế nào?

Mở ba CSV trong `$sessionDir` bằng Excel → Data → From Text/CSV → UTF-8/Comma:

- `Biên_bản_Diễn_tập_Runbook.csv`: một hàng mỗi bước có operator/observer,
  giờ UTC, lệnh, exit, expected/observed, status và đường dẫn file/ảnh. Nếu mất
  ACK thì ghi uncertain; không điền thành công theo suy đoán.
- `Thay_đổi_Runbook.csv`: issue cụ thể, bước lỗi, bằng chứng, cách sửa và run ID
  retest. Không có retest thì để NOT TESTED. v1.1 phải xuất phát từ quan sát thật.
- `Danh_sách_Minh_chứng.csv`: yêu cầu, trạng thái, link, run ID, nền tảng và
  người kiểm. Không đổi mọi dòng sang PASS chỉ vì main kết thúc.

Biên bản **bàn giấy** là buổi thảo luận quyết định, khác log chạy thực tế. Copy
mẫu biên bản sang `Bien_ban_ban_giay.csv` rồi điền ngày, người có mặt, ai cho phép
cô lập, ai giữ chứng cứ, ai quyết định phục hồi và kết thúc; ghi kênh liên hệ
thật của hai người ở bản nội bộ. Khi phát hiện → cô lập → bảo toàn → phục hồi →
xác nhận, nêu vì sao chọn bước và ai được quyền làm. Xác nhận/chữ ký phải do
người thật cung cấp. Không invent nội dung thảo luận hoặc ký thay.

Trong Sheet, với **mỗi run** ghi scenario thực tế, OS, commit, full snapshot,
manifest SHA, số dòng baseline/probe/tail, số ACK thiếu/trùng/uncertain, RTO,
khoảng lag quan sát, status và link. Nếu tab có tên/cột khác, map đúng cột thật,
không tự tạo tên tab rồi nói đã nộp. Hiện chưa có mục tiêu nên để cột đạt RTO/RPO
là NOT TESTED. DB-stop không là mất toàn máy chủ; SQL copy sai không là kho chính
bị mã hóa. Bốn tình huống mở rộng giữ NOT TESTED cho đến khi chạy đúng phạm vi.

### 12.2. Video demo 3–5 phút

OBS: quay bản đầy đủ từ trước fault đến xác minh phục hồi. Bản demo 3–5 phút có
thể rút phần chờ nếu chú thích tua/cắt; không dùng video biên tập để tính RTO.
Trong Guided lưu ảnh/UI trước WEB_OK. Nếu chỉ demo tiến độ, dùng web/health,
evidence lịch sử và CSV ghi rõ ngày/môi trường; không chạy full restore khi gate FAIL.

Mốc dựng bản ngắn gợi ý (đây là **timeline video**, không phải RTO đã đo):

| Mốc video | Khung hình phải thấy | Điều cần nói |
|---|---|---|
| 00:00–00:30 | Ngày/OS, commit, run ID, phạm vi lab và URL | Dữ liệu giả; stop DB là mô phỏng mất khả dụng |
| 00:30–01:00 | UI/health trước lỗi, receipt full ID và SHA | Snapshot cố định, baseline N dòng |
| 01:00–01:35 | INJECT, event fault và HTTP 503 | T0 từ journal; không dùng đồng hồ dựng phim |
| 01:35–02:30 | RECOVER, project target riêng, hash trước import và import thành công | Không đọc volume nguồn; đoạn chờ tua phải chú thích |
| 02:30–03:30 | DATA_VERIFIED/probe/restart, URL trước WEB_OK | Khớp toàn bảng; checkpoint có, tail chưa có |
| 03:30–04:30 | CSV đúng run, hash trước/sau, biên bản/v1.1 | RTO quan sát, lag quan sát, đơn thiếu; chưa cam kết SLA |
| 04:30–05:00 | Nguồn healthy và danh mục năm minh chứng | Hạn chế same-host; phần chưa chạy ghi NOT TESTED |

Giữ video đầy đủ để đối chiếu với events. Không hiện `.env`, `secrets/`, password,
token hoặc trang credential; xem lại cả âm thanh/ảnh desktop trước chia sẻ.
Không quay nguồn sau return rồi nói đó là target trước WEB_OK.

Các lượt khác (backup, Phase 3, đối chứng, v1.0/retest và FAIL) vẫn phải được
liệt kê riêng trong CSV minh chứng và nộp log theo allowlist của chính run đó.
Block bên dưới chỉ đóng gói main được chọn; không tự gộp số đo hoặc chứng nhận
những lượt còn lại. Bản đầy đủ của buổi giữ nguyên tại `work` trên máy lab.

### 12.3. Đóng gói năm minh chứng để nộp (PowerShell 5.1)

Thực hiện sau khi đã chạy main Guided, xuất `--trial-dir` và trả nguồn về healthy.
Các biến `$sessionDir`, `$main`, `$export` là của chính buổi Windows vừa chạy.
Đoạn này dành cho main PASS có `dataset_evidence_version=1`; các lượt FAILED/
ABORTED vẫn giữ nguyên ở work và ghi kết quả riêng, không xóa hoặc đổi thành PASS.
Không sao chép cả `work`, `backups`, `secrets`, không nhập SQL và không cần zip.

Năm minh chứng là: cấu hình đã che; dữ liệu mẫu/baseline; log; biên bản bàn giấy;
video phục hồi. JSONL source/restored là dữ liệu giả toàn bảng theo snapshot,
khác dump SQL private. Nộp JSONL sau khi nhóm xác nhận chỉ có dữ liệu giả.

1. Hoàn thành CSV biên bản, thay đổi runbook, danh sách minh chứng trong
   `$sessionDir`. Hoàn thành `Bien_ban_ban_giay.csv` trong cùng thư mục từ buổi
   bàn giấy (nếu chuyển sang TXT thì sửa allowlist đúng tên). Nội dung từ buổi
   thật: ngày/giờ, người tham dự, kịch bản, kênh báo, người quyết định, phát hiện/
   cô lập/bảo toàn/phục hồi/xác nhận, lỗi/cải tiến, run ID và kết luận. Không ký
   thay hoặc biến mẫu trống thành biên bản đã diễn ra.
2. Kết thúc transcript trước khi sao chép; nếu đã `Stop-Transcript` thì bỏ dòng
   đó. Tạo bản công bố riêng và mở review, giữ nguyên raw `powershell.txt`:

```powershell
Stop-Transcript
$publicTranscript = Join-Path $sessionDir 'powershell-cong-bo.txt'
if (Test-Path -LiteralPath $publicTranscript) { throw 'Public transcript already exists; review the existing copy.' }
$publication = foreach ($transcript in $book.transcript_files) {
    if (-not (Test-Path -LiteralPath $transcript -PathType Leaf)) { throw "Missing original transcript: $transcript" }
    "# Source transcript: $transcript"
    Get-Content -LiteralPath $transcript -Raw -Encoding UTF8
}
$publication | Set-Content -LiteralPath $publicTranscript -Encoding UTF8
notepad.exe $publicTranscript
```

Bản công bố tổng hợp các transcript đã ghi trong sổ run, có nhãn đường dẫn
nguồn; không phải một raw transcript liên tục. Giữ từng raw riêng và điền các
buổi còn thiếu trước đóng gói. Đọc bản công bố, ảnh/video và CSV trước bước tiếp. Nếu cần che bí mật, chỉ che
bản công bố, ghi nguồn và việc che trong biên bản; không sửa raw hoặc seal.
Transcript có thể chứa lệnh/giá trị vô tình nhập nên không tự coi luôn an toàn.
Chuẩn bị MP4 đã review; giữ bản quay đầy đủ ở máy nhóm. Bản demo 3–5 phút nếu
cắt/tua phải chú thích, không dùng thời lượng bản dựng làm RTO.

3. Chạy block đóng gói dưới đây. Khi được hỏi, nhập đường dẫn MP4 thật đã review,
   không nhập dấu ngoặc kép bao quanh. Giữ repo root làm working directory.

```powershell
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($main -notmatch '^p4-[a-z0-9-]{1,40}$') { throw 'Invalid main run ID.' }
$runDir = (Resolve-Path -LiteralPath (Join-Path 'work/recovery' $main)).Path
$metricsDir = (Resolve-Path -LiteralPath $export).Path
$sessionRoot = (Resolve-Path -LiteralPath $sessionDir).Path
$run = Get-Content -LiteralPath (Join-Path $runDir 'result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($run.run_id -ne $main -or $run.scenario -ne 'drill' -or
    $run.status -ne 'PASS' -or $run.return_source_status -ne 'PASS' -or
    $run.dataset_evidence_version -ne 1) { throw 'This block requires a completed main PASS with dataset evidence.' }

# Only fixed files are selected. Never copy a whole input directory recursively.
$runFiles = @(
    'result.json','events.jsonl','acknowledgements.json','backup-receipt.json',
    'observed-baseline.json','target-grants.txt',
    'source-dataset.jsonl','restored-dataset.jsonl',
    'extracted/manifest.json','extracted/payload/metadata.json',
    'extracted/verified.json','evidence-manifest.json'
)
$metricFiles = @('metrics.csv','Đo_lường_RPO_RTO.csv','metrics.json','integrity.json','manifest.json')
$sessionFiles = @(
    'run-sheet.json',
    'Biên_bản_Diễn_tập_Runbook.csv','Thay_đổi_Runbook.csv',
    'Danh_sách_Minh_chứng.csv','Bien_ban_ban_giay.csv','powershell-cong-bo.txt'
)
$configFiles = @(
    'compose.yaml','compose.backup.yaml','compose.restore.yaml',
    'compose.recovery-tools.yaml','.env.example',
    'SOURCE/config/backup_config.example','SOURCE/config/lab_config.example'
)
foreach ($name in $runFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $runDir $name) -PathType Leaf)) { throw "Missing run evidence: $name" }
}
foreach ($name in $metricFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $metricsDir $name) -PathType Leaf)) { throw "Missing metric output: $name" }
}
foreach ($name in $sessionFiles) {
    if (-not (Test-Path -LiteralPath (Join-Path $sessionRoot $name) -PathType Leaf)) { throw "Complete and review session evidence first: $name" }
}
foreach ($name in $configFiles) {
    if (-not (Test-Path -LiteralPath $name -PathType Leaf)) { throw "Missing public config: $name" }
}

# Validate bytes against the original run seal before copying.
$seal = Get-Content -LiteralPath (Join-Path $runDir 'evidence-manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($seal.run_id -ne $main) { throw 'Seal belongs to a different run.' }
foreach ($name in $runFiles) {
    if ($name -eq 'evidence-manifest.json') { continue }
    $entry = $seal.files.PSObject.Properties[$name]
    if ($null -eq $entry) { throw "Unsealed required file: $name" }
    $source = Get-Item -LiteralPath (Join-Path $runDir $name)
    $hash = (Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash
    if ($hash -ine $entry.Value.sha256 -or $source.Length -ne $entry.Value.size_bytes) {
        throw "Run evidence changed: $name"
    }
}

# Check the export really belongs to this run and its four data outputs match.
$metrics = Get-Content -LiteralPath (Join-Path $metricsDir 'metrics.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$metricManifest = Get-Content -LiteralPath (Join-Path $metricsDir 'manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (@($metrics.samples).Count -ne 1 -or $metrics.samples[0].run_id -ne $main -or
    $metricManifest.run_id -ne $main) { throw 'Metrics belong to a different run.' }
foreach ($name in $metricFiles) {
    if ($name -eq 'manifest.json') { continue }
    $expected = $metricManifest.outputs.PSObject.Properties[$name]
    if ($null -eq $expected -or
        (Get-FileHash -LiteralPath (Join-Path $metricsDir $name) -Algorithm SHA256).Hash -ine $expected.Value) {
        throw "Metric output changed: $name"
    }
}

$videoPath = Read-Host 'Duong dan MP4 demo da review'
$video = Get-Item -LiteralPath $videoPath
if ($video.PSIsContainer -or $video.Extension -ine '.mp4' -or $video.Length -le 0) { throw 'Choose an existing nonempty MP4.' }

$pack = Join-Path $sessionRoot ('nop-bai-' + [guid]::NewGuid().ToString('N').Substring(0,8))
New-Item -ItemType Directory -Path $pack | Out-Null
foreach ($name in @('01_cau-hinh','02_du-lieu-baseline','03_log','04_bien-ban','05_video')) {
    New-Item -ItemType Directory -Path (Join-Path $pack $name) | Out-Null
}
function Copy-EvidenceFile {
    param([string]$From,[string]$To)
    if (Test-Path -LiteralPath $To) { throw "Refusing to overwrite submission file: $To" }
    $source = Get-Item -LiteralPath $From
    if ($source.PSIsContainer -or ($source.Attributes -band [IO.FileAttributes]::ReparsePoint)) {
        throw 'Expected a regular reviewed source file.'
    }
    $parent = Split-Path -Parent $To
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -LiteralPath $source.FullName -Destination $To
    if ((Get-FileHash -LiteralPath $source.FullName -Algorithm SHA256).Hash -ne
        (Get-FileHash -LiteralPath $To -Algorithm SHA256).Hash) { throw 'Copy hash mismatch.' }
}

foreach ($name in $configFiles) {
    Copy-EvidenceFile -From $name -To (Join-Path (Join-Path $pack '01_cau-hinh') (Split-Path -Leaf $name))
}
# Keep the complete allowlisted run hierarchy for independent exporter review.
$runOut = Join-Path (Join-Path $pack '03_log') $main
foreach ($name in $runFiles) {
    Copy-EvidenceFile -From (Join-Path $runDir $name) -To (Join-Path $runOut $name)
}
# Presentation copies; originals remain in the sealed run directory above.
foreach ($name in @('source-dataset.jsonl','restored-dataset.jsonl','observed-baseline.json')) {
    Copy-EvidenceFile -From (Join-Path $runDir $name) -To (Join-Path (Join-Path $pack '02_du-lieu-baseline') $name)
}
$metricsOut = Join-Path (Join-Path $pack '03_log') ('metrics-' + $main)
foreach ($name in $metricFiles) {
    Copy-EvidenceFile -From (Join-Path $metricsDir $name) -To (Join-Path $metricsOut $name)
}
foreach ($name in $sessionFiles) {
    $folder = if ($name -eq 'powershell-cong-bo.txt') { '03_log' } else { '04_bien-ban' }
    Copy-EvidenceFile -From (Join-Path $sessionRoot $name) -To (Join-Path (Join-Path $pack $folder) $name)
}
if (-not $book.runbook_copy) { throw 'Record the frozen runbook used before packaging' }
Copy-EvidenceFile -From $book.runbook_copy -To (Join-Path (Join-Path $pack '04_bien-ban') (Split-Path -Leaf $book.runbook_copy))
Copy-EvidenceFile -From $video.FullName -To (Join-Path (Join-Path $pack '05_video') 'Demo_phuc_hoi.mp4')

# All raw/extra Docker or Restic .log files are excluded from this automatic copy.
# Add only separately reviewed publication copies before computing this last manifest.
$forbidden = @(Get-ChildItem -LiteralPath $pack -File -Recurse | Where-Object {
    $_.Extension -ieq '.sql' -or $_.Extension -ieq '.key' -or $_.Extension -ieq '.pem' -or
    $_.Name -ieq '.env' -or $_.Name -match '(?i)(password|access.token|private.key)'
})
if ($forbidden.Count -ne 0) { throw 'Forbidden file found. Review submission; do not share it.' }

# Run last, after human review and any permitted extra files. Do not self-hash.
$manifestPath = Join-Path $pack 'SHA256SUMS.csv'
$packFull = (Resolve-Path -LiteralPath $pack).Path.TrimEnd('\')
$hashes = @(Get-ChildItem -LiteralPath $pack -File -Recurse | Where-Object {
    $_.FullName -ne $manifestPath
} | Sort-Object FullName | ForEach-Object {
    [pscustomobject]@{
        path = $_.FullName.Substring($packFull.Length + 1)
        size_bytes = $_.Length
        sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
})
$hashes | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8
Write-Host ('Submission folder: ' + $pack)
Write-Host ('Files listed in SHA256SUMS.csv: ' + $hashes.Count)
```

4. Hai người kiểm `Danh_sách_Minh_chứng.csv`, điền link thật sau upload và kiểm
   bằng cửa sổ chưa đăng nhập. Nếu sửa file trong bộ nộp sau bước băm (kể cả thêm
   link vào CSV), chạy lại phần tạo `SHA256SUMS.csv` cuối cùng; không sửa raw/seal.
   Bản quay đầy đủ, raw transcript và dump private vẫn giữ trong khu vực lab.

Lưu ý kỹ thuật:
- JSONL chỉ là export dữ liệu giả, không chứa decryption key; tên/hash không làm
  dữ liệu trở nên vô hại nếu người dùng đã đưa thông tin thật vào lab. Review nội
  dung trước public, không chỉ kiểm đuôi file.
- `evidence-manifest.json` không băm chính nó; `SHA256SUMS.csv` không phải chữ ký.
  Review/pin bộ hash qua quy trình nhóm; khác thư mục không tạo storage độc lập.
- Không tự copy SQL hoặc secret để "đủ bộ". Thiếu file bắt buộc thì giữ lỗi và
  điều tra đúng run/version; không dựng file hoặc chép từ run khác.
- Raw allowlist hiện không gồm Docker/Restic logs. Events + bản transcript đã
  review cung cấp log nộp cơ bản; bổ sung log khác chỉ sau review và đưa vào bộ
  hash cuối. Không dùng `Copy-Item -Recurse` trên run root/extracted/payload.
- Đoạn này dùng cú pháp PowerShell 5.1, nhưng chưa có bằng chứng chạy native
  Windows trong môi trường hỗ trợ. Chạy ở đường dẫn repo ngắn, đủ dung lượng
  cho video/bản copy; không dùng cloud đang gần đầy. Không có thao tác service.

### 12.4. Build hồ sơ khi cần

Không phải bước bắt buộc để chạy lab. Môi trường tài liệu riêng cần python-docx,
python-pptx, matplotlib, Pillow; không thêm vào requirements Flask. Nguồn bài
báo cáo `THESIS/REPORT_GROUP08.md`, slide `THESIS/reporting/slides.json` và ba file
tài liệu gốc. Kiểm số liệu trước build; corpus mặc định của báo cáo vẫn là Linux.

Chỉ khi cần build, tạo môi trường tài liệu riêng (không cài vào container web):

```powershell
Invoke-Checked -Exe 'py' -Arguments @('-3','-m','venv','.venv-docs')
Invoke-Checked -Exe '.\.venv-docs\Scripts\python.exe' -Arguments @('-m','pip','install','python-docx','python-pptx','matplotlib','Pillow')
Invoke-Checked -Exe '.\.venv-docs\Scripts\python.exe' -Arguments @('-B','THESIS/reporting/build_documents.py')
Invoke-Checked -Exe '.\.venv-docs\Scripts\python.exe' -Arguments @('-B','THESIS/reporting/build_windows_guide.py')
```

Nếu `.venv-docs` đã có đúng dependencies thì bỏ hai dòng tạo/cài. Giữ môi trường
này ở máy nhóm, không upload vào bộ nộp. Ghi lại phiên bản packages dùng để xuất.

Không chạy builder rồi mặc định báo cáo đã đổi sang kết quả Windows: phải sửa
nguồn nội dung, dữ liệu/đường dẫn biểu đồ để đúng run mới và review trước. Bộ nộp
cần thêm Runbook Final DOCX/PDF đúng tài liệu đã dùng/cải tiến, báo cáo Word,
slide PPTX và biểu đồ nhiều lượt tương đương nếu đã chạy nhiều lượt. Chưa có mục
tiêu thì không tạo biểu đồ so sánh đạt mục tiêu; ghi phần này chưa được đánh giá.

Lệnh thứ nhất xuất lại báo cáo/PPTX và hình từ nguồn đã review; không xuất đè
runbook DOCX lịch sử. Lệnh thứ hai lấy HUONGDAN hiện tại để xuất
`THESIS/runbook/HuongDan_ThucNghiem.docx` và slide hướng dẫn Windows. Hai lệnh có
thể ghi đè artifact xuất của chính chúng, nên lưu/review chỉnh sửa Word/PPTX
trực tiếp và đồng bộ nguồn trước. Không làm giữa demo. PDF render tùy chọn bằng
LibreOffice, Office Windows vẫn cần mở kiểm riêng.

Nếu chưa đóng gói, kết thúc khi nguồn healthy và hồ sơ đã lưu bằng
`Stop-Transcript`. Nếu đã đóng gói theo mục 12.3 thì transcript đã dừng, không
cần dừng lần nữa. Mở folder bằng `Invoke-Item $pack` nếu đã tạo bộ nộp.
Nhóm tự upload folder đã review lên Drive, cấp quyền xem link theo yêu cầu và
kiểm trong cửa sổ chưa đăng nhập. Source code nộp bằng link repo/commit/PR và
bản đã kiểm; không upload `.git` có thông tin xác thực hoặc toàn checkout chứa
secret. Giữ bản quay đầy đủ ở nơi lưu nhóm, link từ danh sách minh chứng.

Chỉ ký nghiệm thu thực nghiệm khi các tiêu chí Windows đã chạy có log thật.
Quy trình phục hồi hoạt động và đạt mục tiêu RTO/RPO là hai kết luận riêng;
hiện kết luận đạt mục tiêu vẫn NOT TESTED.
