# Phần mềm, nguồn và giấy phép — Nhóm 08

| Công cụ | Phiên bản/phạm vi | Nguồn / giấy phép |
|---|---|---|
| Python container | python:3.12.12-slim-bookworm | python.org / PSF |
| Python host | >=3.10 cho observer và exporter | python.org / PSF |
| MySQL Community | mysql:8.4.7 | hub.docker.com/_/mysql / GPL-2.0; xem upstream |
| Flask | 3.1.2; advisory còn mở trong lưu ý | palletsprojects.com / BSD-3-Clause |
| Gunicorn | 23.0.0 | gunicorn.org / MIT |
| PyMySQL | 1.1.2 extra rsa | github.com/PyMySQL/PyMySQL / MIT |
| Restic | 0.18.1 trong image backup | github.com/restic/restic / BSD-2-Clause |
| Docker Desktop | Ghi phiên bản thật của máy nhóm | docker.com / điều khoản Docker Desktop |
| Docker Compose | v2 hỗ trợ --wait/--wait-timeout | github.com/docker/compose / Apache-2.0 |
| Git / PowerShell | Ghi phiên bản máy Windows | git-scm.com / Microsoft |
| OBS / Word / PowerPoint | Quay và biên tập, không cần cho controller | Theo giấy phép từng công cụ |

Dependency app pin ở [requirements](../SOURCE/app/requirements.txt); image tag
khác digest, digest đã quan sát nằm trong evidence môi trường từng phase.
Restic/MySQL chạy trong Docker; Python host là dependency của Phase 3 trở đi.
Không cần SSH/VPS cho lab cục bộ. rest-server/Kopia/pgBackRest/MinIO chưa dùng
để tạo bằng chứng hiện có.

Lệnh chạy nằm ở [HUONGDAN](../HUONGDAN.md); điều kiện/giới hạn và tài liệu
upstream nằm ở [các lưu ý](../LUU_Y_THUC_NGHIEM.md).
