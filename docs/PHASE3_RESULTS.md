# Phase 3 — phục hồi MySQL sạch, 10/11/2026

## Kết luận và phạm vi

**PASS cho luồng phục hồi thực tế trên Linux/cloud**: trích xuất snapshot Restic,
volume/project/network mới, không seed/đọc volume nguồn, import, schema/all rows,
quyền, API đọc/ghi và persistence sau restart. Windows 10: **NOT TESTED**.
Không có kết luận đạt mục tiêu RTO/RPO; không có bài thử mất host/kho độc lập.

Base `37addd764dfd18a48fd2726c9f042c2b19ab6d96`; nhánh
`codex/group08-phase4-safe-drill-20261110`. Thêm phần Phase 3 cần thiết trước khi
chạy Phase 4; không merge starter/audit hoặc sửa DOCX của Minh Quân.

## Tương thích và file

File mới: `compose.restore.yaml`, `compose.recovery-tools.yaml`,
`SOURCE/recovery/{controller.py,archive.py,common.py,run_lab.ps1,README.md}`,
`SOURCE/tests/test_recovery.py`, runbook addendum và evidence. Bộ điều phối dùng
Python 3.10+ trên host; PowerShell là launcher, dependency mới được ghi rõ.
Image app/backup Phase 1/2 được tái sử dụng; code extractor mount read-only.

Giữ manifest v1 của Phase 2: baseline nghiệp vụ nhúng vào **metadata của run mới**,
được hash/readback cùng SQL. Source web dừng, kiểm InnoDB transaction đã drain,
so sánh toàn bảng trước/sau dump. Không hồi tố baseline cho snapshot cũ.
`db_dump.sh` thêm `--skip-add-drop-table` cho dump mới, không sửa backup đã có.

Luồng: guard target → extract full snapshot/digest → verify SHA → MySQL SELECT 1
→ kiểm volume/schema rỗng → import fail-closed → quyền SELECT/INSERT → schema và
hash mọi dòng → API đọc → một write probe → restart → kiểm lại base/probe và health.
SQL không đi qua redirection PowerShell. Không xóa hoặc tự nhập lại target dở.

## Lệnh và kết quả thực tế

```bash
python3 -B SOURCE/recovery/controller.py backup --run-id p3-baseline-20261110
python3 -B SOURCE/recovery/controller.py restore --run-id p3-clean-v2-20261110 --backup-id p2-20261110T134432Z-1c95ac703322 --snapshot-id 42e4948c0d191d32afcd81fb0bca95fa83982f1d0f7162a4c3d6422ff8dc8b9c --manifest-sha256 f27cdaccf18416bd7533af3decbad4015076af3ce563994978013f6d0aeec225 --port 8081 --release-source-containers --return-source
```

Snapshot có 104 dòng theo baseline nguồn, full ID
`42e4948c0d191d32afcd81fb0bca95fa83982f1d0f7162a4c3d6422ff8dc8b9c`.
Target `group08-restore-p3-clean-v2-20261110_restore_data` mới, zero table trước
import; 104 dòng khớp trước probe, 105 sau probe, vẫn đúng sau restart. Role chỉ
SELECT/INSERT. Sau đóng phép thử trả nguồn về healthy/104; volume target giữ lại.

Lần đầu `p3-clean-20261110` **FAILED** ở so schema. MySQL round-trip thêm
`CHARACTER SET utf8mb4` dư thừa vào cột đã có COLLATE. Toàn bộ rows hash vẫn khớp.
Đọc target chẩn đoán, không import lại. Sửa chuẩn hóa có điều kiện và test hồi quy,
dùng run/volume mới cho lần PASS; giữ nguyên kết quả FAILED và volume đầu tiên.

## Test và bằng chứng

| Kiểm tra | Điều kiện đạt | Trạng thái/bằng chứng |
|---|---|---|
| Unit recovery | 15 test PASS, gồm full ID, path, all rows ngoài API limit, integer, schema charset, dirty run, ACK, import nonzero | PASS (mock/fixture), `recovery-unit.txt` |
| Regression Phase 2 | 14 unit backup | PASS, `backup-regression.txt` |
| Regression app | 14 unit app trong web hiện có, DB mock | PASS, `app-regression.txt` |
| Backup baseline thật | Stop writes, before/after khớp, Restic/check/readback | PASS, `baseline-result.json`, `baseline-events.jsonl` |
| Restore sạch thật | Guard volume, import exit 0, toàn bộ data/schema, grants, API, restart | PASS, `clean-result.json`, `clean-events.jsonl`, `target-grants.txt` |
| Schema mismatch không PASS | Run đầu bị chặn và nguồn bật lại | PASS của failure gate; run gốc FAILED, `first-failed-*` |
| Existing run | Exit khác 0, result PASS cũ không đổi | PASS, `existing-run-refused.txt` |
| Legacy snapshot thiếu baseline | Không nghiệm thu đầy đủ và không import | Expected refusal; raw run FAILED, `legacy-refused-result.json` |
| Wrong manifest | Từ chối trước trích SQL/import | PASS bằng mock, unit recovery |
| SQL import lỗi/gián đoạn thực | Full workflow bị ngắt và không resume | NOT TESTED thực; nonzero gate có unit mock |
| Windows/PowerShell | Nhóm chạy trên Windows thật | NOT TESTED |

## Tài nguyên và hạn chế

Dọn duy nhất image build cũ không còn container sử dụng (7abd293d39c0), không xóa
volume/snapshot. Cloud 8 GB/VFS không chứa đủ hai DB container cùng lúc. Profile
`--release-source-containers` lưu log, stop rồi gỡ container nguồn; volume nguồn
vẫn giữ nguyên. ReturnSource sau trial dừng/gỡ container target, giữ volume target
và tạo lại source container với volume cũ. Đây là điều kiện cloud, không chứng minh
giữ nguyên container nguồn hoặc khả năng chống mất host.

`source-sha256.json` và events xác định source của phiên chạy; metadata ghi base
commit trước khi code được commit. Các bổ sung guard sau integration (nếu có)
phải có bằng chứng riêng, không sửa fingerprint/log của lượt đã chạy.
Không có ảnh/video mới, không có CSV phân tích Phase 5 hoặc diễn tập Windows.
Phạm vi backup vẫn chỉ orders, không tự bao phủ bảng mới. Các finding API retry,
Flask advisory, script backup cũ và storage cùng host chưa được đóng bởi lượt này.

Hướng dẫn: `SOURCE/recovery/README.md`; addendum runbook:
`THESIS/runbook/PHASE3_PHASE4_DOCKER.md`.
