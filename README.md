# ĐÁNH GIÁ KHẢ NĂNG PHỤC HỒI TRƯỚC SỰ CỐ MÃ HÓA TỐNG TIỀN BẰNG MÔ PHỎNG AN TOÀN

## 1. Thông tin đề tài

- Môn học: An toàn thông tin
- Đề tài: 08
- Nhóm: 08
- Số lượng thành viên: 02
- Thời gian thực hiện: 06 tuần

## 2. Mục tiêu

Xây dựng môi trường mô phỏng an toàn nhằm đánh giá khả năng phòng ngừa, phát hiện, cô lập và phục hồi dữ liệu trước sự cố mã hóa tống tiền.

## 3. Công nghệ sử dụng

- VirtualBox / VMware
- Python
- Restic / BorgBackup
- MinIO
- SHA-256
- Git và GitHub

## 4. Cấu trúc Repository

- SETUP: Hướng dẫn cài đặt môi trường.
- SOURCE: Mã nguồn và dữ liệu thực nghiệm.
- THESIS: Báo cáo, slide, runbook và minh chứng.
- SOFT: Danh sách phần mềm sử dụng.
- docs: Checklist và tài liệu quản lý dự án.

## 5. Quy trình thực hiện

1. Xây dựng môi trường lab.
2. Tạo dữ liệu mẫu và bản sao lưu.
3. Tạo baseline SHA-256.
4. Mô phỏng sự cố bằng chương trình lành tính.
5. Đánh giá khả năng phát hiện và cô lập.
6. Thực hiện phục hồi.
7. Kiểm tra tính toàn vẹn dữ liệu.
8. Tổng hợp kết quả và đánh giá RPO/RTO.

## 6. Giới hạn an toàn

- Chỉ thao tác trên dữ liệu giả.
- Không sử dụng mã độc thực tế.
- Không có cơ chế tự lây lan hoặc né tránh.
- Chương trình mô phỏng chỉ được phép thao tác trong thư mục lab cố định.
- Bản sao lưu được bảo vệ bằng phân quyền độc lập.

## 7. Kết quả

Các kết quả thực nghiệm, bảng đo lường, hình ảnh và video demo được lưu trong Repository.


