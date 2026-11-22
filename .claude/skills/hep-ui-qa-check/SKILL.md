---
name: hep-ui-qa-check
description: Quy trình kiểm thử giao diện Hép Bookstore bằng script có sẵn - render toàn bộ 36 trang shop và quản trị trên CSDL test, quét luật thương hiệu (tương phản token, gạch ngang dài, alert/confirm, style nội tuyến, reduced-motion, tên cũ "Hép Store"), chụp màn hình desktop và mobile. Dùng sau mỗi lần sửa template, CSS, JS của dự án này, hoặc khi được hỏi "giao diện có vỡ không", "kiểm lại UI". Không dùng để review logic Python.
---

# Kiểm thử giao diện Hép Bookstore

Mọi lệnh chạy từ gốc repo. Script nằm ở `.claude/skills/hep-ui-qa-check/scripts/`, chạy thẳng, không cần đọc nội dung. Gọi thư mục đầu ra là `$W` (mặc định `_workspace/qa`).

## 1. Test Django
```bash
python3 manage.py check && python3 manage.py makemigrations shop --check --dry-run && python3 manage.py test shop
```
Test đỏ là FAIL ngay, ghi nguyên văn lỗi vào báo cáo.

## 2. Render mọi trang
```bash
python3 .claude/skills/hep-ui-qa-check/scripts/smoke_routes.py . $W/html
```
Tạo CSDL test tạm, seed dữ liệu mẫu, tạo đơn và phiếu nhập, rồi GET 36 trang với khách và nhân viên. Trang trả 404 có chủ đích (`scan_missing`, `not_found_404`) là bình thường. Mã 500 hoặc `EXC` là FAIL. Mỗi trang 200 được lưu thành HTML trong `$W/html` để chụp ảnh.

## 3. Quét luật thương hiệu
```bash
python3 .claude/skills/hep-ui-qa-check/scripts/lint_ui.py .
```
Mức CHẶN làm báo cáo FAIL. Mức CẢNH BÁO ghi lại, không chặn, nhưng liệt kê cho lập trình viên.

## 4. Chụp màn hình
```bash
bash .claude/skills/hep-ui-qa-check/scripts/screens.sh $W/html $W/shots
```
Chụp 10 trang chính ở 1440px và 390px, có bật reduced-motion để các phần tử chờ hiệu ứng vẫn hiện. Có thể truyền tên trang cụ thể ở cuối lệnh.

Mở ít nhất ảnh `home`, `catalog`, `book_detail`, `m_dashboard`, `m_pos` ở cả hai cỡ và xem:
- Chữ đè lên nhau, chữ bị cắt, nút xuống 2 dòng ở desktop.
- Cuộn ngang ở mobile (nội dung tràn mép phải).
- Màu ngoài be, navy, cam.
- Khoảng trống bất thường, khối rỗng, ảnh vỡ.
- Còn ký tự hình học cũ (▦ ▤ ✳) ở thanh bên quản trị.

Snapshot là HTML tĩnh: JS động, gửi form và camera không chạy được ở đây. Kiểm phần đó bằng test Django ở bước 1, không kết luận từ ảnh.

## 4b. Luồng thật trong trình duyệt
```bash
python3 manage.py test shop.test_e2e
```
Chạy khách đặt hàng QR, SePay báo tiền, trang tự ăn mừng; POS không hộp thoại; vai trò Kho bị chặn. Dùng Chrome cài trên máy (Playwright headless-shell làm đơ trang khi có View Transitions, không phải lỗi web). Ảnh ở `_workspace/e2e/`. Bất kỳ test nào đỏ là FAIL.

## 4c. 3D (three.js)
Nếu repo có `static/js/three-*.js`: `lint_ui.py` đã kiểm vendor, reduced-motion, dispose, nạp lười. Thêm vào báo cáo:
- E2E có kiểm trang chủ bật canvas (`[data-three="on"]`) trên Chrome thật và tắt hẳn khi `reduced_motion='reduce'`, không lỗi console.
- Mở ảnh chụp hero desktop và mobile: sách 3D không đè chữ, nút hero bấm được, fallback hiện khi 3D tắt.
- Kích thước `static/vendor/three/three.module.min.js` chỉ tải trên trang có `[data-three]` (xem HTML trang quản trị không có thẻ module three).

## 5. Đối chiếu đặc tả
Với mỗi mục trong "Danh sách việc" của `_workspace/01_designer_spec.md`, dùng Grep hoặc Read xác minh có trong code. Ghi XONG, THIẾU hoặc KHÁC.

## 6. Báo cáo
Ghi `_workspace/03_qa_report.md`. Dòng đầu là `KẾT LUẬN: PASS` hoặc `KẾT LUẬN: FAIL`. PASS khi: test xanh, không trang 500 hoặc EXC, lint 0 CHẶN. Mỗi mục FAIL ghi file, hiện tượng, lệnh kiểm lại.
