// Đợt "wa" (tiệm sách Nhật): rèm noren, bảng/POP lắc, giá trưng bày của kệ gáy sách, dấu 入 trên giỏ.
// Chỉ là lớp trang trí: tắt JS thì noren tự rút bằng CSS, gáy sách vẫn là liên kết, giá trưng bày giữ cuốn đầu.
// Đặc tả: _workspace/10_designer_wa_spec.md mục 3.6. Không nghe sự kiện cuộn, không setInterval.
'use strict';
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const motionOff = reduce || root.classList.contains('motion-off');
  const NOREN_CAP_MS = 1400;
  const SKIP_EVENTS = ['pointerdown', 'keydown', 'wheel', 'touchstart'];
  const SWING_ANIMS = new Set(['pop-flick', 'sign-swing', 'valance-sway']);
  const STAND_HOVER_MS = 90;
  const STAND_TOUCH_GAP_MS = 250;
  const FLIP_OUT_MS = 170;
  const FLIP_IN_MS = 420;
  const CART_STAMP_DELAY_MS = 350;

  const safe = (fn) => { try { fn(); } catch (_) { /* hiệu ứng là phần trang trí */ } };

  /** noren-part: rèm rẽ ra (CSS lo chuyển động); JS chỉ ghi phiên, cho bỏ qua bằng mọi tương tác và dọn rèm. */
  const noren = () => {
    const curtain = document.querySelector('.noren-curtain');
    if (!curtain) return;
    if (!root.classList.contains('wa-noren')) { curtain.remove(); return; }
    try { sessionStorage.setItem('hep-noren', '1'); } catch (_) { /* không nhớ được phiên: lần sau rèm vẫn rẽ */ }
    const skip = () => curtain.classList.add('is-skip');
    SKIP_EVENTS.forEach((t) => window.addEventListener(t, skip, { once: true, passive: true }));
    let left = curtain.querySelectorAll('.noren-drape').length;
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      SKIP_EVENTS.forEach((t) => window.removeEventListener(t, skip));
      curtain.remove();
      root.classList.remove('wa-noren');
      const valance = document.querySelector('.noren-valance');
      if (valance) valance.classList.add('is-swing');
    };
    curtain.addEventListener('animationend', (e) => {
      if (e.animationName === 'noren-part' && --left <= 0) finish();
    });
    setTimeout(finish, NOREN_CAP_MS);
  };

  /** swing: một trình nghe uỷ quyền cho mọi [data-swing]; lắc một nhịp khi con trỏ đi vào (bỏ qua chạm). */
  const swing = () => {
    document.addEventListener('pointerenter', (e) => {
      const el = e.target;
      if (e.pointerType === 'touch' || !(el instanceof Element) || !el.hasAttribute('data-swing')) return;
      if (!el.classList.contains('is-swing')) el.classList.add('is-swing');
    }, true);
    document.addEventListener('animationend', (e) => {
      if (!SWING_ANIMS.has(e.animationName) || !(e.target instanceof Element)) return;
      const host = e.target.closest('[data-swing], .noren-valance');
      if (host) host.classList.remove('is-swing');
    });
  };

  /** Lật mặt giá trưng bày: quay đi 90 độ, thay bìa bằng bản sao <template>, quay về. */
  const flipFace = (face, render, animate) => {
    if (!animate || typeof face.animate !== 'function') { render(); return Promise.resolve(); }
    return face.animate([{ transform: 'rotateY(0deg)', opacity: 1 }, { transform: 'rotateY(-90deg)', opacity: 0.4 }],
      { duration: FLIP_OUT_MS, easing: 'cubic-bezier(.4,0,1,1)' }).finished
      .then(() => {
        render();
        return face.animate([{ transform: 'rotateY(90deg)' }, { transform: 'rotateY(0deg)' }],
          { duration: FLIP_IN_MS, easing: 'cubic-bezier(.16,1,.3,1)' }).finished;
      });
  };

  /** Gắn một kệ gáy sách với giá trưng bày của nó (rê chuột, Tab, hoặc vuốt trên màn cảm ứng). */
  const bindShelf = (shelf, animate) => {
    const face = shelf.querySelector('.stand-face');
    const row = shelf.querySelector('.spine-row');
    if (!face || !row) return;
    let shown = row.querySelector('.spine');
    let busy = false;
    let timer = 0;
    if (shown) shown.classList.add('is-shown');
    const render = () => {
      const tpl = shown && shown.querySelector('template.spine-face');
      if (tpl) face.replaceChildren(tpl.content.cloneNode(true));
    };
    const show = (li) => {
      if (!li || li === shown) return;
      if (shown) shown.classList.remove('is-shown');
      shown = li;
      li.classList.add('is-shown');
      if (busy) return; // lượt lật đang chạy sẽ vẽ cuốn mới nhất
      busy = true;
      flipFace(face, render, animate).catch(render).then(() => { busy = false; });
    };
    const queue = (li) => { clearTimeout(timer); timer = setTimeout(() => show(li), STAND_HOVER_MS); };
    row.addEventListener('pointerover', (e) => {
      if (e.pointerType === 'touch') return;
      const li = e.target instanceof Element && e.target.closest('.spine');
      if (li) queue(li);
    });
    row.addEventListener('pointerleave', () => clearTimeout(timer));
    row.addEventListener('focusin', (e) => {
      const li = e.target instanceof Element && e.target.closest('.spine');
      if (li) queue(li);
    });
    if (!matchMedia('(pointer: coarse)').matches || !('IntersectionObserver' in window)) return;
    let last = 0;
    let armed = false; // chỉ đổi bìa khi khách đã chạm vào kệ, không đổi lúc gáy đang xếp lên kệ
    row.addEventListener('pointerdown', () => { armed = true; }, { once: true, passive: true });
    const io = new IntersectionObserver((entries) => {
      if (!armed) return;
      const hit = entries.find((en) => en.isIntersecting);
      const now = performance.now();
      if (!hit || now - last < STAND_TOUCH_GAP_MS) return;
      last = now;
      show(hit.target);
    }, { root: row, rootMargin: '0px -45% 0px -45%', threshold: 0 });
    row.querySelectorAll('.spine').forEach((li) => io.observe(li));
  };

  /** stand: mọi kệ gáy sách trên trang. Giảm chuyển động thì vẫn đổi bìa, chỉ bỏ phần lật. */
  const stand = () => document.querySelectorAll('[data-spines]').forEach((s) => bindShelf(s, !motionOff));

  /** cartStamp: trang giỏ đóng dấu 入 lên đúng dòng sách vừa thêm (id do motion-shop.js ghi). */
  const cartStamp = () => {
    let id = null;
    try {
      id = sessionStorage.getItem('hep-stamp');
      sessionStorage.removeItem('hep-stamp');
    } catch (_) { return; }
    if (!id || !window.CSS || !CSS.escape) return;
    const row = document.querySelector(`.cart-row[data-book-id="${CSS.escape(id)}"]`);
    if (row) setTimeout(() => row.classList.add('is-stamped'), CART_STAMP_DELAY_MS);
  };

  safe(stand);
  if (motionOff) {
    try { sessionStorage.removeItem('hep-stamp'); } catch (_) { /* không có gì để dọn */ }
    return;
  }
  [noren, swing, cartStamp].forEach(safe);
})();
