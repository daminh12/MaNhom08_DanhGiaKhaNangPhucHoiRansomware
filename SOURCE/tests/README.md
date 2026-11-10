# Kiểm thử Phase 1

Phase 2 có suite riêng: `test_backup.py` chạy trong service backup. Xem cuối
tài liệu; dùng pattern cụ thể vì image web và backup có nguồn/dependency khác nhau.

Chạy tại repository root sau khi lab healthy. Hướng dẫn PowerShell: [SETUP/installation/install_guide.md](../../SETUP/installation/install_guide.md).

## Unit test ứng dụng

```powershell
docker compose exec -T web python -m unittest discover -s /tests -p test_app.py -v
```

Suite dùng DB giả lập để kiểm tra endpoint, validation, lỗi đầu vào và lỗi kết nối. Điều kiện đạt: các test được phát hiện và PASS; exit 0; không có lỗi bị che bằng “Ran 0 tests”. Unit test không thay thế kiểm tra MySQL/HTTP thật.

## Smoke test HTTP + MySQL thật

```powershell
docker compose exec -T web python /tests/smoke_phase1.py
```

Script chạy trong container `web`, gọi HTTP nội bộ và thêm một đơn hàng tổng hợp. Điều kiện đạt: health truy vấn DB, đọc danh sách, tạo dữ liệu hợp lệ và xác minh bản ghi vừa tạo; đầu vào sai bị từ chối. Mỗi lần chạy thành công tăng số dòng, nên chỉ đối chiếu seed đúng 100 trước lần ghi đầu tiên. Không xóa các bản ghi để làm lại kết quả “100 dòng”.

## Kiểm tra giữ dữ liệu qua restart

Chạy smoke test hoặc thêm một đơn hàng trên UI trước bước này.

```powershell
$before = Invoke-RestMethod http://127.0.0.1:8080/api/orders
$lastId = $before.orders[0].id
docker compose restart
docker compose up -d --wait --wait-timeout 180
$after = Invoke-RestMethod http://127.0.0.1:8080/api/orders
if ($after.total -ne $before.total) { throw 'FAIL: so dong thay doi sau restart' }
if ($after.orders[0].id -ne $lastId) { throw 'FAIL: khong giu duoc ban ghi moi nhat' }
'PASS: du lieu con sau restart'
```

Không chạy đồng thời thao tác ghi khác trong phép thử này. Đây là kiểm tra persistence, không phải backup/restore.

## Kiểm tra health khi DB không khả dụng

Bài test tạm dừng riêng service DB của project lab để xác nhận healthcheck. Không xóa bảng, file hoặc volume. Chưa phải kịch bản diễn tập hay phép đo RTO.

```powershell
try {
    docker compose stop db
    $status = 0
    try {
        $response = Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing -TimeoutSec 15
        $status = [int]$response.StatusCode
    } catch {
        if ($_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
        } else {
            throw
        }
    }
    if ($status -ne 503) { throw "FAIL: mong doi HTTP 503, nhan $status" }
    'PASS: health tra 503 khi DB dung'
} finally {
    docker compose up -d --wait --wait-timeout 180 db
}
Invoke-RestMethod http://127.0.0.1:8080/health
```

Sau cùng phải thấy HTTP 200, `status=ok`. Nếu shell bị đóng giữa bài test, khởi động lại DB bằng lệnh `up` ở khối `finally` trước khi làm việc tiếp.

## Kiểm tra cổng và quyền

```powershell
docker compose ps
docker compose port web 8000
docker compose port db 3306
docker compose exec db mysql -u group08_app -p -D lab_config
```

Web phải hiển thị `127.0.0.1:8080` (hoặc cổng đã chọn); DB không có host binding nên lệnh tra port DB có thể báo không tìm thấy binding. Trong MySQL CLI, dùng `SHOW GRANTS;` và `SELECT COUNT(*) FROM orders;`. Không cần thử lệnh DROP trên bảng để chứng minh thiếu quyền.

## Ghi bằng chứng

Nếu máy host có Python 3.10+, có thể tự động kiểm tra topology, giữ dữ liệu sau
restart và HTTP 503 khi DB ngừng bằng:

```powershell
python SOURCE/tests/runtime_phase1.py
```

Script chỉ chấp nhận project `group08-lab` đã chạy, tạm dừng DB rồi khởi động
lại trong `finally`; không xóa bảng hay volume. Chạy khi không có người khác
thêm dữ liệu. Nếu đổi port, thêm `--base-url http://127.0.0.1:8081`.
Đây là lựa chọn bổ sung; các lệnh PowerShell ở trên không yêu cầu Python host.

Ghi đúng commit, môi trường, lệnh, số test, mã thoát và output. Đọc log bằng `docker compose logs --tail 80 web db`; kiểm tra và che bí mật trước khi lưu. Mỗi lỗi phải ghi FAIL hoặc NOT TESTED với lý do, không tự tạo kết quả. Kết quả chạy trên Linux/cloud và kết quả Windows 10 là hai mục riêng.

## Kiểm thử Phase 2

Sau Setup, chạy suite backup stdlib trong image công cụ:

```powershell
docker compose -f compose.yaml -f compose.backup.yaml run --rm --no-deps --entrypoint python backup -m unittest discover -s /tests -p test_backup.py -v
```

Điều kiện đạt: 14 test PASS, gồm từ chối symlink/root symlink, manifest không phải
object, traversal/duplicate, file rỗng/thiếu/thừa, dump cắt cụt; lỗi Restic/check/
readback không tạo trạng thái PASS. Đây là module mới có scope cố định, không
sửa hoặc thay kết luận audit về verifier prototype trên nhánh starter cũ.

Nếu host có Python, integration test bổ sung sau ít nhất một backup PASS:

```powershell
python SOURCE/tests/integration_backup.py
```

Script kiểm chứng snapshot thật, init/re-run bị từ chối, tạo riêng một fixture
dump cắt cụt và kiểm tra không có snapshot mới từ đầu vào lỗi, secret thiếu
phải fail. Không sửa backup đã tin cậy hoặc dữ liệu DB. Chạy khi không có lượt
backup khác đồng thời để so sánh danh sách snapshot. Lệnh PowerShell điều phối
và lịch Task Scheduler vẫn cần nhóm kiểm thử trực tiếp trên Windows 10.

## Phase 3/4

Unit stdlib (không kết nối DB/Docker thật):

```powershell
py -3 -B -m unittest discover -s SOURCE/tests -p test_recovery.py -v
```

Kiểm thử thật là các action trong `SOURCE/recovery/README.md`; các action này có
thể dừng dịch vụ lab và tạo đơn giả. Chỉ chạy khi chủ động diễn tập, có đủ tài
nguyên và không có người khác ghi dữ liệu. `docs/PHASE3_RESULTS.md` và
`docs/PHASE4_RESULTS.md` tách unit/mock, test thật Linux, Windows NOT TESTED.
