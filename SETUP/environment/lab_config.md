# Cấu hình lab Phase 1

Đối tượng: Windows 10, Docker Desktop chạy Linux containers; dữ liệu đơn hàng tổng hợp. Cấu hình thực thi nằm ở `compose.yaml` và các file được script khởi tạo cục bộ. `SOURCE/config/lab_config.example` chỉ là bản mô tả không chứa bí mật, không được ứng dụng nạp trực tiếp.

| Thành phần | Giá trị |
|---|---|
| Compose project | `group08-lab` |
| Service Web | `web`: Flask, Gunicorn; cổng container 8000 |
| URL mặc định | `http://127.0.0.1:8080/`; có thể đổi cổng bằng `WEB_PORT` trong `.env` |
| Health | `GET /health`, thực hiện truy vấn bảng `orders`; DB lỗi hoặc bảng thiếu → HTTP 503 |
| API | `GET /api/orders`; `POST /api/orders` thêm đơn hàng tổng hợp |
| Service DB | `db`: MySQL 8.4.7; port 3306 chỉ dùng trong mạng container |
| Database / table | `lab_config.orders`, engine InnoDB |
| Tài khoản ứng dụng | `group08_app`, chỉ SELECT và INSERT trên `lab_config.orders` |
| Mạng backend | Network Compose `lab`, `internal: true`; `db` chỉ nối mạng này, không publish cổng MySQL |
| Mạng frontend | Network Compose `frontend`, bridge; `web` nối cả `frontend` và `lab`, publish web vào localhost |
| Volume DB | Khóa Compose `db_data`, mặc định tên Docker `group08-lab_db_data` |
| Đường dẫn DB trong container | `/var/lib/mysql` |
| Secret cục bộ | `secrets/db_root_password.txt`, `secrets/db_app_password.txt` |
| Secret ứng dụng trong container | `/run/secrets/db_app_password` |
| Dữ liệu seed | 100 đơn hàng tổng hợp, chỉ nạp lúc MySQL khởi tạo volume rỗng |
| Đường dẫn backup / Restic repository | **Chưa thiết lập — Phase 2** |
| Script gây sự cố | **Chưa triển khai — Phase 4** |

`/var/lib/mysql` là dữ liệu đang hoạt động, không phải thư mục backup. Docker volume tồn tại sau restart/down không chứng minh có bản sao lưu hoặc khả năng restore.

Backend DB được tách bằng mạng `lab` nội bộ. Web dùng thêm bridge `frontend` để Docker publish cổng cho trình duyệt trên host. Bridge này không chặn kết nối Internet đi ra từ web; cấu hình Phase 1 không phải môi trường air-gapped. Quyền truy cập Docker trên host cũng vẫn cho phép thao tác với container và volume.

## Schema nghiệp vụ

Bảng `orders` có `id`, `customer_alias`, `product_name`, `quantity`, `unit_price_vnd`, `created_at_utc`. Alias chỉ dùng dạng giả `LAB-...`; không nhập thông tin cá nhân. Timestamp do MySQL tạo và dùng UTC. `created_at_utc` chưa phải bằng chứng độc lập về thời điểm commit cho phép đo RPO; yêu cầu đo lường được bổ sung ở phase sau.

Ứng dụng không có quyền DROP/ALTER/DELETE. Trong Phase 1 không có “table đã bị phá”: `orders` là bảng nghiệp vụ để kiểm tra đọc/ghi trên lab.

## Đối chiếu với bản nháp Runbook của Minh Quân

`THESIS/runbook/Runbook_v1.0.docx` trên main hiện ghi nội dung “RUNBOOK v1.2”, database `lab_config` và nhiều placeholder. Tài liệu dùng giả định VM, SSH, systemd, nginx và ufw; chưa phải runbook đã chạy trên lab Docker này. Giữ nguyên tài liệu nhóm đang viết; các điều chỉnh runbook phục hồi được review ở phase tương ứng.

| Hạng mục Runbook | Đối chiếu lab Phase 1 |
|---|---|
| `web-01`, `db-01`, `<WEB_IP>`, `<DB_IP>` | Service `web`, `db`; web kết nối hostname Docker `db`, không hard-code IP container |
| `sudo systemctl status mysql` | `docker compose ps db` |
| `/var/log/mysql/error.log`, `journalctl` | `docker compose logs db` |
| nginx và log nginx | Gunicorn/Flask; dùng `docker compose logs web` |
| `sudo mysql ...` trên host | `docker compose exec db mysql -u group08_app -p -D lab_config` cho truy vấn SELECT; nhập secret cục bộ tại prompt |
| `<TABLE_NAME>` | `orders` cho thao tác xác minh nghiệp vụ; chưa có kịch bản phá/xóa bảng |
| `<APP_USER>@<APP_HOST>` | Tài khoản MySQL `group08_app`@`%`, giới hạn bằng quyền DB và mạng container; `%` không đồng nghĩa có port host/public |
| `<BACKUP_DIR>`, file dump, SHA-256, lệnh restore | Chưa có trong Phase 1; không điền đường dẫn minh họa thành cấu hình đã chạy |
| SSH/ufw/khóa account để cô lập | Chưa triển khai quy trình cô lập; không áp dụng các lệnh host này nguyên trạng cho Docker Desktop |

Trong MySQL CLI, truy vấn chỉ đọc để đối chiếu:

```sql
SELECT DATABASE(), VERSION();
SHOW TABLES;
SELECT COUNT(*) FROM orders;
SELECT id, customer_alias, product_name, created_at_utc FROM orders ORDER BY id DESC LIMIT 5;
SHOW GRANTS;
```

Không đưa mật khẩu vào tham số dòng lệnh hoặc minh chứng. Không đánh giá RTO/RPO từ các lệnh kiểm tra Phase 1.
