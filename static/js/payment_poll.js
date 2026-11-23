// Polls the order's payment status while a QR bank transfer is pending.
// The server is the only source of truth: this script only displays what it reports.
'use strict';
(() => {
  const box = document.querySelector('[data-payment-poll]');
  if (!box) return;
  const url = box.dataset.paymentPoll;
  const success = document.querySelector('[data-pay-success]');
  const pending = document.querySelector('[data-pay-pending]');
  const text = box.querySelector('[data-pay-text]');
  const INTERVAL_MS = 4000;
  const GIVE_UP_MS = 20 * 60 * 1000;
  const started = Date.now();
  let timer = null;

  function paid() {
    if (pending) pending.hidden = true;
    if (success) {
      success.hidden = false;
      success.classList.add('is-celebrating');
      success.setAttribute('tabindex', '-1');
      success.focus({ preventScroll: false });
    }
    document.dispatchEvent(new CustomEvent('hep:paid'));
  }

  async function tick() {
    if (document.hidden) { timer = setTimeout(tick, INTERVAL_MS); return; }
    try {
      const res = await fetch(url, { headers: { Accept: 'application/json' }, cache: 'no-store', credentials: 'same-origin' });
      if (res.ok) {
        const data = await res.json();
        if (data.paid) { paid(); return; }
        if (data.state === 'cancelled') {
          // Staff or the hold timer cancelled the order while this page was open: stop inviting a transfer.
          // Hide the QR and transfer details but keep this status box (it lives inside the pending block).
          if (pending) [...pending.children].forEach((el) => { if (!el.contains(box)) el.hidden = true; });
          box.classList.add('is-cancelled');
          if (text) text.textContent = 'Đơn này vừa bị hủy. Đừng chuyển tiền cho mã đơn này; muốn mua lại hãy đặt đơn mới.';
          return;
        }
      }
    } catch (_) { /* network blip: try again next tick */ }
    if (Date.now() - started > GIVE_UP_MS) {
      if (text) text.textContent = 'Chưa thấy tiền về sau 20 phút. Nếu bạn đã chuyển, tải lại trang hoặc nhắn Hép kèm mã đơn.';
      return;
    }
    timer = setTimeout(tick, INTERVAL_MS);
  }
  timer = setTimeout(tick, 1500);
  window.addEventListener('pagehide', () => timer && clearTimeout(timer));
})();
