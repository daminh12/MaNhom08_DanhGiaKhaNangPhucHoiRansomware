# Công cụ Phase 1

| Công cụ | Phiên bản dùng trong lab | Nguồn / giấy phép |
|---|---|---|
| Python | Image `python:3.12.12-slim-bookworm` | python.org / PSF |
| MySQL Community | Image `mysql:8.4.7` | hub.docker.com/_/mysql / GPL-2.0, xem license upstream |
| Flask | 3.1.2 | palletsprojects.com / BSD-3-Clause |
| Gunicorn | 23.0.0 | gunicorn.org / MIT |
| PyMySQL | 1.1.2 với extra rsa | github.com/PyMySQL/PyMySQL / MIT |
| Docker Desktop | Dùng bản đã chạy trên máy Windows 10 của nhóm; chưa xác nhận số phiên bản | docker.com; điều khoản Docker Desktop |
| Docker Compose | v2, cần hỗ trợ `--wait` và `--wait-timeout` | github.com/docker/compose / Apache-2.0 |

Dependency Python được pin đầy đủ trong `SOURCE/app/requirements.txt`.
Phiên bản image được pin theo tag; digest quan sát khi test nằm trong báo cáo.
Chưa có kiểm thử trực tiếp trên Windows 10. Nhóm cần ghi `docker version` và
`docker compose version` của máy demo vào minh chứng riêng.

Tham khảo thiết kế networks/healthcheck/secrets từ
https://github.com/docker/awesome-compose/tree/master/nginx-flask-mysql (CC0-1.0).
Không sao chép nguyên stack mẫu. Restic và rest-server dành cho Phase 2, chưa cài
hoặc dùng để tạo kết quả backup trong Phase 1.
