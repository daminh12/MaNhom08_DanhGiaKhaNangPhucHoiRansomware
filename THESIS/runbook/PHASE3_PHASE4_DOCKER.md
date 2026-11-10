# Phần bổ sung Runbook v1.0 — Phase 3/4 Docker

Phần này bổ sung quy trình phục hồi sạch cho DOCX của Minh Quân; DOCX gốc được
giữ nguyên để nhóm review. Không dùng mục 9.2 cũ để import vào DB nguồn.

1. Kiểm tra nguồn healthy, đúng project `group08-lab`, dữ liệu giả LAB-, Docker
   images/secret/repository sẵn sàng, đủ chỗ, không chạy backup/workload khác.
2. Chạy `backup`, lưu receipt full snapshot ID + manifest digest; baseline độc
   lập nằm trong metadata đã được Restic bảo vệ và đọc lại.
3. Chạy `restore` vào project/volume/network mới, cổng 8081; không seed hoặc mount
   source volume. Theo dõi journal, kết quả schema/all rows/quyền/API/restart.
4. Chỉ bắt đầu diễn tập chính trong phạm vi môi trường đã được Phase 3 chứng minh.
   Windows chưa chạy phải giữ NOT TESTED, không lấy kết quả cloud thay thế.
5. `web-outage`: dừng/start web, xác nhận unavailable và dataset không đổi.
6. `reject-corrupt`: kiểm tra bản SQL copy bị sửa phải bị từ chối trước import;
   giữ nguyên repo, snapshot và manifest; RTO/RPO không áp dụng.
7. `drill`: tự ghi canary trước snapshot, ACK các đơn sau snapshot, dừng DB,
   xác nhận 503, chuyển sang recovery stack tại URL gốc. Không retry write.
8. T0 trước stop; Tready sau toàn bộ kiểm chứng, probe/restart và stable health.
   Giữ riêng mất đơn theo ACK, duplicate, uncertain và khoảng tuổi commit từ
   send/ACK. Không coi timestamp created_at_utc là thời điểm commit.
9. Khi kết thúc/hủy, giữ journal/result/volume; không sửa FAILED thành PASS.
   ReturnSource diễn ra sau trial, không phải phục hồi từ snapshot và không nằm
   trong observed RTO. Cleanup lỗi không được che lỗi chính.
10. Copy log/metadata đã kiểm tra vào evidence, không copy secret hoặc SQL dump.
    MQ đối chiếu từng bước trên Windows và ghi sai sót; v1.1 formal thuộc Phase 6.

Lệnh và prerequisite chính xác: [SOURCE/recovery/README.md](../../SOURCE/recovery/README.md).
