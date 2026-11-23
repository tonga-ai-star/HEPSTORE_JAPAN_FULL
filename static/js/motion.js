// Hiệu ứng Hép Bookstore. Chỉ là lớp trang trí: trang vẫn đọc được khi file này lỗi hoặc bị chặn.
// Lớp motion-on/motion-off do script nội tuyến trong <head> đặt (base.html); file này chỉ báo motion-ready.
'use strict';
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const MAX_STAGGER = 8;
  const MAX_TILT_DEG = 8;
  const MAGNET_PX = 10;
  const BEAR_TILT_DEG = 4;
  const BEAR_CURIOUS_DEG = 8;
  const GAZE_X = 2.6;
  const GAZE_Y = 2;
  const GAZE_NEAR_PX = 280;
  const LD_START_MS = 120;
  const LD_STEP_MAX_MS = 24;
  const LD_SPREAD_MS = 500;
  const LD_CHAR_MS = 560;
  const LD_ROT = [-10, 7, -4, 12];
  const FAN_DELAY_MS = 450;
  const FAN_HOLD_MS = 1300;

  /** draw-underline: chèn nét gạch cong vào mọi .scribble (cả khi tắt chuyển động, để vẫn thấy nét). */
  const SCRIBBLE_PATH = 'M2 9 C 20 3, 38 3, 52 7 S 84 12, 98 5';
  const scribbles = () => document.querySelectorAll('.scribble').forEach((el) => {
    if (el.querySelector('svg')) return;
    el.insertAdjacentHTML('beforeend',
      `<svg viewBox="0 0 100 14" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="${SCRIBBLE_PATH}" pathLength="1"/></svg>`);
  });

  // motion-off: do người dùng chọn giảm chuyển động, hoặc do chốt 2.5s trong <head> khi file này tới quá muộn.
  if (reduce || root.classList.contains('motion-off')) { scribbles(); return; }

  const finePointer = (e) => e.pointerType !== 'touch';
  const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

  /** Tách ký tự theo cụm chữ (giữ nguyên dấu tiếng Việt). */
  const graphemes = (text) => {
    if (window.Intl && Intl.Segmenter) return Array.from(new Intl.Segmenter('vi', { granularity: 'grapheme' }).segment(text), (s) => s.segment);
    return Array.from(text.normalize('NFC'));
  };

  /** hero-letter-drop: bọc mỗi từ trong span.ld-w, mỗi ký tự trong span.ld-c; giữ <br>, .scribble và SVG. */
  const splitLetters = (node, chars) => {
    Array.from(node.childNodes).forEach((child) => {
      if (child.nodeType === Node.ELEMENT_NODE) {
        if (child.tagName !== 'BR' && child.tagName.toLowerCase() !== 'svg') splitLetters(child, chars);
        return;
      }
      if (child.nodeType !== Node.TEXT_NODE || !child.textContent.trim()) return;
      const frag = document.createDocumentFragment();
      child.textContent.split(/(\s+)/).forEach((part) => {
        if (!part) return;
        if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(' ')); return; }
        const word = document.createElement('span');
        word.className = 'ld-w';
        word.setAttribute('aria-hidden', 'true');
        graphemes(part).forEach((g) => {
          const c = document.createElement('span');
          c.className = 'ld-c';
          c.textContent = g;
          word.appendChild(c);
          chars.push(c);
        });
        frag.appendChild(word);
      });
      child.replaceWith(frag);
    });
  };
  const letterDrop = () => {
    document.querySelectorAll('[data-letter-drop]').forEach((h) => {
      const label = h.cloneNode(true);
      label.querySelectorAll('br').forEach((br) => br.replaceWith(' '));
      h.setAttribute('aria-label', label.textContent.replace(/\s+/g, ' ').trim());
      const chars = [];
      splitLetters(h, chars);
      const step = Math.min(LD_STEP_MAX_MS, LD_SPREAD_MS / Math.max(1, chars.length));
      chars.forEach((c, i) => {
        c.style.setProperty('--d', `${Math.round(LD_START_MS + i * step)}ms`);
        c.style.setProperty('--r', `${LD_ROT[i % LD_ROT.length]}deg`);
      });
      h.style.setProperty('--ld-end', `${Math.round(LD_START_MS + (chars.length - 1) * step + LD_CHAR_MS * 0.6)}ms`);
      h.classList.add('ld-ready');
      requestAnimationFrame(() => requestAnimationFrame(() => h.classList.add('is-in')));
    });
  };

  /** load-stagger: gán --i cho con trực tiếp rồi bật ở khung hình sau. */
  const stagger = () => {
    document.querySelectorAll('[data-stagger]').forEach((block) => {
      Array.from(block.children).forEach((child, i) => child.style.setProperty('--i', Math.min(i, MAX_STAGGER - 1)));
      requestAnimationFrame(() => requestAnimationFrame(() => block.classList.add('is-in')));
    });
  };

  /** Số cột của khối cha: lưới đọc grid-template-columns, dải flex đếm số ô vừa khung nhìn (rail-stagger). */
  const columnsOf = (parent) => {
    const style = getComputedStyle(parent);
    if (style.display.includes('flex')) {
      const first = parent.firstElementChild;
      return Math.max(1, Math.floor(parent.clientWidth / Math.max(1, first ? first.offsetWidth : 1)));
    }
    const cols = style.gridTemplateColumns;
    return cols && cols !== 'none' ? cols.split(' ').length : 1;
  };

  /** reveal-up + nét gạch + gấu trạng thái rỗng: một IntersectionObserver duy nhất. */
  const reveal = () => {
    const targets = document.querySelectorAll('[data-reveal], .scribble, .empty-state');
    if (!('IntersectionObserver' in window)) {
      targets.forEach((el) => el.classList.add('is-in'));
      return;
    }
    targets.forEach((el) => {
      if (!el.hasAttribute('data-reveal') || !el.parentElement) return;
      const siblings = Array.from(el.parentElement.children).filter((c) => c.hasAttribute('data-reveal'));
      const cols = Math.min(columnsOf(el.parentElement), MAX_STAGGER);
      el.style.setProperty('--i', siblings.indexOf(el) % cols);
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -8% 0px' });
    targets.forEach((el) => io.observe(el));
  };

  /** cover-tilt: nghiêng bìa theo con trỏ, tối đa 8 độ. */
  const tilt = () => {
    document.querySelectorAll('[data-tilt]').forEach((el) => {
      let frame = 0;
      el.addEventListener('pointermove', (e) => {
        if (!finePointer(e)) return;
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          const r = el.getBoundingClientRect();
          const x = (e.clientX - r.left) / r.width;
          const y = (e.clientY - r.top) / r.height;
          el.classList.add('is-tilting');
          el.style.setProperty('--ry', `${((x - 0.5) * 2 * MAX_TILT_DEG).toFixed(2)}deg`);
          el.style.setProperty('--rx', `${((0.5 - y) * 2 * MAX_TILT_DEG).toFixed(2)}deg`);
          el.style.setProperty('--mx', `${(x * 100).toFixed(1)}%`);
          el.style.setProperty('--my', `${(y * 100).toFixed(1)}%`);
        });
      });
      el.addEventListener('pointerleave', () => {
        cancelAnimationFrame(frame);
        el.classList.remove('is-tilting');
        el.style.setProperty('--rx', '0deg');
        el.style.setProperty('--ry', '0deg');
      });
    });
  };

  /** magnetic-btn: nút kéo theo con trỏ tối đa 10px, chữ bên trong kéo thêm. */
  const magnetic = () => {
    document.querySelectorAll('[data-magnetic]').forEach((btn) => {
      if (!btn.querySelector('.mag-inner')) {
        const inner = document.createElement('span');
        inner.className = 'mag-inner';
        while (btn.firstChild) inner.appendChild(btn.firstChild);
        btn.appendChild(inner);
      }
      let frame = 0;
      btn.addEventListener('pointermove', (e) => {
        if (!finePointer(e)) return;
        cancelAnimationFrame(frame);
        frame = requestAnimationFrame(() => {
          const r = btn.getBoundingClientRect();
          const dx = (e.clientX - (r.left + r.width / 2)) / (r.width / 2);
          const dy = (e.clientY - (r.top + r.height / 2)) / (r.height / 2);
          btn.classList.add('is-pulling');
          btn.style.setProperty('--mgx', `${(dx * MAGNET_PX).toFixed(1)}px`);
          btn.style.setProperty('--mgy', `${(dy * MAGNET_PX).toFixed(1)}px`);
        });
      });
      btn.addEventListener('pointerleave', () => {
        cancelAnimationFrame(frame);
        btn.classList.remove('is-pulling');
        btn.style.setProperty('--mgx', '0px');
        btn.style.setProperty('--mgy', '0px');
      });
    });
  };

  /** bear-gaze: một khung hình, đặt hướng mắt (--ex, --ey, đơn vị viewBox) và độ nghiêng đầu. */
  const aimBear = (el, e) => {
    const r = el.getBoundingClientRect();
    const dx = e.clientX - (r.left + r.width / 2);
    const dy = e.clientY - (r.top + r.height * 0.56);
    const dist = Math.hypot(dx, dy) || 1;
    const reach = Math.min(1, dist / GAZE_NEAR_PX);
    const curious = !!(e.target instanceof Element && e.target.closest('.btn-primary, .round-add'));
    const side = clamp(dx / (window.innerWidth / 2), -1, 1);
    el.classList.toggle('is-curious', curious);
    el.classList.remove('is-idle');
    el.style.setProperty('--ex', `${((dx / dist) * GAZE_X * reach).toFixed(2)}px`);
    el.style.setProperty('--ey', `${((dy / dist) * GAZE_Y * reach).toFixed(2)}px`);
    el.style.setProperty('--tilt', `${(curious ? Math.sign(side || 1) * BEAR_CURIOUS_DEG : side * BEAR_TILT_DEG).toFixed(2)}deg`);
  };
  const restBear = (el) => {
    el.classList.add('is-idle');
    el.classList.remove('is-curious');
    ['--ex', '--ey'].forEach((p) => el.style.setProperty(p, '0px'));
    el.style.setProperty('--tilt', '0deg');
  };
  /** bear-gaze: chỉ nghe con trỏ khi gấu nằm trong khung nhìn. */
  const bear = () => {
    const el = document.querySelector('[data-bear]');
    if (!el) return;
    let frame = 0;
    const onMove = (e) => {
      if (!finePointer(e)) return;
      cancelAnimationFrame(frame);
      frame = requestAnimationFrame(() => aimBear(el, e));
    };
    const onOut = (e) => { if (!e.relatedTarget) restBear(el); };
    const listen = (on) => {
      const fn = on ? 'addEventListener' : 'removeEventListener';
      document[fn]('pointermove', onMove, { passive: true });
      document[fn]('pointerout', onOut);
      if (!on) { cancelAnimationFrame(frame); restBear(el); }
    };
    if (!('IntersectionObserver' in window)) { listen(true); return; }
    new IntersectionObserver((entries) => entries.forEach((en) => listen(en.isIntersecting))).observe(el);
  };

  /** hero-fan: chồng bìa xoè ra một nhịp khi trang mở, hover thì CSS lo. */
  const heroFan = () => {
    const art = document.querySelector('.hero-art');
    if (!art) return;
    setTimeout(() => {
      art.classList.add('is-fan');
      setTimeout(() => art.classList.remove('is-fan'), FAN_HOLD_MS);
    }, FAN_DELAY_MS);
  };

  /** cart-bump: số giỏ chỉ nảy khi sách vừa bay vào giỏ (cờ hep-fly); thiếu bộ nhớ phiên thì giữ điều kiện cũ. */
  const cartBump = () => {
    const count = document.querySelector('.site-header .count');
    if (!count || (parseInt(count.textContent, 10) || 0) <= 0) return;
    let flew = null;
    try {
      flew = sessionStorage.getItem('hep-fly') === '1';
      sessionStorage.removeItem('hep-fly');
    } catch (_) { flew = null; }
    const success = !!document.querySelector('.notice.success');
    if (flew === false || !success) return;
    setTimeout(() => count.classList.add('bump'), 300);
    count.addEventListener('animationend', () => count.classList.remove('bump'), { once: true });
  };

  /** Mỗi công thức chạy riêng: một công thức lỗi không kéo theo các công thức khác. */
  const safe = (fn) => { try { fn(); } catch (_) { /* hiệu ứng là phần trang trí */ } };
  safe(letterDrop);
  document.querySelectorAll('[data-letter-drop]').forEach((h) => h.classList.add('ld-ready'));
  safe(scribbles);
  [stagger, reveal, tilt, magnetic, bear, heroFan, cartBump].forEach(safe);
  root.classList.add('motion-ready');
})();
