// three-stage: khung chung cho mọi cảnh 3D của shop (references/threejs-recipes.md mục 4).
// Kiểm điều kiện tắt, nạp lười three vendor, quản lý renderer, vòng lặp, dừng khi không thấy, dọn dẹp.
// Trạng thái ghi lên khung: data-three idle/loading/ready/on/off/done, data-three-reason, data-three-running.
const ROOT = document.documentElement;
const MAX_CANVAS = 2;
const IDLE_FALLBACK_MS = 300;
const DT_MAX = 0.05;
const QUIET_MS = 8000;
const DARK = matchMedia('(prefers-color-scheme: dark)');
let warned = false;
let canvasCount = 0;
let threePromise = null;
const stages = new WeakMap();

/** Ghi cảnh báo [hep-3d] đúng một lần mỗi trang. @param {...*} args nội dung @returns void */
export function warn(...args) { if (!warned) { warned = true; console.warn('[hep-3d]', ...args); } }

import { pointer, readInput } from './three-input.js';

export { readToken, tokenRgba, isDarkTheme, tokenColor, petalGeometry, petalPalette, paperLights } from './three-paint.js';

/** Điều kiện tắt kiểm trước mọi import. @returns {string|null} lý do hoặc null */
function offReason() {
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return 'reduced-motion';
  if (ROOT.classList.contains('motion-off')) return 'motion-off';
  if (navigator.connection && navigator.connection.saveData) return 'save-data';
  if ((navigator.hardwareConcurrency || 4) <= 2) return 'low-cpu';
  return null;
}

/** Đặt trạng thái tắt lên khung. @param {HTMLElement} el @param {string} reason @returns null */
function setOff(el, reason) { el.dataset.three = 'off'; el.dataset.threeReason = reason; el.dataset.threeRunning = '0'; return null; }

/** Chờ khung sắp vào khung nhìn (rootMargin 200px) rồi chờ lúc rảnh. @param {HTMLElement} el @returns {Promise<void>} */
function whenNearAndIdle(el) {
  return new Promise((resolve) => {
    const io = new IntersectionObserver((es) => {
      if (!es.some((e) => e.isIntersecting)) return;
      io.disconnect();
      if (window.requestIdleCallback) requestIdleCallback(() => resolve(), { timeout: 1200 });
      else setTimeout(resolve, IDLE_FALLBACK_MS);
    }, { rootMargin: '200px' });
    io.observe(el);
  });
}

/** Thử WebGL bằng canvas tạm rồi trả context. @returns {boolean} */
function hasWebGL() {
  try {
    const c = document.createElement('canvas');
    const gl = c.getContext('webgl2') || c.getContext('webgl');
    if (!gl) return false;
    const lose = gl.getExtension('WEBGL_lose_context'); if (lose) lose.loseContext();
    return true;
  } catch (_) { return false; }
}

/** Kiểm điều kiện, nạp lười three và thử WebGL. @param {HTMLElement} el @param {{lazy?:boolean}} opts @returns {Promise<object|null>} THREE hoặc null */
async function acquire(el, opts) {
  const reason = offReason();
  if (reason) return setOff(el, reason);
  el.dataset.three = 'loading';
  try {
    if (opts.lazy !== false) await whenNearAndIdle(el);
    threePromise = threePromise || import(window.HEP_THREE_URL);
    const THREE = await threePromise;
    if (!hasWebGL()) { warn('no-webgl'); return setOff(el, 'no-webgl'); }
    return THREE;
  } catch (err) { warn('import', err); return setOff(el, 'error'); }
}

/** Chuẩn bị cho cảnh chạy một lần (paid-burst): nạp three, thử WebGL, không tạo renderer. @param {HTMLElement} el @returns {Promise<object|null>} */
export async function prepareThree(el) {
  const THREE = await acquire(el, { lazy: false });
  if (THREE) el.dataset.three = 'ready';
  return THREE;
}

/** Gắn cảnh vào khung. @param {HTMLElement} el khung [data-three] @param {function} buildScene (THREE, ctx) => {update(t,dt,input)→boolean, dispose(), onTheme?, resize?, degrade?, camera?} @param {{lazy?:boolean, once?:boolean, maxDpr?:number[], onFail?:function}} opts @returns {Promise<object|null>} */
export async function mountStage(el, buildScene, opts = {}) {
  const THREE = await acquire(el, opts);
  if (!THREE) { if (opts.onFail) opts.onFail(); return null; }
  if (ROOT.classList.contains('motion-off')) { if (opts.onFail) opts.onFail(); return setOff(el, 'motion-off'); }
  if (canvasCount >= MAX_CANVAS) { if (opts.onFail) opts.onFail(); return setOff(el, 'canvas-limit'); }
  const st = { el, opts, THREE, mobile: matchMedia('(max-width: 767px)').matches, alive: true };
  const first = !stages.has(el);
  stages.set(el, st);
  try { await startStage(st, buildScene); } catch (err) { failStage(st, 'error', err); return null; }
  if (first && !opts.once) {
    window.addEventListener('pagehide', () => { const cur = stages.get(el); if (cur.alive) { teardown(cur); el.dataset.three = 'idle'; } });
    window.addEventListener('pageshow', (e) => { if (e.persisted && !stages.get(el).alive) mountStage(el, buildScene, opts); });
  } else if (first) window.addEventListener('pagehide', () => teardown(st));
  return st;
}

/** Tạo renderer, dựng cảnh, gắn quan sát và chạy vòng lặp. @param {object} st trạng thái stage @param {function} buildScene @returns {Promise<void>} */
async function startStage(st, buildScene) {
  const { THREE, el, opts } = st;
  const renderer = st.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'low-power' });
  canvasCount += 1;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.setClearColor(0, 0);
  const canvas = renderer.domElement; canvas.setAttribute('aria-hidden', 'true');
  st.onLost = (e) => { e.preventDefault(); failStage(st, 'context-lost'); };
  canvas.addEventListener('webglcontextlost', st.onLost);
  el.prepend(canvas);
  st.scene = new THREE.Scene();
  st.camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
  st.api = await buildScene(THREE, { scene: st.scene, camera: st.camera, renderer, el, mobile: st.mobile });
  if (!st.alive) return;
  st.camera = st.api.camera || st.camera;
  st.dpr = Math.min(devicePixelRatio || 1, (opts.maxDpr || [1.75, 1.25])[st.mobile ? 1 : 0]);
  resize(st);
  st.ro = new ResizeObserver(() => resize(st)); st.ro.observe(el); st.visible = true;
  st.io = new IntersectionObserver((es) => { st.visible = es[es.length - 1].isIntersecting; syncPlay(st); }, { threshold: 0 });
  st.io.observe(el);
  st.onVis = () => syncPlay(st); document.addEventListener('visibilitychange', st.onVis);
  st.onTheme = () => { if (st.api.onTheme) st.api.onTheme(); };
  DARK.addEventListener('change', st.onTheme);
  st.mo = new MutationObserver(st.onTheme); st.mo.observe(ROOT, { attributes: true, attributeFilter: ['data-theme'] });
  Object.assign(st, { t: 0, last: 0, frames: 0, slowSum: 0, slowStage: 0, lastScroll: scrollY, quietAt: performance.now() });
  syncPlay(st);
}

/** Đặt kích thước canvas theo khung và DPR. @param {object} st @returns void */
function resize(st) {
  const w = Math.max(1, st.el.clientWidth); const h = Math.max(1, st.el.clientHeight);
  st.renderer.setPixelRatio(st.dpr);
  st.renderer.setSize(w, h, false);
  if (st.camera.isPerspectiveCamera) { st.camera.aspect = w / h; st.camera.updateProjectionMatrix(); }
  if (st.api.resize) st.api.resize(w, h);
}

/** Chạy hoặc dừng vòng lặp theo việc khung có thấy được. @param {object} st @returns void */
function syncPlay(st) {
  if (!st.alive) return;
  const run = st.visible && !document.hidden;
  if (run === st.running) return;
  st.running = run; st.last = 0;
  st.renderer.setAnimationLoop(run ? (now) => frame(st, now) : null);
  st.el.dataset.threeRunning = run ? '1' : '0';
}

/** Một khung hình: cập nhật cảnh, vẽ, gác FPS, tiết kiệm khi yên. @param {object} st @param {number} now @returns void */
function frame(st, now) {
  try {
    const dt = st.last ? Math.min((now - st.last) / 1000, DT_MAX) : 1 / 60;
    if (pointer.at > st.quietAt || scrollY !== st.lastScroll) st.quietAt = now;
    st.lastScroll = scrollY;
    st.frames += 1;
    if (now - st.quietAt > QUIET_MS && st.frames % 2) return;
    if (st.last) guardFps(st, now - st.last);
    st.last = now;
    st.t += dt;
    const keep = st.api.update(st.t, dt, readInput(st.el));
    st.renderer.render(st.scene, st.camera);
    if (st.el.dataset.three !== 'on') {
      st.el.dataset.three = 'on';
      st.el.dataset.threeTris = String(st.renderer.info.render.triangles);
      st.renderer.domElement.classList.add('is-shown');
    }
    if (keep === false && st.opts.once) { teardown(st); st.el.dataset.three = 'done'; }
  } catch (err) { failStage(st, 'error', err); }
}

/** Gác FPS: khung 30..90 trung bình > 34ms thì hạ cấp, 60 khung sau vẫn > 50ms thì tắt. @param {object} st @param {number} ms @returns void */
function guardFps(st, ms) {
  if (st.opts.once || st.slowStage > 1 || st.frames < 30) return;
  st.slowSum += ms;
  const n = st.frames - 29;
  if (st.slowStage === 0 && n >= 60) {
    if (st.slowSum / n > 34) {
      st.dpr = 1; resize(st); st.el.dataset.threeSlow = '1';
      if (st.api.degrade) st.api.degrade();
      Object.assign(st, { slowStage: 1, slowSum: 0, frames: 29 });
    } else st.slowStage = 2;
  } else if (st.slowStage === 1 && n >= 60) {
    if (st.slowSum / n > 50) failStage(st, 'slow'); else st.slowStage = 2;
  }
}

/** Tắt giữa chừng: dọn dẹp, fallback hiện lại. @param {object} st @param {string} reason @param {*} [err] @returns void */
function failStage(st, reason, err) {
  if (!st.alive) return;
  warn(reason, err || '');
  teardown(st);
  setOff(st.el, reason);
  if (st.opts.onFail) st.opts.onFail();
}

/** Dừng vòng lặp, dispose cảnh và renderer, gỡ canvas. @param {object} st @returns void */
function teardown(st) {
  if (!st.alive) return;
  st.alive = false;
  st.el.dataset.threeRunning = '0';
  [st.io, st.ro, st.mo].forEach((o) => o && o.disconnect());
  document.removeEventListener('visibilitychange', st.onVis);
  DARK.removeEventListener('change', st.onTheme);
  const r = st.renderer;
  if (!r) return;
  r.setAnimationLoop(null);
  try { if (st.api) st.api.dispose(); } catch (_) { /* dispose lỗi vẫn gỡ canvas */ }
  r.domElement.removeEventListener('webglcontextlost', st.onLost);
  r.dispose();
  r.domElement.remove();
  canvasCount -= 1;
}
