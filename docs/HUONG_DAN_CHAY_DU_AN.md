# Hướng dẫn chạy dự án Hép Bookstore

Dành cho chủ tiệm (Nga) và người bạn lập trình giúp chạy dự án.

## Mục lục

- 1. Dự án là gì
- 2. Chuẩn bị trên Windows
- 3. Chạy lần đầu
- 4. Mở hai link
- 5. Cấu hình file .env
- 6. Nhận tiền tự động qua SePay
- 7. Sử dụng hằng ngày
- 8. Dành cho người lập trình
- 9. Sự cố thường gặp
- 10. Bảng tóm tắt lệnh hay dùng

## 1. Dự án là gì

Hép Bookstore là website bán sách Việt Nhật của tiệm Hép. Có hai link riêng:

| Link | Dùng cho | Đăng nhập |
| --- | --- | --- |
| http://shop.localhost:8000 | Khách xem sách, đặt hàng, quét QR thanh toán | Không cần |
| http://quantri.localhost:8000 | Nhân viên: đơn hàng, POS, kho, tiền vào | Bắt buộc, theo vai trò |

- Dự án chạy ngay trên máy tính của bạn. Không cần thuê hosting.
- Dữ liệu nằm trong một file duy nhất tên db.sqlite3 trong thư mục dự án.
- Chỉ khi máy đang chạy và đang mở cửa sổ lệnh thì web mới hoạt động.

## 2. Chuẩn bị trên Windows

### 2.1 Cài Python

1. Vào https://www.python.org/downloads/ và tải Python 3.12 (dự án cần Python 3.10 trở lên).
2. Mở file vừa tải.
3. Ở màn hình đầu tiên, TICK ô "Add Python to PATH" (hoặc "Add python.exe to PATH").
4. Bấm "Install Now" và chờ xong.

> **Lưu ý: Nếu quên tick "Add Python to PATH", lệnh python sẽ báo không tìm thấy. Hãy chạy lại file cài, chọn Modify hoặc gỡ ra cài lại và tick ô này.**

### 2.2 Cài Chrome

Tải Google Chrome tại https://www.google.com/chrome/. Link *.localhost chạy tốt nhất trên Chrome hoặc Edge. Quét mã vạch bằng camera cũng cần Chrome.

### 2.3 Tải và giải nén dự án

1. Nhận file nén (zip) của dự án từ người lập trình.
2. Bấm chuột phải vào file zip, chọn "Extract All" (Giải nén tất cả).
3. Đặt thư mục ở nơi dễ nhớ, ví dụ C:\HepStore. Tránh đường dẫn có dấu tiếng Việt.
4. Mở thư mục và kiểm tra thấy các file start.py, manage.py, CHAY_HEPSTORE.bat.

## 3. Chạy lần đầu

### 3.1 Cách dễ nhất

Bấm đúp vào file CHAY_HEPSTORE.bat trong thư mục dự án. File này tự chạy lệnh py -3 start.py.

### 3.2 Cách dùng cửa sổ lệnh

1. Mở thư mục dự án trong File Explorer.
2. Bấm vào thanh địa chỉ phía trên, gõ powershell rồi nhấn Enter.
3. Gõ lệnh dưới đây rồi nhấn Enter.

```
py start.py
```

Nếu báo không tìm thấy lệnh py, thử:

```
python start.py
```

Trên macOS hoặc Linux dùng python3 start.py.

### 3.3 start.py tự làm gì

- Tạo môi trường Python riêng trong thư mục .venv.
- Tải và cài Django 5.2 (lần đầu cần Internet).
- Tạo bảng dữ liệu trong db.sqlite3.
- Thêm 16 cuốn sách mẫu (nếu không muốn, thêm --no-seed).
- Tạo tài khoản quản trị tên admin kèm mật khẩu ngẫu nhiên.
- Mở web ở cổng 8000.

Các tuỳ chọn thêm của start.py:

| Lệnh | Tác dụng |
| --- | --- |
| py start.py --port 8001 | Chạy ở cổng khác khi cổng 8000 bận (link đổi :8000 thành :8001) |
| py start.py --no-run | Chỉ cài và khởi tạo dữ liệu, không bật web |
| py start.py --no-seed | Không thêm sách mẫu |

### 3.4 Mật khẩu quản trị

Khi chạy lần đầu, cửa sổ lệnh hiện khung như sau (mật khẩu thật sẽ khác):

```
TÀI KHOẢN QUẢN TRỊ DEMO (HÃY ĐỔI MẬT KHẨU SAU KHI ĐĂNG NHẬP)
Tài khoản: admin
Mật khẩu một lần: <chuỗi ngẫu nhiên>
```

> **Lưu ý: Mật khẩu chỉ hiện MỘT LẦN. Hãy chép và cất vào nơi an toàn ngay (sổ tay hoặc trình quản lý mật khẩu). Không gửi mật khẩu qua tin nhắn.**

Nếu quên hoặc muốn đổi mật khẩu, dừng web bằng Ctrl+C rồi chạy:

```
.venv\Scripts\python.exe manage.py changepassword admin
```

Máy sẽ hỏi mật khẩu mới hai lần. Gõ mật khẩu sẽ không hiện ký tự, đó là bình thường.

Lần chạy sau, chỉ cần chạy lại py start.py. Web sẽ lên nhanh hơn và dữ liệu cũ vẫn còn. Dừng web bằng Ctrl+C.

## 4. Mở hai link

1. Mở Chrome hoặc Edge.
2. Link khách hàng: http://shop.localhost:8000
3. Link nhân viên: http://quantri.localhost:8000 rồi đăng nhập bằng tài khoản admin.

Hai link có phiên đăng nhập riêng vì trình duyệt coi chúng là hai trang khác nhau. Việc này có chủ ý:

- Khách không thể vô tình vào khu quản trị.
- Đăng nhập ở link quản trị không làm khách thấy menu nhân viên.
- Mở /management/ trên link shop sẽ tự chuyển sang link quản trị.

> **Lưu ý: Bấm "Tài khoản" trên link quản trị không đăng xuất bạn. Link shop chỉ là phiên khác nên trông như chưa đăng nhập.**

## 5. Cấu hình file .env

File .env chứa thông tin ngân hàng và khoá bí mật. Trong thư mục dự án có file mẫu tên .env.example.

1. Sao chép .env.example thành một file mới tên .env (cùng thư mục).
2. Mở .env bằng Notepad, sửa các dòng theo bảng dưới (mỗi dòng dạng TEN=giá trị, không có khoảng trắng quanh dấu =).
3. Lưu file, dừng web (Ctrl+C) và chạy lại py start.py.

| Biến | Ý nghĩa | Ví dụ (giả) |
| --- | --- | --- |
| HEPSTORE_BANK_BIN | Mã ngân hàng (BIN) để tạo QR | 970422 |
| HEPSTORE_BANK_ACCOUNT | Số tài khoản nhận tiền | 0123456789 |
| HEPSTORE_BANK_OWNER | Tên chủ tài khoản, viết hoa, không dấu | NGUYEN VAN A |
| HEPSTORE_SEPAY_API_KEY | Khoá bí mật để SePay gọi vào web | abc123...chuoi-ngau-nhien |
| HEPSTORE_SHOP_HOST | Tên link khách hàng | shop.localhost |
| HEPSTORE_ADMIN_HOST | Tên link quản trị | quantri.localhost |
| HEPSTORE_TUNNEL_HOSTS | Tên miền tunnel (ngrok) cho SePay, xem mục 6 | abcd-12-34.ngrok-free.app |
| HEPSTORE_ORDER_HOLD_DAYS | Số ngày giữ đơn web chưa trả tiền, mặc định 3 | 3 |
| HEPSTORE_MAX_OPEN_WEB_ORDERS | Số đơn web đang mở tối đa mỗi số điện thoại, mặc định 3 | 3 |
| HEPSTORE_SECRET_KEY | Khoá nội bộ của Django, nên đặt chuỗi ngẫu nhiên riêng | chuoi-ngau-nhien-dai |

Mã BIN ngân hàng thường dùng: MB Bank là 970422, Vietcombank là 970436. Ngân hàng khác, hãy tra danh sách BIN VietQR và kiểm tra lại cho đúng.

Ví dụ một đoạn .env (toàn bộ giá trị là giả):

```
HEPSTORE_BANK_BIN=970422
HEPSTORE_BANK_ACCOUNT=0123456789
HEPSTORE_BANK_OWNER=NGUYEN VAN A
HEPSTORE_SEPAY_API_KEY=thay-bang-chuoi-ngau-nhien
HEPSTORE_TUNNEL_HOSTS=abcd-12-34.ngrok-free.app
```

### Tạo khoá SePay ngẫu nhiên

```
py -c "import secrets; print(secrets.token_urlsafe(32))"
```

Chép chuỗi in ra, dán vào HEPSTORE_SEPAY_API_KEY trong .env. Sau này dán đúng chuỗi đó vào SePay (mục 6).

> **Lưu ý: TUYỆT ĐỐI không gửi file .env cho ai và không đưa lên GitHub. File này chứa khoá bí mật và thông tin ngân hàng. Nếu lỡ lộ, tạo khoá mới, sửa trong .env và trong SePay.**

Nếu không điền thông tin ngân hàng, web không hiện mã QR (chỉ còn thanh toán khi nhận hàng và tiền mặt tại POS).

## 6. Nhận tiền tự động qua SePay

SePay báo cho web biết khi có tiền vào tài khoản, đơn sẽ tự chuyển sang "Đã thanh toán". Việc liên kết ngân hàng cần chính chủ tài khoản làm vì có OTP.

### 6.1 Đăng ký và liên kết ngân hàng

1. Vào https://my.sepay.vn và đăng ký tài khoản.
2. Liên kết tài khoản ngân hàng nhận tiền của tiệm.
3. Trong cấu hình công ty, phần cấu trúc mã thanh toán, đặt tiền tố HEP (mã đơn của web bắt đầu bằng HEP).

### 6.2 Mở tunnel bằng ngrok

SePay cần một địa chỉ công khai để gọi vào máy của bạn. ngrok tạo địa chỉ đó miễn phí.

1. Đăng ký và tải ngrok tại https://ngrok.com, làm theo hướng dẫn gắn authtoken của họ.
2. Chạy web trước (cửa sổ lệnh 1): py start.py
3. Mở cửa sổ lệnh 2 và gõ lệnh dưới đây.
4. ngrok in ra dòng Forwarding, dạng https://abcd-12-34.ngrok-free.app. Chép tên miền đó.
5. Mở .env, thêm dòng HEPSTORE_TUNNEL_HOSTS=abcd-12-34.ngrok-free.app (chỉ tên miền, không có https://).
6. Dừng web (Ctrl+C) và chạy lại py start.py.

```
ngrok http 8000
```

### 6.3 Tạo webhook trên SePay

Vào mục Tích hợp Webhooks, bấm Thêm webhooks, rồi điền từng ô:

| Ô trên SePay | Điền |
| --- | --- |
| Sự kiện | Có tiền vào |
| URL | https://abcd-12-34.ngrok-free.app/api/sepay/webhook/ (thay bằng tên miền ngrok của bạn) |
| Kiểu chứng thực | API Key, dán đúng giá trị HEPSTORE_SEPAY_API_KEY trong .env |
| Xác thực thanh toán | Bật |
| Content type | application/json |

> **Lưu ý: Địa chỉ ngrok bản miễn phí ĐỔI mỗi lần chạy lại ngrok. Mỗi lần đổi, phải sửa HEPSTORE_TUNNEL_HOSTS trong .env, chạy lại start.py và sửa URL webhook trên SePay.**

### 6.4 Thử bằng 2.000đ qua POS

1. Vào link quản trị, mở mục POS.
2. Thêm một sách mẫu rẻ hoặc sách bất kỳ vào giỏ, chọn thanh toán chuyển khoản, tạo hoá đơn.
3. Hoá đơn POS không tính phí ship nên số tiền đúng bằng giá sách. Hãy đặt giá sách thử là 2.000đ.
4. Dùng app ngân hàng quét QR và chuyển 2.000đ, giữ nguyên nội dung chuyển khoản (có mã HEP...).
5. Sau vài giây, đơn tự chuyển sang "Đã thanh toán" và mục "Tiền vào" hiện khoản mới.

### 6.5 Thử không cần tiền thật

Lệnh sau giả lập SePay báo tiền vào. Thay HEP261121A1B2C3D4 bằng mã đơn thật (xem ở trang đơn).

```
.venv\Scripts\python.exe manage.py sepay_thu HEP261121A1B2C3D4
.venv\Scripts\python.exe manage.py sepay_thu HEP261121A1B2C3D4 --amount 1000
```

Lệnh đầu báo đúng số tiền của đơn (đơn tự thành "Đã thanh toán"). Lệnh sau báo sai số tiền (đơn không đổi, giao dịch ở mục Tiền vào chờ xử lý).

## 7. Sử dụng hằng ngày

### 7.1 Phân quyền nhân viên

| Vai trò | Được làm |
| --- | --- |
| Quản lý (chủ tiệm) | Mọi thứ: báo cáo, xuất CSV, tạo nhân viên, xác nhận tiền tay, hoàn tiền |
| Bán hàng | Tổng quan, đơn hàng, POS, đơn Facebook/Instagram, khách hàng, mục Tiền vào (gắn giao dịch) |
| Kho | Tổng quan, sách, tồn kho, nhà cung cấp, phiếu nhập hàng |

Nhân viên mở trang ngoài quyền sẽ thấy thông báo không đủ quyền (mã 403). Xác nhận tiền tay và hoàn tiền chỉ Quản lý làm được, để người bán hàng không tự xác nhận tiền.

### 7.2 Thêm nhân viên

1. Đăng nhập link quản trị bằng tài khoản Quản lý.
2. Mở mục "Nhân viên và quyền".
3. Bấm "Thêm nhân viên", nhập tên đăng nhập, mật khẩu và chọn vai trò.

### 7.3 Thêm sách

1. Mở mục Sách (vai trò Kho hoặc Quản lý), bấm thêm sách.
2. Điền tên, danh mục, giá bán, số lượng tồn và mã ISBN hoặc SKU (mã vạch).
3. Tick "Nhận đặt trước khi hết hàng" nếu cho khách đặt khi hết sách.
4. Điền "Số ngày dự kiến có hàng" (1 đến 90, mặc định 10). Khách sẽ thấy khoảng mấy ngày nữa có hàng.
5. Lưu.

### 7.4 POS và quét mã vạch

1. Vào mục POS trên link quản trị.
2. Quét mã vạch bằng máy quét USB (cắm vào là dùng), hoặc bật camera trong Chrome, hoặc gõ tay ISBN/SKU.
3. Sách vào giỏ. Chỉnh số lượng nếu cần.
4. Chọn tiền mặt hoặc chuyển khoản rồi tạo hoá đơn.

> **Lưu ý: 16 sách mẫu có mã HEP-DEMO-xxx, không phải mã vạch thật. Muốn thử quét, sửa mã sách thành mã vạch in trên sách thật.**

### 7.5 Đơn Facebook và Instagram

1. Mở mục đơn Facebook/Instagram (đường dẫn /management/social/new/).
2. Chọn kênh, khách hàng, sách và số lượng.
3. Tạo đơn. Đơn nằm chung danh sách đơn và trừ kho như đơn web.

### 7.6 Nhập hàng

1. Kho vào mục Nhà cung cấp và thêm nhà cung cấp (nếu chưa có).
2. Vào mục Phiếu nhập, tạo phiếu mới. Phiếu ở trạng thái Bản nháp, kho chưa tăng.
3. Khi hàng về thật, mở phiếu và bấm xác nhận nhập kho. Lúc này tồn kho mới tăng.

### 7.7 Đơn đặt trước và hàng về

- Mỗi cuốn sách có hai cài đặt trong trang sửa sách: "Nhận đặt trước khi hết hàng" và "Số ngày dự kiến có hàng" (mặc định 10 ngày).
- Sách hết hàng mà có bật đặt trước thì khách thấy nút "Đặt trước" và dòng "Có hàng khoảng N ngày". Lúc thanh toán, khách phải thấy dòng báo đặt trước rồi mới đặt được.
- Khách đặt nhiều hơn số còn trong kho: phần còn hàng trừ kho ngay, phần thiếu ghi là "chờ hàng về". Đơn có nhãn "Đặt trước" và ngày dự kiến có hàng.
- Khi hàng về (bấm nhập kho ở phiếu nhập, hoặc điều chỉnh tăng tồn kho), hệ thống tự giữ sách cho đơn đặt trước trước: đơn đã trả tiền nhận trước, sau đó theo thứ tự ai đặt trước. Phần còn dư mới bán cho khách khác.
- Đơn đặt trước chỉ chuyển sang "Đang đóng gói" khi đã đủ sách. Nếu chưa đủ, hệ thống báo cần nhập hàng trước khi giao.
- Huỷ một đơn thì sách đã giữ cho đơn đó tự chuyển sang đơn đặt trước đang chờ tiếp theo.

### 7.8 Xác nhận tiền tay

Tiền chuyển khoản bình thường do SePay tự xác nhận. Xác nhận tay chỉ dùng khi cần, và có hai cách:

- Khách chuyển đúng tiền nhưng ghi sai nội dung: vào mục "Tiền vào (SePay)", tìm giao dịch không khớp, nhập mã đơn để gắn vào đơn. Nhân viên Bán hàng làm được, vì có giao dịch ngân hàng làm bằng chứng. Số tiền phải đúng bằng tổng đơn.
- Không có giao dịch SePay (ví dụ thu tiền mặt khi giao COD): mở chi tiết đơn, bấm "Tôi đã đối soát và nhận tiền", bấm thêm lần nữa để chắc chắn. Chỉ Quản lý làm được.

### 7.9 Huỷ đơn kèm hoàn tiền

1. Chuyển tiền trả khách bằng app ngân hàng trước. Hệ thống không tự chuyển tiền.
2. Mở chi tiết đơn đã thu tiền (chỉ Quản lý thấy phần này). Đơn đang giao hoặc đã hoàn tất thì không huỷ được ở đây.
3. Ghi vào ô ghi chú đã hoàn tiền thế nào (ví dụ: CK trả lại, mã giao dịch), rồi bấm "Hủy đơn và ghi nhận đã hoàn tiền", bấm thêm lần nữa để chắc chắn.
4. Đơn chuyển sang "Đã hủy" và "Đã hoàn tiền", sách trả về kho và được giữ cho đơn đặt trước đang chờ (nếu có).

Đơn chưa trả tiền thì huỷ ở trang đơn bình thường và sách cũng trả về kho.

### 7.10 Đơn tự huỷ sau N ngày

Đơn web chưa xác nhận và chưa trả tiền quá HEPSTORE_ORDER_HOLD_DAYS ngày (mặc định 3) sẽ bị huỷ và trả sách về kho. Hệ thống tự làm việc này khi nhân viên mở trang tổng quan. Muốn chạy ngay:

```
.venv\Scripts\python.exe manage.py huy_don_qua_han
```

## 8. Dành cho người lập trình

| Việc | Lệnh hoặc nơi xem |
| --- | --- |
| Chạy toàn bộ test | python3 manage.py test shop |
| Bỏ test E2E (không cần Chrome) | python3 manage.py test shop --exclude-tag e2e |
| Xuất lại sơ đồ ERD | python3 docs/gen_erd.py rồi python3 docs/render_erd.py |
| Dựng lại file hướng dẫn này | python3 docs/build_huong_dan.py |

- Test E2E dùng Playwright và cần Chrome thật. Cài: pip install playwright. Nếu không có Chrome, bỏ E2E bằng --exclude-tag e2e.
- render_erd.py cũng cần Playwright. gen_erd.py đọc shop/models.py và ghi docs/ERD_Hep_Bookstore.md, erd.mmd, .html. render_erd.py xuất .png và .pdf.
- Giao diện: xem CLAUDE.md ở thư mục gốc. Thư mục .claude chứa agents (hep-ui-designer, hep-frontend-dev, hep-ui-qa, hep-code-auditor) và skills (hep-redesign, hep-brand-ui, hep-ui-qa-check). Mọi thay đổi giao diện đi qua skill hep-redesign.
- Sao lưu: tắt web rồi chép db.sqlite3 sang nơi khác (ổ USB, đám mây) kèm ngày, ví dụ db-2026-11-23.sqlite3. Nên sao lưu mỗi ngày. Khôi phục bằng cách chép đè lại file.
- Chế độ runserver chỉ để chạy thử trên máy. Không mở DEBUG ra Internet. Muốn chạy công khai, cần đặt SECRET_KEY riêng, HTTPS và máy chủ WSGI.

## 9. Sự cố thường gặp

| Hiện tượng | Cách xử lý |
| --- | --- |
| Cổng 8000 bận | Chạy py start.py --port 8001 và mở link với :8001. Hoặc tắt chương trình đang dùng cổng 8000. |
| Link *.localhost không mở | Dùng Chrome hoặc Edge. Kiểm tra gõ đúng http:// và có :8000. Đừng dùng trình duyệt cũ. |
| Báo không tìm thấy python hoặc py | Cài lại Python và tick Add Python to PATH. Mở cửa sổ lệnh mới rồi thử lại. |
| Lần đầu báo lỗi khi cài | Kiểm tra mạng Internet (lần đầu cần tải Django), rồi chạy lại. |
| Quên mật khẩu quản trị | .venv\Scripts\python.exe manage.py changepassword admin |
| Khách chuyển tiền mà đơn không tự xác nhận | 1) ngrok còn chạy không. 2) URL webhook trên SePay đúng tên miền ngrok hiện tại và kết thúc bằng /api/sepay/webhook/. 3) Khoá API trong SePay trùng HEPSTORE_SEPAY_API_KEY. 4) Tên miền ngrok có trong HEPSTORE_TUNNEL_HOSTS. 5) Nội dung chuyển khoản phải có mã đơn HEP... 6) Vào mục Tiền vào trên link quản trị, tìm giao dịch và gắn tay vào đơn. |
| QR không hiện | Kiểm tra .env có đủ BANK_BIN, BANK_ACCOUNT, BANK_OWNER, đúng chính tả, rồi chạy lại start.py. Cần Internet để tải ảnh QR. |
| Sửa .env mà không thấy đổi | Dừng web (Ctrl+C) và chạy lại py start.py. |

## 10. Bảng tóm tắt lệnh hay dùng

Chạy các lệnh trong thư mục dự án. Trên Windows, lệnh manage.py dùng .venv\Scripts\python.exe (macOS và Linux: python3).

| Việc | Lệnh |
| --- | --- |
| Chạy web | py start.py |
| Chạy cổng khác | py start.py --port 8001 |
| Dừng web | Ctrl+C trong cửa sổ lệnh |
| Đổi mật khẩu admin | .venv\Scripts\python.exe manage.py changepassword admin |
| Mở tunnel cho SePay | ngrok http 8000 |
| Sinh khoá SePay ngẫu nhiên | py -c "import secrets; print(secrets.token_urlsafe(32))" |
| Giả lập tiền về | .venv\Scripts\python.exe manage.py sepay_thu <mã đơn> [--amount SỐ_TIỀN] |
| Huỷ đơn quá hạn | .venv\Scripts\python.exe manage.py huy_don_qua_han |
| Chạy test | .venv\Scripts\python.exe manage.py test shop --exclude-tag e2e |
| Sao lưu dữ liệu | Chép file db.sqlite3 khi web đã tắt |
