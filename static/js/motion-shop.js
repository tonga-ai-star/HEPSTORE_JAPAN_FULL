// Hiệu ứng shop đợt 2: sách bay vào giỏ (kèm dấu 入 đợt wa), bìa nối sang trang chi tiết, kệ sách ghim theo cuộn.
// Chỉ là lớp trang trí: tắt JS hoặc giảm chuyển động thì form và liên kết chạy như bình thường.
'use strict';
(() => {
  const root = document.documentElement;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches || root.classList.contains('motion-off')) return;
  const FLY_MS = 420;
  const FLY_CAP_MS = 450;
  const FLY_W = 56;
  const FLY_H = 76;
  const FLY_RISE_PX = 90;
  const SHELF_PAD_PX = 32;

  /** Tìm bìa gần nhất của form thêm giỏ: thẻ sách, bìa trang chi tiết, bìa trang quét, hoặc chính nút. */
  const coverOf = (form, button) => {
    const card = form.closest('.book-card');
    return (card && card.querySelector('.cover-link'))
      || (form.closest('.detail-grid') && document.querySelector('.detail-cover'))
      || (form.closest('.scan-result-card') && document.querySelector('.scan-cover-tilt'))
      || button || form;
  };

  /** Dựng bản sao bìa nhỏ 56x76 đặt ở tâm bìa nguồn. */
  const makeFlyBook = (src) => {
    const r = src.getBoundingClientRect();
    const fly = document.createElement('div');
    fly.className = 'fly-book';
    fly.setAttribute('aria-hidden', 'true');
    const face = src.querySelector('.book-cover, img');
    if (face) {
      const clone = face.cloneNode(true);
      clone.removeAttribute('id');
      fly.appendChild(clone);
      fly.style.backgroundColor = getComputedStyle(face).backgroundColor;
    }
    fly.style.left = `${r.left + r.width / 2 - FLY_W / 2}px`;
    fly.style.top = `${r.top + r.height / 2 - FLY_H / 2}px`;
    document.body.appendChild(fly);
    return { fly, x: r.left + r.width / 2, y: r.top + r.height / 2 };
  };

  /** Gửi form thật, giữ name/value của nút bấm nếu có. */
  const sendForm = (form, submitter) => {
    if (submitter && submitter.name) {
      const keep = document.createElement('input');
      keep.type = 'hidden';
      keep.name = submitter.name;
      keep.value = submitter.value;
      form.appendChild(keep);
    }
    try { sessionStorage.setItem('hep-fly', '1'); } catch (_) { /* thiếu bộ nhớ phiên: cart-bump dùng điều kiện cũ */ }
    HTMLFormElement.prototype.submit.call(form);
  };

  /** hanko-cart: dấu 入 đập xuống obi lúc sách bay; ghi id sách để trang giỏ đóng dấu đúng dòng (wa.js cartStamp). */
  const stampCart = (form) => {
    (form.closest('.cover-wrap') || form).classList.add('is-stamping');
    try { if (form.dataset.bookId) sessionStorage.setItem('hep-stamp', form.dataset.bookId); } catch (_) { /* thiếu bộ nhớ phiên: giỏ không đóng dấu */ }
  };

  /** fly-to-cart: bìa bay lên rồi rơi vào số đếm giỏ, form gửi chậm nhất sau 450ms. */
  const flyToCart = (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement) || !form.hasAttribute('data-fly-cart')) return;
    if (form.dataset.flying) { e.preventDefault(); return; }
    const count = document.querySelector('.site-header .count');
    if (!count || typeof Element.prototype.animate !== 'function') return;
    e.preventDefault();
    form.dataset.flying = '1';
    const button = e.submitter || form.querySelector('button');
    if (button) button.setAttribute('aria-busy', 'true');
    stampCart(form);
    const { fly, x, y } = makeFlyBook(coverOf(form, button));
    const c = count.getBoundingClientRect();
    const dx = c.left + c.width / 2 - x;
    const dy = c.top + c.height / 2 - y;
    const anim = fly.animate([
      { transform: 'translate(0,0) scale(1) rotate(0deg)', opacity: 1 },
      { transform: `translate(${dx * 0.4}px,${Math.min(-FLY_RISE_PX, dy * 0.45 - 40)}px) scale(.7) rotate(-14deg)`, opacity: 1, offset: 0.45 },
      { transform: `translate(${dx}px,${dy}px) scale(.18) rotate(8deg)`, opacity: 0.4 },
    ], { duration: FLY_MS, easing: 'cubic-bezier(.5,0,.25,1)', fill: 'forwards' });
    let sent = false;
    const go = () => {
      if (sent) return;
      sent = true;
      count.classList.add('bump');
      sendForm(form, e.submitter);
    };
    anim.finished.then(go, go);
    setTimeout(go, FLY_CAP_MS);
  };

  /** Quay lại bằng nút Back (bfcache): gỡ cờ đang bay, bản sao bìa và tên chuyển tiếp. */
  const resetOnShow = () => {
    document.querySelectorAll('form[data-flying]').forEach((f) => {
      delete f.dataset.flying;
      f.querySelectorAll('[aria-busy]').forEach((b) => b.removeAttribute('aria-busy'));
    });
    document.querySelectorAll('.fly-book').forEach((n) => n.remove());
    document.querySelectorAll('.is-stamping').forEach((n) => n.classList.remove('is-stamping'));
    document.querySelectorAll('.cover-link').forEach((n) => { n.style.viewTransitionName = ''; });
    const detail = document.querySelector('.detail-cover');
    if (detail) detail.style.viewTransitionName = '';
    const count = document.querySelector('.site-header .count');
    if (count) count.classList.remove('bump');
  };

  /** cover-morph: chỉ bìa của thẻ vừa bấm mang tên book-cover, để View Transitions nối sang bìa trang chi tiết. */
  const coverMorph = (e) => {
    if (!document.startViewTransition && !('onpagereveal' in window)) return;
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const link = e.target instanceof Element && e.target.closest('.book-card a[href]');
    if (!link) return;
    const cover = link.closest('.book-card').querySelector('.cover-link');
    if (!cover) return;
    document.querySelectorAll('.cover-link').forEach((n) => { n.style.viewTransitionName = ''; });
    const detail = document.querySelector('.detail-cover');
    if (detail) detail.style.viewTransitionName = 'none';
    cover.style.viewTransitionName = 'book-cover';
  };

  /** shelf-pin: đo quãng kệ phải trượt; CSS scroll-timeline lo phần chuyển động, không nghe sự kiện cuộn. */
  const shelfPin = () => {
    const pin = document.querySelector('[data-shelf-pin]');
    if (!pin || !('ResizeObserver' in window)) return;
    const sticky = pin.querySelector('.shelf-sticky');
    const track = pin.querySelector('.shelf-track');
    if (!sticky || !track) return;
    const measure = () => {
      const pinned = getComputedStyle(track).display === 'flex' && getComputedStyle(sticky).position === 'sticky';
      const shift = pinned ? Math.max(0, track.scrollWidth - sticky.clientWidth + SHELF_PAD_PX) : 0;
      pin.style.setProperty('--shelf-shift', `${shift}px`);
    };
    new ResizeObserver(measure).observe(sticky);
    measure();
  };

  document.addEventListener('submit', flyToCart);
  document.addEventListener('click', coverMorph);
  window.addEventListener('pageshow', resetOnShow);
  try { shelfPin(); } catch (_) { /* kệ vẫn là lưới thường */ }
})();
