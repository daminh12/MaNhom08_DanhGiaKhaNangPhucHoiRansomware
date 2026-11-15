# Rà soát cuối mã nguồn, kết quả và hồ sơ — Phase 7

Ngày 15/11/2026. Base `8bb0d8e21485590258c2dd7e54562c5a3da4c3b9` (Phase 6).
Nhánh `codex/group08-phase7-report-20261115`; main còn ở Phase 2 tại lúc đối chiếu.
Các review mã nguồn và evidence được thực hiện song song, không chạy thao tác
gây outage hoặc ghi đơn hàng. Đây không phải chữ ký nghiệm thu của hai thành viên.

## Quyết định

GO cho hồ sơ Word/PPTX có nguồn và demo tiến độ đúng phạm vi Linux. Chưa đủ điều
kiện ghi toàn bộ dự án PASS: clean restore mới thiếu tài nguyên, Windows và lượt
Minh Quân độc lập chưa có bằng chứng. Không đưa action `verify_retained.py` vào
demo hiện tại vì còn kiểm tra tài nguyên muộn; không gọi số đo cũ là lượt chạy mới.

## Finding cuối

| ID | File / bằng chứng | Kết luận và xử lý |
|---|---|---|
| P7-01 | `SOURCE/recovery/controller.py`, `validate_source`, `recovery_resource_check`; `test_recovery.py` direct CLI cases | Đã xác nhận code: direct restore/drill trước đây chỉ kiểm host, có thể bỏ Docker-VM gate của preflight. **FIXED** tại `5d6c8328b621c5cc3e8d08d4a303da3d8bb3d686`: dùng chung host + Docker gate trước POST/stop. Test cả DB/staging full và đủ chỗ; 29 recovery tests PASS bằng mock. Restore thật trên bản patch/Windows NOT TESTED |
| P7-02 | `SOURCE/metrics/verify_retained.py:102` | `source_unchanged` so health JSON/count, không so nội dung/schema nguồn. Không sửa proof cũ. Báo cáo mô tả đúng Phase 5 là healthy/count không đổi; Phase 6 có full baseline/hash riêng. Chấp nhận hồ sơ khi giữ giới hạn này. Nếu mở rộng tool, capture full source baseline hai đầu và test nội dung đổi cùng count |
| P7-03 | `SOURCE/metrics/verify_retained.py:55`, `:72` | Stop nguồn trước resource check; lỗi runtime trường hợp đầy đĩa chưa inject. **OPEN**, không chạy action này khi disk hiện tại gần đầy. Hướng sửa: resource gate trước stop và regression bảo đảm không mutation; cần test profile hậu kiểm riêng. Đa Minh, khoảng 1–2 giờ + tài nguyên cho integration |
| P7-04 | `docs/evidence/phase4/main-events.jsonl` | REQUEST_COMPARISON_FINISHED sau SERVICE_VERIFIED 396,797 ns. RTO đã định nghĩa gồm full baseline/API/probe/restart/cleanup/stable health, không nói chứa bước chốt comparison ACK sau ready. Không hồi tố timestamp hoặc thay số 54.198351197 s |
| P7-05 | `THESIS/DanYBaoCaoLyThuyet.docx`, `DanY_BaoCaoLyThuyet_v1.docx` | Dàn ý có nội dung lý thuyết hữu ích, nhưng các ý phá/xóa bảng, Wazuh/SSH và 3-2-1 chưa phải chức năng đã thực hiện. Giữ bản gốc; báo cáo mới tách lý thuyết và triển khai Docker/service-stop có bằng chứng |
| P7-06 | `SOURCE/app/app.py:147`, requirements; legacy backup PS/SH; review Phase 6 | Retry/idempotency, cleanup/log/concurrency cũ và Flask 3.1.2 vẫn **OPEN** theo phạm vi trước. Không đóng bằng tài liệu mới. Không mở profile retry/Scheduler hoặc tuyên bố đã patch dependency |
| P7-07 | `THESIS/runbook/Runbook_v1.1.md`; phase reports | `restore` bắt đầu từ nguồn healthy, không hỗ trợ sẵn incident nguồn đã hỏng. Bản sao/password/journal vẫn cùng host. Windows, kho độc lập, exact RPO và mục tiêu chưa chọn giữ **NOT TESTED** |

## Bằng chứng được chấp nhận

- Bốn case CSV đã pin: main, web-only control, corrupt candidate, FAILED restore.
  Main là **một** trial, không dùng bốn dòng CSV làm bốn mẫu hiệu năng.
- Main: 105 base rows, thêm probe riêng thành 106 trên target; nguồn trả về 108
  sau trial. ACK subset có 1 checkpoint phục hồi và 3 tail requests chưa phục hồi.
- RTO 54.198351197 s; MTTD một quan sát 1.986393601 s; backup age 0.091588006 s;
  import 0.133908284 s; send/ACK commit-age bounds 10.518407983–10.532435583 s.
  Không gọi backup age hoặc bounds là exact RPO/đạt SLA.
- Các FAIL thật được giữ. Phase 6 controls và hash toàn bảng trước/sau có phạm vi
  riêng; Phase 7 chỉ đọc evidence, unit/mock và resource gate không mutation.

## Kiểm thử Phase 7

Tại code commit `5d6c8328b621c5cc3e8d08d4a303da3d8bb3d686`: recovery 29, metrics
21, backup 14, app 14 = **78 unit tests PASS**, không skip trên máy có artifact
private. App chạy trong container hiện có; các suite còn lại đúng runtime stdlib.
Log/command/exit code ở `docs/evidence/phase7/`; lỗi mock fixture ban đầu được giữ.
Không coi 78 test này là 78 lần restore thật. Gate preflight Linux thật từ chối
thiếu disk trước source mutation/target creation, không phải clean restore mới.

Các kiểm tra DOCX/PPTX, render PDF và tính nhất quán số liệu được ghi riêng trong
`docs/PHASE7_RESULTS.md` sau khi build; không thay nội dung các raw phase trước.
