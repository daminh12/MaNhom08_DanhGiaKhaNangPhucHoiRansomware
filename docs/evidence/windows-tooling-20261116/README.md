# Bằng chứng bổ sung công cụ Windows — thực thi trên Linux

Code commit: 01396dd6b7efd5e1b84d78b963b0299f2b39982a.
tests.json và bốn test log ghi 102 unit PASS (38 recovery, 36 metrics, 14 backup,
14 app). Test Guided/live metrics dùng fixture/mock, không là diễn tập người thật.

p3-windows-tooling-gate-20261116 là **preflight Linux thật FAILED vì thiếu disk**,
không tác động source hoặc tạo target. Bundle chỉ copy allowlist của seal. Bộ
gate-export là output thật từ --trial-dir, giữ FAILED và không tạo RTO mới.
Không dùng nó làm số liệu Windows hoặc main trial. Manifest hash không có chữ ký.

read-only-verification.json ghi command/exit, health/count, volume name và snapshot
file hash trước/sau; không phải full source-data comparison. preservation.json
đối chiếu 148 file lịch sử với base Git. artifact-qa.json/contact sheet là kiểm
định dạng tài liệu, không phải ảnh lab. PDF preview ở THESIS/previews/windows.

Windows/PowerShell/Office native, full Guided recovery và retest hai người:
**NOT TESTED**. Không có video hoặc chữ ký được tạo thay thành viên.
