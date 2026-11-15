# Nhật ký thực nghiệm tổng hợp — Nhóm 08

Tổng hợp ngày 15/11/2026 từ raw evidence có sẵn. Timestamp ở evidence là UTC;
thời gian Việt Nam = UTC+7. Đây là nhật ký đối chiếu do Codex biên soạn, không là
xác nhận Đa Minh/Minh Quân đã trực tiếp thao tác các lượt cloud. Không tự điền
giờ chạy, người chạy, ảnh hoặc số đo cho việc chưa thực hiện.

| Ngày UTC | Công việc thực tế / kết quả | Bằng chứng | Phạm vi và ghi chú |
|---|---|---|---|
| 09/11/2026 | Lab Flask/MySQL, seed mới 100 dòng, đọc/ghi, health và grants; browser tạo đơn, count 102→103 | [Phase 1](PHASE1_RESULTS.md), [browser JSON](evidence/phase1/browser-results.json), [runtime](evidence/phase1/runtime-results.txt) | Linux/Chromium; ảnh desktop/mobile đã có từ lượt này. Không dùng như ảnh Windows hoặc ảnh restore |
| 09/11/2026, 13:51–13:54 | Hai backup PASS, dump lần lượt 103 và 104 dòng giả; Restic check/readback | [successful runs](evidence/phase2/successful-runs.json), [integration](evidence/phase2/integration.json) | Số dòng trong dump chưa là số dòng sau restore; giữa hai backup có thêm một đơn thử |
| 10/11/2026, 13:44 | Capture baseline 104 dòng và snapshot mới đủ metadata nghiệp vụ | [baseline result](evidence/phase3/baseline-result.json), [events](evidence/phase3/baseline-events.jsonl) | Full snapshot `42e4948c0d191d32afcd81fb0bca95fa83982f1d0f7162a4c3d6422ff8dc8b9c` |
| 10/11/2026, 13:45–13:46 | Restore lần đầu FAILED ở schema compare; giữ nguyên run/volume lỗi | [first failed result](evidence/phase3/first-failed-result.json), [diagnostic](evidence/phase3/diagnostic-schema.json) | MySQL thêm CHARACTER SET dư thừa; không đổi FAILED thành PASS, không import lại target đó |
| 10/11/2026, 13:48–13:49 | Run mới restore 104 baseline rows, thêm 1 probe riêng, schema/hash/grants/API/restart PASS | [clean result](evidence/phase3/clean-result.json), [events](evidence/phase3/clean-events.jsonl) | Stack/volume/network sạch; trả nguồn healthy/104 sau trial |
| 10/11/2026 | Web-only control PASS; candidate SQL copy bị sửa bị SHA từ chối trước import | [web control](evidence/phase4/web-control-result.json), [corrupt guard](evidence/phase4/corrupt-result.json) | Hai scenario khác nhau; corrupt guard không có RTO/RPO, control không là backup restore |
| 10/11/2026, 13:55–13:57 | Main drill: canary ACK, snapshot baseline 105, ba tail ACK, DB stop→503, clean restore về URL 8080 | [main result](evidence/phase4/main-result.json), [raw events](evidence/phase4/main-events.jsonl), [ACK](evidence/phase4/acknowledgements.json) | 105 rows nền + 1 probe target; nguồn trả về 108. Một main trial Linux, không phải ba lần lặp |
| 10/11/2026, 15:36–15:38 | Hậu kiểm Restic và retained target thực, không reimport/ghi order; 105 nền + 1 probe còn khớp | [retained integrity](evidence/phase5/retained-integrity.json), [integrity events](evidence/phase5/integrity-events.jsonl) | Có timestamp riêng; không là main RTO trial mới. Giữ đủ 4 snapshot, nguồn healthy/108 |
| 10/11/2026 | Tính lại metric từ raw monotonic/pin Git, xuất 4 case CSV; 69 unit lúc Phase 5 | [Phase 5](PHASE5_RESULTS.md), [CSV](evidence/phase5/export-20261110/metrics.csv) | Main RTO 54.198351197 s; commit-age bounds 10.518407983–10.532435583 s; exact RPO/target NOT TESTED |
| 15/11/2026 | Review v1.0, chạy các bước chỉ đọc; clean gate FAIL trước stop/target vì disk | [v1 safe checks](evidence/phase6/v1.0-safe-checks.json), [post-review gate](evidence/phase6/post-review-release-result.json) | Lượt restore sạch mới không thực hiện. Giữ raw FAIL; không xóa dữ liệu để vượt gate |
| 15/11/2026, 02:56 | Web control và DB-stop/start/restart nguồn PASS; toàn bảng trước/sau bằng nhau | [web result](evidence/phase6/web-rehearsal-result.json), [DB control](evidence/phase6/v1.0-db-control.txt), [inventory after](evidence/phase6/inventory-after.json) | Observed web interval 5.050724009 s, không thay main RTO cũ; 108 rows, 5 volume, 4 encrypted snapshot file hashes không đổi |
| 15/11/2026 | Fix uncertain HTTP 201 malformed, preflight; 76 unit PASS; tạo Runbook v1.1 và replay CSV cũ | [Phase 6](PHASE6_RESULTS.md), [verification](evidence/phase6/verification.json), [v1.1](../THESIS/runbook/Runbook_v1.1.md) | Test mock/fixture không là 76 lần phục hồi; chưa nghiệm thu đầy đủ Phase 6 |
| Chưa thực hiện | Workflow Windows thật, lượt Minh Quân độc lập, restore mới Phase 6, host/repo-loss từ bản sao độc lập | Chưa có transcript/evidence tương ứng | NOT TESTED; không tự điền ngày hoặc người chạy |

Main trial sử dụng snapshot
`23a5aa61e65808bcae3680900a5f708f7c42ef1af64ef28ca5f2a842b36f6f78`.
RTO bao gồm kiểm tra dữ liệu, quyền, API/URL, probe/restart và stable health;
return-source diễn ra sau trial. Backup age, thời gian import và số đơn ACK thiếu
phải để riêng, không gọi chung là RPO. Mục tiêu RTO/RPO chưa chốt.

Sau mỗi lượt mới, bổ sung entry dẫn tới raw run ID/result/events đúng phiên bản;
giữ entry lỗi cũ. Người thực thi thật và người ghi chép tự xác nhận sau khi chạy,
không lấy bảng tổng hợp này làm chữ ký nghiệm thu.
