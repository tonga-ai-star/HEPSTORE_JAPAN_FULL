# Three.js trong Hép Bookstore

Đọc file này trước khi thêm hoặc sửa bất kỳ cảnh 3D nào. Mục tiêu: 3D làm thương hiệu "lồng lộn" hơn nhưng không làm chậm việc mua sách, không vỡ trên máy yếu, và trang vẫn đầy đủ khi 3D không chạy.

## Mục lục
1. Nguồn thư viện
2. Cảnh được phép
3. Luật cứng (hiệu năng, an toàn, truy cập)
4. Khung code bắt buộc
5. Màu và vật liệu
6. Kiểm thử

## 1. Nguồn thư viện
- Dùng bản đã vendor: `static/vendor/three/three.module.min.js` (three r170, MIT, LICENSE cùng thư mục). Không nạp từ CDN: máy của khách chạy không hosting, có thể mất mạng.
- Nạp bằng ES module động, chỉ khi trang có phần tử `[data-three]`:
  `const THREE = await import(window.HEP_THREE_URL)` với `HEP_THREE_URL` đặt trong template bằng `{% static 'vendor/three/three.module.min.js' %}`.
- Không thêm addon (OrbitControls, postprocessing, loader GLTF) trừ khi ghi lý do vào bảng mục 2. Không tải model 3D ngoài: hình học dựng bằng code.
- Mỗi cảnh một file `static/js/three-<tên>.js`, dùng chung `static/js/three-stage.js` (khung mục 4).

## 2. Cảnh được phép

| Cảnh | Trang | Ý tưởng | Lý do có |
| --- | --- | --- | --- |
| `hero-shelf` | Trang chủ, cột phải hero | Chồng 5 đến 7 cuốn sách 3D (hộp bo cạnh, gáy màu navy/cam/be, bìa là texture canvas vẽ tên sách thật lấy từ dữ liệu trang) xoay lệch, lơ lửng nhẹ, nghiêng theo con trỏ, tách ra khi cuộn | Thay chồng bìa phẳng bằng cảm giác cầm sách thật |
| `sakura-drift` | Hero trang chủ, nền mờ phía sau | Cánh hoa anh đào (InstancedMesh, tối đa 120) rơi chậm, gió lệch theo con trỏ | Văn hoá Nhật đúng brief của khách, nhẹ vì instanced |
| `paid-burst` | Trang đơn khi `hep:paid` bắn ra | Mưa sách nhỏ và cánh hoa bung từ vùng "Thanh toán thành công", 1.2 giây rồi tự huỷ canvas | Khoảnh khắc cảm xúc nhất của khách; thay hoặc nâng cấp `celebrate.js` |
| `book-turn` | Trang chi tiết sách, khi rê chuột bìa (desktop) | Bìa xoay 3D để lộ gáy và mặt sau | Tuỳ chọn, chỉ làm nếu còn ngân sách hiệu năng |

Không được: 3D trong trang quản trị, POS, thanh toán (form checkout), trang đăng nhập. Không dùng 3D thay chữ hay nút: mọi thông tin và nút phải là HTML thật.

## 3. Luật cứng
- **Tắt 3D** khi: `prefers-reduced-motion: reduce`, lớp `motion-off` trên `<html>`, `navigator.connection.saveData`, không tạo được WebGL context, hoặc `navigator.hardwareConcurrency <= 2`. Khi tắt, giữ nguyên bố cục CSS/SVG cũ (fallback đã có), không để khung trống.
- **Nạp lười**: chỉ import three khi phần tử `[data-three]` sắp vào khung nhìn (IntersectionObserver, rootMargin 200px) và sau `requestIdleCallback` (dự phòng `setTimeout` 300ms). Không chặn LCP: chữ và nút hero hiện trước, canvas mờ dần vào sau.
- **Ngân sách**: pixel ratio tối đa `Math.min(devicePixelRatio, 1.75)`, dưới 768px tối đa 1.25. Tổng tam giác dưới 60 000 mỗi trang. Texture canvas tối đa 512x768. Một renderer mỗi canvas, tối đa 2 canvas mỗi trang.
- **Dừng khi không thấy**: dừng `setAnimationLoop` khi canvas ra khỏi khung nhìn hoặc `document.hidden`. Không chạy vòng lặp khi không có gì chuyển động.
- **Dọn dẹp**: `pagehide` gọi `renderer.dispose()`, dispose geometry, material, texture. `paid-burst` tự xoá canvas sau khi xong.
- **Không bắt sự kiện**: canvas có `pointer-events:none` và `aria-hidden="true"`. Con trỏ đọc từ `pointermove` trên `window` với `{passive:true}`; không nghe `scroll` (dùng IntersectionObserver hoặc đọc `scrollY` trong vòng lặp render đang chạy).
- **Lỗi không được lan**: mọi lỗi khởi tạo bị bắt, ghi `console.warn('[hep-3d]', ...)` một lần, rồi giữ fallback. Không để lỗi đỏ trong console (E2E bắt `pageerror` và `console.error`).
- **Không dịch chuyển bố cục**: canvas đặt `position:absolute; inset:0` trong khung có kích thước cố định từ CSS (CLS = 0).
- **Bảo mật**: texture chữ vẽ bằng `ctx.fillText` từ `textContent` của phần tử trên trang, không chèn HTML.

## 4. Khung code bắt buộc (`static/js/three-stage.js`)
Một module xuất hàm `mountStage(el, buildScene)`:
1. Kiểm điều kiện tắt ở mục 3; không đạt thì `return null` và để `el.dataset.three = 'off'`.
2. Đợi IntersectionObserver + idle, rồi `await import(HEP_THREE_URL)`.
3. Tạo `WebGLRenderer({antialias:true, alpha:true, powerPreference:'low-power'})`, `outputColorSpace = SRGBColorSpace`, gắn canvas vào `el`.
4. Gọi `buildScene(THREE, {scene, camera, renderer, el})` để lấy `{update(t, pointer), dispose()}`.
5. Quản lý resize bằng ResizeObserver, pointer chuẩn hoá -1..1, play/pause theo visibility, dispose khi `pagehide`.
6. Thành công thì `el.dataset.three = 'on'` để CSS ẩn fallback bằng `opacity` (fallback vẫn trong DOM).

## 5. Màu và vật liệu
- Lấy màu từ token CSS lúc chạy: `getComputedStyle(document.documentElement).getPropertyValue('--navy')`, không viết hex trong JS. Chế độ tối tự đổi theo token.
- Vật liệu `MeshStandardMaterial` roughness 0.6 đến 0.85 (giấy), không kim loại bóng, không phát sáng neon, không bloom.
- Ánh sáng: 1 HemisphereLight (be/navy) + 1 DirectionalLight ấm, bóng đổ tắt (tiết kiệm). Nếu cần bóng, dùng một mặt phẳng với texture bóng mờ vẽ sẵn.
- Cánh hoa anh đào: màu be hồng pha từ `--surface-2` và `--orange` (lerp), không thêm hồng neon ngoài bảng màu.

## 6. Kiểm thử
- `lint_ui.py` kiểm: three chỉ nạp từ `static/vendor/three/`, mọi file `three-*.js` có kiểm reduced-motion, có `dispose`, không có `addEventListener('scroll'`, không nạp three trong template quản trị.
- E2E (`shop/test_e2e.py`) kiểm: trang chủ có canvas khi WebGL có, `data-three="on"`, không lỗi console; với `reduced_motion='reduce'` không có canvas và fallback hiện.
- Đo FPS thô trong E2E: 60 khung hình đầu không quá 1 giây trên Chrome thật (chỉ cảnh báo, không chặn).

## Đợt 1 (2026-11-22)
Đặc tả gốc: `_workspace/05_designer_three_spec.md`. Code: `static/js/three-stage.js` (khung), `three-paint.js` (màu, ánh sáng, cánh hoa; xuất lại qua `three-stage.js`), `three-input.js` (con trỏ), `three-hero-shelf.js`, `three-sakura.js`, `three-paid-burst.js`; partial `templates/shop/_three.html` đặt `HEP_THREE_URL`, chỉ include ở `home.html`, `order_success.html`, `track.html`; CSS ở mục `3D (three.js)` của `static/css/motion.css`.

**Giao ước khung**
- `mountStage(el, buildScene, opts)`, `opts = {lazy, once, maxDpr:[desktop, <768px], onFail}`. `buildScene(THREE, {scene, camera, renderer, el, mobile})` trả `{update(t, dt, input) → boolean, dispose(), onTheme?, resize?(w,h), degrade?, camera?}`; `input = {fine, active, pointer:{x,y,inside}, windowPointer, scrollY}`, pointer -1..1 (y hướng xuống), `inside` là trong khung nới 120px.
- `prepareThree(el)`: kiểm điều kiện, nạp three, thử WebGL rồi trả context; không tạo renderer (dùng cho cảnh chạy một lần).
- Thuộc tính trên khung: `data-three` idle → loading → on (đã vẽ khung đầu) | off (+ `data-three-reason`: reduced-motion, motion-off, save-data, low-cpu, no-webgl, canvas-limit, error, context-lost, slow); riêng burst: ready → on → done. `data-three-running` 1/0, `data-three-tris` (tam giác khung đầu), `data-three-slow="1"` khi đã hạ cấp.
- Ba điều kiện đầu và low-cpu: không tải `three.module.min.js`. Cảnh báo `console.warn('[hep-3d]', ...)` tối đa 1 lần mỗi trang.
- Gác FPS: khung 30 đến 90 trung bình > 34ms thì DPR = 1 và `degrade()`; 60 khung sau vẫn > 50ms thì `off` lý do `slow`. SwiftShader (Chrome headless không GPU) chạy khoảng 120ms/khung ở 1280px nên sẽ chạm gác này sau vài giây; đó là hành vi đúng, E2E kiểm trước lúc đó.
- Vật liệu trong suốt hai mặt (`DoubleSide` + `transparent`) phải đặt `forceSinglePass:true`, nếu không three r170 vẽ hai lượt và số tam giác nhân đôi.

**hero-shelf** (khung `.hero-art`): 7 cuốn (5 dưới 768px), mỗi cuốn vỏ Extrude bo góc 1.00 × 1.42 + ruột Box + mặt bìa Plane texture canvas 384×576 (256×384 mobile); bóng giả Plane 4.2 × 1.4 ở y -1.45. Camera fov 28 ở z 9 (7 mobile; nhóm scale .8, y -.45). Khoảng 520 tam giác.

| Slot | x | y | z | rotX | rotY | rotZ | dày | bìa | chữ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | -1.05 | -0.35 | 0.4 | 0 | 18 | -8 | 0.22 | `--navy` | `--on-navy` |
| 2 | 0.00 | -0.55 | 0.9 | 0 | -6 | 5 | 0.26 | `--orange` | `--on-orange` |
| 3 | 1.05 | -0.20 | 0.3 | 0 | -22 | 12 | 0.20 | `--surface-2` | `--ink` |
| 4 | -1.35 | 0.95 | -0.6 | 0 | 30 | -16 | 0.18 | `--navy-deep` | `--on-navy` |
| 5 | 1.40 | 1.00 | -0.9 | 0 | -35 | 20 | 0.24 | `--orange-ink` | `--on-navy` |
| 6 | -1.55 | -1.05 | -1.4 | 72 | 0 | 8 | 0.20 | `--surface-2` | `--ink` |
| 7 | 1.55 | -1.05 | -0.8 | 80 | 0 | -14 | 0.28 | `--navy` | `--on-navy` |

Vào cảnh: rơi từ y + 1.4, rotZ + 20°, scale .85, 720ms easeOutBack 1.56, thứ tự slot 4, 6, 1, 2, 3, 5, 7 so le 90ms. Lơ lửng chu kỳ 4.2 + 0.37·i giây. Con trỏ fine: nhóm xoay y ≤ 14°, x ≤ 8°, cuốn gần nhất nhấc z + .25 và xoay 8°. Cảm ứng: lắc 6° chu kỳ 9s. Cuộn: tách theo hướng slot 0.9·s, nhóm lên 0.6·s. Bìa có ảnh tải lên thì vẽ ảnh cover-fit đè lên chữ. Tắt: `.hero-stack` (fallback) giữ opacity 1, `hero-fan` chạy như cũ.

**sakura-drift** (khung `.hero-sakura`, con đầu của `section.hero`): 1 InstancedMesh, 120 cánh (72 khi CPU ≤ 4 nhân, 48 dưới 768px), khoảng 10 tam giác mỗi cánh. Camera fov 40 ở z 10. Rơi 0.28 đến 0.6/s, lắc 0.15 đến 0.35, gió `0.08 + 0.45·pointer.x` (cảm ứng 0.08), cuộn mạnh tăng tốc rơi tối đa 1.2/s. Opacity .6. Màu: lerp(be, `--orange`, .15 đến .45), be là `--surface-2` ở chế độ sáng và **`--ink` ở chế độ tối** (lệch mục 5 có chủ đích: `--surface-2` tối làm cánh hoa thành vệt bẩn trên nền navy đêm). Đất của HemisphereLight cũng là màu be đó (đất navy làm cánh hoa xám). Tắt: hero như cũ, không có fallback.

**paid-burst** (khung `.three-burst` fixed toàn màn, chỉ đơn chuyển khoản chưa trả): `prepareThree` lúc rảnh, thành công đặt `<html data-three-burst="ready">`. Khi `hep:paid`: tạo renderer ngay, OrthographicCamera theo CSS px, nổ ở 520ms (lúc con dấu 済 chạm) từ giữa cạnh trên `[data-pay-success]`: 36 sách Box 18×24×5 (20 mobile) và 60 cánh hoa (30 mobile), 1200ms, mờ dần từ 900ms, xong thì gỡ canvas, `data-three="done"`. DPR 1.25 / 1.
- Một kiểu mưa mỗi lần trả tiền: `celebrate.js` chỉ `rain()` khi cờ khác `ready`, và nghe `hep:burst-fallback` (do `three-paid-burst.js` phát khi tạo cảnh lỗi) để mưa sách DOM thay.

**book-turn: không làm.** Trang chi tiết đã có `cover-tilt` và `cover-morph` trên cùng bìa; tải 691 KB three ở trang có nút mua là không xứng; không có dữ liệu gáy và bìa sau thật. Làm khi khách gửi ảnh bìa sau, và chỉ thay `cover-tilt`.
