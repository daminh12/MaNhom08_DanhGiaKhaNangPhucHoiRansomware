# Phase 5 — RTO, bounded recovery lag, integrity và CSV

Chỉ đọc dữ liệu diễn tập đã có; exporter không gọi Docker, tạo đơn, dừng service
hoặc chỉnh bằng chứng Phase 4. Python 3.10+ và Git với đầy đủ commit evidence.
Không có dependency Python ngoài stdlib. Windows workflow ứng dụng vẫn NOT TESTED;
việc mở CSV Linux trên Excel không chứng minh lab đã chạy Windows.

## Lệnh xuất và tái lập

Tại repository root:

```powershell
py -3 -B SOURCE/metrics/export_metrics.py --output-dir work/metrics-new-export
```

Linux thay `py -3` bằng `python3`. Output directory phải chưa tồn tại. Default
pin raw evidence commit `258ebc8b7bddb7b5fd4ce9562a37889bf1c2a36a`; source thực
thi main trial được đối chiếu theo fingerprint với commit `dde61a2241de9bfd2b9f8138433b60f63d140cdd`.
Không tự chuẩn hóa hoặc chấp nhận input khác Git blob. `.gitattributes` giữ LF
cho JSON/JSONL/CSV khi checkout Windows để không tạo hash mismatch do CRLF.

Nếu còn artifact SQL private của phiên chạy và có proof hậu kiểm:

```powershell
py -3 -B SOURCE/metrics/export_metrics.py --artifact-root work/recovery --verification docs/evidence/phase5/retained-integrity.json --output-dir work/metrics-with-integrity
```

Trên clone mới không có SQL, bỏ `--artifact-root`: fresh artifact check là
NOT TESTED, không giả PASS. Proof `retained-integrity.json` ghi rõ hậu kiểm tại thời
điểm nào, không phải lần chạy mới; đọc nó không biến thành kiểm tra DB hiện tại.

Output:
- `metrics.csv`: UTF-8 BOM, comma, decimal point, LF; mở Excel bằng Data → From
  Text/CSV → UTF-8/Comma nếu thiết lập vùng không tự nhận delimiter.
- `metrics.json`: cùng số liệu, decimal seconds lưu dạng chuỗi đúng 9 chữ số.
- `integrity.json`: hash byte từng artifact, kết quả negative candidate riêng.
- `manifest.json`: pin input Git/hash, source processor/helper và SHA-256 output.
  Manifest không tự băm chính nó; file được giữ qua Git review.

CSV trống = không áp dụng hoặc chưa kiểm thử, đọc cột status để phân biệt. Không
điền 0 cho thiếu dữ liệu. String có thể thành công thức Excel được quote an toàn.

## Định nghĩa

| Cột | Định nghĩa |
|---|---|
| observed_rto_seconds | (SERVICE_VERIFIED.ns − FAULT_REQUESTED.ns)/1e9, cùng observer |
| observed_mttd_seconds | (FAULT_DETECTED.ns − FAULT_REQUESTED.ns)/1e9; detection của script, không phải IDS |
| backup_age_since_verified_seconds | (FAULT_REQUESTED.ns − SNAPSHOT_VERIFIED.ns)/1e9; không gọi đây là RPO |
| sql_import_seconds | Thời gian IMPORT_STARTED → IMPORT_FINISHED, không thay RTO |
| dump_started/finished_at_utc | Giữ nguyên mốc container UTC độ phân giải giây; không coi là commit timestamp |
| recovered_commit_lag_lower/upper_seconds | [T0−ACK, T0−first-send] của yêu cầu cuối phục hồi, theo profile tuần tự |
| exact_rpo_seconds | Trống: không có timestamp commit độc lập chính xác |
| unrecovered_acknowledged_requests | Số yêu cầu đã ACK trước T0 nhưng thiếu trong snapshot đã phục hồi |
| write_probe_rows | Probe tạo sau khi đọc/verify; tách khỏi dataset snapshot và tập ACK nghiệp vụ |
| historical_data_integrity | Kết quả tại trial, từ raw/pinned evidence |
| fresh_artifact_integrity | Hash artifact SQL/metadata được đọc tại lúc export, nếu có file private |
| fresh_retained_db_integrity | Proof hậu kiểm target sau trial, có timestamp riêng |

Main trial có ảnh cached/VFS/release-stopped-container, validation, cutover,
write probe và restart trong RTO. Return-source sau TRIAL_ENDED không nằm trong
RTO. Không lấy created_at_utc làm commit; interval từ send/ACK không phải thời
điểm capture của backup, không phải RPO SLA chính xác. Người dùng chưa chốt target,
mọi target result để NOT TESTED, không tự đặt mục tiêu sau khi thấy số đo.

Một main trial chỉ là một mẫu, không thống kê trung bình ba lần. Web-only control
là scenario khác; reject-corrupt không có outage nên RTO/RPO N/A. Lần restore
FAILED ở Phase 3 vẫn xuất nhưng không có T0 nên N/A. Failed/aborted outage trong
input tương lai phải ghi censored/NOT TESTED, không dùng 0 hoặc thời điểm abort.

## Hậu kiểm DB và Restic thật (không phải benchmark)

```powershell
py -3 -B SOURCE/metrics/verify_retained.py --verification-id p3-check-<id-moi> --output work/integrity-new.json
```

Chỉ target PASS của main trial đã pin được kiểm. Tool xác minh local receipt,
full snapshot/digest, volume ownership và target không đang chạy; không init hay
import. Tạm dừng nguồn, Restic check/readback, khởi động lại đúng DB target đã giữ,
đọc schema/all rows, so baseline loại probe, grants và membership của bốn ACK.
Cuối cùng giữ mọi volume và trả nguồn về healthy, không thêm đơn hàng.

Cloud VFS nhỏ cần cờ rõ ràng `--release-source-containers`; cờ gỡ container đã
dừng, không gỡ volume. Không chạy khi người khác dùng lab hoặc backup cũ đang chạy.
Đây là cửa sổ kiểm chứng, không được đếm thành một sample RTO mới. SQL, secret và
full dump không được đưa vào repository. Exact SQL interruption, retry benchmark,
Windows và independent/offsite recovery giữ NOT TESTED nếu chưa thử.

## Test

```powershell
py -3 -B -m unittest discover -s SOURCE/tests -p test_metrics.py -v
py -3 -B -m unittest discover -s SOURCE/tests -p test_recovery.py -v
```

Test dùng fixture/mock hoặc copy artifact vào thư mục tạm. Một test hash SQL có
thể SKIP trên clone không có artifact private; không báo toàn suite không skip
nếu điều đó xảy ra. Số liệu CSV chính thức chỉ từ corpus đã pin, không từ fixture.
