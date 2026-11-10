# Phase 4 — diễn tập lành tính, 10/11/2026

## Kết luận

**PASS kỹ thuật trên Linux/cloud** cho ba kịch bản: web unavailable, SQL candidate
sai SHA bị từ chối, DB unavailable → phục hồi Restic vào stack sạch tại URL gốc.
Phase 3 đã chạy trước (xem `PHASE3_RESULTS.md`). Không có malware, không phá bảng
để gây sự cố, không xóa volume hoặc snapshot. Windows 10: **NOT TESTED**.
Không có RTO/RPO mục tiêu định lượng: không kết luận đạt SLA hoặc hoàn thành Phase 5.

## Main drill và bằng chứng

Lệnh thực tế:

```bash
python3 -B SOURCE/recovery/controller.py drill --run-id p4-main-20261110 --port 8080 --post-orders 3 --release-source-containers --return-source
```

1. Nguồn healthy, 104 dòng. Gửi một đơn checkpoint, nhận HTTP 201 và fsync journal.
2. Tạm ngừng web, capture baseline và consistent dump; source ổn định 105 dòng.
   Restic/check/readback PASS, snapshot
   `23a5aa61e65808bcae3680900a5f708f7c42ef1af64ef28ca5f2a842b36f6f78`,
   backup run `p2-20261110T135557Z-b85d7691e0d9`.
3. Gửi ba đơn mới, ghi ACK độc lập; không retry, không request in-flight khi fault.
4. T0 ngay trước stop DB; web nguồn trả **503**. Stop web, lưu logs, giải phóng
   stopped containers trong profile cloud; source volume vẫn tồn tại.
5. Trích xuất lại từ snapshot, kiểm manifest/dump/baseline. DB readiness SELECT 1,
   volume target mới `group08-restore-p4-main-20261110_restore_data`, không init seed.
6. Import exit 0, 105 dòng và schema khớp baseline. Role chỉ SELECT/INSERT.
7. Web target phục vụ đúng `http://127.0.0.1:8080`; kiểm binding container và API.
   Thêm một probe riêng (106 dòng), hash base loại probe vẫn khớp; restart và kiểm lại.
8. Sau ba health probe liên tiếp, ghi Tready; chốt request comparison trước return.
9. ReturnSource sau đóng trial: giữ target volume, bật lại lab gốc healthy/108 dòng.

| Chỉ số quan sát | Kết quả thật |
|---|---|
| Observed RTO | 54.198351197 giây, một lượt; từ stop requested đến toàn bộ verification/stable health |
| Checkpoint được phục hồi | 1 yêu cầu có ACK trước snapshot |
| Đơn ACK sau snapshot chưa phục hồi | 3; đúng phạm vi snapshot, không phải hash mismatch |
| Duplicate trong tập yêu cầu diễn tập | 0 |
| Uncertain trong producer | 0; không retry |
| Tuổi commit cuối phục hồi theo send/ACK | Khoảng 10.518407983–10.532435583 giây; **không phải RPO chính xác** |
| Phục hồi base dataset/schema/API/persistence | PASS |
| Đạt RTO/RPO mục tiêu | NOT TESTED, chưa có mục tiêu cấu hình |

T0/Tready dùng monotonic cùng observer; UTC để đối chiếu. Khoảng commit từ
client send/ACK, không dùng created_at_utc. RTO bao gồm stop, release container,
extract/check, DB khởi tạo, import, cấp quyền, cutover, probe/restart và validation.
Không tính return-source sau trial. Không dùng riêng thời gian import làm RTO.

## Các kịch bản bổ sung

```bash
python3 -B SOURCE/recovery/controller.py web-outage --run-id p4-web-final-20261110
python3 -B SOURCE/recovery/controller.py reject-corrupt --run-id p4-corrupt-20261110 --backup-id p2-20261110T134432Z-1c95ac703322 --snapshot-id 42e4948c0d191d32afcd81fb0bca95fa83982f1d0f7162a4c3d6422ff8dc8b9c --manifest-sha256 f27cdaccf18416bd7533af3decbad4015076af3ce563994978013f6d0aeec225
```

| Test | Điều kiện đạt | Trạng thái/bằng chứng |
|---|---|---|
| Web-only | Quan sát unavailable; start web; dataset không đổi | PASS, `web-control-result.json`/events; observed interval 4.918264275 giây, không phải restore backup |
| SQL candidate hỏng | Sửa một byte của bản copy, manifest không đổi; từ chối trước import | PASS, `corrupt-result.json`/events, import_attempted=false; RTO/RPO không áp dụng |
| DB unavailable → clean restore | 503, target sạch, full hash, quyền/API/restart/URL gốc | PASS, `main-result.json`, `main-events.jsonl`, logs target/source, grants |
| ACK đối chiếu | Checkpoint phục hồi, ba tail orders thiếu đúng dự kiến, không duplicate | PASS, `acknowledgements.json`, main result |
| Unit hồi quy | Recovery 15 + backup 14 + app 14, mock/fixture | PASS, xem evidence Phase 3; không thay thế test thật |
| Windows/PowerShell | Chạy thật trên máy nhóm | NOT TESTED |
| Mất kho chính/host | Chỉ phục hồi từ bản sao khác vị trí/thiết bị | NOT TESTED, chưa có bản sao độc lập |
| Retry khi mất ACK/ghi liên tục | Durable idempotency và commit evidence | NOT TESTED thật; không thuộc profile tuần tự đã chạy |

## File và cách lặp lại

Mã: `SOURCE/recovery/`, Compose restore/tools, simulator README và addendum
runbook. Lệnh Windows, dependency Python host mới, cách chọn full ID/digest,
abort/return-source và giới hạn: `SOURCE/recovery/README.md`.
Mỗi lần dùng ID mới; không import lại vào volume cũ. Không chạy producer/backup
khác hoặc admin DDL trong trial. Event log ghi mã thoát, cleanup, uncertainty.

## Giới hạn và việc sau

Một main trial trên cloud VFS, không phải thống kê ba lần lặp; image có sẵn,
resource profile release container, không air-gap/immutable/offsite. Journal ngoài
web/DB nhưng cùng host, đủ cho kịch bản dừng DB, chưa đủ kịch bản mất host.
Không kiểm chứng chống/diệt ransomware, phục hồi host thật hoặc chống sửa baseline
bởi host admin. Chưa có video/ảnh, CSV phân tích, Windows hoặc Runbook v1.1 formal.

Phase 5 cần chốt mục tiêu trước các lượt tiếp theo, chuẩn hóa CSV, ghi uncertainty,
tách backup age/recovery point lag/lost count, lặp trong cùng điều kiện. Phase 6:
MQ thực hiện độc lập, cập nhật Runbook v1.1 từ lỗi thật. Không merge tự động.
