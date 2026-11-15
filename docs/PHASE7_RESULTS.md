# Phase 7 — rà soát cuối và hồ sơ Word/PowerPoint

Ngày 15/11/2026. Nhánh `codex/group08-phase7-report-20261115`, dựa trên Phase 6
`8bb0d8e21485590258c2dd7e54562c5a3da4c3b9`. **GO cho bộ hồ sơ để review và demo
tiến độ có giới hạn; chưa nghiệm thu toàn bộ dự án.** Các PR Phase 3–6 chưa merge
main tại lúc đối chiếu. Không tự merge bất kỳ nhánh nào.

## Hồ sơ đã hoàn thiện để review

| File | Nội dung / kết quả kiểm |
|---|---|
| `THESIS/BaoCao_Nhom08.docx` | Báo cáo Word 17 trang render, 13 chương, mục lục theo chương; phương pháp, kiến trúc, kết quả, giới hạn, nguồn và phụ lục snapshot |
| `THESIS/ThuyetTrinh_Nhom08.pptx` | 15 slide 16:9, có speaker notes/sources ở từng slide; text/shapes chỉnh sửa được |
| `THESIS/runbook/Runbook_v1.1.docx` | Bản Word 11 trang từ Markdown v1.1; giữ v1.0 của Minh Quân và hai dàn ý DOCX gốc |
| `THESIS/previews/*.pdf` | PDF render bằng LibreOffice/Linux để đọc/soát layout, không là ảnh minh chứng diễn tập |
| `THESIS/REPORT_GROUP08.md`, `SLIDES_GROUP08.md`, `reporting/slides.json` | Nguồn nội dung có thể đối chiếu và build lại |
| `THESIS/reporting/build_documents.py`, `README.md` | Build artifact và sơ đồ/timeline; không gọi Docker hoặc sửa raw evidence |
| `docs/reviews/PHASE7_REVIEW.md` | Finding mới, patch, giới hạn và quyết định bàn giao |
| `docs/CHECKLIST_YEU_CAU.md` | 21 yêu cầu gắn file, evidence và PASS/FAIL/NOT TESTED theo phạm vi |
| `docs/NHAT_KY_THUC_NGHIEM.md`, `PHAN_CONG_CONG_VIEC.md`, `KICH_BAN_DEMO.md` | Nhật ký dựa evidence, phân công đề xuất chưa ký xác nhận, demo 5–7 phút |
| `THESIS/templates/report_outline.md`, `slide_outline.md` | Dàn ý cập nhật cho hồ sơ hiện hành; các file này trước đó trống |

Không tự thêm trường/lớp/MSSV/giảng viên hoặc chữ ký chưa được cung cấp. Hai tên
thành viên và mốc sáu tuần là thông tin nhóm đã cho. Không gán Codex/Linux checks
là hai thành viên đã trực tiếp chạy Windows. Mục tiêu RTO/RPO vẫn chưa chọn.

## Review mã nguồn và patch cần thiết

Phát hiện direct `restore`/`drill` có thể bỏ Docker-capacity gate riêng của
preflight. Commit `5d6c8328b621c5cc3e8d08d4a303da3d8bb3d686` dùng chung kiểm host và
filesystem Docker trước POST/stop, không cộng credit host vào free space Docker.
Sửa `SOURCE/recovery/controller.py` và thêm hai test có nhiều case trong
`SOURCE/tests/test_recovery.py`. Không sửa app/dependency/Compose hoặc hồi tố timing.

Finding còn mở: API idempotency; backup entrypoint cũ staging/cleanup/log;
Flask 3.1.2; `verify_retained` còn kiểm resource sau stop; cùng host; yêu cầu nguồn
healthy khi bắt đầu; workflow Windows/Task Scheduler. Không đưa action hậu kiểm
retained vào demo trong điều kiện disk hiện tại. Chi tiết file/dòng và hướng xử
lý trong review cuối; Word/PPTX không biến các finding này thành đã đóng.

## Kiểm thử thực tế của lượt Phase 7

| Kiểm tra | Bằng chứng | Kết luận |
|---|---|---|
| Recovery guard/ACK/full dataset | `recovery-unit.txt`: 29 tests | PASS unit/mock, bao gồm direct CLI VM DB/staging đầy và đủ chỗ |
| App / backup / metrics | `app-unit.txt` 14, `backup-unit.txt` 14, `metrics-unit.txt` 21 | PASS, tổng hiện tại **78** unit, không skip trong môi trường có private artifact |
| Resource gate hiện tại | `resource-gate-result.json`, `events.jsonl`, console | Expected refusal PASS; requirement đủ disk FAIL; source_touched=false, target_created=false |
| Runtime/restore mới trên code patch | Không chạy vì gate thiếu tài nguyên | NOT TESTED; không có outage hoặc main trial mới |
| Word/PPTX packages | XML/ZIP, 15 slides/notes, metric content đối chiếu CSV | PASS theo `artifact-qa.json` |
| Render/layout | 17 trang report, 11 trang runbook, 15 slide PDF; contact sheets | PASS kiểm LibreOffice/Linux; không trang chỉ có header/footer hoặc chữ ra ngoài trang |
| Microsoft Office native trên Windows | Chưa mở trên máy Windows trong phiên này | NOT TESTED; nhóm cần kiểm máy trình chiếu trước nộp |
| Provenance/evidence | Snapshot/CSV/raw phases trước, source/build/output SHA | PASS theo `verification.json` và `manifest.json`; metadata lịch sử kiểm qua đúng Git ref |

Lệnh đã chạy và exit code ở `docs/evidence/phase7/test-commands.json`. Các suite
đúng runtime: app trong container web hiện có; các suite còn lại host stdlib.
Một lỗi fixture mock lúc thêm test được giữ riêng, không gọi là lỗi DB thật.
Code báo cáo đọc CSV/raw events và kiểm tiêu đề biểu đồ RTO khớp trước build.

Render ban đầu phát hiện trang trắng và header card slide sát body; đã sửa ngắt
trang ở heading, khoảng cách và kích thước chữ, sau đó render/soát lại toàn bộ.
Contact sheets là bằng chứng kiểm tài liệu, không phải screenshot Windows/lab.
LibreOffice đã dùng font thay thế tương ứng trên Linux; Office file khai báo
Arial/Consolas. Microsoft Word/PowerPoint Windows vẫn cần kiểm riêng.

## Những kết luận được giữ nguyên

- Chỉ một main sample Linux: RTO 54.198351197 s; detection interval 1.986393601 s;
  send/ACK commit-age bounds 10.518407983–10.532435583 s. Không exact RPO hoặc SLA.
- ACK comparison đóng sau ready 396,797 ns; không nói RTO chứa bước chốt đó.
- Snapshot 105 base rows, probe thêm riêng thành 106 trên target; nguồn về 108
  sau trial. 3 tail ACK chưa phục hồi, 0 duplicate/uncertain trong profile không retry.
- Phase 5 source_unchanged chỉ health/count. Phase 6 full-source hash là kiểm
  riêng; không dùng hai bằng chứng thay thế lẫn nhau.
- Failed restore và corrupt-input test vẫn giữ đúng trạng thái. Tái xuất corpus
  lịch sử không được tính là performance trial mới.
- Phase 6 đầy đủ, clean restore mới, Windows và lượt Minh Quân độc lập vẫn NOT
  TESTED; thiếu disk chưa được giải quyết bằng xóa dữ liệu hoặc volume/snapshot.

## Điều kiện bàn giao/việc còn lại

Hồ sơ sẵn sàng để hai thành viên đọc và phản biện. Đa Minh được đề xuất chuẩn bị
đủ disk, chạy Windows theo runbook; Minh Quân chạy độc lập và đồng bộ bản Word
với kết quả thực, kiểm speaker notes/CSV và ghi biên bản. Nhóm review PR phụ thuộc
trước khi tích hợp, không ký nghiệm thu thay thành viên hoặc giảng viên.

Để gọi toàn bộ dự án hoàn thành cần đóng các yêu cầu còn thiếu trong checklist
đúng phạm vi cam kết, kiểm artifact trên máy trình chiếu, và xác nhận của nhóm.
Hồ sơ Phase 7 không phải lý do bỏ qua blocker Phase 6 hoặc tự đặt mục tiêu SLA.
