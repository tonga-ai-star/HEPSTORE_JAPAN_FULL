// Progressive enhancement only. No client-side prices are authoritative.
'use strict';
(() => {
  const CONFIRM_WINDOW_MS = 4000;
  const TOAST_MS = 3500;
  const TOAST_OUT_MS = 250;
  const SIDEBAR_KEY = 'hep-sidebar';
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /** Vùng đọc cho trình đọc màn hình, dùng chung cho xác nhận hai lần bấm. */
  const liveRegion = () => {
    let el = document.getElementById('hep-live');
    if (!el) {
      el = document.createElement('div');
      el.id = 'hep-live';
      el.className = 'sr-only';
      el.setAttribute('aria-live', 'polite');
      document.body.appendChild(el);
    }
    return el;
  };

  /** Toast góc dưới phải, tự ẩn sau 3.5s. Thay cho hộp thoại trình duyệt. */
  const toast = (message) => {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      stack.setAttribute('role', 'status');
      stack.setAttribute('aria-live', 'polite');
      document.body.appendChild(stack);
    }
    const item = document.createElement('div');
    item.className = 'toast';
    item.textContent = String(message);
    stack.appendChild(item);
    setTimeout(() => {
      item.classList.add('is-out');
      setTimeout(() => item.remove(), reduce ? 0 : TOAST_OUT_MS);
    }, TOAST_MS);
  };
  window.hepToast = toast;

  /** Xác nhận hai lần bấm: lần 1 đổi chữ nút thành câu cảnh báo, lần 2 trong 4s mới thực hiện. Thay cho hộp xác nhận trình duyệt. */
  const disarm = (el) => {
    clearTimeout(Number(el.dataset.confirmTimer));
    if (el.dataset.confirmLabel !== undefined) el.innerHTML = el.dataset.confirmLabel;
    delete el.dataset.confirmLabel;
    delete el.dataset.confirmTimer;
    el.classList.remove('is-armed');
  };
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-confirm]');
    if (!el) return;
    if (el.classList.contains('is-armed')) {
      clearTimeout(Number(el.dataset.confirmTimer));
      return;
    }
    e.preventDefault();
    el.dataset.confirmLabel = el.innerHTML;
    el.textContent = el.dataset.confirm;
    el.classList.add('is-armed');
    liveRegion().textContent = el.dataset.confirm;
    el.dataset.confirmTimer = String(setTimeout(() => disarm(el), CONFIRM_WINDOW_MS));
  });
  window.addEventListener('pageshow', () => document.querySelectorAll('[data-confirm].is-armed').forEach(disarm));

  /** Thanh bên quản trị thu gọn được, nhớ trạng thái qua localStorage. */
  const shell = document.querySelector('[data-shell]');
  const toggle = document.querySelector('[data-sidebar-toggle]');
  if (shell && toggle) {
    const apply = (collapsed) => {
      shell.classList.toggle('is-collapsed', collapsed);
      toggle.setAttribute('aria-expanded', String(!collapsed));
      const label = collapsed ? 'Mở rộng thanh bên' : 'Thu gọn thanh bên';
      toggle.setAttribute('aria-label', label);
      toggle.title = label;
    };
    let saved = false;
    try { saved = localStorage.getItem(SIDEBAR_KEY) === 'collapsed'; } catch (_) { saved = false; }
    apply(saved);
    toggle.addEventListener('click', () => {
      const next = !shell.classList.contains('is-collapsed');
      apply(next);
      try { localStorage.setItem(SIDEBAR_KEY, next ? 'collapsed' : 'open'); } catch (_) { /* bộ nhớ bị chặn: chỉ giữ trong phiên */ }
    });
  }
})();
