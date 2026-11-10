
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

## 8. Lab Phase 1 — đơn hàng giả (Docker)

Phase 1 chọn Docker Compose + Flask/Gunicorn + MySQL 8.4.7; database
`lab_config`, bảng `orders`, 100 đơn hàng tổng hợp khi khởi tạo volume lần đầu.
Ứng dụng dùng `http://127.0.0.1:8080`, MySQL không publish cổng ra host.

Trên Windows 10, mở PowerShell tại repository root với Docker Desktop ở chế độ
Linux containers:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SETUP\installation\init_lab.ps1
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
Start-Process http://127.0.0.1:8080/
```

Chạy script tạo cấu hình một lần; nó từ chối ghi đè secret đã có.
Xem [hướng dẫn Windows 10](SETUP/installation/install_guide.md),
[cấu hình lab và đối chiếu Runbook](SETUP/environment/lab_config.md),
[các lệnh test](SOURCE/tests/README.md) và
[kết quả Phase 1](docs/PHASE1_RESULTS.md).
Các lựa chọn VM/BorgBackup/MinIO ở phần công nghệ phía trên là phạm vi nghiên cứu
ban đầu. Phase 1 chưa triển khai backup, restore, mô phỏng sự cố hoặc đo RTO/RPO.

## 9. Backup Phase 2 — MySQL + Restic

Trên nhánh có Phase 2, sau khi lab Phase 1 hoạt động, chạy tại repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Setup
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Backup
powershell -NoProfile -ExecutionPolicy Bypass -File .\SOURCE\backup\backup.ps1 -Action Snapshots
```

Setup giữ nguyên mật khẩu đã có, cấp tài khoản backup SELECT-only và khởi tạo
kho Restic mới nếu chưa có. Mỗi lần backup tạo run riêng với dump, manifest,
snapshot ID và kết quả kiểm chứng. Xem [hướng dẫn backup](SOURCE/backup/README.md)
và [kết quả Phase 2](docs/PHASE2_RESULTS.md). Restore DB sạch thuộc Phase 3.

## 10. Phục hồi sạch và diễn tập Phase 3/4

Workflow trong [SOURCE/recovery/README.md](SOURCE/recovery/README.md) dùng Restic,
baseline nghiệp vụ độc lập trong metadata, MySQL target mới và ghi sự kiện observer.
Cần thêm Python 3.10+ trên host; có PowerShell launcher cho Windows 10 (chưa chạy
trực tiếp trên Windows). Phase 1/2 vẫn chạy theo hướng dẫn Docker hiện có.

[Kết quả Phase 3](docs/PHASE3_RESULTS.md), [Phase 4](docs/PHASE4_RESULTS.md) và
[bổ sung Runbook](THESIS/runbook/PHASE3_PHASE4_DOCKER.md) ghi bằng chứng Linux thật,
bao gồm cả run FAILED, giới hạn cloud và các hạng mục NOT TESTED.

## 11. Review Phase 0–4 và số đo Phase 5

[Code review](docs/reviews/PHASE0_4_REVIEW_2026-11-10.md) ghi finding còn mở và
phạm vi GO. [Phase 5](docs/PHASE5_RESULTS.md) tính lại số đo từ raw events đã pin,
kiểm toàn vẹn và xuất [CSV](docs/evidence/phase5/export-20261110/metrics.csv).
[Hướng dẫn exporter](SOURCE/metrics/README.md) chạy offline bằng Python/Git, không
gây outage; fresh retained-DB verification là một action riêng có tác động lab.
Người dùng chưa chọn RTO/RPO target; không tự kết luận đạt SLA hoặc Windows PASS.
