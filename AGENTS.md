# AGENTS.md — Quy tac phat trien Group 08

## Muc tieu
De tai: Danh gia kha nang phuc hoi truoc su co ma hoa tong tien bang mo phong an toan. Nhom 2 nguoi, 6 tuan.
Nguon yeu cau: Google Sheet https://docs.google.com/spreadsheets/d/1akuMwhM-N3BXN0V8xOcPl2OdIb3PAh_oW5JUYyJivjI/edit
Chuyen cac yeu cau thanh acceptance criteria, test case va minh chung; khong tu suy ra rubric chinh thuc.

## Pham vi an toan bat buoc
- Chi dung du lieu gia tong hop, lab cach ly, thu muc du an duoc chi dinh.
- Khong xay dung ransomware, ma doc, co che ma hoa tong tien, lay lan, ne tranh phat hien, pha hoai du lieu that.
- Mo phong su co bang che do ung dung khong kha dung / du lieu gia khong kha dung; khong can xoa bang database.
- Khong dung tai khoan that, du lieu ca nhan, mat khau trong repo.
- Restore vao dich moi sach; khong ghi de nguon hoac backup dang tin cay khi chua duoc review.
- Khong khang dinh co RTO/RPO thuc te khi chua co log ve thoi diem gian doan va verify dich vu.

## Cach lam viec voi Codex
1. Doc README va cac file lien quan; kiem tra git status / branch hien tai.
2. De xuat ke hoach ngan + file du kien sua + acceptance criteria truoc khi code.
3. Moi thay doi chi trong pham vi mot task, khong ghi de tai lieu nhom dang viet.
4. Them test tu dong va huong dan chay de lap lai. Bao cao chinh xac pass/fail/not run.
5. Moi PR kem mo ta file thay doi, lenh test, output, rui ro va gioi han.
6. Khong ghi so lieu minh hoa thanh so lieu thuc nghiem.

## Kien truc muc tieu (khong phai da hoan thanh)
Docker Compose + Flask + MySQL du lieu gia; dump DB nhat quan;
Restic de backup/restore; SHA-256 va test du lieu de xac minh;
runbook v1.0 -> dien tap -> runbook v1.1; RTO/RPO co minh chung.

## Phan cong
Da Minh: setup lab, code, backup, kiem thu, do luong va bieu do.
Minh Quan: NIST, runbook, nguoi phuc hoi doc lap, bao cao/slide.
Ca hai: review PR, dien tap lan cuoi, doi chieu checklist.

## Hien trang
File SOURCE/verification/verify_hashes.py la module kiem tra SHA-256 cho du lieu gia.
KHONG dong nhat mot kiem thu SHA-256 PASS voi su co ransomware duoc phuc hoi thanh cong.
