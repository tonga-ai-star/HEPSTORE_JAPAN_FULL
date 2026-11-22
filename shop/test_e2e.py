"""End-to-end flows in a real browser against Django's live test server.

Run: python3 manage.py test shop.test_e2e   (skipped when Playwright is not installed)
Screenshots go to _workspace/e2e/.
"""
import base64
import os
import re
import unittest
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import override_settings, tag

from .models import Order, StaffProfile
from .payments import record_sepay

try:
    from playwright.sync_api import sync_playwright
except ImportError:  # pragma: no cover
    sync_playwright = None

# Playwright's sync API runs an event loop in this thread; Django refuses ORM calls there otherwise.
os.environ.setdefault('DJANGO_ALLOW_ASYNC_UNSAFE', 'true')
SHOTS = Path(__file__).resolve().parent.parent / '_workspace' / 'e2e'
PASSWORD = 'E2e-Staff-Pass-2026'
CHROME_ARGS = ['--headless=new', '--enable-unsafe-swiftshader', '--use-angle=swiftshader']
# Makes every WebGL getContext call fail, to exercise the CSS/DOM fallbacks of the 3D scenes.
NO_WEBGL = ("(() => { const orig = HTMLCanvasElement.prototype.getContext;"
            " HTMLCanvasElement.prototype.getContext = function (type, ...rest) {"
            " return /webgl/.test(type) ? null : orig.call(this, type, ...rest); }; })()")
# Hosts outside the app (web fonts, icon font, VietQR images). No test needs their real bytes, and loading them
# made runs flaky (net::ERR_NETWORK_CHANGED), so every context answers them locally with an empty stub.
EXTERNAL = re.compile(r'^https?://(fonts\.googleapis\.com|fonts\.gstatic\.com|unpkg\.com|img\.vietqr\.io)/')
PNG_1PX = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')


def stub_external(route):
    url = route.request.url
    if 'img.vietqr.io' in url:
        route.fulfill(status=200, content_type='image/png', body=PNG_1PX)
    elif route.request.resource_type == 'stylesheet' or url.endswith('.css'):
        route.fulfill(status=200, content_type='text/css', body='')
    else:
        route.fulfill(status=200, content_type='application/octet-stream', body=b'')


OPACITY = "getComputedStyle(document.querySelector('.hero-stack')).opacity"


@tag('e2e')
@unittest.skipIf(sync_playwright is None, 'Playwright chưa cài')
@override_settings(BANK_BIN='970436', BANK_ACCOUNT='0011002233445', BANK_OWNER='NGUYEN VAN MAU', SEPAY_API_KEY='e2e-key')
class BrowserFlows(StaticLiveServerTestCase):
    # Chrome's own notices, not page errors: headless often skips cross-document view transitions,
    # and the 403 test loads a forbidden page on purpose.
    # External hosts are stubbed (EXTERNAL), but a stray network notice about them is not a page error either.
    BENIGN = ('Transition was skipped', 'status of 403', 'fonts.googleapis.com', 'fonts.gstatic.com', 'unpkg.com',
              'img.vietqr.io')

    def setUp(self):
        SHOTS.mkdir(parents=True, exist_ok=True)
        # One Playwright instance per test: a class-wide instance stalls once the live server thread
        # and the sync event loop interleave across tests.
        self.pw = sync_playwright().start()
        # Prefer installed Google Chrome: Playwright's bundled headless-shell cannot render cross-document
        # View Transitions and freezes the next page (real Chrome 147 is fine, verified 2026-11-21).
        try:
            # SwiftShader gives headless Chrome a software WebGL without a GPU (needed from Chrome 137 on).
            self.browser = self.pw.chromium.launch(channel='chrome', args=CHROME_ARGS)
            self.strip_vt = False
        except Exception:
            self.browser = self.pw.chromium.launch()
            self.strip_vt = True
        call_command('seed_demo', verbosity=0)
        User = get_user_model()
        for name, role in (('banhang', 'sales'), ('kho', 'warehouse')):
            u = User.objects.create_user(name, password=PASSWORD, is_staff=True)
            StaffProfile.objects.create(user=u, role=role)
        self.errors, self.dialogs, self.warns, self.three_requests = [], [], [], []
        self.ctx = None
        self.use_context()

    def use_context(self, init_script=None, **options):
        """Open a fresh browser context (closing the previous one) with the shared error listeners."""
        if self.ctx:
            self.ctx.close()
        options.setdefault('viewport', {'width': 1280, 'height': 860})
        self.ctx = self.browser.new_context(**options)
        self.ctx.route(EXTERNAL, stub_external)
        if init_script:
            self.ctx.add_init_script(init_script)
        self.page = self.ctx.new_page()
        if self.strip_vt:
            self.page.route('**/motion.css', lambda r: r.fulfill(status=200, content_type='text/css',
                            body=r.fetch().text().replace('@view-transition{navigation:auto}', '')))
        # Chrome itself rejects the cross-document view transition when a click lands mid-transition
        # ("Transition was skipped"); the site has no JS of its own on that promise, so it is not a page bug.
        self.page.on('pageerror', lambda e: 'Transition was skipped' not in str(e) and self.errors.append(str(e)))
        self.page.on('console', self._on_console)
        self.page.on('dialog', lambda d: (self.dialogs.append(d.message), d.dismiss()))
        self.page.on('request', lambda r: ('vendor/three/' in r.url or '/js/three-' in r.url)
                     and self.three_requests.append(r.url))
        return self.page

    def _on_console(self, m):
        if m.type == 'warning' and '[hep-3d]' in m.text:
            self.warns.append(m.text)
        elif m.type == 'error' and EXTERNAL.match((m.location or {}).get('url') or ''):
            return  # resource notice from a stubbed external host (Chrome puts the URL in location, not text)
        elif m.type == 'error' and not any(b in m.text for b in self.BENIGN):
            self.errors.append(m.text)

    def need_webgl(self):
        if self.strip_vt:
            self.skipTest('headless-shell không có WebGL ổn định')

    def tearDown(self):
        if self.ctx:
            self.ctx.close()
        self.browser.close(); self.pw.stop()
        self.assertEqual(self.errors, [], 'Lỗi JS trong trình duyệt')
        self.assertEqual(self.dialogs, [], 'Có hộp thoại alert/confirm bật lên')

    def url(self, path):
        return self.live_server_url + path

    def login(self, username):
        self.page.goto(self.url('/tai-khoan/login/'))
        self.page.fill('input[name=username]', username)
        self.page.fill('input[name=password]', PASSWORD)
        self.page.get_by_role('button', name='Đăng nhập').click()
        self.page.wait_for_load_state('networkidle')

    def place_order(self, method='bank'):
        """Add one book to the cart, check out with the given payment method, return the order."""
        p = self.page
        p.goto(self.url('/sach/'))
        with p.expect_navigation():
            p.locator('.round-add').first.click()
        self.assertEqual(p.locator('.count').first.inner_text().strip(), '1')
        p.goto(self.url('/thanh-toan/'))
        p.fill('input[name=full_name]', 'Tôn Nữ Minh Thư')
        p.fill('input[name=phone]', '0938114276')
        p.fill('textarea[name=address]', '18 Phan Đình Phùng, Huế')
        p.check(f'input[name=payment_method][value={method}]')
        with p.expect_navigation():
            p.get_by_role('button', name='Đặt hàng và nhận mã đơn').click()
        order = Order.objects.latest('created_at')
        self.assertIn(order.order_code, p.url)
        return order

    def place_bank_order(self):
        return self.place_order('bank')

    def test_guest_buys_with_qr_and_sees_payment_success(self):
        p = self.page
        order = self.place_bank_order()
        self.assertTrue(p.locator('img.qr-image').get_attribute('src').startswith('https://img.vietqr.io/image/970436-0011002233445'))
        self.assertTrue(p.locator('[data-pay-success]').is_hidden())
        p.screenshot(path=str(SHOTS / 'guest_waiting_qr.png'), full_page=True)
        has_3d = not self.strip_vt
        if has_3d:
            p.locator('.three-burst[data-three="ready"]').wait_for(state='attached', timeout=6000)
        # SePay reports the transfer while the customer's page is open
        txn, _ = record_sepay({'id': 'E2E-1', 'gateway': 'Vietcombank', 'transferType': 'in',
                               'transferAmount': order.total, 'content': f'MBVCB {order.order_code}', 'referenceCode': 'FT-E2E'})
        self.assertEqual(txn.status, 'matched')
        p.locator('[data-pay-success]').wait_for(state='visible', timeout=12000)
        self.assertTrue(p.locator('[data-pay-pending]').is_hidden())
        if has_3d:
            self.check_paid_burst()
        else:
            p.wait_for_timeout(900)
        self.assertEqual(p.locator('.pay-stamp').count(), 1)
        p.screenshot(path=str(SHOTS / 'guest_paid_celebration.png'))

    def test_open_qr_page_stops_asking_for_money_when_order_is_cancelled(self):
        from .services import change_order_status
        p = self.page
        order = self.place_bank_order()
        p.locator('img.qr-image').wait_for(state='visible', timeout=5000)
        change_order_status(order.pk, 'cancelled', None)  # staff (or the hold timer) cancels it meanwhile
        p.wait_for_function("document.querySelector('[data-pay-text]').textContent.includes('vừa bị hủy')", timeout=12000)
        self.assertTrue(p.locator('img.qr-image').is_hidden(), 'QR phải ẩn khi đơn đã hủy')
        self.assertTrue(p.locator('[data-pay-success]').is_hidden())

    def check_paid_burst(self):
        """3D burst: canvas within 800ms, never blocks the button, no DOM rain, gone by 1800ms."""
        p = self.page
        p.locator('.three-burst canvas').wait_for(state='attached', timeout=800)
        rains, at_700 = [], None
        btn = p.get_by_role('link', name='Tiếp tục khám phá sách')
        for tick in range(1, 21):
            p.wait_for_timeout(100)
            rains.append(p.locator('.pay-rain').count())
            if tick == 6:
                btn.scroll_into_view_if_needed()
            if tick == 7:
                at_700 = p.evaluate("""(b) => { const r = b.getBoundingClientRect();
                    const hit = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                    return !!hit && (hit === b || b.contains(hit)); }""", btn.element_handle())
            if tick == 18:
                self.assertEqual(p.locator('.three-burst canvas').count(), 0, 'Canvas nổ phải tự gỡ trước 1800ms')
                self.assertEqual(p.get_attribute('.three-burst', 'data-three'), 'done')
        self.assertTrue(at_700, 'Nút Tiếp tục khám phá sách bị chặn bấm khi đang nổ')
        self.assertEqual(max(rains), 0, 'Đã có mưa sách 3D thì không được mưa sách DOM')

    def test_sales_staff_pos_flow_without_browser_dialogs(self):
        self.login('banhang')
        p = self.page
        p.goto(self.url('/management/pos/'))
        p.locator('[data-pos-submit]').click()
        self.assertTrue(p.locator('#pos-msg').inner_text().strip(), 'POS phải báo lỗi giỏ trống ngay trên trang')
        first_book = p.locator('#book-select option:not([value=""])').first.get_attribute('value')
        p.select_option('#book-select', first_book)
        p.locator('#pos-add').click()
        self.assertEqual(p.locator('#pos-cart input[name=quantity]').count(), 1)
        if p.locator('#cash-confirm').is_checked():
            p.locator('#cash-confirm').uncheck()
        p.locator('[data-pos-submit]').click()
        self.assertIn('/management/pos/', p.url)  # first press only warns
        with p.expect_navigation():
            p.locator('[data-pos-submit]').click()
        self.assertIn('/management/orders/', p.url)
        self.assertEqual(Order.objects.filter(source='pos').count(), 1)
        p.screenshot(path=str(SHOTS / 'pos_order_created.png'))

    def test_warehouse_role_is_blocked_from_sales_pages(self):
        self.login('kho')
        p = self.page
        resp = p.goto(self.url('/management/pos/'))
        self.assertEqual(resp.status, 403)
        p.wait_for_timeout(1500)
        opacity = p.evaluate("getComputedStyle(document.querySelector('.empty-state')).opacity")
        self.assertEqual(opacity, '1', 'Trang báo không đủ quyền phải hiện rõ sau hiệu ứng')
        p.screenshot(path=str(SHOTS / 'forbidden_page.png'))
        self.assertEqual(p.goto(self.url('/management/books/')).status, 200)
        self.assertEqual(p.locator('.manager-sidebar a[href="/management/pos/"]').count(), 0)

    def test_view_transitions_navigation_has_no_errors(self):
        p = self.page
        p.goto(self.url('/'))
        with p.expect_navigation():
            p.locator('.book-card a').first.click()
        self.assertIn('/sach/', p.url)
        with p.expect_navigation():
            p.locator('a[href="/sach/"]').first.click()
        p.wait_for_timeout(400)

    # ---------- 3D (three.js), _workspace/05_designer_three_spec.md mục 6 ----------
    def wait_home_3d(self):
        p = self.page
        p.locator('.hero-art[data-three="on"]').wait_for(state='attached', timeout=8000)
        p.locator('.hero-sakura[data-three="on"]').wait_for(state='attached', timeout=8000)

    def canvas_facts(self, frame_sel):
        return self.page.evaluate("""(sel) => { const c = document.querySelector(sel + ' > canvas');
            return c && { w: c.width, cw: c.clientWidth, aria: c.getAttribute('aria-hidden'),
                          pe: getComputedStyle(c).pointerEvents }; }""", frame_sel)

    def test_home_mounts_3d_scenes_in_real_chrome(self):
        self.need_webgl()
        p = self.use_context(device_scale_factor=2)
        p.goto(self.url('/'))
        self.wait_home_3d()
        self.assertEqual(p.locator('canvas').count(), 2)
        for sel, dpr in (('.hero-art', 1.75), ('.hero-sakura', 1.5)):
            f = self.canvas_facts(sel)
            self.assertEqual(f['aria'], 'true')
            self.assertEqual(f['pe'], 'none')
            self.assertLessEqual(f['w'], f['cw'] * dpr + 1, f'{sel}: pixel ratio vượt trần')
        self.assertLessEqual(int(p.get_attribute('.hero-art', 'data-three-tris')), 800)
        self.assertLessEqual(int(p.get_attribute('.hero-sakura', 'data-three-tris')), 1500)
        # The flat fallback fades out once 3D is on; under a loaded suite the fade can lag, so wait for it.
        p.wait_for_function(f"{OPACITY} === '0'", timeout=5000)
        self.assertEqual(p.locator('.hero-stack .stack-cover').count(), 3)
        btn = p.get_by_role('link', name='Khám phá tủ sách')
        hit = p.evaluate("""(b) => { const r = b.getBoundingClientRect();
            const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            return !!el && (el === b || b.contains(el)); }""", btn.element_handle())
        self.assertTrue(hit, 'Canvas 3D che nút chính')
        ms = p.evaluate("""() => new Promise((done) => { const t0 = performance.now(); let n = 0;
            const tick = () => (++n < 60 ? requestAnimationFrame(tick) : done(performance.now() - t0));
            requestAnimationFrame(tick); })""")
        if ms > 1000:
            print(f'\n[cảnh báo] 60 khung hình trang chủ mất {ms:.0f}ms')
        p.screenshot(path=str(SHOTS / 'home_3d.png'))
        with p.expect_navigation():
            btn.click()
        self.assertTrue(p.url.endswith('/sach/'))

    def test_home_reduced_motion_has_no_canvas_and_no_three_download(self):
        p = self.use_context(reduced_motion='reduce')
        p.goto(self.url('/'))
        p.wait_for_timeout(1500)
        self.assertEqual(p.locator('canvas').count(), 0)
        self.assertEqual(p.get_attribute('.hero-art', 'data-three'), 'off')
        self.assertEqual(p.get_attribute('.hero-art', 'data-three-reason'), 'reduced-motion')
        self.assertEqual(p.evaluate(OPACITY), '1')
        self.assertEqual([u for u in self.three_requests if 'vendor/three/' in u], [])
        p.screenshot(path=str(SHOTS / 'home_3d_reduced.png'))

    def test_home_without_webgl_keeps_css_fallback(self):
        p = self.use_context(init_script=NO_WEBGL)
        p.goto(self.url('/'))
        p.locator('.hero-art[data-three="off"]').wait_for(state='attached', timeout=8000)
        self.assertEqual(p.get_attribute('.hero-art', 'data-three-reason'), 'no-webgl')
        self.assertEqual(p.locator('canvas').count(), 0)
        p.wait_for_timeout(500)
        self.assertEqual(p.evaluate(OPACITY), '1')
        self.assertLessEqual(len(self.warns), 1)

    def test_paid_burst_falls_back_to_dom_rain_without_webgl(self):
        p = self.use_context(init_script=NO_WEBGL)
        self.place_bank_order()
        p.wait_for_timeout(1500)
        self.assertEqual(p.get_attribute('.three-burst', 'data-three'), 'off')
        self.assertIsNone(p.evaluate('document.documentElement.dataset.threeBurst || null'))
        p.evaluate("""() => { document.querySelector('[data-pay-success]').hidden = false;
            document.dispatchEvent(new CustomEvent('hep:paid')); }""")
        p.locator('.pay-rain').wait_for(state='attached', timeout=400)
        p.wait_for_timeout(3200)
        self.assertEqual(p.locator('.pay-rain').count(), 0)
        self.assertEqual(p.locator('canvas').count(), 0)

    def test_no_three_on_checkout_login_admin_pos(self):
        p = self.page
        cod = self.place_order('cod')
        self.login('banhang')  # login lands on the home page, which is allowed to load 3D
        p.goto(self.url('/sach/'))
        with p.expect_navigation():
            p.locator('.round-add').first.click()
        for path in ('/thanh-toan/', '/tai-khoan/login/', '/management/', '/management/pos/',
                     f'/dat-hang-thanh-cong/{cod.order_code}/'):
            self.three_requests.clear()
            p.goto(self.url(path))
            p.wait_for_load_state('networkidle')
            self.assertEqual(p.evaluate("document.querySelectorAll('[data-three]').length"), 0, path)
            self.assertEqual(self.three_requests, [], path)

    def test_home_3d_mobile_no_horizontal_scroll(self):
        self.need_webgl()
        p = self.use_context(viewport={'width': 390, 'height': 844}, device_scale_factor=3, has_touch=True, is_mobile=True)
        p.goto(self.url('/'), wait_until='domcontentloaded')
        # Measured once web fonts settle, so a font swap in the hero copy is not mistaken for a 3D shift.
        rect = "(() => { const r = document.querySelector('.hero-art').getBoundingClientRect(); return [r.x, r.y, r.width, r.height]; })()"
        before = p.evaluate(f'document.fonts.ready.then(() => {rect})')
        self.wait_home_3d()
        self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'), 390)
        for sel in ('.hero-art', '.hero-sakura'):
            f = self.canvas_facts(sel)
            self.assertLessEqual(f['w'], f['cw'] * 1.25 + 1, f'{sel}: pixel ratio vượt trần mobile')
        self.assertEqual(p.evaluate("document.querySelector('.hero-art').getBoundingClientRect().height"), 256)
        self.assertEqual(p.evaluate(rect), before, 'Bật 3D làm dịch bố cục hero')
        p.wait_for_timeout(1500)
        p.screenshot(path=str(SHOTS / 'home_3d_mobile.png'))

    def test_3d_pauses_offscreen(self):
        self.need_webgl()
        p = self.page
        p.goto(self.url('/'))
        self.wait_home_3d()
        p.mouse.move(640, 600)
        p.mouse.wheel(0, 4000)
        p.wait_for_timeout(600)
        self.assertEqual(p.get_attribute('.hero-art', 'data-three-running'), '0')
        self.assertEqual(p.get_attribute('.hero-sakura', 'data-three-running'), '0')
        p.mouse.wheel(0, -8000)
        p.wait_for_timeout(600)
        self.assertEqual(p.get_attribute('.hero-art', 'data-three-running'), '1')
        self.assertEqual(p.get_attribute('.hero-sakura', 'data-three-running'), '1')

    # ---------- đợt "wa", _workspace/10_designer_wa_spec.md mục 11 (W3, W5, W6, W11) ----------
    HIT = """(b) => { const r = b.getBoundingClientRect();
        const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return !!el && (el === b || b.contains(el)); }"""

    # Ghi lại trạng thái rèm ngay lúc DOMContentLoaded (wa.js chạy defer, trước sự kiện này), nên phép đo không
    # phụ thuộc tốc độ máy: chạy cả bộ, Chrome bị chậm đi vẫn đo đúng khoảnh khắc rèm vừa dựng.
    NOREN_PROBE = NO_WEBGL + """;document.addEventListener('DOMContentLoaded', () => {
        const c = document.querySelector('.noren-curtain');
        const b = [...document.querySelectorAll('a')].find((a) => a.textContent.trim() === 'Khám phá tủ sách');
        const r = b && b.getBoundingClientRect();
        const hit = r && document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        const ms = (v) => v.split(',').map((x) => parseFloat(x) * (x.trim().endsWith('ms') ? 1 : 1000));
        const ends = c ? [...c.querySelectorAll('.noren-drape')].map((d) => { const s = getComputedStyle(d);
            return Math.max(...ms(s.animationDuration)) + Math.max(...ms(s.animationDelay)); }) : [];
        window.__noren = { display: c ? getComputedStyle(c).display : 'gone', pe: c ? getComputedStyle(c.parentElement).pointerEvents : '',
                           hit: !!hit && (hit === b || b.contains(hit)), end: Math.max(0, ...ends) };
    }, { once: true });"""

    def test_noren_parts_once_per_session_and_never_blocks(self):
        # Tắt WebGL và đo theo điều kiện DOM, không theo đồng hồ: 3D trên SwiftShader làm trễ bộ đếm giờ khi chạy cả bộ.
        p = self.use_context(init_script=self.NOREN_PROBE)
        p.goto(self.url('/'), wait_until='domcontentloaded')
        self.assertTrue(p.evaluate("document.documentElement.classList.contains('wa-noren')"), 'Lần đầu vào trang chủ phải có rèm')
        probe = p.wait_for_function('window.__noren', timeout=10000).json_value()
        self.assertEqual(probe['display'], 'flex')
        self.assertEqual(probe['pe'], 'none')
        self.assertTrue(probe['hit'], 'Rèm noren chặn nút chính')
        self.assertLessEqual(probe['end'], 1160, 'Rèm phải rẽ xong trong 1160ms (CSS)')
        p.wait_for_function("!document.querySelector('.noren-curtain')", timeout=10000)
        self.assertFalse(p.evaluate("document.documentElement.classList.contains('wa-noren')"))
        p.goto(self.url('/'), wait_until='domcontentloaded')
        self.assertFalse(p.evaluate("document.documentElement.classList.contains('wa-noren')"), 'Rèm chỉ rẽ một lần mỗi phiên')
        p = self.use_context(reduced_motion='reduce')
        p.goto(self.url('/'))
        self.assertFalse(p.evaluate("document.documentElement.classList.contains('wa-noren')"))
        self.assertEqual(p.evaluate("getComputedStyle(document.querySelector('.noren-curtain')).display"), 'none')
        opacities = p.evaluate("[...document.querySelectorAll('.hanko:not(.cart-stamp)')].map((h) => getComputedStyle(h).opacity)")
        self.assertTrue(opacities and set(opacities) == {'1'}, 'Giảm chuyển động: mọi con dấu phải hiện sẵn')

    def test_spine_shelf_follows_keyboard_and_scrolls_on_mobile(self):
        # Tắt WebGL: cảnh 3D trên SwiftShader chiếm luồng chính, làm sai số đo độ trễ của kệ (kệ không dùng 3D).
        p = self.use_context(init_script=NO_WEBGL)
        p.goto(self.url('/'))
        p.wait_for_load_state('networkidle')
        third = p.locator('.spine-row .spine').nth(2)
        title = third.locator('.spine-vi').inner_text().strip()
        third.locator('.spine-link').focus()
        # Chờ theo điều kiện: trễ rê 90ms + lật 590ms; trần 5s chỉ để không treo khi máy bận.
        p.wait_for_function("(t) => document.querySelector('.stand-title').textContent.trim() === t", arg=title, timeout=5000)
        p = self.use_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        for path in ('/', '/sach/'):
            p.goto(self.url(path))
            self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'), 390, path)
        p.goto(self.url('/'))
        self.assertTrue(p.evaluate("(() => { const r = document.querySelector('.spine-row'); return r.scrollWidth > r.clientWidth"
                                   " && getComputedStyle(r).overflowX === 'auto'; })()"), 'Kệ gáy phải cuộn ngang ở 390px')
        p = self.use_context(java_script_enabled=False)
        p.goto(self.url('/'))
        first = p.locator('.spine-row .spine').first.locator('.spine-vi').inner_text().strip()
        self.assertEqual(p.locator('.stand-title').inner_text().strip(), first, 'Không JS: giá trưng bày giữ cuốn đầu')

    def test_add_buttons_are_never_covered_by_pop_or_obi(self):
        p = self.use_context(init_script=NO_WEBGL)
        for path in ('/', '/sach/'):
            p.goto(self.url(path))
            bad = p.evaluate("""async () => { const out = [];
                for (const b of document.querySelectorAll('.book-card .round-add')) {
                    b.scrollIntoView({ block: 'center', behavior: 'instant' });
                    await new Promise((r) => setTimeout(r, 300));
                    // Đợi thẻ vào cảnh xong (đặt xuống bàn, đóng dấu); bỏ qua POP đung đưa vô hạn.
                    const card = b.closest('.book-card');
                    await Promise.all(card.getAnimations({ subtree: true })
                        .filter((a) => a.effect && a.effect.getComputedTiming().iterations !== Infinity)
                        .map((a) => a.finished.catch(() => null)));
                    const r = b.getBoundingClientRect();
                    const el = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
                    if (!el || !(el === b || b.contains(el))) out.push(b.getAttribute('aria-label') + ' <- ' + (el ? el.tagName + '.' + el.className : 'null') + ' ' + Math.round(r.top) + '/' + innerHeight);
                }
                return out; }""")
            self.assertEqual(bad, [], f'{path}: nút thêm giỏ bị che')
            boxes = p.evaluate("[...document.querySelectorAll('.book-card')].map((c) => getComputedStyle(c).backgroundColor)")
            self.assertEqual(set(boxes), {'rgba(0, 0, 0, 0)'}, f'{path}: thẻ sách không được là hộp có nền')

    # ---------- đợt "wa" lượt B: chi tiết, giỏ, không cuộn ngang (W9, W10, W11 c/e) ----------
    # Đợi các hiệu ứng có hạn chạy xong (dấu đang đập xuống phóng to 1.9 lần chỉ trong 380ms), bỏ qua lặp vô hạn.
    OVERFLOW = """async () => { await Promise.race([new Promise((r) => setTimeout(r, 6000)), Promise.all(document.getAnimations()
            .filter((a) => a.effect && a.effect.getComputedTiming().iterations !== Infinity && !a.timeline?.source)
            .map((a) => a.finished.catch(() => null)))]);
        const W = innerWidth, bad = [];
        for (const e of document.querySelectorAll('body *')) {
            const r = e.getBoundingClientRect();
            if (!r.width || (r.right <= W + 1 && r.left >= -1)) continue;
            let a = e.parentElement, clipped = false;
            while (a && a !== document.body) { if (getComputedStyle(a).overflowX !== 'visible') { clipped = true; break; } a = a.parentElement; }
            if (!clipped) bad.push(e.tagName + '.' + e.className + ' ' + Math.round(r.left) + '..' + Math.round(r.right));
        }
        return bad.slice(0, 5); }"""

    def test_detail_stage_keeps_cover_obi_and_stays_in_view(self):
        p = self.use_context(init_script=NO_WEBGL, viewport={'width': 1440, 'height': 900})
        p.goto(self.url('/sach/bon-mua-o-kyoto/'))
        self.assertEqual(p.locator('.detail-cover[data-tilt] .detail-obi').count(), 1, 'Obi phải nằm trong bìa để nghiêng và bay cùng bìa')
        self.assertEqual(p.locator('.wa-similar .spine-row .spine').count(), p.locator('.wa-similar .spine').count())
        self.assertGreater(p.locator('.wa-similar .spine-foot .hanko-st').count(), 0, 'Kệ cùng chủ đề dùng dấu trạng thái')
        self.assertEqual(p.locator('.section-top').count(), 0)
        p.evaluate('window.scrollTo(0, 900)')
        p.wait_for_function("""() => { const r = document.querySelector('.detail-stage').getBoundingClientRect();
            return r.top >= 0 && r.top < innerHeight && r.bottom > 0; }""", timeout=5000)

    def test_cart_row_gets_stamped_after_adding(self):
        p = self.use_context(init_script=NO_WEBGL)
        p.goto(self.url('/sach/'))
        form = p.locator('.book-card form[data-fly-cart]').first
        book_id = form.get_attribute('data-book-id')
        with p.expect_navigation():
            form.locator('button').click()
        self.assertIn('/gio-hang/', p.url)
        p.wait_for_selector(f'.cart-row.is-stamped[data-book-id="{book_id}"]', timeout=5000)
        self.assertEqual(p.locator('.cart-row.is-stamped').count(), 1)
        # Dấu đập xuống 380ms rồi ở lại: chờ tới khi hiện hẳn.
        p.wait_for_function("getComputedStyle(document.querySelector('.cart-row.is-stamped .cart-stamp')).opacity === '1'", timeout=5000)
        p.reload()
        p.wait_for_load_state('networkidle')
        self.assertEqual(p.locator('.cart-row.is-stamped').count(), 0, 'Dấu chỉ đóng một lần cho lần thêm vừa rồi')

    def test_shop_pages_have_no_horizontal_overflow_at_390(self):
        p = self.use_context(init_script=NO_WEBGL, viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        p.goto(self.url('/sach/'))
        with p.expect_navigation():
            p.locator('.round-add').first.click()
        for path in ('/', '/sach/', '/sach/bon-mua-o-kyoto/', '/gio-hang/', '/thanh-toan/', '/ve-hep/', '/chinh-sach/'):
            p.goto(self.url(path))
            p.wait_for_load_state('networkidle')
            self.assertLessEqual(p.evaluate('document.documentElement.scrollWidth'), 390, path)
            self.assertEqual(p.evaluate(self.OVERFLOW), [], f'{path}: phần tử tràn ngang ngoài khung cuộn riêng')

