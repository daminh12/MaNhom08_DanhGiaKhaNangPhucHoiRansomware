# Build và sử dụng hồ sơ Nhóm 08

Bộ file để nhóm review trước khi nộp:

- `THESIS/BaoCao_Nhom08.docx`: báo cáo tổng hợp, mở/sửa bằng Word.
- `THESIS/ThuyetTrinh_Nhom08.pptx`: 15 slide 16:9, text/shapes có thể chỉnh;
  mỗi slide có ghi chú thuyết trình và đường dẫn nguồn trong Notes.
- `THESIS/runbook/Runbook_v1.1.docx`: bản Word từ Markdown v1.1, không ghi đè v1.0.
- `THESIS/previews/`: PDF render để kiểm nhanh, không là ảnh minh chứng diễn tập.

Nguồn chỉnh nội dung là `THESIS/REPORT_GROUP08.md`, `reporting/slides.json` và
`runbook/Runbook_v1.1.md`. Build lại sẽ thay các file xuất ở trên và
`THESIS/SLIDES_GROUP08.md`, không đổi code lab, raw evidence hoặc DOCX dàn ý/v1.0.
Chỉnh trực tiếp Word/PPTX cần đồng bộ nguồn nếu muốn giữ khi build lại.

## Tái lập

Python cùng các thư viện python-docx, python-pptx, matplotlib và Pillow; phiên
bản thực đã dùng ở `docs/evidence/phase7/document-tools.json`. Không thêm các thư
viện này vào requirements của Flask hoặc Docker image lab. Không cần chạy Docker
để build hồ sơ. Nếu máy chưa có dependency, cài trong môi trường Python riêng
dành cho soạn tài liệu; không làm lúc bắt đầu demo.

```powershell
py -3 -B THESIS/reporting/build_documents.py
```

Build đọc metric từ CSV Phase 5 và raw main events, đối chiếu tiêu đề RTO trước
vẽ timeline. Slides/Markdown báo cáo vẫn là nội dung review của corpus cố định;
không tự nhận trial mới. Nếu đổi corpus, cập nhật nội dung, pin và kiểm lại mọi
con số; không chỉ chạy builder rồi nhận là có số đo mới.

Linux đã chạy để xuất PDF bằng LibreOffice headless:

```bash
soffice --headless --convert-to pdf --outdir work/phase7-preview THESIS/BaoCao_Nhom08.docx THESIS/ThuyetTrinh_Nhom08.pptx THESIS/runbook/Runbook_v1.1.docx
```

Font Office là Arial (code Consolas); biểu đồ dùng font DejaVu Sans đã rasterize.
Bản render kiểm tra bằng LibreOffice/Linux, chưa kiểm mở bằng Microsoft Office
trên Windows. Nhóm cần mở Word/PPTX trên máy thuyết trình, kiểm font/bảng/Notes
và lưu lại bản đã review trước khi nộp. Không suy ra Windows lab PASS từ việc
mở thành công tài liệu Office.

## Nội dung phải giữ khi chỉnh

Một main RTO 54.198351197 s; bounds send/ACK không là exact RPO; chưa có mục tiêu
SLA. Giữ FAILED/N/A và phân biệt history với proof mới. Phase 5 source health/count
unchanged khác Phase 6 full-source hash. Không dùng ghi chú phân công để ký thay
hoặc nhận thành viên đã thực hiện Codex/cloud checks. Trạng thái kỹ thuật còn
thiếu và action không được đưa vào demo nằm ở review/PHASE7_RESULTS.
