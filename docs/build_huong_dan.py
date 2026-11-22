#!/usr/bin/env python3
"""Dựng docs/HUONG_DAN_CHAY_DU_AN.docx và .md từ cùng một nội dung.

Chạy:  python3 docs/build_huong_dan.py   (cần python-docx: pip install python-docx)
"""
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

DOCS = Path(__file__).resolve().parent
PY = r'.venv\Scripts\python.exe'
TITLE = 'Hướng dẫn chạy dự án Hép Bookstore'

# Khối nội dung: (loại, dữ liệu). Loại: h1, h2, p, steps, bullets, code, note, table
C = []
def add(kind, *data): C.append((kind, *data))

add('h1', '1. Dự án là gì')
add('p', 'Hép Bookstore là website bán sách Việt Nhật của tiệm Hép. Có hai link riêng:')
add('table', ['Link', 'Dùng cho', 'Đăng nhập'], [
    ['http://shop.localhost:8000', 'Khách xem sách, đặt hàng, quét QR thanh toán', 'Không cần'],
    ['http://quantri.localhost:8000', 'Nhân viên: đơn hàng, POS, kho, tiền vào', 'Bắt buộc, theo vai trò'],
])
add('bullets', [
    'Dự án chạy ngay trên máy tính của bạn. Không cần thuê hosting.',
    'Dữ liệu nằm trong một file duy nhất tên db.sqlite3 trong thư mục dự án.',
    'Chỉ khi máy đang chạy và đang mở cửa sổ lệnh thì web mới hoạt động.',
])

add('h1', '2. Chuẩn bị trên Windows')
add('h2', '2.1 Cài Python')
add('steps', [
    'Vào https://www.python.org/downloads/ và tải Python 3.12 (dự án cần Python 3.10 trở lên).',
    'Mở file vừa tải.',
    'Ở màn hình đầu tiên, TICK ô "Add Python to PATH" (hoặc "Add python.exe to PATH").',
    'Bấm "Install Now" và chờ xong.',
])
add('note', 'Lưu ý: Nếu quên tick "Add Python to PATH", lệnh python sẽ báo không tìm thấy. Hãy chạy lại file cài, chọn Modify hoặc gỡ ra cài lại và tick ô này.')
add('h2', '2.2 Cài Chrome')
add('p', 'Tải Google Chrome tại https://www.google.com/chrome/. Link *.localhost chạy tốt nhất trên Chrome hoặc Edge. Quét mã vạch bằng camera cũng cần Chrome.')
add('h2', '2.3 Tải và giải nén dự án')
add('steps', [
    'Nhận file nén (zip) của dự án từ người lập trình.',
    'Bấm chuột phải vào file zip, chọn "Extract All" (Giải nén tất cả).',
    'Đặt thư mục ở nơi dễ nhớ, ví dụ C:\\HepStore. Tránh đường dẫn có dấu tiếng Việt.',
    'Mở thư mục và kiểm tra thấy các file start.py, manage.py, CHAY_HEPSTORE.bat.',
])

add('h1', '3. Chạy lần đầu')
add('h2', '3.1 Cách dễ nhất')
add('p', 'Bấm đúp vào file CHAY_HEPSTORE.bat trong thư mục dự án. File này tự chạy lệnh py -3 start.py.')
add('h2', '3.2 Cách dùng cửa sổ lệnh')
add('steps', [
    'Mở thư mục dự án trong File Explorer.',
    'Bấm vào thanh địa chỉ phía trên, gõ powershell rồi nhấn Enter.',
    'Gõ lệnh dưới đây rồi nhấn Enter.',
])
add('code', 'py start.py')
add('p', 'Nếu báo không tìm thấy lệnh py, thử:')
add('code', 'python start.py')
add('p', 'Trên macOS hoặc Linux dùng python3 start.py.')
add('h2', '3.3 start.py tự làm gì')
add('bullets', [
    'Tạo môi trường Python riêng trong thư mục .venv.',
    'Tải và cài Django 5.2 (lần đầu cần Internet).',
    'Tạo bảng dữ liệu trong db.sqlite3.',
    'Thêm 16 cuốn sách mẫu (nếu không muốn, thêm --no-seed).',
    'Tạo tài khoản quản trị tên admin kèm mật khẩu ngẫu nhiên.',
    'Mở web ở cổng 8000.',
])
add('p', 'Các tuỳ chọn thêm của start.py:')
add('table', ['Lệnh', 'Tác dụng'], [
    ['py start.py --port 8001', 'Chạy ở cổng khác khi cổng 8000 bận (link đổi :8000 thành :8001)'],
    ['py start.py --no-run', 'Chỉ cài và khởi tạo dữ liệu, không bật web'],
    ['py start.py --no-seed', 'Không thêm sách mẫu'],
])
add('h2', '3.4 Mật khẩu quản trị')
add('p', 'Khi chạy lần đầu, cửa sổ lệnh hiện khung như sau (mật khẩu thật sẽ khác):')
add('code', 'TÀI KHOẢN QUẢN TRỊ DEMO (HÃY ĐỔI MẬT KHẨU SAU KHI ĐĂNG NHẬP)\nTài khoản: admin\nMật khẩu một lần: <chuỗi ngẫu nhiên>')
add('note', 'Lưu ý: Mật khẩu chỉ hiện MỘT LẦN. Hãy chép và cất vào nơi an toàn ngay (sổ tay hoặc trình quản lý mật khẩu). Không gửi mật khẩu qua tin nhắn.')
add('p', 'Nếu quên hoặc muốn đổi mật khẩu, dừng web bằng Ctrl+C rồi chạy:')
add('code', PY + ' manage.py changepassword admin')
add('p', 'Máy sẽ hỏi mật khẩu mới hai lần. Gõ mật khẩu sẽ không hiện ký tự, đó là bình thường.')
add('p', 'Lần chạy sau, chỉ cần chạy lại py start.py. Web sẽ lên nhanh hơn và dữ liệu cũ vẫn còn. Dừng web bằng Ctrl+C.')

add('h1', '4. Mở hai link')
add('steps', [
    'Mở Chrome hoặc Edge.',
    'Link khách hàng: http://shop.localhost:8000',
    'Link nhân viên: http://quantri.localhost:8000 rồi đăng nhập bằng tài khoản admin.',
])
add('p', 'Hai link có phiên đăng nhập riêng vì trình duyệt coi chúng là hai trang khác nhau. Việc này có chủ ý:')
add('bullets', [
    'Khách không thể vô tình vào khu quản trị.',
    'Đăng nhập ở link quản trị không làm khách thấy menu nhân viên.',
    'Mở /management/ trên link shop sẽ tự chuyển sang link quản trị.',
])
add('note', 'Lưu ý: Bấm "Tài khoản" trên link quản trị không đăng xuất bạn. Link shop chỉ là phiên khác nên trông như chưa đăng nhập.')

add('h1', '5. Cấu hình file .env')
add('p', 'File .env chứa thông tin ngân hàng và khoá bí mật. Trong thư mục dự án có file mẫu tên .env.example.')
add('steps', [
    'Sao chép .env.example thành một file mới tên .env (cùng thư mục).',
    'Mở .env bằng Notepad, sửa các dòng theo bảng dưới (mỗi dòng dạng TEN=giá trị, không có khoảng trắng quanh dấu =).',
    'Lưu file, dừng web (Ctrl+C) và chạy lại py start.py.',
])
add('table', ['Biến', 'Ý nghĩa', 'Ví dụ (giả)'], [
    ['HEPSTORE_BANK_BIN', 'Mã ngân hàng (BIN) để tạo QR', '970422'],
    ['HEPSTORE_BANK_ACCOUNT', 'Số tài khoản nhận tiền', '0123456789'],
    ['HEPSTORE_BANK_OWNER', 'Tên chủ tài khoản, viết hoa, không dấu', 'NGUYEN VAN A'],
    ['HEPSTORE_SEPAY_API_KEY', 'Khoá bí mật để SePay gọi vào web', 'abc123...chuoi-ngau-nhien'],
    ['HEPSTORE_SHOP_HOST', 'Tên link khách hàng', 'shop.localhost'],
    ['HEPSTORE_ADMIN_HOST', 'Tên link quản trị', 'quantri.localhost'],
    ['HEPSTORE_TUNNEL_HOSTS', 'Tên miền tunnel (ngrok) cho SePay, xem mục 6', 'abcd-12-34.ngrok-free.app'],
    ['HEPSTORE_ORDER_HOLD_DAYS', 'Số ngày giữ đơn web chưa trả tiền, mặc định 3', '3'],
    ['HEPSTORE_MAX_OPEN_WEB_ORDERS', 'Số đơn web đang mở tối đa mỗi số điện thoại, mặc định 3', '3'],
    ['HEPSTORE_SECRET_KEY', 'Khoá nội bộ của Django, nên đặt chuỗi ngẫu nhiên riêng', 'chuoi-ngau-nhien-dai'],
])
add('p', 'Mã BIN ngân hàng thường dùng: MB Bank là 970422, Vietcombank là 970436. Ngân hàng khác, hãy tra danh sách BIN VietQR và kiểm tra lại cho đúng.')
add('p', 'Ví dụ một đoạn .env (toàn bộ giá trị là giả):')
add('code', 'HEPSTORE_BANK_BIN=970422\nHEPSTORE_BANK_ACCOUNT=0123456789\nHEPSTORE_BANK_OWNER=NGUYEN VAN A\nHEPSTORE_SEPAY_API_KEY=thay-bang-chuoi-ngau-nhien\nHEPSTORE_TUNNEL_HOSTS=abcd-12-34.ngrok-free.app')
add('h2', 'Tạo khoá SePay ngẫu nhiên')
add('code', 'py -c "import secrets; print(secrets.token_urlsafe(32))"')
add('p', 'Chép chuỗi in ra, dán vào HEPSTORE_SEPAY_API_KEY trong .env. Sau này dán đúng chuỗi đó vào SePay (mục 6).')
add('note', 'Lưu ý: TUYỆT ĐỐI không gửi file .env cho ai và không đưa lên GitHub. File này chứa khoá bí mật và thông tin ngân hàng. Nếu lỡ lộ, tạo khoá mới, sửa trong .env và trong SePay.')
add('p', 'Nếu không điền thông tin ngân hàng, web không hiện mã QR (chỉ còn thanh toán khi nhận hàng và tiền mặt tại POS).')

add('h1', '6. Nhận tiền tự động qua SePay')
add('p', 'SePay báo cho web biết khi có tiền vào tài khoản, đơn sẽ tự chuyển sang "Đã thanh toán". Việc liên kết ngân hàng cần chính chủ tài khoản làm vì có OTP.')
add('h2', '6.1 Đăng ký và liên kết ngân hàng')
add('steps', [
    'Vào https://my.sepay.vn và đăng ký tài khoản.',
    'Liên kết tài khoản ngân hàng nhận tiền của tiệm.',
    'Trong cấu hình công ty, phần cấu trúc mã thanh toán, đặt tiền tố HEP (mã đơn của web bắt đầu bằng HEP).',
])
add('h2', '6.2 Mở tunnel bằng ngrok')
add('p', 'SePay cần một địa chỉ công khai để gọi vào máy của bạn. ngrok tạo địa chỉ đó miễn phí.')
add('steps', [
    'Đăng ký và tải ngrok tại https://ngrok.com, làm theo hướng dẫn gắn authtoken của họ.',
    'Chạy web trước (cửa sổ lệnh 1): py start.py',
    'Mở cửa sổ lệnh 2 và gõ lệnh dưới đây.',
    'ngrok in ra dòng Forwarding, dạng https://abcd-12-34.ngrok-free.app. Chép tên miền đó.',
    'Mở .env, thêm dòng HEPSTORE_TUNNEL_HOSTS=abcd-12-34.ngrok-free.app (chỉ tên miền, không có https://).',
    'Dừng web (Ctrl+C) và chạy lại py start.py.',
])
add('code', 'ngrok http 8000')
add('h2', '6.3 Tạo webhook trên SePay')
add('p', 'Vào mục Tích hợp Webhooks, bấm Thêm webhooks, rồi điền từng ô:')
add('table', ['Ô trên SePay', 'Điền'], [
    ['Sự kiện', 'Có tiền vào'],
    ['URL', 'https://abcd-12-34.ngrok-free.app/api/sepay/webhook/ (thay bằng tên miền ngrok của bạn)'],
    ['Kiểu chứng thực', 'API Key, dán đúng giá trị HEPSTORE_SEPAY_API_KEY trong .env'],
    ['Xác thực thanh toán', 'Bật'],
    ['Content type', 'application/json'],
])
add('note', 'Lưu ý: Địa chỉ ngrok bản miễn phí ĐỔI mỗi lần chạy lại ngrok. Mỗi lần đổi, phải sửa HEPSTORE_TUNNEL_HOSTS trong .env, chạy lại start.py và sửa URL webhook trên SePay.')
add('h2', '6.4 Thử bằng 2.000đ qua POS')
add('steps', [
    'Vào link quản trị, mở mục POS.',
    'Thêm một sách mẫu rẻ hoặc sách bất kỳ vào giỏ, chọn thanh toán chuyển khoản, tạo hoá đơn.',
    'Hoá đơn POS không tính phí ship nên số tiền đúng bằng giá sách. Hãy đặt giá sách thử là 2.000đ.',
    'Dùng app ngân hàng quét QR và chuyển 2.000đ, giữ nguyên nội dung chuyển khoản (có mã HEP...).',
    'Sau vài giây, đơn tự chuyển sang "Đã thanh toán" và mục "Tiền vào" hiện khoản mới.',
])
add('h2', '6.5 Thử không cần tiền thật')
add('p', 'Lệnh sau giả lập SePay báo tiền vào. Thay HEP261121A1B2C3D4 bằng mã đơn thật (xem ở trang đơn).')
add('code', PY + ' manage.py sepay_thu HEP261121A1B2C3D4\n' + PY + ' manage.py sepay_thu HEP261121A1B2C3D4 --amount 1000')
add('p', 'Lệnh đầu báo đúng số tiền của đơn (đơn tự thành "Đã thanh toán"). Lệnh sau báo sai số tiền (đơn không đổi, giao dịch ở mục Tiền vào chờ xử lý).')

add('h1', '7. Sử dụng hằng ngày')
add('h2', '7.1 Phân quyền nhân viên')
add('table', ['Vai trò', 'Được làm'], [
    ['Quản lý (chủ tiệm)', 'Mọi thứ: báo cáo, xuất CSV, tạo nhân viên, xác nhận tiền tay, hoàn tiền'],
    ['Bán hàng', 'Tổng quan, đơn hàng, POS, đơn Facebook/Instagram, khách hàng, mục Tiền vào (gắn giao dịch)'],
    ['Kho', 'Tổng quan, sách, tồn kho, nhà cung cấp, phiếu nhập hàng'],
])
add('p', 'Nhân viên mở trang ngoài quyền sẽ thấy thông báo không đủ quyền (mã 403). Xác nhận tiền tay và hoàn tiền chỉ Quản lý làm được, để người bán hàng không tự xác nhận tiền.')
add('h2', '7.2 Thêm nhân viên')
add('steps', [
    'Đăng nhập link quản trị bằng tài khoản Quản lý.',
    'Mở mục "Nhân viên và quyền".',
    'Bấm "Thêm nhân viên", nhập tên đăng nhập, mật khẩu và chọn vai trò.',
])
add('h2', '7.3 Thêm sách')
add('steps', [
    'Mở mục Sách (vai trò Kho hoặc Quản lý), bấm thêm sách.',
    'Điền tên, danh mục, giá bán, số lượng tồn và mã ISBN hoặc SKU (mã vạch).',
    'Tick "Nhận đặt trước khi hết hàng" nếu cho khách đặt khi hết sách.',
    'Điền "Số ngày dự kiến có hàng" (1 đến 90, mặc định 10). Khách sẽ thấy khoảng mấy ngày nữa có hàng.',
    'Lưu.',
])
add('h2', '7.4 POS và quét mã vạch')
add('steps', [
    'Vào mục POS trên link quản trị.',
    'Quét mã vạch bằng máy quét USB (cắm vào là dùng), hoặc bật camera trong Chrome, hoặc gõ tay ISBN/SKU.',
    'Sách vào giỏ. Chỉnh số lượng nếu cần.',
    'Chọn tiền mặt hoặc chuyển khoản rồi tạo hoá đơn.',
])
add('note', 'Lưu ý: 16 sách mẫu có mã HEP-DEMO-xxx, không phải mã vạch thật. Muốn thử quét, sửa mã sách thành mã vạch in trên sách thật.')
add('h2', '7.5 Đơn Facebook và Instagram')
add('steps', [
    'Mở mục đơn Facebook/Instagram (đường dẫn /management/social/new/).',
    'Chọn kênh, khách hàng, sách và số lượng.',
    'Tạo đơn. Đơn nằm chung danh sách đơn và trừ kho như đơn web.',
])
add('h2', '7.6 Nhập hàng')
add('steps', [
    'Kho vào mục Nhà cung cấp và thêm nhà cung cấp (nếu chưa có).',
    'Vào mục Phiếu nhập, tạo phiếu mới. Phiếu ở trạng thái Bản nháp, kho chưa tăng.',
    'Khi hàng về thật, mở phiếu và bấm xác nhận nhập kho. Lúc này tồn kho mới tăng.',
])
add('h2', '7.7 Đơn đặt trước và hàng về')
add('bullets', [
    'Mỗi cuốn sách có hai cài đặt trong trang sửa sách: "Nhận đặt trước khi hết hàng" và "Số ngày dự kiến có hàng" (mặc định 10 ngày).',
    'Sách hết hàng mà có bật đặt trước thì khách thấy nút "Đặt trước" và dòng "Có hàng khoảng N ngày". Lúc thanh toán, khách phải thấy dòng báo đặt trước rồi mới đặt được.',
    'Khách đặt nhiều hơn số còn trong kho: phần còn hàng trừ kho ngay, phần thiếu ghi là "chờ hàng về". Đơn có nhãn "Đặt trước" và ngày dự kiến có hàng.',
    'Khi hàng về (bấm nhập kho ở phiếu nhập, hoặc điều chỉnh tăng tồn kho), hệ thống tự giữ sách cho đơn đặt trước trước: đơn đã trả tiền nhận trước, sau đó theo thứ tự ai đặt trước. Phần còn dư mới bán cho khách khác.',
    'Đơn đặt trước chỉ chuyển sang "Đang đóng gói" khi đã đủ sách. Nếu chưa đủ, hệ thống báo cần nhập hàng trước khi giao.',
    'Huỷ một đơn thì sách đã giữ cho đơn đó tự chuyển sang đơn đặt trước đang chờ tiếp theo.',
])
add('h2', '7.8 Xác nhận tiền tay')
add('p', 'Tiền chuyển khoản bình thường do SePay tự xác nhận. Xác nhận tay chỉ dùng khi cần, và có hai cách:')
add('bullets', [
    'Khách chuyển đúng tiền nhưng ghi sai nội dung: vào mục "Tiền vào (SePay)", tìm giao dịch không khớp, nhập mã đơn để gắn vào đơn. Nhân viên Bán hàng làm được, vì có giao dịch ngân hàng làm bằng chứng. Số tiền phải đúng bằng tổng đơn.',
    'Không có giao dịch SePay (ví dụ thu tiền mặt khi giao COD): mở chi tiết đơn, bấm "Tôi đã đối soát và nhận tiền", bấm thêm lần nữa để chắc chắn. Chỉ Quản lý làm được.',
])
add('h2', '7.9 Huỷ đơn kèm hoàn tiền')
add('steps', [
    'Chuyển tiền trả khách bằng app ngân hàng trước. Hệ thống không tự chuyển tiền.',
    'Mở chi tiết đơn đã thu tiền (chỉ Quản lý thấy phần này). Đơn đang giao hoặc đã hoàn tất thì không huỷ được ở đây.',
    'Ghi vào ô ghi chú đã hoàn tiền thế nào (ví dụ: CK trả lại, mã giao dịch), rồi bấm "Hủy đơn và ghi nhận đã hoàn tiền", bấm thêm lần nữa để chắc chắn.',
    'Đơn chuyển sang "Đã hủy" và "Đã hoàn tiền", sách trả về kho và được giữ cho đơn đặt trước đang chờ (nếu có).',
])
add('p', 'Đơn chưa trả tiền thì huỷ ở trang đơn bình thường và sách cũng trả về kho.')
add('h2', '7.10 Đơn tự huỷ sau N ngày')
add('p', 'Đơn web chưa xác nhận và chưa trả tiền quá HEPSTORE_ORDER_HOLD_DAYS ngày (mặc định 3) sẽ bị huỷ và trả sách về kho. Hệ thống tự làm việc này khi nhân viên mở trang tổng quan. Muốn chạy ngay:')
add('code', PY + ' manage.py huy_don_qua_han')

add('h1', '8. Dành cho người lập trình')
add('table', ['Việc', 'Lệnh hoặc nơi xem'], [
    ['Chạy toàn bộ test', 'python3 manage.py test shop'],
    ['Bỏ test E2E (không cần Chrome)', 'python3 manage.py test shop --exclude-tag e2e'],
    ['Xuất lại sơ đồ ERD', 'python3 docs/gen_erd.py rồi python3 docs/render_erd.py'],
    ['Dựng lại file hướng dẫn này', 'python3 docs/build_huong_dan.py'],
])
add('bullets', [
    'Test E2E dùng Playwright và cần Chrome thật. Cài: pip install playwright. Nếu không có Chrome, bỏ E2E bằng --exclude-tag e2e.',
    'render_erd.py cũng cần Playwright. gen_erd.py đọc shop/models.py và ghi docs/ERD_Hep_Bookstore.md, erd.mmd, .html. render_erd.py xuất .png và .pdf.',
    'Giao diện: xem CLAUDE.md ở thư mục gốc. Thư mục .claude chứa agents (hep-ui-designer, hep-frontend-dev, hep-ui-qa, hep-code-auditor) và skills (hep-redesign, hep-brand-ui, hep-ui-qa-check). Mọi thay đổi giao diện đi qua skill hep-redesign.',
    'Sao lưu: tắt web rồi chép db.sqlite3 sang nơi khác (ổ USB, đám mây) kèm ngày, ví dụ db-2026-11-23.sqlite3. Nên sao lưu mỗi ngày. Khôi phục bằng cách chép đè lại file.',
    'Chế độ runserver chỉ để chạy thử trên máy. Không mở DEBUG ra Internet. Muốn chạy công khai, cần đặt SECRET_KEY riêng, HTTPS và máy chủ WSGI.',
])

add('h1', '9. Sự cố thường gặp')
add('table', ['Hiện tượng', 'Cách xử lý'], [
    ['Cổng 8000 bận', 'Chạy py start.py --port 8001 và mở link với :8001. Hoặc tắt chương trình đang dùng cổng 8000.'],
    ['Link *.localhost không mở', 'Dùng Chrome hoặc Edge. Kiểm tra gõ đúng http:// và có :8000. Đừng dùng trình duyệt cũ.'],
    ['Báo không tìm thấy python hoặc py', 'Cài lại Python và tick Add Python to PATH. Mở cửa sổ lệnh mới rồi thử lại.'],
    ['Lần đầu báo lỗi khi cài', 'Kiểm tra mạng Internet (lần đầu cần tải Django), rồi chạy lại.'],
    ['Quên mật khẩu quản trị', PY + ' manage.py changepassword admin'],
    ['Khách chuyển tiền mà đơn không tự xác nhận',
     '1) ngrok còn chạy không. 2) URL webhook trên SePay đúng tên miền ngrok hiện tại và kết thúc bằng /api/sepay/webhook/. '
     '3) Khoá API trong SePay trùng HEPSTORE_SEPAY_API_KEY. 4) Tên miền ngrok có trong HEPSTORE_TUNNEL_HOSTS. '
     '5) Nội dung chuyển khoản phải có mã đơn HEP... 6) Vào mục Tiền vào trên link quản trị, tìm giao dịch và gắn tay vào đơn.'],
    ['QR không hiện', 'Kiểm tra .env có đủ BANK_BIN, BANK_ACCOUNT, BANK_OWNER, đúng chính tả, rồi chạy lại start.py. Cần Internet để tải ảnh QR.'],
    ['Sửa .env mà không thấy đổi', 'Dừng web (Ctrl+C) và chạy lại py start.py.'],
])

add('h1', '10. Bảng tóm tắt lệnh hay dùng')
add('p', 'Chạy các lệnh trong thư mục dự án. Trên Windows, lệnh manage.py dùng ' + PY + ' (macOS và Linux: python3).')
add('table', ['Việc', 'Lệnh'], [
    ['Chạy web', 'py start.py'],
    ['Chạy cổng khác', 'py start.py --port 8001'],
    ['Dừng web', 'Ctrl+C trong cửa sổ lệnh'],
    ['Đổi mật khẩu admin', PY + ' manage.py changepassword admin'],
    ['Mở tunnel cho SePay', 'ngrok http 8000'],
    ['Sinh khoá SePay ngẫu nhiên', 'py -c "import secrets; print(secrets.token_urlsafe(32))"'],
    ['Giả lập tiền về', PY + ' manage.py sepay_thu <mã đơn> [--amount SỐ_TIỀN]'],
    ['Huỷ đơn quá hạn', PY + ' manage.py huy_don_qua_han'],
    ['Chạy test', PY + ' manage.py test shop --exclude-tag e2e'],
    ['Sao lưu dữ liệu', 'Chép file db.sqlite3 khi web đã tắt'],
])


# ---------- Markdown ----------
def md_table(head, rows):
    esc = lambda s: s.replace('|', '\\|').replace('\n', ' ')
    out = ['| ' + ' | '.join(head) + ' |', '| ' + ' | '.join('---' for _ in head) + ' |']
    out += ['| ' + ' | '.join(esc(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)

def build_md():
    out = ['# ' + TITLE, '', 'Dành cho chủ tiệm (Nga) và người bạn lập trình giúp chạy dự án.', '', '## Mục lục', '']
    out += [f'- {t}' for k, t, *_ in C if k == 'h1']
    out.append('')
    for k, *d in C:
        if k == 'h1': out += ['## ' + d[0], '']
        elif k == 'h2': out += ['### ' + d[0], '']
        elif k == 'p': out += [d[0], '']
        elif k == 'steps': out += [f'{i}. {s}' for i, s in enumerate(d[0], 1)] + ['']
        elif k == 'bullets': out += ['- ' + s for s in d[0]] + ['']
        elif k == 'code': out += ['```', d[0], '```', '']
        elif k == 'note': out += ['> **' + d[0] + '**', '']
        elif k == 'table': out += [md_table(*d), '']
    return '\n'.join(out)


# ---------- Word ----------
def shade(el_pr, fill):
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill)
    el_pr.append(shd)

def font(run, name=None, size=None, bold=None, color=None):
    if name:
        run.font.name = name
        run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
        run._element.rPr.rFonts.set(qn('w:cs'), name)
    if size: run.font.size = Pt(size)
    if bold is not None: run.bold = bold
    if color: run.font.color.rgb = RGBColor.from_string(color)

def para_shade(p, fill, border=None):
    ppr = p._p.get_or_add_pPr()
    shade(ppr, fill)
    if border:
        bd = OxmlElement('w:pBdr')
        for side in ('top', 'left', 'bottom', 'right'):
            e = OxmlElement(f'w:{side}')
            e.set(qn('w:val'), 'single'); e.set(qn('w:sz'), '8'); e.set(qn('w:space'), '4'); e.set(qn('w:color'), border)
            bd.append(e)
        ppr.append(bd)

def build_docx(path):
    doc = Document()
    st = doc.styles['Normal']; st.font.name = 'Calibri'; st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri')
    for lvl, size in ((1, 18), (2, 14)):
        h = doc.styles[f'Heading {lvl}']; h.font.name = 'Calibri'; h.font.size = Pt(size); h.font.color.rgb = RGBColor(0x1F, 0x2A, 0x44)
        h.element.rPr.rFonts.set(qn('w:eastAsia'), 'Calibri'); h.element.rPr.rFonts.set(qn('w:ascii'), 'Calibri'); h.element.rPr.rFonts.set(qn('w:hAnsi'), 'Calibri')
    t = doc.add_heading(TITLE, 0); t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub = doc.add_paragraph('Dành cho chủ tiệm (Nga) và người bạn lập trình giúp chạy dự án.'); sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph().add_run('Mục lục').bold = True
    for k, text, *_ in C:
        if k == 'h1': doc.add_paragraph(text, style='List Bullet')
    doc.add_page_break()
    for k, *d in C:
        if k == 'h1': doc.add_heading(d[0], 1)
        elif k == 'h2': doc.add_heading(d[0], 2)
        elif k == 'p': doc.add_paragraph(d[0])
        elif k == 'steps':
            for i, s in enumerate(d[0], 1):
                q = doc.add_paragraph(f'{i}. {s}')
                q.paragraph_format.left_indent = Pt(24); q.paragraph_format.first_line_indent = Pt(-18)
        elif k == 'bullets':
            for s in d[0]: doc.add_paragraph(s, style='List Bullet')
        elif k == 'code':
            for line in d[0].split('\n'):
                p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(0)
                para_shade(p, 'EDEDED')
                font(p.add_run(line or ' '), 'Consolas', 10.5)
            doc.add_paragraph()
        elif k == 'note':
            p = doc.add_paragraph(); para_shade(p, 'FFF4DC', 'E0A030')
            font(p.add_run(d[0]), bold=True)
        elif k == 'table':
            head, rows = d
            tb = doc.add_table(rows=1, cols=len(head)); tb.style = 'Table Grid'
            for i, h in enumerate(head):
                c = tb.rows[0].cells[i]; c.text = ''
                font(c.paragraphs[0].add_run(h), bold=True); shade(c._tc.get_or_add_tcPr(), 'D9E2F3')
            for r in rows:
                cells = tb.add_row().cells
                for i, v in enumerate(r):
                    cells[i].text = ''
                    run = cells[i].paragraphs[0].add_run(v)
                    if v.startswith(('.venv', 'py ', 'ngrok ', 'python', 'http', 'HEPSTORE_')) or '.venv' in v:
                        font(run, 'Consolas', 10)
            doc.add_paragraph()
    doc.save(path)


if __name__ == '__main__':
    (DOCS / 'HUONG_DAN_CHAY_DU_AN.md').write_text(build_md(), encoding='utf-8')
    build_docx(DOCS / 'HUONG_DAN_CHAY_DU_AN.docx')
    print('Đã dựng xong .md và .docx')
