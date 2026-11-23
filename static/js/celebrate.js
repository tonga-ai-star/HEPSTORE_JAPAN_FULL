// pay-celebrate: ăn mừng khi ngân hàng báo tiền về. Chỉ nghe sự kiện hep:paid do payment_poll.js phát.
// Khối "Thanh toán thành công" đọc được không cần file này: payment_poll.js chỉ bỏ thuộc tính hidden.
'use strict';
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    || document.documentElement.classList.contains('motion-off');
  const SPRING = 'cubic-bezier(.34,1.56,.64,1)';
  const OUT = 'cubic-bezier(.16,1,.3,1)';
  const RAIN_CLEAR_MS = 3000;
  const RAIN_END_MS = 2700;
  const RAIN_MOBILE_PX = 768;
  const BEARS_IN_RAIN = 3;
  const BOOK_TONES = ['b1', 'b2', 'b3'];

  const rand = (lo, hi) => lo + Math.random() * (hi - lo);

  /** Con dấu hanko "済" ở góc khối thành công; chèn một lần, đứng yên ở -8 độ. */
  const ensureStamp = (box) => {
    let stamp = box.querySelector('.pay-stamp');
    if (!stamp) {
      stamp = document.createElement('span');
      stamp.className = 'pay-stamp';
      stamp.lang = 'ja';
      stamp.setAttribute('aria-hidden', 'true');
      stamp.textContent = '済';
      box.appendChild(stamp);
    }
    return stamp;
  };

  /** Nhịp 1 đến 3: khối bung, con dấu đóng xuống làm khối rung, dấu tích xoay vào. */
  const popBox = (box) => {
    box.animate([
      { transform: 'scale(.6) translateY(16px)', opacity: 0 },
      { transform: 'scale(1.04)', opacity: 1, offset: 0.6 },
      { transform: 'none', opacity: 1 },
    ], { duration: 620, easing: SPRING, fill: 'backwards' });
    const stamp = ensureStamp(box);
    const hit = stamp.animate([
      { transform: 'scale(2.4) rotate(-28deg)', opacity: 0 },
      { transform: 'scale(1) rotate(-8deg)', opacity: 1 },
    ], { duration: 360, delay: 180, easing: 'cubic-bezier(.2,1.4,.4,1)', fill: 'backwards' });
    hit.finished.then(() => box.animate([
      { transform: 'translateY(0)' }, { transform: 'translateY(3px)' }, { transform: 'translateY(-2px)' }, { transform: 'translateY(0)' },
    ], { duration: 180, composite: 'add' }), () => {});
    const icon = box.querySelector('.ph');
    if (icon) {
      icon.animate([{ transform: 'rotate(-90deg) scale(0)' }, { transform: 'none' }],
        { duration: 480, delay: 200, easing: SPRING, fill: 'backwards' });
    }
  };

  /** Một vật rơi: sách nhỏ có gáy, hoặc gấu mini clone từ gấu có sẵn trên trang. */
  const rainItem = (i, bearSvg) => {
    if (bearSvg && i < BEARS_IN_RAIN) {
      const b = bearSvg.cloneNode(true);
      b.removeAttribute('data-bear');
      b.setAttribute('width', '22');
      b.setAttribute('height', '22');
      b.classList.add('rain-bear');
      return b;
    }
    const s = document.createElement('span');
    s.className = `rain-book ${BOOK_TONES[i % BOOK_TONES.length]}`;
    return s;
  };

  /** Nhịp 4: mưa sách thưa, không chặn bấm, tự xoá sau 3s. */
  const rain = () => {
    const layer = document.createElement('div');
    layer.className = 'pay-rain';
    layer.setAttribute('aria-hidden', 'true');
    const n = window.innerWidth < RAIN_MOBILE_PX ? 16 : 28;
    const bearSvg = document.querySelector('svg.bear');
    const h = window.innerHeight;
    for (let i = 0; i < n; i += 1) {
      const item = rainItem(i, bearSvg);
      item.style.left = `${rand(0, 100).toFixed(2)}vw`;
      layer.appendChild(item);
      const delay = 250 + rand(0, 500);
      const drift = rand(-60, 60);
      item.animate([
        { transform: 'translate(0,-40px) rotate(0deg)' },
        { transform: `translate(${drift}px,${h + 40}px) rotate(${rand(180, 540)}deg)` },
      ], { duration: rand(1600, Math.min(2400, RAIN_END_MS - delay + 250)), delay, easing: 'cubic-bezier(.3,.6,.5,1)', fill: 'both' });
    }
    document.body.appendChild(layer);
    setTimeout(() => layer.remove(), RAIN_CLEAR_MS);
  };

  /** Nhịp 5 và 6: gấu sống nhảy hai nhịp, cười híp mắt; tổng tiền nảy. */
  const cheer = () => {
    const bear = document.querySelector('[data-bear]');
    if (bear) {
      bear.animate([
        { transform: 'translateY(0) rotate(0deg)' }, { transform: 'translateY(-18px) rotate(-6deg)' },
        { transform: 'translateY(0) rotate(6deg)' }, { transform: 'translateY(-10px) rotate(-3deg)' },
        { transform: 'translateY(0) rotate(0deg)' },
      ], { duration: 900, delay: 300, easing: OUT });
      bear.querySelectorAll('.eye').forEach((eye) => eye.animate([
        { transform: 'scaleY(1)' }, { transform: 'scaleY(.1)', offset: 0.15 },
        { transform: 'scaleY(.1)', offset: 0.85 }, { transform: 'scaleY(1)' },
      ], { duration: 600, delay: 300 }));
    }
    const total = document.querySelector('.total-row.big strong');
    if (total) {
      total.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.12)' }, { transform: 'scale(1)' }],
        { duration: 500, delay: 400, easing: OUT });
    }
  };

  /** Đơn đã trả từ trước khi mở trang: con dấu đứng yên. */
  const already = document.querySelector('[data-pay-success]:not([hidden])');
  if (already) ensureStamp(already);

  document.addEventListener('hep:burst-fallback', () => { if (!reduce) rain(); }, { once: true });

  document.addEventListener('hep:paid', () => {
    const box = document.querySelector('[data-pay-success]');
    if (!box || box.hidden) return;
    box.classList.add('is-celebrating');
    if (reduce || typeof box.animate !== 'function') { ensureStamp(box); return; }
    try {
      popBox(box);
      if (document.documentElement.dataset.threeBurst !== 'ready') rain();
      cheer();
    } catch (_) { ensureStamp(box); }
  });
})();
