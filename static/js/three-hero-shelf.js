// hero-shelf: chồng sách 3D ở cột phải hero trang chủ (05_designer_three_spec.md mục 2.1).
// Tên sách lấy từ textContent của thẻ sách trên trang; fallback .hero-stack luôn nằm trong DOM.
import { mountStage, readToken, tokenColor, tokenRgba, paperLights } from './three-stage.js';

const DEG = Math.PI / 180;
// slot: x, y, z, rotX, rotY, rotZ (độ), dày, token bìa, token chữ
const SLOTS = [
  [-1.05, -0.35, 0.4, 0, 18, -8, 0.22, '--navy', '--on-navy'],
  [0.0, -0.55, 0.9, 0, -6, 5, 0.26, '--orange', '--on-orange'],
  [1.05, -0.2, 0.3, 0, -22, 12, 0.2, '--surface-2', '--ink'],
  [-1.35, 0.95, -0.6, 0, 30, -16, 0.18, '--navy-deep', '--on-navy'],
  [1.4, 1.0, -0.9, 0, -35, 20, 0.24, '--orange-ink', '--on-navy'],
  [-1.55, -1.05, -1.4, 72, 0, 8, 0.2, '--surface-2', '--ink'],
  [1.55, -1.05, -0.8, 80, 0, -14, 0.28, '--navy', '--on-navy'],
];
const ENTRY_ORDER = [3, 5, 0, 1, 2, 4, 6];
const ENTRY_MS = 720;
const ENTRY_STEP_MS = 90;
const DEFAULTS = [['Đọc chậm', 'ゆっくり読む', ''], ['Học tiếng Nhật', '日本語', ''], ['Sách Nhật', '本が好き', '']];

/** Dữ liệu sách từ thẻ nổi bật, thiếu thì lấp bằng bìa mặc định. @param {number} n số cuốn @returns {object[]} */
function readBooks(n) {
  const text = (root, sel) => { const x = root.querySelector(sel); return x ? x.textContent.trim() : ''; };
  const cards = [...document.querySelectorAll('.picks .book-grid > .book-card')].slice(0, n).map((c) => {
    const img = c.querySelector('.cover-link img.book-cover-upload');
    return { vi: text(c, '.book-details h3 a'), ja: text(c, '.cover-link .book-cover small[lang="ja"]') || '日本の本', cat: text(c, '.book-cat'), src: img ? img.src : '' };
  });
  const stack = [...document.querySelectorAll('.hero-stack .stack-cover .book-cover')].map((b) => [text(b, 'strong'), text(b, 'small'), '']);
  const fill = stack.length ? stack : DEFAULTS;
  for (let i = 0; cards.length < n; i += 1) { const f = fill[i % fill.length]; cards.push({ vi: f[0], ja: f[1], cat: f[2], src: '' }); }
  return cards;
}

/** Xuống dòng theo từ, tối đa 3 dòng, dòng cuối cắt thêm "…". @param {CanvasRenderingContext2D} ctx @param {string} s @param {number} maxW @returns {string[]} */
function wrapLines(ctx, s, maxW) {
  const lines = [];
  let cur = '';
  for (const w of s.split(/\s+/)) {
    const next = cur ? `${cur} ${w}` : w;
    if (ctx.measureText(next).width <= maxW || !cur) cur = next; else { lines.push(cur); cur = w; }
  }
  if (cur) lines.push(cur);
  if (lines.length <= 3) return lines;
  let last = lines[2];
  while (last && ctx.measureText(`${last}…`).width > maxW) last = last.slice(0, -1);
  return [lines[0], lines[1], `${last.trim()}…`];
}

/** Vẽ chữ bìa lên canvas 2D. @param {HTMLCanvasElement} cv @param {object} book @param {string[]} slot @param {boolean} mobile @returns void */
function paintCover(cv, book, slot, mobile) {
  const ctx = cv.getContext('2d');
  const W = cv.width; const H = cv.height; const k = mobile ? 2 / 3 : 1;
  const ink = readToken(slot[8]);
  ctx.fillStyle = readToken(slot[7]); ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = 0.35; ctx.strokeStyle = ink; ctx.lineWidth = 3; const m = mobile ? 12 : 18; ctx.strokeRect(m, m, W - 2 * m, H - 2 * m);
  ctx.fillStyle = ink; ctx.textBaseline = 'top'; const x = 28 * k;
  ctx.globalAlpha = 0.8; ctx.font = `600 ${Math.round(22 * k)}px "Be Vietnam Pro", sans-serif`; ctx.fillText('hép bookstore', x, 28 * k);
  ctx.globalAlpha = 1; const fs = Math.round(46 * k); ctx.font = `700 ${fs}px "Baloo 2", sans-serif`;
  wrapLines(ctx, book.vi, W - 2 * x).forEach((ln, i) => ctx.fillText(ln, x, H * 0.38 + i * fs * 1.05));
  ctx.textBaseline = 'alphabetic'; ctx.font = `500 ${Math.round(26 * k)}px "Zen Maru Gothic", sans-serif`; ctx.fillText(book.ja, x, H - 40 * k);
  if (book.cat) { ctx.globalAlpha = 0.7; ctx.font = `600 ${Math.round(18 * k)}px "Be Vietnam Pro", sans-serif`; ctx.fillText(book.cat.toUpperCase(), x, H - 40 * k - 34 * k); }
  ctx.globalAlpha = 1;
}

/** Ảnh bìa thật (cùng nguồn) vẽ kiểu cover-fit đè lên chữ khi tải xong. @param {HTMLCanvasElement} cv @param {string} src @param {object} tex @returns void */
function overlayImage(cv, src, tex) {
  const img = new Image();
  img.onload = () => {
    const iw = img.naturalWidth || cv.width; const ih = img.naturalHeight || cv.height;
    const s = Math.max(cv.width / iw, cv.height / ih);
    cv.getContext('2d').drawImage(img, (cv.width - iw * s) / 2, (cv.height - ih * s) / 2, iw * s, ih * s);
    tex.needsUpdate = true;
  };
  img.src = src;
}

/** Chờ font thương hiệu tối đa 1500ms. @returns {Promise<void>} */
function fontsReady() {
  const load = document.fonts ? Promise.all([document.fonts.load('700 46px "Baloo 2"'), document.fonts.load('500 26px "Zen Maru Gothic"')]) : Promise.resolve();
  return Promise.race([load.catch(() => {}), new Promise((r) => setTimeout(r, 1500))]);
}

/** Geometry dùng chung: vỏ bo góc, ruột, mặt bìa, bóng. @param {object} THREE @returns {object} */
function sharedGeometry(THREE) {
  const s = new THREE.Shape(); const w = 0.5; const h = 0.71; const r = 0.04;
  s.moveTo(-w + r, -h); s.lineTo(w - r, -h); s.quadraticCurveTo(w, -h, w, -h + r); s.lineTo(w, h - r);
  s.quadraticCurveTo(w, h, w - r, h); s.lineTo(-w + r, h); s.quadraticCurveTo(-w, h, -w, h - r); s.lineTo(-w, -h + r); s.quadraticCurveTo(-w, -h, -w + r, -h);
  const shell = new THREE.ExtrudeGeometry(s, { depth: 1, bevelEnabled: false, curveSegments: 3 }).translate(0, 0, -0.5);
  return { shell, pages: new THREE.BoxGeometry(0.96, 1.36, 1), face: new THREE.PlaneGeometry(0.96, 1.38), shadow: new THREE.PlaneGeometry(4.2, 1.4) };
}

/** Bóng đổ giả bằng texture radial-gradient navy. @param {object} THREE @param {object} geo @returns {object} mesh */
function fakeShadow(THREE, geo) {
  const cv = document.createElement('canvas'); cv.width = 128; cv.height = 64;
  const ctx = cv.getContext('2d'); const g = ctx.createRadialGradient(64, 32, 0, 64, 32, 64);
  g.addColorStop(0, tokenRgba('--navy', 0.22)); g.addColorStop(1, tokenRgba('--navy', 0));
  ctx.fillStyle = g; ctx.fillRect(0, 0, 128, 64);
  const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace;
  const mesh = new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false }));
  mesh.rotation.x = -Math.PI / 2; mesh.position.y = -1.45;
  return mesh;
}

/** Dựng một cuốn sách 3 mesh theo slot. @param {object} THREE @param {object} geo @param {string[]} slot @param {object} tex @returns {object} group */
function makeBook(THREE, geo, slot, tex) {
  const d = slot[6]; const book = new THREE.Group();
  const shell = new THREE.Mesh(geo.shell, new THREE.MeshStandardMaterial({ color: tokenColor(THREE, slot[7]), roughness: 0.78, metalness: 0 }));
  shell.scale.z = d;
  const pages = new THREE.Mesh(geo.pages, new THREE.MeshStandardMaterial({ color: tokenColor(THREE, '--surface'), roughness: 0.85, metalness: 0 }));
  pages.scale.z = d - 0.03; pages.position.x = 0.04;
  const face = new THREE.Mesh(geo.face, new THREE.MeshStandardMaterial({ map: tex, roughness: 0.7, metalness: 0 }));
  face.position.z = d / 2 + 0.002;
  book.add(shell, pages, face);
  return book;
}

/** easeOutBack hệ số 1.56. @param {number} x 0..1 @returns {number} */
const easeBack = (x) => { const c1 = 1.56; const c3 = c1 + 1; return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2; };
/** Giảm chấn mũ. @param {number} cur @param {number} target @param {number} k @param {number} dt @returns {number} */
const damp = (cur, target, k, dt) => cur + (target - cur) * (1 - Math.exp(-k * dt));

/** Dựng cảnh hero-shelf. @param {object} THREE @param {object} ctx {scene, camera, renderer, el, mobile} @returns {Promise<object>} api cảnh */
async function buildShelf(THREE, { scene, camera, renderer, mobile }) {
  await fontsReady();
  const n = mobile ? 5 : 7; const books = readBooks(n); const geo = sharedGeometry(THREE);
  camera.fov = 28; camera.position.set(0, 0, mobile ? 7 : 9); camera.lookAt(0, 0, 0);
  paperLights(THREE, scene);
  const group = new THREE.Group(); scene.add(group);
  if (mobile) { group.scale.setScalar(0.8); group.position.y = -0.45; }
  group.add(fakeShadow(THREE, geo.shadow));
  const aniso = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  const items = SLOTS.slice(0, n).map((slot, i) => {
    const cv = document.createElement('canvas'); cv.width = mobile ? 256 : 384; cv.height = mobile ? 384 : 576;
    const tex = new THREE.CanvasTexture(cv); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = aniso;
    const mesh = makeBook(THREE, geo, slot, tex); mesh.visible = false; group.add(mesh);
    const dir = new THREE.Vector3(slot[0], slot[1], 0.4).normalize();
    return { slot, i, cv, tex, mesh, dir, book: books[i], painted: false, lift: 0, turn: 0, delay: ENTRY_ORDER.indexOf(i) * ENTRY_STEP_MS };
  });
  return shelfApi(THREE, { group, items, geo, camera, mobile, hero: document.querySelector('.hero') });
}

/** Tư thế một cuốn mỗi khung: rơi vào, lơ lửng, tách khi cuộn, nhấc khi con trỏ gần. @param {object} it @param {number} ms thời gian từ khi vào cảnh @param {number} t giây @param {number} s tỉ lệ cuộn @returns void */
function poseBook(it, ms, t, s) {
  const [x, y, z, rx, ry, rz] = it.slot; const m = it.mesh;
  const p = Math.max(0, Math.min(1, (ms - it.delay) / ENTRY_MS)); const e = easeBack(p);
  m.visible = ms >= it.delay;
  const P = 4.2 + 0.37 * it.i;
  const fall = 1 - e;
  m.position.set(x + it.dir.x * 0.9 * s, y + 1.4 * fall + 0.05 * Math.sin((2 * Math.PI * t) / P + it.i) + it.dir.y * 0.9 * s, z + it.dir.z * 0.9 * s + 0.25 * it.lift);
  const rot = rz + 20 * fall + 1.2 * Math.sin((2 * Math.PI * t) / (1.3 * P)) + Math.sign(rz) * 14 * s;
  m.rotation.set(rx * DEG, (ry + 8 * it.turn) * DEG, rot * DEG);
  m.scale.setScalar(0.85 + 0.15 * e);
}

/** API cảnh hero-shelf cho stage. @param {object} THREE @param {object} c ngữ cảnh đã dựng @returns {object} */
function shelfApi(THREE, c) {
  let heroH = c.hero ? c.hero.offsetHeight : 600; let painted = 0;
  const v = new THREE.Vector3();
  return {
    resize() { heroH = c.hero ? c.hero.offsetHeight : heroH; },
    update(t, dt, input) {
      const next = c.items.find((it) => !it.painted);
      if (next) { paintCover(next.cv, next.book, next.slot, c.mobile); if (next.book.src) overlayImage(next.cv, next.book.src, next.tex); next.tex.needsUpdate = true; next.painted = true; painted += 1; }
      if (painted < c.items.length) return true;
      c.start = c.start === undefined ? t : c.start;
      const ms = (t - c.start) * 1000; const s = Math.max(0, Math.min(1, input.scrollY / (0.9 * heroH)));
      const usePtr = input.fine && input.active;
      const ty = usePtr ? input.pointer.x * 14 * DEG : (input.fine ? 0 : 6 * DEG * Math.sin((2 * Math.PI * t) / 9));
      c.group.rotation.y = usePtr || input.fine ? damp(c.group.rotation.y, ty, 6, dt) : ty;
      c.group.rotation.x = damp(c.group.rotation.x, usePtr ? input.pointer.y * 8 * DEG : 0, 6, dt);
      c.group.position.y = (c.mobile ? -0.45 : 0) + 0.6 * s;
      let near = null; let best = Infinity;
      if (usePtr && input.pointer.inside) {
        c.items.forEach((it) => { it.mesh.getWorldPosition(v).project(c.camera); it.px = v.x; const d = (v.x - input.pointer.x) ** 2 + (v.y + input.pointer.y) ** 2; if (d < best) { best = d; near = it; } });
      }
      c.items.forEach((it) => {
        it.lift = damp(it.lift, it === near ? 1 : 0, 10, dt);
        if (it === near) it.turn = damp(it.turn, Math.sign(input.pointer.x - it.px) || 0, 10, dt); else it.turn = damp(it.turn, 0, 10, dt);
        poseBook(it, ms, t, s);
      });
      return true;
    },
    dispose() {
      Object.values(c.geo).forEach((g) => g.dispose());
      c.group.traverse((o) => { if (o.material) { if (o.material.map) o.material.map.dispose(); o.material.dispose(); } });
    },
  };
}

const el = document.querySelector('.hero-art[data-three-scene="hero-shelf"]');
if (el) mountStage(el, buildShelf, { lazy: true, maxDpr: [1.75, 1.25] });
