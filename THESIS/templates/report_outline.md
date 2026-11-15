# Cấu trúc báo cáo tổng hợp — Nhóm 08

Đầu ra Phase 7 dự kiến: `THESIS/REPORT_GROUP08.md` là nội dung nguồn để review,
`THESIS/BaoCao_Nhom08.docx` là bản Word xuất từ nội dung đã đối chiếu. Giữ nguyên
hai DOCX dàn ý của Minh Quân; không sửa tài liệu lịch sử để hợp thức hóa kết quả.

1. **Trang bìa và phạm vi nghiệm thu:** tên đề tài, Nhóm 08, Đa Minh/Minh Quân;
   để trống thông tin trường/lớp/MSSV/giảng viên khi chưa có, không bịa dữ liệu.
2. **Tóm tắt:** mục tiêu, lab giả, một main trial Linux, kết quả quan sát và giới
   hạn Windows/targets/storage; không mở đầu bằng tuyên bố đã chống ransomware.
3. **Cơ sở lý thuyết:** ransomware/RaaS ở mức bối cảnh; SANS PICERL/NIST CSF,
   backup/restore/integrity và RTO/RPO objective. Phân biệt lý thuyết 3-2-1 với
   triển khai cùng host thực tế; không gán Wazuh/Sysmon/SSH cho lab chưa có.
4. **Yêu cầu và kiến trúc:** Docker Compose, Flask/MySQL 8.4.7, lab_config.orders,
   fake-only, app role, consistent dump/Restic/SHA, target sạch. Dẫn tới checklist.
5. **Phương pháp và an toàn:** stop service; selected full snapshot; baseline
   độc lập với import, hash toàn bảng và schema, API window 100, probe riêng,
   restart và cutover; không malware/phá bảng/xóa volume.
6. **Thực hiện Phase 0–6:** mô tả code/bằng chứng theo mốc; ghi run FAILED, code
   hardening sau integration có bằng chứng riêng; không gộp unit và runtime.
7. **Kết quả và cách đo:** T0/Tready monotonic, RTO, MTTD quan sát, backup age,
   import duration, send/ACK bounds và missing count. Bốn case CSV, một main trial;
   không tạo average/CI, exact RPO hoặc mục tiêu sau khi thấy số.
8. **Review và runbook:** finding đã sửa/còn mở, v1.0→v1.1, nguồn healthy là
   precondition hiện tại; Windows và rehearsal Minh Quân độc lập NOT TESTED.
9. **Thảo luận/giới hạn:** same-host backup/secret/journal, resource gate FAIL,
   retry/idempotency, dependency/legacy entrypoint, single Linux/VFS sample,
   không airgap/offsite/immutable/host-loss evidence.
10. **Kết luận và công việc tiếp:** đánh giá quy trình đã chứng minh trong phạm vi;
    tách kết quả này với đạt objective; đề xuất owner/dependency, không ký thay nhóm.
11. **Tài liệu tham khảo/phụ lục:** nguồn chính thức có metadata đã kiểm chứng,
    bản đồ requirement→code→test→evidence, run/snapshot/digest, file/log và demo.

Kiểm trước khi xuất Word: số liệu khớp CSV/JSON/raw events; mọi hình thật ghi ngày/
OS/source; sơ đồ là sơ đồ kiến trúc, không gọi ảnh test. Các citation chưa xác minh
tác giả/năm không được chép nguyên như tài liệu đã đọc. Định nghĩa metric dùng
Phase 5/v1.1 thay công thức T0−backup hoặc lựa chọn T3/T4 trong dàn ý cũ.

Trạng thái chi tiết: `docs/CHECKLIST_YEU_CAU.md`, `docs/PHASE6_RESULTS.md` và hồ sơ
review/kiểm định artifact Phase 7. Có file DOCX/PPTX không tự chứng minh các test
còn thiếu đã PASS.
