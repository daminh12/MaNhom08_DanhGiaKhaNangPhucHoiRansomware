# Hướng dẫn chạy thực nghiệm — Nhóm 08

Phiên bản thực hành Windows **v1.0**, cập nhật 16/11/2026 (UTC+7).
Đọc [các lưu ý](LUU_Y_THUC_NGHIEM.md) trước khi thao tác.
[Báo cáo các phase](BAO_CAO_CAC_PHASE.md) là nơi xem kết quả đã có.

Đây là đầu mối lệnh hiện hành thay cho các hướng dẫn module/runbook Markdown
trùng trước đây. Mã các lệnh đã tồn tại; PowerShell/Windows, Guided hai người và
video vẫn **NOT TESTED** cho đến khi nhóm thực hành. Làm từng bước, không copy
chạy cả tài liệu một lượt. Một bước FAIL dừng các bước phụ thuộc.

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

Mở PowerShell ở **repository root**, nơi có compose.yaml. Dùng nhánh đã review
chứa `-Guided` và `--trial-dir`, không mặc định main đã tích hợp các PR.

```powershell
git status --short --branch
git rev-parse HEAD
. .\SOURCE\recovery\start_session.ps1
```

Nếu policy PowerShell chặn script, có thể đặt `Set-ExecutionPolicy -Scope Process
-ExecutionPolicy Bypass` cho phiên đó rồi chạy lại dòng dot-source. Policy tổ chức
nếu có cần được xử lý trên máy nhóm; không sửa policy toàn máy để chạy lab.

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

Cổng target Phase 3 phải khác cổng nguồn và đang trống. Không thay .env/secret
hoặc rebuild giữa lượt đo. Guided yêu cầu file source đã commit và đúng byte Git;
nếu từ chối vì CRLF/thay đổi chưa commit, lưu/review thay đổi, chuẩn bị checkout LF
phù hợp trước lượt mới. Không reset để mất công việc và không sửa fingerprint.

## 3. Chuẩn bị lab và backup tool — trước thực nghiệm

### 3.1. Chỉ đối với lab mới hoàn toàn

Nếu đã có .env/secret/volume nguồn, bỏ qua init và giữ bản gốc. Trạng thái tạo
dở hoặc sai password cần điều tra, không tự tạo secret mới cho DB cũ.

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
Invoke-Recovery -LabArgs @('-Action','backup','-RunId',$backup)
$r = Get-Content "work/recovery/$backup/backup-receipt.json" -Raw -Encoding UTF8 | ConvertFrom-Json
if ($r.status -ne 'PASS' -or $r.snapshot_id -notmatch '^[a-f0-9]{64}$' -or
    $r.manifest_sha256 -notmatch '^[a-f0-9]{64}$') { throw 'Invalid backup receipt' }
$r | Select-Object run_id,snapshot_id,manifest_sha256
```

Controller dừng web, kiểm drained transactions, capture toàn bảng trước/sau dump
và buộc khớp; metadata baseline được hash/readback cùng SQL. Không admin writer/
DDL là điều kiện bắt buộc. Giữ receipt/full snapshot/digest/Git commit/baseline.
Không dùng latest hoặc ID/số liệu Linux cũ trên kho mới ở Windows.

## 6. Phase 3 — Minh Quân phục hồi sạch

Đa Minh quan sát/ghi lại. Lệnh này tạm dừng nguồn; target dùng cổng riêng. Không
có incident T0 nên chưa là mẫu RTO diễn tập:

```powershell
$restore = New-LabRunId -Phase p3 -Label restore
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

## 7. Phase 4 — hai đối chứng riêng

### 7.1. Dừng riêng web

```powershell
$gateWeb = New-LabRunId -Phase p4 -Label gate-web
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateWeb,'-PreflightScope','web-control')
$web = New-LabRunId -Phase p4 -Label web
Invoke-Recovery -LabArgs @('-Action','web-outage','-RunId',$web,'-ReturnSource')
Get-Content "work/recovery/$web/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
```

Đạt khi quan sát web unavailable rồi hoạt động, schema/toàn bảng không đổi và
return-source PASS. Không restore snapshot, RPO N/A; không tính thành main repeat.

### 7.2. SQL copy hỏng bị từ chối

Sau clean gate còn hợp lệ và receipt bước 5:

```powershell
$corrupt = New-LabRunId -Phase p4 -Label corrupt
Invoke-Recovery -LabArgs @('-Action','reject-corrupt','-RunId',$corrupt,
    '-BackupId',$r.run_id,'-SnapshotId',$r.snapshot_id,'-ManifestSha256',$r.manifest_sha256)
Get-Content "work/recovery/$corrupt/result.json" -Raw -Encoding UTF8 | ConvertFrom-Json
```

Chỉ sửa bản SQL copy trong work, giữ manifest/snapshot gốc. Expected:
`rejection=PASS`, `import_attempted=false`. Candidate integrity FAIL dự kiến,
negative test PASS; không outage nên RTO/RPO N/A. Thiếu disk không chạy được
Restic extract thì ghi NOT TESTED, không lấy local-copy check thay lượt đầy đủ.

## 8. Main Guided — diễn tập hai người

Đóng băng commit/hash **HUONGDAN v1.0** và biên bản trước lượt đầu. Minh Quân chỉ
nhìn bản đã đóng băng; mọi hỗ trợ hoặc sai sót phải ghi. Bật OBS trước fault;
không mở secret. Giữ một terminal/observer suốt ba xác nhận, không pipe đáp án.

```powershell
$gateMain = New-LabRunId -Phase p3 -Label gate-main
Invoke-Recovery -LabArgs @('-Action','preflight','-RunId',$gateMain)
$main = New-LabRunId -Phase p4 -Label main
Invoke-Recovery -LabArgs @('-Action','drill','-RunId',$main,
    '-Port',"$sourcePort",'-PostOrders','3','-Guided','-ReturnSource')
```

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

Expected profile: checkpoint phục hồi, ba tail ACK chưa phục hồi, duplicate/
uncertain = 0; base data/schema/grants/API/persistence PASS, probe riêng. Thiếu
ba tail đơn đúng snapshot khác sai SHA. Hủy/thất bại giữ kết quả thật và target dở.

## 9. Phase 5 — xuất đúng lượt và kiểm số đo

Chỉ đọc evidence của lượt mới, không gây outage:

```powershell
$export = "work/metrics-$main"
Invoke-Checked -Exe 'py' -Arguments @('-3','-B','SOURCE/metrics/export_metrics.py',
    '--trial-dir',"work/recovery/$main",'--output-dir',$export)
Import-Csv "$export/metrics.csv" -Encoding UTF8 |
    Format-Table run_id,trial_status,measurement_version,observed_rto_seconds,unrecovered_acknowledged_requests
```

Có thể thay `$main` bằng `$restore`, `$web`, `$corrupt` hoặc gate để xuất riêng.
Output phải mới, ngoài thư mục input. Giữ `result/events`, seal, ACK, receipt,
manifest/metadata/verified/observed baseline theo allowlist; đừng đổi tên thư mục
run hoặc sửa raw. Commit source thực thi cần có trong clone để kiểm fingerprints.

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

Mỗi lượt dùng preflight mới. Không gộp automated-v1 với guided-v2 hoặc gọi hai
mẫu là bằng chứng chắc chắn v1.1 nhanh hơn. Hai người review kết quả retest rồi
mới đánh dấu các mục Windows tương ứng PASS.

## 11. Lỗi, hủy và trả nguồn

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
# Đặt đúng port target của lệnh thất bại: sourcePort cho main, restorePort cho Phase 3.
$env:RESTORE_WEB_PORT = "$sourcePort"
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

OBS: quay bản đầy đủ từ trước fault đến xác minh phục hồi. Bản demo 3–5 phút có
thể rút phần chờ nếu chú thích tua/cắt; không dùng video biên tập để tính RTO.
Trong Guided lưu ảnh/UI trước WEB_OK. Nếu chỉ demo tiến độ, dùng web/health,
evidence lịch sử và CSV ghi rõ ngày/môi trường; không chạy full restore khi gate FAIL.

### Build hồ sơ khi cần

Không phải bước bắt buộc để chạy lab. Môi trường tài liệu riêng cần python-docx,
python-pptx, matplotlib, Pillow; không thêm vào requirements Flask. Nguồn bài
báo cáo `THESIS/REPORT_GROUP08.md`, slide `THESIS/reporting/slides.json` và ba file
tài liệu gốc. Kiểm số liệu trước build; corpus mặc định của báo cáo vẫn là Linux.

```powershell
py -3 -B THESIS/reporting/build_documents.py
py -3 -B THESIS/reporting/build_windows_guide.py
```

Lệnh thứ nhất xuất lại báo cáo/PPTX và hình từ nguồn đã review; không xuất đè
runbook DOCX lịch sử. Lệnh thứ hai lấy HUONGDAN hiện tại để xuất
`THESIS/runbook/HuongDan_ThucNghiem.docx` và slide hướng dẫn Windows. Hai lệnh có
thể ghi đè artifact xuất của chính chúng, nên lưu/review chỉnh sửa Word/PPTX
trực tiếp và đồng bộ nguồn trước. Không làm giữa demo. PDF render tùy chọn bằng
LibreOffice, Office Windows vẫn cần mở kiểm riêng.

Kết thúc khi nguồn healthy, dữ liệu/evidence giữ nguyên và hồ sơ đã lưu:

```powershell
Stop-Transcript
```

Chỉ ký nghiệm thu thực nghiệm khi các tiêu chí Windows đã chạy có log thật.
Quy trình phục hồi hoạt động và đạt mục tiêu RTO/RPO là hai kết luận riêng;
hiện kết luận đạt mục tiêu vẫn NOT TESTED.
