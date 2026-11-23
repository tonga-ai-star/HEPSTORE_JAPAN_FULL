// Hiệu ứng quản trị (MOTION 6): số chạy, báo tiền vào, rung khi POS báo lỗi.
// Báo tiền vào vẫn chạy khi giảm chuyển động (chỉ tắt phần chuyển động); mọi lỗi mạng bị bỏ qua im lặng.
'use strict';
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches
    || document.documentElement.classList.contains('motion-off');
  const COUNT_MS = 900;
  const FEED_MS = 8000;
  const LAST_KEY = 'hep-last-txn';
  const SHAKE = ['translateX(0)', 'translateX(-6px)', 'translateX(6px)', 'translateX(-4px)', 'translateX(4px)', 'translateX(-2px)', 'translateX(0)'];

  const toast = (msg) => { if (typeof window.hepToast === 'function') window.hepToast(msg); };
  const money = (v) => `${Math.round(Number(v) || 0).toLocaleString('vi-VN')} ₫`;
  const readLast = () => {
    try { const v = localStorage.getItem(LAST_KEY); return v === null ? null : Number(v) || 0; } catch (_) { return undefined; }
  };
  const writeLast = (id) => { try { localStorage.setItem(LAST_KEY, String(id)); } catch (_) { /* bộ nhớ bị chặn: chỉ nhớ trong trang */ } };

  /** count-up: chạy 0 tới giá trị server, cuối cùng ghi lại đúng chữ gốc. */
  const runCount = (el, original, value, prefix, suffix) => {
    const start = performance.now();
    el.setAttribute('aria-label', original);
    const frame = (now) => {
      const t = Math.min(1, (now - start) / COUNT_MS);
      const eased = 1 - (1 - t) ** 3;
      el.textContent = `${prefix}${Math.round(value * eased).toLocaleString('vi-VN')}${suffix}`;
      if (t < 1) { requestAnimationFrame(frame); return; }
      el.textContent = original;
      el.removeAttribute('aria-label');
    };
    requestAnimationFrame(frame);
  };
  const countUp = () => {
    const items = Array.from(document.querySelectorAll('[data-count]')).map((el) => {
      const original = el.textContent;
      const m = original.match(/^(\D*?)(\d[\d.]*)(.*)$/s);
      const value = m ? Number(m[2].replace(/\./g, '')) : 0;
      return m && value > 0 ? { el, original, value, prefix: m[1], suffix: m[3] } : null;
    }).filter(Boolean);
    if (!items.length || !('IntersectionObserver' in window)) return;
    items.forEach((it) => { it.el.textContent = `${it.prefix}0${it.suffix}`; });
    const io = new IntersectionObserver((entries) => entries.forEach((en) => {
      if (!en.isIntersecting) return;
      io.unobserve(en.target);
      const it = items.find((x) => x.el === en.target);
      runCount(it.el, it.original, it.value, it.prefix, it.suffix);
    }), { threshold: 0.4 });
    items.forEach((it) => io.observe(it.el));
  };

  /** txn-fresh: dòng có mã giao dịch lớn hơn lần xem trước nhận chấm cam, kèm đúng một toast. */
  let known = null;
  const markFresh = () => {
    const rows = Array.from(document.querySelectorAll('[data-txn-id]'));
    const ids = rows.map((r) => Number(r.dataset.txnId) || 0);
    const stored = readLast();
    known = stored === undefined ? null : stored;
    if (!ids.length) return;
    const max = Math.max(...ids);
    if (known !== null) {
      const fresh = rows.filter((r, i) => ids[i] > known);
      fresh.forEach((r) => r.classList.add('is-fresh'));
      if (fresh.length) toast(`${fresh.length} khoản tiền mới từ lần xem trước`);
    }
    known = Math.max(known || 0, max);
    writeLast(known);
  };

  /** Báo tiền vào trực tiếp: hỏi API mỗi 8 giây khi tab đang mở, khoản mới thì toast và chấm cam ở mục Tiền vào. */
  const notifyNew = (items) => {
    const fresh = items.filter((it) => Number(it.id) > known);
    if (!fresh.length) return;
    const item = fresh[0];
    toast(fresh.length === 1
      ? `Tiền vào: ${money(item.amount)}${item.order_code ? ` cho đơn ${item.order_code}` : `, ${item.status_label}`}`
      : `${fresh.length} khoản tiền mới vừa về, mới nhất ${money(item.amount)}`);
    const side = document.querySelector('[data-side-payments]');
    if (side) side.classList.add('has-fresh');
  };
  const paymentsFeed = () => {
    const host = document.querySelector('[data-payments-feed]');
    if (!host || location.protocol === 'file:' || !window.fetch) return;
    const url = host.dataset.paymentsFeed;
    let timer = 0;
    let stopped = false;
    const tick = async () => {
      timer = 0;
      if (stopped || document.hidden) return;
      try {
        const res = await fetch(url, { headers: { Accept: 'application/json' }, cache: 'no-store', credentials: 'same-origin' });
        if (res.status === 403 || res.status === 401) { stopped = true; return; }
        if (res.ok) {
          const items = ((await res.json()) || {}).items || [];
          const max = items.reduce((m, it) => Math.max(m, Number(it.id) || 0), 0);
          if (known === null) known = max;
          else notifyNew(items);
          known = Math.max(known, max);
          writeLast(known);
        }
      } catch (_) { /* mạng chập chờn: thử lại lượt sau */ }
      if (!stopped && !document.hidden) timer = setTimeout(tick, FEED_MS);
    };
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && !timer && !stopped) timer = setTimeout(tick, 600);
    });
    window.addEventListener('pagehide', () => { stopped = true; clearTimeout(timer); });
    timer = setTimeout(tick, FEED_MS);
  };

  /** pos-shake: thông báo POS và nút tạo hóa đơn rung mỗi lần thông báo hiện hoặc đổi chữ. */
  const posShake = () => {
    const msg = document.querySelector('#pos-msg');
    if (!msg || !('MutationObserver' in window)) return;
    const submit = document.querySelector('[data-pos-submit]');
    let frame = 0;
    new MutationObserver(() => {
      if (msg.hidden) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => [msg, submit].forEach((el) => el && el.animate(
        SHAKE.map((transform) => ({ transform })), { duration: 360, easing: 'cubic-bezier(.36,.07,.19,.97)' })));
    }).observe(msg, { attributes: true, attributeFilter: ['hidden'], childList: true, characterData: true, subtree: true });
  };

  const safe = (fn) => { try { fn(); } catch (_) { /* phần trang trí, không chặn thao tác */ } };
  safe(markFresh);
  safe(paymentsFeed);
  if (reduce) return;
  safe(countUp);
  safe(posShake);
})();
