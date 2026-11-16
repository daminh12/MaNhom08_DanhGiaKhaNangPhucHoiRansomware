# Phân công đề xuất và bàn giao — Nhóm 08

Nhóm: Đa Minh và Minh Quân; thời lượng kế hoạch 6 tuần. Bảng này là **đề xuất để
hai thành viên xác nhận**, không là bảng chấm công hoặc chứng nhận đã hoàn thành.
Các lượt Linux/cloud trong evidence do Codex hỗ trợ không được gán là hai thành
viên đã chạy trên Windows. Chưa đặt ngày hoàn thành giả hoặc ký thay thành viên.

| Hạng mục | Người đề xuất phụ trách | Người đối chiếu | Đầu ra/điều kiện xác nhận | Tình trạng căn cứ evidence |
|---|---|---|---|---|
| Lab/app/database/Compose | Đa Minh | Minh Quân | Lệnh cài đặt, health, schema/grants, fake-only UI; transcript Windows | Code và Linux evidence có; Windows NOT TESTED |
| Backup nhất quán/Restic/manifest | Đa Minh | Minh Quân | Receipt full snapshot/digest, repo check/readback; kiểm cleanup/log | Linux PASS trong phạm vi thử; entrypoint cũ còn finding |
| Clean restore và kiểm dữ liệu | Đa Minh | Minh Quân | Volume/network/project sạch, no seed/source mount; full schema/hash, quyền, API, restart | Linux historical PASS; lượt Windows/restore mới Phase 6 NOT TESTED |
| Diễn tập lành tính và nhật ký ACK | Đa Minh gây sự cố/ghi nhận; Minh Quân phục hồi | Hai người đối chiếu | Gate PASS, Guided INJECT/RECOVER/WEB_OK, raw events và request comparison, return-source | Có một main trial Linux; Guided Windows và hai người thật NOT TESTED |
| Lý thuyết, runbook và truy vết yêu cầu | Minh Quân | Đa Minh kiểm lệnh/path | Đồng bộ Word với v1.1, giải thích RTO/lag/scope, bỏ placeholder/import nguồn | Outline/Word cũ có; v1.1 Markdown đã soạn; lượt Minh Quân độc lập NOT TESTED |
| CSV/kết quả và bằng chứng | Đa Minh tính/kiểm exporter | Minh Quân đối chiếu báo cáo | Các số trong Word/PPTX khớp raw Git pin và CSV; giữ FAILED/N/A/NOT TESTED | Có CSV lịch sử, hash và provenance; replay không thành trial mới |
| Nguồn lực cho lượt nghiệm thu tiếp | Đa Minh | Minh Quân ghi gate | Đủ disk host và Docker; không xóa volume/snapshot để có chỗ | Clean gate FAIL tại Phase 6; cần mở rộng/chuẩn bị lab khác |
| Chạy độc lập Runbook v1.1 | Minh Quân thao tác | Đa Minh hỗ trợ khi có lỗi | Windows transcript, Git/tool versions, exit code, result/journal và nhận xét từng bước | NOT TESTED; không ký PASS trước khi thực hiện |
| Báo cáo Word và slide cuối kỳ | Minh Quân biên tập nội dung | Đa Minh xác nhận kỹ thuật | Review `THESIS/REPORT_GROUP08.md`/`BaoCao_Nhom08.docx` và `SLIDES_GROUP08.md`/`ThuyetTrinh_Nhom08.pptx` | Có artifact Phase 7 dựa trên Linux; cần bổ sung Windows thật và kiểm native Office |
| Review/merge PR và kết luận nộp bài | Cả hai thành viên | Cả hai thành viên | Review PR phụ thuộc đúng thứ tự, đối chiếu trạng thái thật; không auto-merge | Chưa có chữ ký/họp nghiệm thu trong hồ sơ hiện có |

Ưu tiên phụ thuộc: đủ disk → clean gate → Windows Phase 3 → main drill mới (nếu
chạy) → kết quả/pin mới → review báo cáo. Đồng bộ tài liệu và xem evidence lịch sử
có thể thực hiện khi đang chờ tài nguyên.

Mục bổ sung khi nhóm thực hiện thật: ngày UTC, máy/OS, Git commit, run ID, tên
người thao tác/người ghi, kết quả PASS/FAIL/NOT TESTED, link raw evidence và ý kiến
review. Chỉ ghi hoàn thành sau khi các điều kiện tương ứng đã được đối chiếu.
