# Checklist nghiệm thu Phase 1

Đây là checklist chưa điền kết quả. Người chạy ghi PASS/FAIL/NOT TESTED cùng đường dẫn bằng chứng; không đánh dấu theo kết quả máy khác. Phạm vi Windows 10 của nhóm cần kiểm tra trực tiếp.

| ID | Kiểm tra và điều kiện đạt | Kết quả / bằng chứng |
|---|---|---|
| P1-01 | Docker client/server hoạt động; Compose v2; `docker info --format '{{.OSType}}'` trả `linux` | Chưa ghi |
| P1-02 | Script tạo cấu hình thành công; các file bí mật được Git bỏ qua; chạy lại không ghi đè file có sẵn | Chưa ghi |
| P1-03 | `docker compose config --quiet` trả exit 0 | Chưa ghi |
| P1-04 | `docker compose up -d --build --wait --wait-timeout 180` thành công; `web` và `db` healthy | Chưa ghi |
| P1-05 | Lần khởi tạo volume đầu tiên có đúng 100 dòng tại `lab_config.orders`, trước smoke test/thêm trên UI | Chưa ghi |
| P1-06 | `/health` trả 200 và kết quả truy vấn DB thật; số dòng đồng nhất với API | Chưa ghi |
| P1-07 | Trang danh sách hiển thị dữ liệu giả; thêm đơn hàng hợp lệ được lưu và xem lại | Chưa ghi |
| P1-08 | Dữ liệu không hợp lệ bị từ chối; lỗi DB không lộ mật khẩu/chi tiết kết nối | Chưa ghi |
| P1-09 | Unit test và smoke test được phát hiện, chạy thật và PASS; không dùng “Ran 0 tests” làm bằng chứng | Chưa ghi |
| P1-10 | Sau restart, số dòng và ID bản ghi đã tạo còn nguyên; seed không bị chạy lặp | Chưa ghi |
| P1-11 | Web chỉ publish `127.0.0.1`, nối `frontend` và `lab`; DB chỉ nối mạng `lab` internal, không publish port host | Chưa ghi |
| P1-12 | `SHOW GRANTS` của `group08_app` chỉ cấp quyền nghiệp vụ SELECT/INSERT; không DROP/ALTER/DELETE | Chưa ghi |
| P1-13 | Khi dừng riêng DB trong bài test health, web trả 503; sau khởi động lại DB health trở về 200 | Chưa ghi |
| P1-14 | Nhóm chạy lại hướng dẫn trên Windows 10 và ghi phiên bản Docker/Compose, log thật | Chưa ghi |

Hồ sơ mỗi lần chạy cần có thời điểm, OS, phiên bản công cụ, commit/branch, lệnh, mã thoát, kết quả và lỗi/hạn chế. Che bí mật trước khi đưa log vào repository.

Giới hạn nghiệm thu: chưa có backup/restore, diễn tập độc lập theo Runbook, RTO/RPO hoặc kiểm chứng chống ransomware. Persistence qua restart chỉ kiểm tra volume, không phải phục hồi từ bản sao lưu. Bridge frontend không chặn outbound Internet của web, nên không đánh giá lab là air-gapped.
