# Công thức chuyển động Hép Bookstore

Mọi công thức nằm trong `static/js/motion.js` và phần `/* motion */` của `static/css/app.css`. Thuộc tính `data-*` trên HTML bật hiệu ứng, nên template chỉ cần thêm thuộc tính.

## Khung chung (motion.js)
```js
'use strict';
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  document.documentElement.classList.add(reduce ? 'motion-off' : 'motion-on');
  if (reduce) return;
  // mỗi công thức là một hàm nhỏ, gọi ở cuối file
})();
```
CSS chỉ ẩn phần tử chờ hiện khi có lớp `motion-on`, để trang vẫn đọc được nếu JS lỗi:
```css
.motion-on [data-reveal]{opacity:0;transform:translateY(24px)}
.motion-on [data-reveal].is-in{opacity:1;transform:none;transition:opacity .7s var(--ease-out),transform .7s var(--ease-out);transition-delay:calc(var(--i,0)*70ms)}
@media (prefers-reduced-motion: reduce){*,*::before,*::after{animation:none!important;transition:none!important}}
```

## load-stagger
Thêm `data-stagger` lên khối cha. JS gán `--i` cho từng con trực tiếp rồi thêm `is-in` sau một khung hình. Độ trễ 70ms mỗi phần tử, tối đa 8 phần tử.

## reveal-up
`data-reveal` trên phần tử. Một IntersectionObserver duy nhất, `threshold:.15`, `rootMargin:'0px 0px -8% 0px'`, thêm `is-in` rồi `unobserve`. Trong lưới, `--i` lấy theo vị trí trong hàng để thẻ hiện lần lượt.

## cover-tilt
`data-tilt` trên thẻ sách. Trên `pointermove` tính độ lệch so với tâm, đặt biến `--rx` và `--ry` tối đa 8 độ, cập nhật trong `requestAnimationFrame`. CSS: `transform:perspective(900px) rotateX(var(--rx)) rotateY(var(--ry)) translateY(-4px)`. Thêm lớp bóng sáng `::after` dùng `radial-gradient` theo `--mx`, `--my`. Bỏ qua khi `pointerType` là touch. Về 0 khi `pointerleave` với transition 500ms `--ease-spring`.

## magnetic-btn
`data-magnetic` trên nút chính. Kéo nút tối đa 10px theo con trỏ trong bán kính nút, chữ bên trong kéo thêm 4px. Thả về bằng `--ease-spring` 450ms.

## draw-underline
Bọc từ nhấn bằng `<span class="scribble">`. Một SVG đường cong nét cam 6px, `stroke-dasharray` bằng chiều dài đường, animate `stroke-dashoffset` về 0 trong 900ms khi phần tử vào khung nhìn. Đây là SVG đường đơn, không phải minh hoạ.

## bear-blink
Gấu linh vật ở hero. Hai mắt là `<path class="eye">` animate `transform:scaleY(.1)` 120ms, lặp mỗi 4.2s bằng keyframes có khoảng nghỉ dài. Gấu nghiêng đầu 4 độ theo con trỏ khi ở hero. Chỉ một gấu chuyển động trên mỗi trang.

## cart-bump
Sau khi thêm vào giỏ, trang tải lại với thông báo thành công. Nếu có thông báo lớp `success` và số giỏ hàng, chạy keyframes `scale(1)→scale(1.35)→scale(.92)→scale(1)` 600ms trên `.count`.

## marquee
Một dải duy nhất ở trang chủ, chữ Baloo 2 lớn xen chữ Nhật. Nhân đôi nội dung, animate `translateX(-50%)` 28s tuyến tính. Dừng khi hover. Có `aria-hidden="true"` vì là trang trí.

## scroll-progress
Trang chi tiết sách. Ưu tiên CSS:
```css
@supports (animation-timeline: scroll()){
  .read-progress{transform-origin:0 50%;animation:grow linear both;animation-timeline:scroll(root)}
  @keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
}
```
Không hỗ trợ thì ẩn thanh, không dùng sự kiện scroll.

## press
Mọi `.btn`, `button`: `:active{transform:translateY(1px) scale(.98)}`, transition 160ms. Hover nút chính: nền cam đậm lên khoảng 6%, nhích lên 2px.

## Toast và xác nhận nội tuyến (thay alert, confirm)
- Toast: phần tử `role="status"` cố định góc dưới, trượt lên 16px và hiện dần 250ms, tự ẩn sau 3.5s.
- Xác nhận: nút có `data-confirm` lần bấm đầu đổi chữ thành nội dung xác nhận và viền cam trong 4s; bấm lần hai mới gửi. Không mở hộp thoại trình duyệt.

## Đợt 2 (MOTION 10 shop, 6 quản trị)
Bật lớp: script nội tuyến 1 dòng trong `<head>` của `base.html` đặt `motion-on`/`motion-off` trước khi vẽ (hết nháy hero). Sau 2500ms chưa có `motion-ready` (do `motion.js` đặt) thì đổi sang `motion-off`. Các file: `motion.js` (lõi), `motion-shop.js` (giỏ, bìa, kệ), `celebrate.js` (trang đơn, tra cứu), `admin-motion.js` (quản trị); CSS đợt 2 ở `static/css/motion.css`, khối reduced-motion cuối `app.css` vẫn tắt mọi animation và transition.

| Công thức | Thông số | RM | Lý do |
| --- | --- | --- | --- |
| page-transition | `@view-transition{navigation:auto}` trong `no-preference`. Cũ: 180ms `cubic-bezier(.4,0,1,1)` mờ + lên 12px; mới: 420ms `--ease-out` trễ 60ms từ dưới 24px. Header (`site-header`) và thanh bên quản trị (`admin-sidebar`) đứng yên; quản trị chỉ mờ chéo 160ms. | Không khai báo, đổi trang tức thì | Trang mới lật lên như trang sách thay vì chớp trắng |
| cover-morph | Bấm thẻ sách: JS gán `view-transition-name:book-cover` cho `.cover-link` của đúng thẻ đó (xoá ở thẻ khác và ở `.detail-cover` trang hiện tại), trang chi tiết có `.detail-cover{view-transition-name:book-cover}`. Nhóm 520ms `--ease-spring`. `pageshow` xoá tên. | Không gán tên | Nối mạch "cầm cuốn sách lên xem" |
| hero-letter-drop | `data-letter-drop` trên `h1`. JS tách từ `span.ld-w` (nowrap) và ký tự `span.ld-c` (theo cụm chữ, giữ dấu), giữ `<br>`, `.scribble`, SVG; `h1` nhận `aria-label`, span `aria-hidden`. Ký tự: `translateY(-.9em) rotate(--r)` về 0, 560ms `--ease-spring`, opacity 240ms; trễ 120ms + i × min(24ms, 500ms/n), tổng ≤ 1.2s. `--ld-end` làm trễ nét scribble. `h1` ẩn tới khi tách xong (`.ld-ready`). | Không tách, hiện tĩnh | Chữ rơi xuống kệ có lò xo, tinh nghịch như gấu; chỉ 1 tiêu đề |
| bear-gaze | `_bear.html` bọc hai mắt trong `g.bear-eyes` khi `blink`. `pointermove` trên `document` chỉ gắn khi gấu trong khung nhìn (IO); mỗi rAF đặt `--ex` ≤ 2.6, `--ey` ≤ 2 đơn vị viewBox, 180ms `--ease-out`. Con trỏ rời cửa sổ: về 0 trong 600ms `--ease-spring`. Trên `.btn-primary`, `.round-add`: `is-curious`, đầu nghiêng 8 độ. Bỏ qua touch. | Không gắn trình nghe | Linh vật "để ý" tới khách |
| fly-to-cart | `data-fly-cart` trên form thêm giỏ. Bắt `submit`, chặn gửi đôi bằng `dataset.flying`, bản sao bìa `.fly-book` 56×76 bay WAAPI 3 khoá (lên ≥ 90px, `scale(.7) rotate(-14deg)` ở 45%, tới số giỏ `scale(.18)`), 420ms `cubic-bezier(.5,0,.25,1)`; gửi form thật khi xong hoặc chốt cứng 450ms. Đặt `sessionStorage['hep-fly']=1` để trang sau mới nảy số giỏ. | Không chặn submit | Xác nhận bằng mắt "cuốn này đã vào túi", trễ ≤ 450ms |
| shelf-pin | ≥ 1024px trong `@supports (animation-timeline: view())`: `.shelf-pin` cao `100vh + --shelf-shift`, `view-timeline:--shelf`; `.shelf-sticky` sticky top 96px; `.shelf-track` flex trượt `translateX(-shift)` theo `animation-range:contain`. JS chỉ đo `--shelf-shift` bằng ResizeObserver. Thẻ xoay ±1.5 độ, vệt gáy kệ navy. < 1024px: dải cuộn ngang có snap. | Lưới/dải thường | Lướt dọc mà kệ trượt ngang như đi dọc kệ trong tiệm |
| pay-celebrate | Nghe `hep:paid` (không phát lại). 0ms khối bung `scale(.6)` → 1.04 → 1, 620ms lò xo; 180ms con dấu hanko "済" đóng xuống 360ms rồi khối rung 180ms; 200ms dấu tích xoay vào; 250ms mưa 28 cuốn sách (16 trên điện thoại) và 3 gấu mini, lớp phủ `pointer-events:none` xoá ở 3s; 300ms gấu sống nhảy 2 nhịp, híp mắt; 400ms tổng tiền nảy. | Chỉ bỏ `hidden`, con dấu đứng yên ở -8 độ | Chuyển khoản là lúc khách lo nhất; con dấu "đã xong" và mưa sách biến lo thành vui |
| pay-wait-pulse | `.pay-wait-dot::after` vòng 2px cam `scale(1)` .7 → `scale(2.6)` 0, 1400ms lặp. | Chấm đứng yên | Cho khách biết trang vẫn đang nghe ngân hàng |
| hero-fan | Bìa `.s1`, `.s3` cộng `--fan-x/y/r` vào transform; hover hoặc một nhịp lúc mở trang (`is-fan` 1.3s), 600ms lò xo. Trôi theo cuộn bằng thuộc tính `translate` trên `view()` (exit range). | Tĩnh | Chồng sách "thở", hero có chiều sâu |
| rail-stagger | `columnsOf` của dải flex = số ô vừa khung nhìn, ô hiện so le 70ms. Hover ô: `translateY(-6px) rotate(-1.5deg)` 450ms lò xo, chữ Hán `rotate(-8deg) scale(1.08)`. | Tĩnh | Danh mục hiện lần lượt, có phản hồi tay |
| empty-bear-sway | Gấu trong `.empty-state` lắc ±4 độ 2.4s khi vào khung nhìn, chỉ khi trang không có `[data-bear]` khác. | Tĩnh | Trạng thái rỗng bớt lạnh |
| count-up | `.stat-card strong[data-count]`: IO threshold .4, 0 → giá trị 900ms `1-(1-t)^3`, định dạng `vi-VN`, kết thúc ghi lại đúng chữ server; `aria-label` chữ gốc khi chạy. | Không chạy | Mắt dừng ở chỉ số |
| bar-grow (sửa) | Cột 700ms `--ease-spring` trễ `i × 60ms + 120ms`; nhãn hiện sau cột 500ms; cột hôm nay nảy `scaleY(1.06)` 300ms. | Tĩnh | Thấy xu hướng theo thứ tự thời gian |
| txn-fresh | `data-txn-id` trên dòng tiền vào. So với `localStorage['hep-last-txn']`: dòng mới có chấm cam nảy rồi nhấp 3 lần, một toast. Báo trực tiếp: `admin-motion.js` hỏi `payments_latest` mỗi 8s khi tab mở (chỉ khi trang có `data-payments-feed`, tức vai trò được phép), khoản mới thì toast + chấm cam ở mục "Tiền vào"; lỗi mạng bỏ qua im lặng. | Chấm tĩnh, toast vẫn hiện | Nhân viên thấy ngay khoản nào mới về |
| pos-shake | MutationObserver trên `#pos-msg`; mỗi lần hiện hoặc đổi chữ, thông báo và nút tạo hóa đơn rung `translateX` ±6px 360ms. Không sửa `pos.js`. | Không rung | Quét nhanh vẫn nhận ra có lỗi |
| forbidden-shake | Gấu trang không đủ quyền lắc đầu ±8 độ 700ms một lần. | Tĩnh | Báo "không được" nhẹ nhàng |

Ghi chú: nét scribble bỏ `vector-effect:non-scaling-stroke` (nó làm `pathLength` lệch nên nét bị đứt đôi), dùng `stroke-width:3.4` theo viewBox.

## Đợt wa (和): tiệm sách Nhật, 2026-11-22
Đặc tả: `_workspace/10_designer_wa_spec.md`. CSS ở `static/css/wa.css` (trang chủ, thẻ sách, đồ vật dùng chung, keyframes gốc) và `static/css/wa-pages.css` (các trang còn lại); JS ở `static/js/wa.js` (`noren`, `swing`, `stand`, `cartStamp`) và một đoạn `stampCart` trong `motion-shop.js`. Mọi hiệu ứng nằm sau `.motion-on`; khối reduced-motion cuối `app.css` tắt hết, trạng thái tĩnh là trạng thái cuối.

Quy ước tránh đè `transform`: tilt dùng `transform` trên `.cover-wrap`/`.detail-cover`; độ nghiêng tĩnh dùng thuộc tính `rotate`/`translate` riêng; hiệu ứng vào cảnh đặt ở phần tử cha khác (`.cover-slot`, `.scroll-hang`) hoặc con. `.hanko` tĩnh nghiêng bằng `transform:rotate(-8deg)`, ẩn trước khi đóng dấu chỉ dưới `.motion-on ...:not(.is-in)`. Không gắn `data-reveal` lên `.pop` (luật reveal chung đặt `transform:none` xoá độ nghiêng). Lắc khi rê chuột: gắn `data-swing`, `wa.js swing()` thêm/gỡ `is-swing` (tên animation phải nằm trong `SWING_ANIMS`). Khối chứa `.three-burst` (fixed) không được có `filter`: dùng `.washi.washi--flat`.

| Công thức | Thông số | RM | Lý do |
| --- | --- | --- | --- |
| noren-part | Lần đầu vào `/` trong phiên (script đầu trang đặt `wa-noren`): 4 `.noren-drape` `translateX(±38..62vw) rotate(±5..9deg) scaleY(.08)` rồi `opacity:0`, 900ms `cubic-bezier(.7,0,.2,1)`, tấm giữa trễ 200ms, tấm ngoài 260ms (xong ≤ 1160ms). `pointer-events:none`; chạm, phím, lăn chuột thì rút trong 160ms; `wa.js` gỡ rèm ở `animationend` hoặc chốt 1400ms | Không đặt lớp, không có rèm | Khách "vén rèm bước vào tiệm" thay vì mở một trang web |
| valance-sway | Diềm noren lắc quanh thanh treo: `rotate` 0 → 4.2 → -3 → 1.5 → 0deg, 1000ms ease-out, trễ `--n × 60ms`; một nhịp khi rèm vừa rút (trang chủ) hoặc lúc tải (about, lớp `is-swing` sẵn), và khi rê từng tấm | Tĩnh | Vải rèm sống, không phải dãy tab |
| hanko-stamp | `scale(1.9) rotate(-22deg)` opacity 0 → `scale(.9) rotate(-6deg)` (55%) → `scale(1.04) rotate(-9deg)` → `scale(1) rotate(-8deg)`, 380ms `--ease-thud` `both`; trễ theo chỗ (thẻ `--i × 70ms + 420ms`, chi tiết 760ms, footer 200ms, 404 1300ms, tra cứu 300/420/540ms, about `--i × 120ms + 600ms`) | Hiện tĩnh, nghiêng -8deg | Dấu đỏ cam là nhãn trạng thái thật của tiệm Nhật, thay pill bo tròn |
| stamp-thud | Phần tử đỡ dấu `translateY(2px)` ở 40%, 160ms ease-out, chạy đúng lúc dấu chạm (`.cover-slot`, `.stage-easel`, `.cart-row`, `.letter`) | Không | Có lực, như vừa đóng dấu xuống bàn |
| hanko-cart | Submit `form[data-fly-cart]`: `motion-shop.js` thêm `is-stamping` vào `.cover-wrap` (hoặc chính form, ví dụ `.detail-buy`) và ghi `sessionStorage['hep-stamp']=data-book-id`; `.cart-stamp` 入 chạy `hanko-stamp` rút còn 300ms. Không đổi `FLY_MS`, chốt 450ms | Không chạy | Xác nhận "đã lấy cuốn này" ngay trên đai sách |
| cart-stamp | Trang giỏ: `wa.js cartStamp()` đọc rồi xoá `hep-stamp`, tìm `.cart-row[data-book-id]` (`CSS.escape`), sau 350ms thêm `is-stamped`: dấu 入 `hanko-stamp` 380ms và dòng `stamp-thud` trễ 220ms; dấu ở lại | Không đóng dấu | Nối mạch giữa thẻ và giỏ: đúng cuốn vừa thêm được đóng dấu |
| pop-sway | `.pop` `rotate(--pop-r ± 2deg)`, 2.8 đến 3.4s `ease-in-out` `infinite alternate`, lệch pha `--i × -0.7s`; chỉ chạy khi cha `.is-in` | Tĩnh ở `--pop-r` | Thẻ giấy kẹp băng dính đung đưa như vừa có người đi qua |
| pop-flick | Rê chuột vào POP (hoặc thẻ chứa): `--pop-r` → +9 → -5 → +2 → `--pop-r`, 900ms ease-out, một nhịp | Không | Phản hồi tay, POP "bị chạm" |
| sign-drop | Bảng treo, tranh cuộn about: `translateY(-110%) rotate(-6deg)` → 4%/3deg → yên, 820ms `--ease-spring`, so le 90ms (bảng) hoặc 120ms (tranh cuộn) | Tĩnh | Đồ vật treo từ trần rơi xuống đúng dây |
| sign-swing | Thuộc tính `rotate` quanh móc: 0 → 7 → -5 → 2.5 → 0deg, 1200ms ease-out khi rê (`data-swing`); màn cảm ứng chạy một lần sau `sign-drop`. Đặt trên phần tử con (`.sign>a`, `.scroll-panel`) để không khởi động lại `sign-drop` của cha | Không | Bảng gỗ lắc khi khách lướt tay qua |
| wave-drift | Dải seigaiha `::before` `translateX(0 → -96px)` (2 ô mẫu 48px, mobile 72px), 9s linear vô hạn; `paused` tới khi `.wa-wave.is-in` | Tĩnh | Sóng ở cửa tiệm và chân trang, nối các section |
| kanji-drift | Chữ dọc lớn trôi lệch tốc độ bằng `animation-timeline:view()` trong `@supports`: hero 本 `0 → -140px` (exit), thư 店主より `30 → -60px`, chân trang và 本棚 `40 → -40px`, about `0 → -60px`, kanji 書 trên washi chi tiết `30 → -90px` | Tĩnh | Parallax bằng CSS, không nghe cuộn |
| spine-shelve | Gáy sách xếp lên kệ từ phải: `translateX(48px) rotate(6deg)` opacity 0 → yên, `transform-origin:50% 100%`, 520ms `--ease-spring`, so le 55ms; dấu trên gáy đóng sau 380ms | Hiện tĩnh | Kệ gáy sách là đồ vật đặc trưng nhất của tiệm Nhật |
| stand-flip | Rê chuột hoặc Tab lên gáy (trễ 90ms), hoặc vuốt kệ trên màn cảm ứng sau khi đã chạm: giá trưng bày quay `rotateY(0 → -90deg)` 170ms, thay bìa từ `<template class="spine-face">`, quay về `90 → 0deg` 420ms `--ease-out`; gáy đang chọn `translateY(-12px)`, gáy hover `-36px rotate(-2deg)`, hai gáy bên dạt 6px | Đổi bìa không lật | Rút sách khỏi kệ để xem mặt bìa |
| bear-peek | Gấu sau ván kệ `translateY(78% → 14%)`, 640ms `--ease-spring`, trễ 900ms sau `.is-in`, một lần, không chớp, không nhìn theo (kệ trang chủ, kệ cùng chủ đề, 404) | Đứng ở 14% | Gấu "ló đầu" mà không phá luật một gấu chuyển động mỗi trang |
| shelf-settle | Thẻ sách (lưới thường): `.cover-slot` `translateY(-18px) rotate(-2.5deg)` → yên, 560ms `--ease-spring`, trễ `--i × 70ms`; `.book-details` mờ vào 300ms trễ +200ms | Tĩnh | Sách được đặt lên ván kệ, thay reveal-up chung |
| book-lay-down | Bàn bày trang chủ: `.cover-slot` `translateY(-40px) rotate(-8deg)` → yên, 640ms `--ease-spring`, so le 80ms | Tĩnh | Sách được đặt nằm xuống bàn |
| cover-lay | Bàn bày: `.cover-wrap` nằm `rotateX(--lay:22deg)`; hover/focus `--lay:0`, `--lift:-14px`, bóng co `scale(.86)`, 420ms `--ease-spring` | `--lay:0` | Cầm sách từ bàn lên xem |
| obi-slip | Hover bìa: `.obi` `translateY(6px) rotate(-1.2deg)`, 380ms `--ease-spring` | Không | Đai lỏng trượt khi cầm sách |
| obi-wrap | Chi tiết: `.detail-obi` (nằm trong `.detail-cover`, bay cùng View Transition) `translateX(-28px) scaleX(.6)` opacity 0 → yên, `transform-origin:0 50%`, 520ms `--ease-out`, trễ 380ms khi `.detail-stage.is-in` | Tĩnh | Đai được quấn vào sách trước mắt khách |
| obi-scroll-slip | Chi tiết, trong `@supports (animation-timeline: scroll())`: `.detail-obi` thuộc tính `translate:0 0 → 0 10px` theo `scroll(root)` `animation-range:0 600px` | Tĩnh | Đai tuột dần khi đọc xuống |
| okuzuke-rule | Hộp 奥付 viền kép: vạch dưới mỗi `dt`/`dd` (`::after`) `scaleX(0 → 1)` `transform-origin:0`, transition 420ms `--ease-out`, trễ dòng `--r × 70ms` khi `dl[data-reveal].is-in` | Hiện vạch | Trang thông tin cuối sách Nhật kẻ từng dòng |
| letter-unfold | Thư washi trang chủ: `perspective(1200px) rotateX(-24deg) translateY(28px)` → yên, 760ms `--ease-out`; biến thể `story-unfold` ở chi tiết `-14deg`, `20px`, 640ms | Tĩnh | Lá thư được mở ra |
| tape-press | Băng dính trên thư: `scale(1.4)` opacity 0 → yên, 300ms `--ease-thud`, trễ 520/600ms | Tĩnh | Giấy được dán xuống |
| photo-drop | Ảnh polaroid (hình vẽ mặt tiền tiệm): `translateY(-30px) rotate(8deg)` → yên, 700ms `--ease-spring`, trễ 300ms | Tĩnh | Ảnh được thả lên bàn cạnh thư |
| slip-in | Dòng giỏ: `translateX(-16px)` opacity 0 → yên, 420ms `--ease-out`, `--i × 60ms` | Tĩnh | Dòng được ghi vào sổ |
| receipt-print | Hoá đơn giỏ (`.receipt[data-reveal]` trong `.receipt-slot` có khe navy, `overflow:clip`): `translateY(-42%)` → yên, 680ms `cubic-bezier(.3,.7,.2,1)`; `.total-row` mờ vào so le 80ms từ 240ms. Checkout dùng cùng hoá đơn nhưng không `data-reveal` nên tĩnh | Tĩnh | Giấy chạy ra từ khe máy in |
| ticket-tear | Mã đơn thành công là vé số thứ tự (lỗ đục mép trái bằng mask): `translateY(-14px) rotate(-4deg)` opacity 0 → yên (tĩnh `rotate:-1deg`), 520ms `--ease-spring`, trễ 600ms | Tĩnh | Khách "nhận vé" sau khi đặt |
| book-tip | 404: cuốn `.lost-fall` đổ quanh góc dưới phải `rotate(0 → 90deg)`, nảy 82deg rồi nằm 90deg, 900ms, trễ 500ms | Nằm sẵn 90deg | "Kệ này trống trơn", một cuốn đổ xuống |
| filter-sway | Phiếu lọc washi `/sach/`: thuộc tính `rotate` -1.4 ↔ -.2deg, 4s `ease-in-out` vô hạn alternate | Tĩnh -.8deg | Giấy kẹp nhẹ trên quầy |

### Chỗ lệch luật có chủ đích (người điều phối đã duyệt 2026-11-22)
1. **"Chỉ một gấu chuyển động mỗi trang" (bear-blink):** gấu ló đầu sau kệ chỉ có MỘT chuyển động vào cảnh (`bear-peek`, trồi lên rồi đứng yên), không chớp mắt, không nhìn theo con trỏ, không lặp. Gấu "sống" (`data-bear`) vẫn chỉ có 1 ở hero trang chủ.
2. **Luật mục 5 "lưới sách lệch nhịp":** `/sach/` dùng hàng kệ thẳng vì sách đứng trên một tấm ván phải thẳng hàng; lệch nhịp chuyển sang bàn bày (hiradai) ở trang chủ. Mục 6b (cấm lặp khuôn) mới hơn và được ưu tiên.
3. **`shelf-pin` bị thay bằng kệ gáy sách:** template không còn `[data-shelf-pin]`; `shelfPin()` trong `motion-shop.js` và CSS `.shelf-*` trong `motion.css` vẫn giữ (tự thoát, vô hại) vì JS còn nhắc tới các class này.
