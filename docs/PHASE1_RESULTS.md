# Phase 1 — Lab đơn hàng giả, hồ sơ ngày 09/11/2026

## Kết luận

**PASS trên môi trường Linux/cloud** cho Docker Compose, Flask + MySQL,
100 bản ghi seed, API đọc/ghi, healthcheck DB thật, phân quyền ứng dụng,
persistence qua restart và giao diện desktop/mobile.
**Windows 10 / Docker Desktop của nhóm: NOT TESTED trực tiếp.**

Nguồn yêu cầu đã chốt: nhóm chưa có lab; máy trình diễn dùng Windows 10,
Docker đã chạy; chọn đơn hàng giả. Nhánh triển khai:
`codex/group08-phase1-orders-20261108`, tách từ `main` tại
`03767a33aec895aec3428610b3ccef2170e60c6d`.
Các PR starter/verifier và audit Phase 0 được giữ riêng; mã Phase 1 chạy độc lập
trên nền main. Hai lỗi verifier của audit chưa được sửa trong Phase 1 và cần PR
riêng trước khi dùng verifier làm điều kiện nghiệm thu restore.

## Cấu hình đã triển khai

| Hạng mục | Giá trị thực thi |
|---|---|
| Compose project | `group08-lab` |
| Web | Flask 3.1.2 + Gunicorn 23.0.0, service `web` |
| URL | `http://127.0.0.1:8080/`, thay port qua `.env` |
| DB / table | MySQL 8.4.7, `lab_config.orders`, InnoDB |
| Dữ liệu | 100 đơn hàng tổng hợp khi volume mới được khởi tạo |
| App role | `group08_app`@`%`, SELECT/INSERT trên duy nhất `lab_config.orders` |
| Health | `/health` thực sự truy vấn bảng; DB không khả dụng → HTTP 503 |
| API | GET/POST `/api/orders`, giá nguyên VND, timestamp UTC, dữ liệu được kiểm tra |
| Mạng | DB chỉ nối `lab` internal; web nối `lab` + bridge `frontend` |
| Port host | Chỉ web bind `127.0.0.1`; MySQL không publish port |
| Persistence | Volume `group08-lab_db_data`, `/var/lib/mysql` trong DB |
| Secret | Hai file cục bộ trong `secrets/`, không commit; app chỉ mount secret của app |
| Backup | Chưa triển khai; `/var/lib/mysql` là dữ liệu đang dùng, không phải backup |

Ứng dụng chạy non-root, filesystem read-only và tmpfs `/tmp`. Query thêm đơn
hàng dùng tham số; không có API sửa/xóa hay script phá hoại. UI chỉ dùng asset
cục bộ. Bridge frontend cho phép web kết nối ra ngoài nên cấu hình này không
chứng minh air-gap hoặc phân đoạn mạng của hạ tầng thực tế.

100 timestamp trong seed là fixture cố định, không phải mốc backup hay số đo
RPO. Các bản ghi do smoke/UI tạo có timestamp MySQL thật; cũng chưa được dùng
để tính RPO vì chưa có workflow backup và nhật ký commit độc lập.

## File tạo hoặc chỉnh sửa

| Nhóm file | Nội dung thay đổi |
|---|---|
| `compose.yaml`, `.env.example`, `.gitignore` | Lab services, mạng/volume/secrets, port localhost, bỏ qua output cục bộ |
| `SOURCE/app/` | Flask, template/CSS/JS, Dockerfile non-root, dependencies pin đầy đủ |
| `SOURCE/database/01_schema.sql`, `02_seed.sql`, `03_privileges.sql` | Schema InnoDB, 100 dòng seed và thu hẹp quyền trước khi dùng |
| `SETUP/installation/init_lab.ps1` | Sinh secret ngẫu nhiên bằng RNG, UTF-8 không BOM, từ chối ghi đè |
| `SOURCE/tests/test_app.py` | 14 unit test cho API, đầu vào, quyền truy cập HTTP và lỗi DB |
| `SOURCE/tests/smoke_phase1.py` | HTTP thật trong web, thêm một đơn hàng tổng hợp và đọc lại |
| `SOURCE/tests/runtime_phase1.py` | Kiểm tra topology, restart giữ dữ liệu, DB-down 503 và DB-up 200 |
| README, SETUP, SOFT, config example, tests README | Hướng dẫn PowerShell Windows 10 và bảng đối chiếu lệnh lab |
| `docs/PHASE1_RESULTS.md`, `docs/evidence/phase1/` | Báo cáo, log, metadata, checksum source và ảnh kiểm thử thật |

Giữ nguyên DOCX của Minh Quân. File `THESIS/runbook/Runbook_v1.0.docx` hiện có
nội dung ghi v1.2 và nhiều lệnh VM/systemd/SSH; hướng dẫn SETUP mới có bảng đối
chiếu Compose. Database giữ tên `lab_config`; bảng nghiệp vụ được chốt `orders`.

## Lệnh chạy trên Windows 10

Mở PowerShell tại repository root trên nhánh Phase 1, Docker Desktop dùng Linux
containers. Lệnh init chỉ chạy lần đầu, không chạy lại khi đã có cấu hình:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SETUP\installation\init_lab.ps1
docker compose config --quiet
docker compose up -d --build --wait --wait-timeout 180
Invoke-RestMethod http://127.0.0.1:8080/health
Start-Process http://127.0.0.1:8080/
docker compose exec -T web python -m unittest discover -s /tests -p test_app.py -v
docker compose exec -T web python /tests/smoke_phase1.py
```

Xem [hướng dẫn đầy đủ](../SETUP/installation/install_guide.md),
[cấu hình và Runbook mapping](../SETUP/environment/lab_config.md),
[tests](../SOURCE/tests/README.md) và
[checklist để nhóm điền trên máy Windows](../SETUP/checklist/setup_checklist.md).

## Test case và bằng chứng thực tế

| Test / điều kiện đạt | Kết quả | Bằng chứng |
|---|---|---|
| Compose config exit 0; hai service healthy | PASS | `test-log.txt`, `runtime-results.txt` |
| Volume mới có đúng 100 dòng, ID 1–100 | PASS trước lần ghi đầu tiên | `seed-and-grants.txt` |
| SHOW GRANTS chỉ có USAGE và SELECT/INSERT trên orders | PASS | `seed-and-grants.txt` |
| 14 unit test được phát hiện, không skip | PASS 14/14 | `unit-final.txt` |
| Python dependency consistency | PASS (`pip check`) | `test-log.txt` |
| Smoke HTTP tạo đúng dữ liệu, từ chối quantity kiểu boolean | PASS, 100 → 101 dòng | `test-log.txt` |
| Trình duyệt thêm đơn, UI hiển thị thành công và đọc lại | PASS, lần xác nhận cuối 102 → 103 | `browser-results.json`, ảnh desktop/mobile |
| Desktop 1440×1000 và mobile 390×844, không có page JS error hoặc tràn ngang toàn trang | PASS | `browser-results.json`; bảng có vùng cuộn riêng trên mobile |
| Web bind localhost thật; DB không có host binding, DB chỉ mạng internal | PASS | `runtime-results.txt` |
| Web non-root và read-only | PASS | `runtime-results.txt` |
| Restart giữ nguyên API data, không seed lại | PASS, 103 → 103 | `runtime-results.txt` |
| Dừng DB: health và list API HTTP 503; khởi động lại: health 200 | PASS, DB được khởi động lại trong finally | `runtime-results.txt` |
| PowerShell bootstrap chạy trên Windows 10 và toàn bộ hướng dẫn máy nhóm | NOT TESTED; mới review script | Nhóm cần ghi bằng chứng riêng |
| Backup, snapshot, restore, Runbook drill, RTO/RPO | NOT TESTED; ngoài Phase 1 | Không có số liệu được điền thay |

Thư mục [evidence/phase1](evidence/phase1/) chứa các file nêu trên. Log đầu phiên
được giữ nguyên nên Compose ps trong `test-log.txt` chưa hiện port host ở giai
đoạn phát hiện lỗi mạng; phép kiểm topology cuối trong `runtime-results.txt`
đã xác minh cổng publish thật sau sửa. Số dòng lớn hơn 100 là hệ quả của các
lần ghi thử: một smoke tạo ID101 và hai lần trình duyệt tạo ID102/103.
Không xóa dữ liệu để làm lại con số seed.

Môi trường kiểm thử: Linux x86_64, Docker 29.9.2, Compose 2.40.3,
Python trong container 3.12.12; trình duyệt Chromium headless.
Metadata/digest quan sát nằm ở `environment.json`; checksum trong
`source-sha256.json` gắn nội dung mã được kiểm thử với hồ sơ. Windows 10 chưa
được suy ra PASS từ những kết quả này.

Lệnh integration đã chạy từ host Linux:

```bash
python3 SOURCE/tests/runtime_phase1.py
```

Kiểm thử UI dùng Playwright với Chromium cài sẵn `/usr/bin/chromium`: mở trang
localhost, đọc count hiện có, điền alias LAB-BROWSER / Folder / quantity 3 /
unit_price_vnd 17000, submit và xác nhận count tăng 1 cùng bản ghi mới. Chụp ảnh
desktop rồi đổi viewport mobile; kiểm tra không có `pageerror` và chiều rộng
document không vượt viewport. Không có ảnh minh chứng giả.

## Lỗi đã gặp và cách khắc phục

| Phát hiện trong kiểm thử | Khắc phục và kiểm chứng |
|---|---|
| Quyền file do công cụ tạo trong cloud khiến MySQL không đọc được init scripts | Điều chỉnh quyền file dữ liệu lab ở cloud; Dockerfile COPY chown để app non-root đọc được code; lần khởi tạo sạch có seed/grants đúng |
| Thu hồi quyền theo schema gặp grant escape dấu `_` của MySQL entrypoint | Thu hồi mọi quyền của đúng app role rồi cấp SELECT/INSERT ở table; SHOW GRANTS xác nhận |
| Web chỉ ở mạng internal không publish port trên Docker đang test | Thêm frontend bridge cho riêng web; kiểm binding thực và truy cập browser localhost |
| Build cloud thiếu CA proxy; ổ đĩa cloud hết chỗ khi tải browser bổ sung | Mount CA qua BuildKit secret, giữ xác thực TLS; dọn tải browser tạm rồi dùng Chromium có sẵn |

Lần khởi tạo thử bị lỗi đã được bỏ cùng volume thử chỉ chứa dữ liệu tổng hợp
do phiên này vừa tạo, trước lần xác minh sạch. Hướng dẫn sử dụng không tự xóa
volume để chữa lỗi: entrypoint có thể bỏ qua init trên volume đã tồn tại,
vì vậy healthy chưa đủ chứng minh phân quyền/seed đã hoàn tất.

Để build trong cloud có proxy CA, phiên này đã dùng:

```bash
docker build --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt --tag group08-lab-web SOURCE/app
docker compose up -d --no-build --wait --wait-timeout 180
```

Môi trường Docker Desktop thông thường dùng lệnh Compose build trong hướng dẫn;
CA cloud không được commit vào image hoặc repository.

## Hạn chế và bước tiếp theo

- Nhóm cần chạy checklist trực tiếp trên Windows 10; số phiên bản Docker Desktop
  và kết quả bootstrap PowerShell hiện chưa được xác minh.
- Secret Compose ở local là file trên host; người có quyền Docker/host vẫn có thể
  truy cập dữ liệu. Đây chưa là thiết kế backup tách quyền/vị trí.
- Không có đăng nhập hoặc rate limiting; ứng dụng dành cho localhost với dữ liệu
  tổng hợp. Không triển khai lên Internet bằng cấu hình này.
- Image pin theo tag và dependencies pin theo phiên bản; digest test đã lưu.
  Chưa thực hiện audit lỗ hổng dependency đầy đủ hoặc chạy CI remote.
- Persistence qua restart chưa chứng minh khả năng phục hồi từ bản sao lưu.
  Backup MySQL nhất quán và Restic thuộc Phase 2; restore sang môi trường sạch
  thuộc Phase 3. Hai lỗi verifier cần PR sửa riêng trước bước xác minh restore.

Phase 1 được gửi bằng PR để nhóm review, không tự merge vào main.
