# Kịch bản demo 5–7 phút — Nhóm 08

Mục tiêu: trình bày kiến trúc, quy trình backup/restore và kết quả quan sát đã có.
Đây là demo tiến độ/kết quả có giới hạn, không tuyên bố toàn bộ dự án đã nghiệm
thu trên Windows hoặc chống được ransomware thực tế. Slide và báo cáo Phase 7
được soạn tại `THESIS/SLIDES_GROUP08.md`/`ThuyetTrinh_Nhom08.pptx` và
`THESIS/REPORT_GROUP08.md`/`BaoCao_Nhom08.docx`.

## Chuẩn bị trước giờ trình bày

- Dùng nhánh chứa code và evidence Phase 3–7, không giả định main đã có các PR
  này. Ghi branch/commit; giữ `.env`, secret và DB volume gốc.
- Mở sẵn báo cáo/slide, web nếu lab đang healthy, [main result](evidence/phase4/main-result.json),
  [CSV](evidence/phase5/export-20261110/metrics.csv), [Phase 6](PHASE6_RESULTS.md)
  và [Runbook v1.1](../THESIS/runbook/Runbook_v1.1.md).
- Mặc định demo bằng bằng chứng đã pin và web chỉ đọc. Nếu máy Windows chưa chạy
  thử launcher hoặc không có lab, trình bày evidence Linux; không bắt đầu cài lab
  hay diễn tập restore mới giữa giờ bảo vệ.
- Đề xuất Đa Minh thao tác, Minh Quân giải thích/ghi chép. Đây là phân công chưa
  xác nhận, không ghi là hai người đã thực hiện nếu chưa có biên bản.

## Thứ tự trình bày

| Thời lượng | Thao tác / nội dung nói | Điều cần nói đúng |
|---|---|---|
| 0:00–0:45 | Giới thiệu dữ liệu đơn hàng giả và kiến trúc Flask/MySQL/Restic/SHA | Thử khả năng phục hồi trước mất khả dụng; không chạy malware, không xóa bảng/volume |
| 0:45–1:30 | Mở web và GET health/API nếu lab có sẵn; nếu không mở ảnh Phase 1 đã lưu | 100 là số seed ban đầu, số hiện tại có thể lớn hơn. Ảnh cũ phải ghi ngày/OS cũ, không gọi ảnh Windows mới |
| 1:30–2:30 | Chỉ luồng consistent dump → manifest → full snapshot → stack sạch | Target không dùng volume nguồn, không seed; hash kiểm trước import và so schema/toàn bảng sau import |
| 2:30–3:45 | Mở main result và raw events ngày 10/11 | 105 dòng snapshot khớp, probe thêm riêng thành 106; nguồn trở lại 108. 1 ACK trước snapshot phục hồi, 3 ACK sau snapshot chưa phục hồi, 0 duplicate/uncertain trong profile này |
| 3:45–4:45 | Mở CSV bằng Excel hoặc PowerShell | Một main RTO 54.198351197 s; commit-age bounds 10.518407983–10.532435583 s không là exact RPO. Bốn CSV rows không phải bốn main trials |
| 4:45–5:45 | Show negative guard và lỗi đã giữ; nếu đủ điều kiện có thể demo web control | SQL copy hỏng bị từ chối trước import; first restore FAILED vẫn giữ. Start lại service nguồn không là Restic restore |
| 5:45–6:30 | Trình bày runbook v1.0→v1.1 và việc còn thiếu | Windows, independent storage, mục tiêu SLA và lượt Minh Quân độc lập chưa kiểm chứng; Phase 6 đầy đủ NOT TESTED |
| 6:30–7:00 | Giải đáp và kết luận phạm vi | Quy trình Linux đã hoạt động trong phép thử; chưa chứng minh đạt RTO/RPO objective hoặc khả năng chống mất host |

Không cần thêm đơn bằng UI trong phần trình bày chỉ đọc. Nếu nhóm chủ động tạo
đơn demo, ghi nhận nó riêng và không thay count/baseline/số đo lịch sử để làm đẹp.

## Lựa chọn live control chỉ khi đã chạy thử trước

Các lệnh dưới là workflow **đã có code** nhưng **native Windows NOT TESTED** trong
hồ sơ hiện tại. Chỉ chạy trên máy có lab healthy, Python 3.10+, Docker hoạt động,
không writer/backup/Scheduler khác. Không dùng gate web để cấp phép clean restore.

```powershell
$gate = 'p4-demo-gate-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action preflight -RunId $gate -PreflightScope web-control
if ($LASTEXITCODE -ne 0) { throw 'Gate FAIL: chỉ trình bày bằng chứng đã có' }
$trial = 'p4-demo-web-' + [guid]::NewGuid().ToString('N').Substring(0,12)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\recovery\run_lab.ps1 -Action web-outage -RunId $trial -ReturnSource
if ($LASTEXITCODE -ne 0) { throw 'Control/return-source lỗi: giữ journal và xử lý theo runbook' }
Invoke-RestMethod http://127.0.0.1:8080/health
```

Đổi URL nếu WEB_PORT đã thay. Kịch bản web chỉ dừng/start web, đối chiếu full DB
không đổi và ghi kết quả riêng; RPO N/A. Control thường ngắn, không hứa người xem
sẽ nhìn thấy outage qua thao tác refresh thủ công. Có thể dùng raw journal để chỉ
thời điểm script quan sát unavailable. Không gọi live control là clean restore.

PowerShell xem CSV lịch sử, không gây outage:

```powershell
Import-Csv .\docs\evidence\phase5\export-20261110\metrics.csv |
    Format-Table scenario,trial_status,observed_rto_seconds,rpo_status
```

Nếu script/gate lỗi, giữ result/events và chuyển sang trình bày evidence có sẵn;
không retry POST, reset repo hoặc xóa dữ liệu để chạy lại. Nguồn phải được trả về
healthy theo runbook; lỗi cleanup/return-source phải ghi riêng. Lượt mới có metric
riêng, không tái dùng 54.198351197 s như kết quả vừa chạy trên Windows.

## Câu trả lời ngắn khi giảng viên hỏi “đã hoàn thành chưa?”

“Nhóm đã có code và bằng chứng backup/clean restore/diễn tập trên Linux, kèm
metric và CSV truy vết. Runbook đã được cải tiến lên v1.1. Workflow Windows và
lượt chạy độc lập của thành viên vẫn cần kiểm chứng; chưa chốt mục tiêu RTO/RPO,
nên nhóm chỉ báo số quan sát và giới hạn, chưa kết luận đạt SLA.”
