# Phase 1 — Chạy lab đơn hàng giả trên Windows 10

Phạm vi: Docker Compose + Flask/Gunicorn + MySQL, gồm 100 đơn hàng tổng hợp khi khởi tạo lần đầu. Hướng dẫn dùng PowerShell trên Windows 10 với Docker Desktop đã chạy. Các lệnh thực hiện tại thư mục gốc repository, nơi có `compose.yaml`.

Chưa có backup/restore, kho Restic hoặc script sự cố trong Phase 1. Trạng thái kiểm thử thực tế nằm trong báo cáo Phase 1; hướng dẫn này không xác nhận đã chạy trên máy Windows của nhóm.

## 1. Kiểm tra Docker

```powershell
docker version
docker compose version
docker info --format '{{.OSType}}'
```

Điều kiện đạt: Docker client kết nối được server; có Compose v2; lệnh cuối trả `linux`. Nếu đang ở chế độ Windows containers, chuyển Docker Desktop sang Linux containers. Nếu Compose không nhận `--wait`, cần dùng phiên bản Compose hỗ trợ tùy chọn này trước khi theo các bước dưới.

Không chạy `sudo`, `systemctl`, `ufw` hay SSH vào máy ảo theo bản Runbook cũ cho lab Compose này. Xem bảng đối chiếu trong [cấu hình lab](../environment/lab_config.md).

## 2. Tạo cấu hình cục bộ

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\SETUP\installation\init_lab.ps1
docker compose config --quiet
```

Script tạo `.env` với `WEB_PORT=8080` cùng hai file mật khẩu ngẫu nhiên:

- `secrets/db_root_password.txt`: mật khẩu quản trị MySQL.
- `secrets/db_app_password.txt`: mật khẩu tài khoản ứng dụng `group08_app`.

Các file này được Git bỏ qua. Không đưa nội dung mật khẩu vào log minh chứng, ảnh hoặc PR. Script từ chối ghi đè cấu hình/secret đã có, kể cả trạng thái tạo dở; đây không phải công cụ đổi mật khẩu. Khi cấu hình đã được tạo đầy đủ, bỏ qua bước chạy lại script và tiếp tục bằng `docker compose config --quiet`.

Compose dùng secrets dạng file. Không cần cài Python hoặc MySQL trực tiếp trên Windows để chạy lab và các test trong container.

## 3. Khởi động

```powershell
docker compose up -d --build --wait --wait-timeout 180
docker compose ps
Invoke-RestMethod http://127.0.0.1:8080/health
Start-Process http://127.0.0.1:8080/
```

Điều kiện đạt:

- Hai service `db` và `web` healthy.
- `/health` trả HTTP 200, `status=ok`, `database=ok` và `orders_count=100` khi volume được khởi tạo lần đầu, trước khi thêm dữ liệu.
- Trang web hiển thị đơn hàng tổng hợp và cho phép thêm đơn hàng giả.
- Chỉ web có cổng host `127.0.0.1:8080`; MySQL không có cổng publish ra Windows.

DB chỉ nằm trên mạng `lab` nội bộ. Web nối thêm bridge `frontend` để publish cổng localhost; mạng frontend không chặn outbound Internet. Lab này chưa phải môi trường air-gapped.

MySQL tạo database `lab_config`, bảng `orders`, dữ liệu seed và quyền ứng dụng trong lần khởi tạo volume rỗng đầu tiên. Container khởi động lại không nạp lại 100 dòng seed. Nếu đã thêm dữ liệu, số dòng lớn hơn 100 là bình thường.

Kiểm tra log khởi tạo không có lỗi SQL và `SHOW GRANTS` theo hướng dẫn test.
Một lần khởi tạo lỗi có thể để lại volume đã có dữ liệu, khiến entrypoint bỏ qua
script init khi restart. Trạng thái healthy một mình chưa chứng minh seed và
phân quyền đã hoàn tất; không xóa volume có dữ liệu để chữa lỗi một cách tự động.

Nếu cổng 8080 đã được sử dụng, sửa `WEB_PORT` trong `.env` sang cổng trống, ví dụ `8081`, chạy lại lệnh `up`, và đổi cổng trong các URL hướng dẫn. Cổng luôn bind vào `127.0.0.1` trong Compose.

## 4. Kiểm thử

```powershell
docker compose exec -T web python -m unittest discover -s /tests -p test_app.py -v
docker compose exec -T web python /tests/smoke_phase1.py
```

Unit test chạy với kết nối DB giả lập; smoke test gọi HTTP thật và thêm một đơn hàng giả vào DB. Mỗi lần chạy smoke test thành công có thể tăng số bản ghi; không dùng thao tác này để đo RTO/RPO. Xem [hướng dẫn kiểm thử](../../SOURCE/tests/README.md) để kiểm tra health khi DB ngừng và dữ liệu sau restart.

Kiểm tra dữ liệu qua API:

```powershell
$result = Invoke-RestMethod http://127.0.0.1:8080/api/orders
$result.total
$result.orders | Select-Object -First 5
```

API danh sách chỉ trả tối đa 100 đơn hàng gần nhất; `total` là tổng số dòng trong bảng.

## 5. Dừng và chạy lại

```powershell
docker compose down
docker compose up -d --wait --wait-timeout 180
```

`down` không kèm tùy chọn xóa volume nên giữ dữ liệu. Giữ nguyên tên project `group08-lab` để dùng lại cùng volume. `docker compose restart` khởi động lại container nhưng không phải thao tác khôi phục từ backup.

Không xóa volume để xử lý lỗi khởi động. Mật khẩu MySQL được thiết lập lúc volume khởi tạo: sửa file secret hoặc biến cấu hình về sau không tự đổi mật khẩu trong DB đã tồn tại. Nếu sai mật khẩu, đối chiếu file gốc đang dùng và nhật ký trước khi thay đổi cấu hình.

## 6. Chẩn đoán cơ bản

```powershell
docker compose ps -a
docker compose logs --tail 80 db
docker compose logs --tail 80 web
```

| Biểu hiện | Kiểm tra |
|---|---|
| Không kết nối được Docker server | Docker Desktop đã sẵn sàng, Linux containers, kết quả `docker version` |
| Không có file secret | Đúng thư mục repository; script tạo cấu hình đã hoàn thành |
| Port đã dùng | Đổi `WEB_PORT` trong `.env`, chạy lại `up` |
| DB chưa healthy | Log `db`; lần khởi tạo đầu có thể lâu hơn; sau khi kiểm tra nguyên nhân có thể tăng thời gian chờ |
| Web trả 503 | Trạng thái DB, bảng `orders`, quyền ứng dụng và secret đang dùng |
| Số dòng không còn 100 | Đối chiếu lần thêm trên UI/smoke test; seed chỉ áp dụng lần đầu |
| Lệnh trong Runbook Word không chạy | Bản nháp dùng VM/Linux host; dùng bảng đối chiếu Compose thay vì thực thi nguyên lệnh |

Ghi lệnh, thời điểm, mã thoát và lỗi thực tế vào hồ sơ kiểm thử. Windows 10 cần được nhóm xác minh trực tiếp; kết quả Linux/cloud không thay thế bằng chứng trên máy trình diễn.
