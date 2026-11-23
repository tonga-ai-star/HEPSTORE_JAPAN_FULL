---
name: hep-brand-ui
description: Luật nhận diện thương hiệu và giao diện của Hép Bookstore - bảng màu theo logo (be, navy, cam), chữ, bố cục, bộ hiệu ứng chuyển động và các dấu hiệu "giao diện AI" phải tránh. Dùng mỗi khi thiết kế, sửa CSS, template hay JS giao diện của shop hoặc trang quản trị Hép, kể cả khi chỉ đổi màu một nút. Không dùng cho logic Django, thanh toán, kho.
---

# Hép Bookstore - luật giao diện

## 1. Đọc bối cảnh
**Design read:** tiệm sách Việt - Nhật nhỏ, khách là người trẻ yêu văn hoá Nhật, ngôn ngữ thị giác ấm, tinh nghịch, thủ công, có chú gấu nét vẽ tay làm linh vật.

| Khu vực | VARIANCE | MOTION | DENSITY | Lý do |
| --- | --- | --- | --- | --- |
| Shop (khách) | 8 | 10 | 4 | Khách yêu cầu hiệu ứng "lồng lộn"; trang bán lẻ cảm xúc, chuyển động là cá tính thương hiệu |
| Quản trị, POS | 5 | 6 | 7 | Nhân viên thao tác nhanh; hiệu ứng phản hồi thao tác, số liệu chạy, báo tiền về nổi bật |

Hai khu vực dùng chung token và chữ, khác nhau ở mật độ và cường độ chuyển động.

## 2. Màu (bắt buộc, lấy từ logo)
Logo: nền be, gấu vẽ nét navy, chữ "hép bookstore" màu cam. Bảng màu be + cam bình thường bị coi là mặc định của AI, nhưng ở đây là màu thương hiệu thật nên được dùng. Không thêm màu nhấn thứ ba, không dùng tím, xanh lá, gradient tím xanh.

Tên token cố định (script QA đọc đúng các tên này):

```css
:root{
  --bg:#f4ece0;        /* be sáng, nền trang */
  --surface:#fbf6ee;   /* thẻ, ô nhập */
  --surface-2:#e8dcc9; /* be của nền logo, khối nhấn */
  --line:#d9c9b2;
  --ink:#1f2547;       /* chữ chính, navy rất đậm */
  --ink-soft:#4f5679;  /* chữ phụ */
  --navy:#2c3a7e;      /* nét gấu, liên kết, nút phụ */
  --navy-deep:#1b2452;
  --orange:#ec8a3d;    /* màu nhấn duy nhất, nền nút chính */
  --orange-ink:#a8501a;/* cam dùng làm CHỮ trên nền sáng */
  --on-orange:#1f2547; /* chữ trên nền cam */
  --on-navy:#f4ece0;   /* chữ trên nền navy */
  --shadow: 0 14px 40px -18px rgb(44 58 126 / .35); /* bóng nhuốm navy, không đen */
  --radius-s:8px; --radius-m:14px; --radius-l:24px; --radius-pill:999px;
  --ease-out:cubic-bezier(.16,1,.3,1); --ease-spring:cubic-bezier(.34,1.56,.64,1);
}
```

Quy tắc:
- Cam `--orange` chỉ làm nền (nút chính, huy hiệu, vệt gạch chân). Cam làm chữ trên nền sáng phải dùng `--orange-ink`, vì cam sáng trên be chỉ đạt khoảng 2.3:1.
- Chữ trên nền cam dùng `--on-orange` (navy), không dùng trắng: trắng trên cam không đạt 4.5:1.
- Được tinh chỉnh giá trị tối đa khoảng 6% độ sáng để đạt tương phản, không đổi sắc độ.
- Chế độ tối: khai báo lại cùng tên token dưới `@media (prefers-color-scheme: dark)` với `:root:not([data-theme="light"])` và dưới `:root[data-theme="dark"]`. Nền tối là navy đêm (`#141936`), không phải đen. Cam giữ nguyên làm nhấn.
- Mọi màu trong CSS phải gọi `var(--...)`. Mã hex chỉ xuất hiện trong các khối token.

## 3. Chữ
- Tiêu đề: **Baloo 2** (600, 700). Tròn, mập, hợp nét gấu vẽ tay, có đủ dấu tiếng Việt.
- Thân bài và giao diện: **Be Vietnam Pro** (400, 500, 600). Không dùng Inter, không dùng serif.
- Tiếng Nhật: **Zen Maru Gothic** (500, 700), chỉ cho tên sách tiếng Nhật và chữ trang trí.
- Chữ viết tay cho thẻ POP: **Patrick Hand** (400), token `--font-hand`. Có subset `vietnamese` đủ dấu. Giới hạn cứng: chỉ dùng trong selector chứa `.pop` hoặc `.hand`; cỡ tối thiểu 16px; không dùng cho nút, giá, form, tiêu đề h1/h2; tối đa 6 thẻ `.pop` mỗi trang; không đặt POP ở checkout.
- Số tiền, mã đơn, ISBN: `font-variant-numeric: tabular-nums`.
- Tiêu đề lớn: `letter-spacing:-0.02em`, `line-height:1.05`, `text-wrap:balance`. Đoạn văn tối đa `65ch`, `text-wrap:pretty`.
- Nạp một lần trong `templates/base.html`:
  `https://fonts.googleapis.com/css2?family=Baloo+2:wght@600;700&family=Be+Vietnam+Pro:wght@400;500;600&family=Zen+Maru+Gothic:wght@500;700&family=Patrick+Hand&display=swap`

## 4. Hình dạng và bề mặt
- Bo góc theo luật: nút và huy hiệu bo tròn hẳn (`--radius-pill`), thẻ sách `--radius-m`, khối lớn `--radius-l`, ô nhập `--radius-s`. Không trộn khác luật này.
- Nét viền "vẽ tay": viền 2px màu `--navy` cho khối nhấn, gợi nét gấu trong logo. Dùng có chủ đích, không bao mọi thẻ.
- Lớp hạt giấy (grain) cố định toàn trang, `pointer-events:none`, độ mờ 0.05 đến 0.08, làm bằng SVG `feTurbulence` trong data URI.
- Bóng chỉ dùng `--shadow`. Không dùng bóng đen.
- Thang z-index: header 40, drawer 60, toast 70, grain 80. Không dùng 9999.

## 5. Bố cục
**Shop**
- Hero tách đôi lệch: chữ bên trái chiếm khoảng 7/12, bên phải là chồng bìa sách xoay lệch nhau kèm gấu linh vật. Tiêu đề tối đa 2 dòng, mô tả tối đa 20 từ, 1 nút chính + 1 liên kết chữ.
- Danh mục: dải cuộn ngang có snap, không làm 3 hoặc 5 ô đều nhau.
- Lưới sách: lưới lệch nhịp (cột lẻ đẩy xuống `margin-top`), dưới 768px thành 2 cột đều.
- Tối đa 1 dải chữ chạy (marquee) toàn trang.
- Eyebrow (nhãn chữ hoa nhỏ trên tiêu đề): tối đa 1 trên mỗi 3 section.
- Không đặt section nền tối giữa trang sáng. Khối nhấn dùng `--surface-2` hoặc `--navy` có chủ đích trải hết chiều ngang, tối đa 1 lần.

**Quản trị**
- Giữ thanh bên nhưng thu gọn được, mục đang mở có nền `--surface-2` và vạch cam bên trái.
- Ký tự hình học (▦ ▤ ✳ ♙ ⚙) thay bằng icon Phosphor qua CDN `https://unpkg.com/@phosphor-icons/web@2.1.1`, một độ dày duy nhất (regular).
- Thẻ số liệu: số to dùng Baloo 2 và tabular-nums; không dùng thanh tiến độ có rãnh nền.
- Bảng: chỉ viền dưới giữa các dòng, dòng hover nền `--surface-2`.

## 6. Chuyển động
Chi tiết công thức và đoạn code mẫu ở `references/motion-recipes.md`. Danh sách được phép:

| Công thức | Dùng ở | Lý do có |
| --- | --- | --- |
| `load-stagger` | Hero, tiêu đề trang | Dẫn mắt theo thứ tự đọc |
| `reveal-up` | Section, thẻ sách khi cuộn tới | Báo nội dung mới xuất hiện |
| `cover-tilt` | Thẻ sách (shop) | Phản hồi con trỏ, cảm giác cầm sách |
| `magnetic-btn` | Nút chính shop | Mời bấm |
| `draw-underline` | Từ nhấn trong tiêu đề | Gợi nét vẽ tay của logo |
| `bear-blink` | Gấu linh vật | Cá tính thương hiệu, 1 chỗ duy nhất |
| `cart-bump` | Số đếm giỏ hàng | Xác nhận đã thêm vào giỏ |
| `marquee` | 1 dải chữ chạy ở trang chủ | Tạo nhịp, tối đa 1 |
| `scroll-progress` | Thanh mảnh trên header trang chi tiết | Cho biết vị trí đọc |
| `press` | Mọi nút | Phản hồi bấm |

Ngoài bảng trên, được thêm công thức mới nếu ghi vào `references/motion-recipes.md` kèm lý do. Hướng "lồng lộn" hợp thương hiệu: chuyển trang bằng View Transitions, chữ tiêu đề rơi từng chữ có lò xo, kệ sách cuộn ngang ghim theo cuộn (CSS scroll-timeline), sách bay vào giỏ, mắt gấu nhìn theo con trỏ, ăn mừng thanh toán thành công bằng mưa sách và gấu nhỏ, số liệu quản trị chạy lên, báo tiền về trong quản trị.
Không được: con trỏ chuột tuỳ biến, hiệu ứng làm chậm thao tác mua (nút phải bấm được ngay), hiệu ứng che nội dung quá 1.2 giây.

**3D (three.js):** chỉ ở shop, chỉ các cảnh trong `references/threejs-recipes.md` (sách 3D ở hero, cánh hoa anh đào, mưa sách khi thanh toán xong, xoay bìa). Dùng bản vendor `static/vendor/three/`, nạp lười, tự tắt khi giảm chuyển động hoặc máy yếu và giữ fallback CSS. Đọc file đó trước khi viết bất kỳ dòng three.js nào.

Luật cứng:
- Chỉ animate `transform` và `opacity`.
- Không dùng `window.addEventListener('scroll')`. Dùng IntersectionObserver hoặc CSS `animation-timeline: view()` có kiểm `@supports`.
- Mọi hiệu ứng tắt hẳn dưới `@media (prefers-reduced-motion: reduce)` và JS kiểm `matchMedia('(prefers-reduced-motion: reduce)')`.
- Không con trỏ chuột tuỳ biến, không phát sáng neon, không chữ gradient.
- Trang quản trị: `press`, `reveal-up` nhẹ, số chạy, cột biểu đồ mọc lên, toast báo tiền về; không dùng tilt, magnetic, marquee.

## 6b. Chất "tiệm sách Nhật" và dấu hiệu AI phải gỡ (phản hồi 2026-11-22)
Người dùng xem bản có 3D vẫn chê "AI quá, ít hiệu ứng quá". Nguyên nhân: mọi section cùng một khuôn (tiêu đề trái, liên kết phải, lưới thẻ bo góc trên nền be), chất Nhật chỉ là vài chữ kanji, hiệu ứng dồn ở hero còn phần dưới đứng yên. Từ nay:

**Cấm lặp khuôn:** không quá 1 section trên mỗi trang dùng khuôn "tiêu đề + liên kết phải + lưới thẻ đều". Thẻ bo góc nền `--surface` không được là thành phần mặc định; mỗi section phải có một ý tưởng bố cục riêng lấy từ bảng dưới.

**Từ vựng thị giác của tiệm sách Nhật (dùng thật, không trang trí suông):**
| Thành phần | Ý nghĩa thật | Dùng ở |
| --- | --- | --- |
| Kệ gáy sách (背表紙) | Sách xếp đứng, chỉ thấy gáy có tên dọc; rê chuột thì cuốn sách trượt ra, nghiêng lộ bìa | Kệ sách trang chủ, sách cùng chủ đề |
| Đai sách obi (帯) | Dải giấy quấn 1/3 dưới bìa ghi lời giới thiệu, giá | Thẻ sách, trang chi tiết |
| Thẻ POP viết tay (手書きPOP) | Mẩu giấy nhân viên tiệm viết tay giới thiệu sách, dán lệch, có băng dính | Sách nổi bật, trang chi tiết |
| Con dấu hanko (判子) | Dấu đỏ cam tròn hoặc vuông: 新 (mới), 人気 (bán chạy), 予約 (đặt trước), 済 (đã trả) | Nhãn trạng thái, thay pill |
| Rèm noren (暖簾) | Rèm vải trước cửa tiệm, xẻ dọc | Mở trang lần đầu, header trang chủ |
| Chữ dọc tategaki | `writing-mode: vertical-rl` | Nhãn section, tên tiếng Nhật |
| Hoa văn truyền thống | seigaiha (sóng), asanoha (lá gai), kẻ sọc noren; vẽ SVG một màu, độ mờ thấp | Nền khối nhấn, đường chia section |
| Số thứ tự kanji | 一 二 三 thay 01 02 03 | Đánh số section, bước thanh toán |
| Giấy washi, mép xé | Mép giấy không thẳng, sợi giấy | Khối thông tin, đường chia |

Chỉ ba màu thương hiệu: dấu hanko dùng `--orange`/`--orange-ink`, không thêm đỏ.

**Chỗ lệch luật có chủ đích (đợt wa, đã duyệt 2026-11-22):**
- Gấu ló đầu sau kệ (`bear-peek`) không tính là gấu chuyển động thứ hai: chỉ trồi lên một lần rồi đứng yên, không chớp, không nhìn theo, không lặp. Gấu sống `data-bear` vẫn tối đa 1 mỗi trang.
- `/sach/` dùng hàng kệ thẳng (sách đứng trên ván phải thẳng); lệch nhịp mục 5 chỉ còn ở bàn bày trang chủ. Mục 6b được ưu tiên hơn mục 5.
- Kệ ghim cuộn ngang (`shelf-pin`) bị thay bằng kệ gáy sách; code `shelfPin()` giữ lại và tự thoát.
Công thức chi tiết: `references/motion-recipes.md`, bảng "Đợt wa".

**Mật độ hiệu ứng:** mỗi màn hình cuộn (khoảng 800px) của trang shop phải có ít nhất 2 chuyển động nhìn thấy được khi cuộn tới hoặc khi rê chuột, không riêng hero. Ưu tiên hiệu ứng gắn với đồ vật thật: sách trượt khỏi kệ, lật bìa, dấu đóng xuống có rung, rèm rẽ ra, giấy POP đung đưa, sóng seigaiha trôi, kanji lớn trôi lệch tốc độ (parallax bằng CSS scroll-timeline), gấu ló đầu sau kệ. Vẫn giữ luật cứng mục 6 (transform/opacity, reduced-motion, không chặn thao tác mua).

## 7. Nội dung và trạng thái
- Không dùng ký tự gạch ngang dài (U+2014) và gạch ngang vừa (U+2013) ở bất kỳ chữ hiển thị nào. Dùng dấu chấm, dấu phẩy hoặc gạch nối thường.
- Dấu chấm giữa (·) tối đa 1 lần mỗi dòng.
- Không dùng `alert()`, `confirm()`, `prompt()`. Thay bằng thông báo nội tuyến hoặc hộp xác nhận nội tuyến.
- Mỗi danh sách có trạng thái rỗng được thiết kế, có gấu và một câu hướng dẫn.
- Thông báo lỗi nói thẳng việc cần làm, không "Oops", không dấu chấm than.
- Tên thương hiệu hiển thị: "Hép Bookstore". Chữ "Hép Store" cũ phải đổi hết.
- Có liên kết "Bỏ qua tới nội dung" và vòng focus rõ (`outline:3px solid var(--orange)`, `outline-offset:3px`).

## 8. Logo
Chưa có file logo gốc trong repo. Dùng tạm `static/img/brand/hep-bear.svg`: mặt gấu nét navy 2.5px, đơn giản (hai tai, hai mắt cong, mũi, miệng), và chữ "hép bookstore" dựng bằng Baloo 2 màu `--orange-ink`. Ghi chú trong changelog rằng cần thay bằng logo thật khi khách gửi. Favicon dùng cùng mặt gấu.

## 9. Kiểm tra trước khi bàn giao
- [ ] Chỉ có be, navy, cam và các sắc độ của chúng.
- [ ] Tương phản đạt 4.5:1 cho chữ thường ở cả hai chế độ sáng tối (script QA đo).
- [ ] Không còn "Hép Store", không gạch ngang dài, không `alert(`.
- [ ] Mọi hiệu ứng có lý do trong bảng mục 6 và tắt dưới reduced-motion.
- [ ] Bố cục dưới 768px không cuộn ngang.
- [ ] `python3 manage.py test shop` xanh.
