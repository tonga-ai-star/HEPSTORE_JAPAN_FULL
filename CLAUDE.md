# Hép Bookstore

Website bán sách Django 5.2 + trang quản trị. Chạy: `python3 start.py`. Test: `python3 manage.py test shop`.

## Harness: giao diện Hép Bookstore

**Mục tiêu:** thiết kế lại và giữ giao diện shop và quản trị đúng nhận diện logo (be, navy, cam), nhiều hiệu ứng nhưng không lộ dấu "giao diện AI".

**Điều kiện gọi:** mọi yêu cầu đổi giao diện, màu, hiệu ứng, bố cục, hoặc kiểm lại UI thì dùng skill `hep-redesign`. Câu hỏi đơn giản có thể trả lời trực tiếp. Sửa nhỏ một chỗ CSS vẫn phải theo skill `hep-brand-ui`.

**Lịch sử thay đổi:**
| Ngày | Thay đổi | Đối tượng | Lý do |
| --- | --- | --- | --- |
| 2026-11-21 | Dựng harness v2 lần đầu | Toàn bộ | Khách yêu cầu đổi tone theo logo, thêm hiệu ứng |
| 2026-11-21 | Chạy harness lần 1: đổi toàn bộ shop và quản trị sang be, navy, cam; thêm motion.js | templates, static | QA PASS, lint 0 lỗi |
| 2026-11-21 | Logo gấu `static/img/brand/hep-bear.svg` là bản tạm | Logo, favicon | Chưa có file logo gốc, thay khi khách gửi |
| 2026-11-21 | `screens.sh` chụp mobile 390px qua iframe, thêm `HEP_THEME=dark` | hep-ui-qa-check | Chrome headless không mở cửa sổ dưới 500px |
| 2026-11-21 | Đợt hiệu ứng v2: shop MOTION 10, View Transitions, chữ rơi, sách bay vào giỏ, kệ ghim, ăn mừng thanh toán; quản trị số chạy, báo tiền vào trực tiếp | hep-brand-ui, static, templates | Người dùng yêu cầu hiệu ứng "lồng lộn" |
| 2026-11-21 | Thêm test E2E Playwright `shop/test_e2e.py` (ưu tiên Chrome thật) và bước 4b trong hep-ui-qa-check | hep-ui-qa-check, shop | Ảnh tĩnh không bắt được lỗi luồng thật; headless-shell của Playwright đơ với View Transitions |
| 2026-11-22 | Thêm đặt trước sách hết hàng: nút "Đặt trước" viền cam, `.pill.preorder`, ngày dự kiến có hàng trên giỏ, đơn, tra cứu, quản trị | shop, templates, app.css | Khách yêu cầu cho đặt sách hết hàng và báo khoảng mấy ngày có |
| 2026-11-22 | Link quản trị không hiện menu, footer, đăng ký của shop; header có nhãn Khu quản trị và nút Thoát; Xem website trỏ đúng link shop | base.html, login.html, context_processors | Bấm Tài khoản trên link quản trị nhảy sang tên miền shop (phiên riêng) nên trông như bị đăng xuất |
| 2026-11-22 | Harness thêm 3D: vendor three r170, `references/threejs-recipes.md`, lint 3D, QA bước 4c; agent mới `hep-code-auditor` (opus) chạy song song QA; orchestrator thêm bước 3b | hep-brand-ui, hep-ui-qa-check, hep-redesign, agents | Người dùng yêu cầu nạp three.js cho hiệu ứng và cho agent kiểm soát lại toàn bộ |
| 2026-11-22 | Vòng sửa sau kiểm toán: đơn đã hủy ẩn QR/chờ tiền/3D và báo đừng chuyển tiền | order_success.html, track.html | 09_auditor_recheck TRUNG BÌNH 2 |
| 2026-11-22 | Thêm mục 6b vào hep-brand-ui: cấm lặp khuôn section, từ vựng tiệm sách Nhật (kệ gáy sách, obi, POP viết tay, hanko, noren, tategaki, hoa văn), mật độ hiệu ứng mỗi màn hình cuộn | hep-brand-ui | Người dùng chê bản có 3D vẫn "AI quá, ít hiệu ứng quá" |
| 2026-11-22 | Lint W12 đợt wa: chặn .section-top ở home/detail, chặn POP/data-swing ở checkout, cảnh báo --font-hand ngoài .pop/.hand và quá 6 POP mỗi trang | hep-ui-qa-check | Giữ luật mục 6b không bị trôi ở các lần sửa sau |
