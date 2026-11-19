# HÉP STORE · Website bán sách Việt–Nhật và quản trị đa kênh

## Đọc trước

Đây là **source Django mới dựng lại theo nghiệp vụ Hép Store**, không phải bản merge tự động vào mã nguồn ZIP gốc (source ZIP không được cung cấp ở lượt yêu cầu này). Website demo; cần kiểm thử và bổ sung điều khoản, dữ liệu nguồn cung, hạ tầng và pháp lý trước khi vận hành thật.

Dữ liệu sản phẩm trong lần khởi tạo là **dữ liệu mẫu hư cấu**, không phải ấn phẩm, ISBN, nhà xuất bản hay nhà cung cấp có thật. Đây là giải pháp học tập, không phải bảo chứng đủ tiêu chuẩn vận hành thương mại công khai.

## Chạy trên Windows — 1 bước

1. Cài Python 3.12 tại python.org, tick **Add Python to PATH**.
2. Giải nén cả thư mục, nhấp đúp **CHAY_HEPSTORE.bat** hoặc mở PowerShell trong thư mục có `start.py` và nhập `py -3 start.py`.
3. Lần đầu cần Internet để `pip` tải Django 5.2 vào môi trường `.venv` riêng. `start.py` tự tạo migration, SQLite `db.sqlite3`, 16 sách mẫu và tài khoản quản trị.
4. **Ghi lại mật khẩu quản trị ngẫu nhiên hiển thị ở terminal**. Tên tài khoản: `admin` (mặc định). Mật khẩu chỉ hiển thị lần đầu. Nếu quên, chạy `.venv\Scripts\python.exe manage.py changepassword admin`.
5. Mở http://127.0.0.1:8000/ (khách hàng) và http://127.0.0.1:8000/management/ (nhân viên).
6. Dừng bằng Ctrl+C.

Cách chạy bằng terminal:
```
python start.py
```
Nếu cổng 8000 bận:
```
python start.py --port 8001
```
Kiểm thử Django:
```
.venv\Scripts\python.exe manage.py test shop
```

## Chạy trên macOS / Linux

```
python3 start.py
```

## Bốn kênh bán thống nhất

- Website: giỏ hàng, checkout COD hoặc QR khi có cấu hình ngân hàng.
- Facebook/Instagram: nhân viên vào `/management/social/new/`, chọn kênh, khách, sản phẩm, số lượng, tạo đơn.
- POS: nhân viên vào `/management/pos/`, tìm ISBN/SKU, sử dụng máy quét USB hoặc camera BarcodeDetector hỗ trợ (Chrome phù hợp, HTTPS/localhost), thêm sách vào giỏ và tạo hóa đơn.
- Đơn tạo tại bất cứ kênh nào đều dùng `Order`, `OrderItem`, `Book.stock` và `StockMovement`; tạo đơn trừ kho có điều kiện trong transaction; hủy được phép hoàn kho một lần.

## Cấu hình thanh toán QR ngân hàng

Không có số tài khoản giả mạo hay thông tin ngân hàng mặc định. Nếu không khai báo, website chỉ hỗ trợ COD và POS thanh toán tiền mặt.

PowerShell, từ thư mục dự án (thay bằng ngân hàng & số tài khoản THẬT của bạn):
```
$env:HEPSTORE_BANK_BIN="970436"       # chỉ là ví dụ BIN, cần xác minh BIN ngân hàng thật
$env:HEPSTORE_BANK_ACCOUNT="SO_TAI_KHOAN_THAT"
$env:HEPSTORE_BANK_OWNER="TEN_CHU_TAI_KHOAN_THAT"
py -3 start.py
```
**Chú ý:** trang thanh toán sinh link ảnh VietQR bên thứ ba `img.vietqr.io` chỉ khi các biến hợp lệ. Ngân hàng cần xác nhận bằng cách đối chiếu giao dịch thực nhận. Chỉ nhân viên có quyền staff mới nhấn nút "Tôi đã đối soát và nhận tiền". Hệ thống demo KHÔNG tích hợp webhook ngân hàng, KHÔNG tự nhận tiền, KHÔNG đối chiếu tự động. Không gửi dữ liệu nhạy cảm qua mã QR, chỉ mã đơn và số tiền.

## Đăng nhập quản trị và quyền

Tài khoản quản trị đầu tiên do chương trình tạo với mật khẩu ngẫu nhiên. Khách đăng ký ở `/dang-ky/` chỉ là user thường. Trang `/management/` kiểm tra `is_staff` bằng staff_member_required, tất cả thao tác POST cần CSRF. Django Admin `/admin/` dùng để quản lý nâng cao; không sửa trực tiếp trường tồn kho/trạng thái đơn khi muốn giữ nhật ký. Các đường dẫn nguồn cung, phiếu nhập, khách chỉ hiển thị cho nhân viên.

## Nguồn cung và kho

- `/management/suppliers/` — nhà cung cấp, chi tiết các sách được cung ứng và phiếu nhập.
- `/management/purchases/` — tạo phiếu nhập DRAFT, chỉ tăng kho khi xác nhận hàng đã về.
- `/management/inventory/` — điều chỉnh kho có lý do và nhật ký, cảnh báo tồn.
- `/management/orders/` — xử lý đơn, xác nhận thanh toán, hủy đơn và hoàn kho.
- `/management/reports/` — báo cáo theo kênh, trạng thái, số lượng bán và CSV.

## Camera / AI nhận diện bìa sách

Bản demo hỗ trợ `BarcodeDetector` của trình duyệt để quét mã EAN/ISBN, không cần học máy. Hỗ trợ nhập tay hoặc máy quét USB nếu thiết bị không hỗ trợ API. **Dữ liệu 16 sách demo có SKU `HEP-DEMO-xxx`, không phải ISBN thật để dùng camera**; thay SKU/ISBN trong quản trị bằng mã vạch thực tế nếu muốn thử quét.

Teachable Machine là *tùy chọn*, không có model bìa sách thực sự được huấn luyện trong gói. Tạo Image Project, đặt tên class chính xác là ISBN/SKU của sách tương ứng, train, export model rồi khai báo biến `HEPSTORE_TM_MODEL_URL`. Model cũ trong `index.html` nhận diện hàng tiêu dùng, không dùng cho sách. Nếu không cấu hình model, nút AI không hiển thị.

## Các URL chính

- `/` Trang chủ; `/sach/` danh mục; `/gio-hang/`; `/thanh-toan/`; `/tra-cuu-don/`.
- `/dang-ky/`; `/tai-khoan/login/`; `/tai-khoan-cua-toi/`.
- `/management/`; `/management/books/`; `/management/orders/`; `/management/pos/`; `/management/social/new/`; `/management/inventory/`; `/management/purchases/`; `/management/suppliers/`; `/management/customers/`; `/management/reports/`.
- `/admin/`.

## Phạm vi & giới hạn trước triển khai thật

- Demo SQLite/runserver, chưa có SSL, triển khai production, backend thanh toán chính thức, email xác nhận/khôi phục pass qua email, phí giao vận theo địa chỉ, hóa đơn điện tử, vận chuyển, sao lưu, kiểm toán nâng cao, giám sát và giới hạn tốc độ đăng nhập/tra cứu, chính sách riêng tư/đổi trả được luật sư duyệt.
- Không có cách xác thực tự động chuyển khoản; đánh dấu đã thu là hành động thủ công, cần quy trình đối soát.
- Đơn thủ công và checkout guest hiện vẫn tạo hồ sơ khách; cần rà soát quy tắc nhận diện khách và quyền riêng tư trước khi dùng thật.
- Chỉ chạy localhost cho mục tiêu môn học. **Đừng mở DEBUG=True ra Internet.** Đặt SECRET_KEY riêng, ALLOWED_HOSTS, secure cookies, HTTPS, server WSGI, backup, CSRF origins trước deployment.
- Tài liệu GitHub ví dụ người dùng cung cấp không truy cập được trong phiên xây dựng, nên không tuyên bố đã copy/đối chiếu mã của repo đó.

## Liên kết mô hình dữ liệu

`Category → Book ← Supplier` ; `Customer → Order → OrderItem → Book` ; `Book → StockMovement` ; `Supplier → PurchaseOrder → PurchaseItem → Book`.

Luồng tiền: Order.payment_method (bank/cod/cash), Order.payment_status (unpaid/paid), staff xác nhận `paid_at` và `payment_confirmed_by`. Luồng giao hàng: new → confirmed → packing → shipped → completed; hủy hợp lệ (đơn chưa thanh toán) hoàn tồn qua StockMovement; đơn đã thu tiền cần quy trình hoàn tiền riêng, demo chặn hủy trực tiếp.

## Bảo lưu source gốc

Không chép đè thư mục dự án cũ. Mở bản này ở thư mục riêng. Để hợp nhất *đúng phiên bản cũ* cần source gốc có `shop/models.py`, `shop/services.py`, `shop/dashboard.py`, `shop/urls.py`, templates và migrations.

## Thay ảnh bìa thật

Đặt ảnh của bạn vào `static/img/` (ví dụ `books/bia-001.jpg`), tạo thư mục tương ứng nếu cần, và cập nhật `Book.cover` thành `books/bia-001.jpg` trên trang quản lý sách. Các ảnh SVG hiện tại đều do dự án tạo cho dữ liệu demo, không phải bìa sách xuất bản.
