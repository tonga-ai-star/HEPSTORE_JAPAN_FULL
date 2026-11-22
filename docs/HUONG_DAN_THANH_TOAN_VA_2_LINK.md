# Thanh toán QR tự động, 2 link và phân quyền

## 1. Hai link (chạy thử, chưa cần hosting)

`python3 start.py` rồi mở:

| Link | Dùng cho | Đăng nhập |
| --- | --- | --- |
| http://shop.localhost:8000/ | Khách xem sách, đặt hàng, quét QR thanh toán | Không cần |
| http://quantri.localhost:8000/ | Nhân viên: đơn, POS quét mã, đơn Facebook/Instagram, kho, tiền vào | Bắt buộc, theo vai trò |

`*.localhost` tự trỏ về máy mình trong Chrome, Edge, Firefox nên không cần sửa file hosts. Khi có tên miền thật, đổi `HEPSTORE_SHOP_HOST` và `HEPSTORE_ADMIN_HOST` trong `.env`.

Mở `/management/` trên link bán hàng sẽ tự chuyển sang link quản trị. Mở trang sách trên link quản trị sẽ tự chuyển về link bán hàng.

## 2. Vai trò nhân viên

| Vai trò | Được dùng |
| --- | --- |
| Quản lý (chủ cửa hàng là superuser) | Toàn bộ, kể cả báo cáo, xuất CSV, tạo nhân viên |
| Bán hàng | Tổng quan, đơn hàng, POS quét mã, đơn Facebook/Instagram, khách hàng, tiền vào |
| Kho | Tổng quan, sách, tồn kho, nhà cung cấp, phiếu nhập |

Tạo nhân viên: link quản trị, mục "Nhân viên và quyền", nút "Thêm nhân viên". Mở trang ngoài quyền sẽ thấy trang báo không đủ quyền (mã 403).

## 3. Thanh toán QR không cần đăng nhập

1. Khách đặt hàng, chọn chuyển khoản. Trang đơn hiện QR VietQR (MB Bank) với đúng số tiền và nội dung là mã đơn (ví dụ `HEP261121A1B2C3D4`).
2. Khách quét QR bằng app ngân hàng và chuyển.
3. Ngân hàng báo SePay, SePay gọi `POST /api/sepay/webhook/` của web kèm khoá API.
4. Web lưu giao dịch, tìm mã đơn trong nội dung, so số tiền. Khớp thì đơn tự sang "Đã thanh toán" và "Đã xác nhận".
5. Trang đơn của khách đang mở tự hiện "Thanh toán thành công" (hỏi lại mỗi 4 giây). Nhân viên thấy khoản tiền mới ở mục "Tiền vào".

Sai số tiền hoặc không có mã đơn: giao dịch vẫn được lưu với trạng thái cần xử lý. Nhân viên gắn tay vào đơn ở mục "Tiền vào".

## 4. Cài SePay (bản miễn phí)

Việc này cần chủ tài khoản ngân hàng tự làm vì có xác thực OTP.

1. Đăng ký tại https://my.sepay.vn, liên kết tài khoản MB Bank (số tài khoản ghi trong .env) nhận tiền.
2. Vào **Tích hợp Webhooks**, bấm **Thêm webhooks**:
   - Sự kiện: **Có tiền vào**.
   - URL: `https://<địa-chỉ-tunnel>/api/sepay/webhook/`
   - Kiểu chứng thực: **API Key**, dán đúng giá trị `HEPSTORE_SEPAY_API_KEY` trong file `.env`.
   - Content type: `application/json`.
3. Trong **Cấu hình công ty > Cấu trúc mã thanh toán**, đặt tiền tố `HEP` để SePay nhận diện mã đơn.

### Chạy thử không có hosting

SePay cần một địa chỉ công khai. Dùng tunnel miễn phí:

```bash
python3 start.py                                   # terminal 1
cloudflared tunnel --url http://localhost:8000     # terminal 2, in ra https://xxxx.trycloudflare.com
```

Thêm vào `.env`: `HEPSTORE_TUNNEL_HOSTS=.trycloudflare.com` rồi chạy lại `start.py`. Dán `https://xxxx.trycloudflare.com/api/sepay/webhook/` vào SePay. Địa chỉ tunnel đổi mỗi lần chạy lại.

### Thử không cần SePay

```bash
python3 manage.py sepay_thu HEP261121A1B2C3D4              # tiền về đúng số
python3 manage.py sepay_thu HEP261121A1B2C3D4 --amount 1000  # sai số tiền
```

Trang đơn đang mở sẽ tự chuyển sang "Thanh toán thành công" trong vài giây.

## 5. Bảo mật cần nhớ

- File `.env` chứa khoá API và không được commit. Nếu lộ khoá, đổi chuỗi mới trong `.env` và trong SePay.
- Không gửi mật khẩu email hay ngân hàng qua tin nhắn. Nếu đã gửi, đổi mật khẩu và bật lại xác thực 2 lớp ngay sau khi cài xong.
- Webhook từ chối mọi request sai khoá (401), bỏ qua giao dịch gửi lại trùng mã, không bao giờ đánh dấu đã thanh toán khi sai số tiền.
