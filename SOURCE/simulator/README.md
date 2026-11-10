# Phase 4 — diễn tập tình trạng dịch vụ không khả dụng

Triển khai dùng chung baseline/restore trong `SOURCE/recovery/`, không dùng mã độc.
Ba action: `web-outage`, `reject-corrupt`, `drill`.

Xem [hướng dẫn và lệnh Windows/Linux](../recovery/README.md).
Kịch bản chính dừng DB nguồn, xác nhận HTTP 503, phục hồi snapshot vào volume mới,
đưa web target về URL nguồn và ghi đầy đủ sự kiện. Không đọc volume nguồn để
phục hồi, không giả số đo, không xóa volume/snapshot hay phá bảng để gây sự cố.
