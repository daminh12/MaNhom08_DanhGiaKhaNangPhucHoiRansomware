# Cấu trúc slide bảo vệ — Nhóm 08

Đầu ra Phase 7 dự kiến: `THESIS/SLIDES_GROUP08.md` và
`THESIS/ThuyetTrinh_Nhom08.pptx`. Thiết kế một ý chính mỗi slide, chữ đủ lớn để
trình chiếu; các con số hiển thị làm tròn nhưng ghi giá trị chính xác ở notes hoặc
bảng evidence. Mỗi hình/log/số đo phải có nguồn để người xem đối chiếu.

| Slide | Nội dung | Điều bắt buộc nói rõ |
|---|---|---|
| 1 | Đề tài, Nhóm 08, hai thành viên | Bản tổng kết có giới hạn nghiệm thu, không tuyên bố Windows đã PASS |
| 2 | Vấn đề và mục tiêu | Mất khả dụng, backup phục hồi, kiểm toàn vẹn; không triển khai malware |
| 3 | Phạm vi/lý thuyết | Liên hệ ransomware và quy trình recovery; chưa thử encryption/exfiltration/host-loss |
| 4 | Kiến trúc lab | Flask/MySQL/Restic; DB nội bộ, localhost web, kho/secret cùng host |
| 5 | Backup và baseline | Dump nhất quán, metadata/manifest, full snapshot/digest, readback |
| 6 | Clean restore | Volume/network/project độc lập, no seed/source mount, readiness SELECT 1 |
| 7 | Dữ liệu và xác minh | Schema/toàn bảng trước probe, API tối đa 100, app grants và restart |
| 8 | Main drill timeline | Canary→snapshot→3 tail ACK→DB stop→target URL ready; return-source sau trial |
| 9 | Kết quả chính | RTO khoảng 54.20 s một mẫu; 105 baseline rows, 1 recovered ACK, 3 missing ACK, 0 duplicate/uncertain |
| 10 | Đọc đúng RPO/metric | Bounds khoảng 10.5184–10.5324 s không là exact RPO; backup age/import riêng; chưa target |
| 11 | Failure/negative tests | Schema mismatch FAILED giữ nguyên; corrupt copy từ chối; unsafe target/resource guard |
| 12 | Runbook v1.0→v1.1 | Bỏ placeholder/import nguồn, bổ sung gate/exit/evidence/abort; full Phase 6 NOT TESTED |
| 13 | Review/giới hạn | 76 unit Phase 6 khác runtime; Windows, independent storage, legacy backup, Flask/idempotency còn việc |
| 14 | Demo và kết luận | Ưu tiên evidence + chỉ đọc; control chỉ khi có gate/ReturnSource; việc tiếp theo có dependency |

Có thể gộp bớt slide khi trình bày 5–7 phút; xem `docs/KICH_BAN_DEMO.md`. Không
dùng ba scenario khác nhau làm ba lần lặp main, không vẽ chart “RPO đạt 0” và không
thể hiện Phase 7 soạn báo cáo như đã nghiệm thu toàn bộ công việc kỹ thuật.
