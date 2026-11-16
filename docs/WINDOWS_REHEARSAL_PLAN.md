# Kế hoạch thực hành và bàn giao Windows — Nhóm 08

[Google Sheets yêu cầu](https://docs.google.com/spreadsheets/d/1akuMwhM-N3BXN0V8xOcPl2OdIb3PAh_oW5JUYyJivjI/edit).
[Kết quả triển khai và giới hạn kiểm thử](WINDOWS_TOOLING_RESULTS.md).

Ngày 16/11/2026 (UTC+7). Nguồn yêu cầu: Google Sheets PROJECT NHÓM 8 ATTT,
tab `planning `, `Đo lường RPO & RTO`, `Danh sách Minh chứng`,
`Biên bản Diễn tập & Runbook` đã đọc trong phiên review. Người dùng chưa xác nhận
bốn kịch bản mở rộng bắt buộc; hoàn tất MVP service-stop trước, không đổi tên
phép thử thành mất host/kho. Chưa đặt mục tiêu RTO/RPO.

## Bắt đầu ở đâu

Dùng [Runbook Windows v1.0](../THESIS/runbook/windows/Runbook_Windows_v1.0.md).
PowerShell tại repo root: `. .\SOURCE\recovery\start_session.ps1`.
Đa Minh chuẩn bị/gây sự cố/ghi nhận; Minh Quân phục hồi chỉ theo runbook.
Helper và Guided có mã, nhưng Windows/Powershell/OBS/hai người thật vẫn NOT TESTED.

| Bước | Ai | Công việc và điều kiện chuyển bước | Đầu ra |
|---|---|---|---|
| 1 | Cả hai | Ghi phạm vi, vai trò và hỏi giảng viên bốn tình huống mở rộng; không chờ để chuẩn bị MVP | Quyết định phạm vi trong biên bản |
| 2 | Đa Minh | Kiểm branch/commit, công cụ, source healthy, tài nguyên host/Docker; giữ secret cũ | Transcript, phiên bản, gate |
| 3 | Đa Minh | Controller backup mốc 0; receipt/check/readback PASS | Full snapshot, digest, baseline |
| 4 | Minh Quân | Restore sạch Windows, schema/toàn bảng/quyền/API/restart/cleanup/return PASS | Phase 3 Windows result/events |
| 5 | Đa Minh | Web-only và reject-corrupt tách riêng, gate đúng scope | Hai kết quả đối chứng, N/A đúng nghĩa |
| 6 | Cả hai | Đóng băng Windows v1.0, clean gate mới; Guided INJECT → RECOVER → WEB_OK | Raw journal, ACK, biên bản lỗi |
| 7 | Đa Minh | Export bằng --trial-dir, đối chiếu số đo và input hashes | CSV/JSON/manifest của đúng run |
| 8 | Minh Quân | Sửa v1.1 theo quan sát thật; ghi hỗ trợ, không tạo lỗi giả | Runbook v1.1 và changelog |
| 9 | Cả hai | Chạy lại cùng guided-v2 với run mới; quay đầy đủ và demo 3–5 phút | Retest, video, CSV mới |
| 10 | Cả hai | Cập nhật Sheets/Word/PPTX, review link và số liệu | Bộ nộp có trạng thái thật |

Buổi 1 chuẩn bị mã/tài liệu; buổi 2 nghiệm thu Phase 3 và lượt đầu; buổi 3 cải
tiến/retest/video; buổi 4 hoàn thiện hồ sơ. Đây là lịch đề xuất, không là chấm công.
Mỗi gate FAIL dừng nhánh phụ thuộc. Không xóa dữ liệu hoặc bỏ qua gate để kịp lịch.

## Mã và tương thích

- `drill --guided` / PowerShell `-Guided` giữ một observer trong toàn bộ bàn giao.
  Chỉ nhận terminal tương tác, không pipe xác nhận; source thực thi phải committed.
  guided-v2 chốt RTO sau comparison ACK, WEB_OK, recheck dữ liệu và stable health.
  Thời gian đọc tài liệu nằm trong RTO. Automated-v1 vẫn giữ định nghĩa cũ.
- Result schema 2 và evidence-manifest ghi runtime, observer ID và hash mã nguồn.
  Manifest băm các file cho phép, bỏ SQL/secret, không phải chữ ký/immutable storage.
- `export_metrics.py --trial-dir work/recovery/<run-id> --output-dir work/metrics-<run-id>`
  kiểm seal, source Git, snapshot, baseline, thời gian, ACK và xuất CSV mới.
  Không --trial-dir vẫn là corpus lịch sử. Không ghi đè export cũ.
- Giữ bộ Word/PPTX Phase 7 là hồ sơ Linux lịch sử. Có phụ lục thực hành mới;
  chỉ thay số đo chính sau khi có Windows evidence thực sự và review nguồn.

## Dữ liệu ghi vào Sheets

Giữ tên kịch bản đúng với phép thử; không điền số vào bốn hàng mở rộng chưa chạy.
Cột phát hiện dùng một khoảng phát hiện của script, không phải mean IDS. Cột cô
lập N/A nếu chưa có phép đo hành động cô lập riêng. Cột RPO diễn giải bounds
send/ACK và số ACK chưa phục hồi; exact RPO/đạt target vẫn NOT TESTED. Tỷ lệ file
ghi rõ mẫu số SQL/metadata; không thay tỷ lệ toàn bộ đơn hàng trước sự cố.

CSV mẫu trong docs/templates/windows được copy vào session: biên bản, danh sách
minh chứng, bảng thay đổi. Đo_lường_RPO_RTO.csv do exporter tạo, không nhập số giả.
Không ghi tên người ký hoặc trạng thái PASS thay hai thành viên.

## Giới hạn và việc chưa làm

Không có Windows 10/PowerShell/Desktop tại cloud này; còn thiếu thực hành thật,
video, Word/PowerPoint native và cập nhật Sheet từ kết quả đó. Disk cloud khoảng
122 MiB tại kiểm kê, không chạy restore mới. API chưa idempotent: profile tuần tự,
không retry, uncertain phải dừng. Legacy PS/SH backup còn finding concurrency/
cleanup/log; chỉ Setup tuần tự khi cần, không Scheduler song song. Flask advisory,
verify_retained gate muộn và storage độc lập chưa được đóng bởi phần bổ sung này.

Phục hồi kỹ thuật PASS khác đạt mục tiêu RTO/RPO; mục tiêu chưa chọn. Bốn kịch bản
mở rộng chỉ được nghiệm thu sau khi xác nhận yêu cầu và có lab/bằng chứng tương ứng.
