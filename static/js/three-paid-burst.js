// paid-burst: mưa sách 3D và cánh hoa bung từ khối "Thanh toán thành công" (05_designer_three_spec.md mục 2.3).
// Chuẩn bị trước bằng prepareThree; khi hep:paid tới mới tạo renderer qua three-stage.js, nổ một lần rồi tự huỷ.
// Lỗi khi đang nổ: phát hep:burst-fallback để celebrate.js mưa sách DOM thay.
import { mountStage, prepareThree, tokenColor, petalGeometry, petalPalette, paperLights } from './three-stage.js';

const ROOT = document.documentElement;
const DEG = Math.PI / 180;
const START_MS = 520;
const FADE_FROM = 0.9;
const END_S = 1.2;
const TONES = ['--navy', '--orange', '--surface-2'];
const rand = (lo, hi) => lo + Math.random() * (hi - lo);

/** Vận tốc bắn lên theo góc trong [-160°, -20°] (toạ độ màn hình). @param {number} lo tốc độ nhỏ nhất @param {number} hi lớn nhất @returns {number[]} [vx, vy] với y hướng lên */
function shoot(lo, hi) {
  const a = rand(-160, -20) * DEG; const sp = rand(lo, hi);
  return [Math.cos(a) * sp, -Math.sin(a) * sp];
}

/** Trạng thái đầu các vật thể. @param {number} n số vật @param {object} o tâm nổ {x, y, spread} @param {boolean} isBook sách hay cánh hoa @returns {object[]} */
function particles(n, o, isBook) {
  return Array.from({ length: n }, () => {
    const [vx, vy] = isBook ? shoot(420, 900) : shoot(200, 480);
    const w = () => rand(4, 12) * (Math.random() < 0.5 ? -1 : 1);
    return { x: o.x + rand(-o.spread, o.spread), y: o.y, vx, vy, rx: 0, ry: 0, rz: 0, wx: w(), wy: w(), wz: w(), ph: rand(0, 6.28) };
  });
}

/** Một bước vật lý cho một nhóm và ghi ma trận instance. @param {object} mesh @param {object[]} list @param {object} cfg {g, drag, sway, scale} @param {number} dt @param {number} te @param {object} dummy @returns void */
function step(mesh, list, cfg, dt, te, dummy) {
  list.forEach((p, i) => {
    if (cfg.drag) { const f = Math.exp(-cfg.drag * dt); p.vx *= f; p.vy *= f; }
    p.vy -= cfg.g * dt; p.x += p.vx * dt; p.y += p.vy * dt;
    p.rx += p.wx * dt * cfg.spin; p.ry += p.wy * dt * cfg.spin; p.rz += p.wz * dt * cfg.spin;
    dummy.position.set(p.x + (cfg.sway ? cfg.sway * Math.sin(te * 6 + p.ph) : 0), p.y, 0);
    dummy.rotation.set(p.rx, p.ry, p.rz);
    dummy.scale.setScalar(cfg.scale);
    dummy.updateMatrix();
    mesh.setMatrixAt(i, dummy.matrix);
  });
  mesh.instanceMatrix.needsUpdate = true;
}

/** Dựng cảnh nổ theo đơn vị CSS px. @param {object} THREE @param {object} ctx {scene, el, mobile} @param {number} t0 mốc sự kiện (performance.now) @returns {object} api cảnh */
function buildBurst(THREE, { scene, el, mobile }, t0) {
  const w = el.clientWidth; const h = el.clientHeight;
  const camera = new THREE.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, -1000, 1000);
  paperLights(THREE, scene);
  const box = document.querySelector('[data-pay-success]').getBoundingClientRect();
  const o = { x: box.left + box.width / 2 - w / 2, y: h / 2 - box.top, spread: box.width * 0.4 };
  const bookGeo = new THREE.BoxGeometry(18, 24, 5); const petalGeo = petalGeometry(THREE);
  const bookMat = new THREE.MeshStandardMaterial({ roughness: 0.75, metalness: 0, transparent: true });
  const petalMat = new THREE.MeshStandardMaterial({ roughness: 0.8, metalness: 0, side: THREE.DoubleSide, forceSinglePass: true, transparent: true });
  const books = new THREE.InstancedMesh(bookGeo, bookMat, mobile ? 20 : 36);
  const petals = new THREE.InstancedMesh(petalGeo, petalMat, mobile ? 30 : 60);
  const mix = petalPalette(THREE);
  for (let i = 0; i < books.count; i += 1) books.setColorAt(i, tokenColor(THREE, TONES[i % TONES.length]));
  for (let i = 0; i < petals.count; i += 1) petals.setColorAt(i, mix(rand(0.15, 0.45)));
  [books, petals].forEach((m) => { m.frustumCulled = false; m.visible = false; scene.add(m); });
  const bookList = particles(books.count, o, true); const petalList = particles(petals.count, o, false);
  const dummy = new THREE.Object3D();
  return {
    camera,
    resize(nw, nh) { Object.assign(camera, { left: -nw / 2, right: nw / 2, top: nh / 2, bottom: -nh / 2 }); camera.updateProjectionMatrix(); },
    update(t, dt) {
      const te = (performance.now() - t0 - START_MS) / 1000;
      if (te < 0) return true;
      books.visible = true; petals.visible = true;
      step(books, bookList, { g: 1400, spin: 1, scale: 1 }, dt, te, dummy);
      step(petals, petalList, { g: 260, drag: 1.8, sway: 40, spin: 0.6, scale: 14 }, dt, te, dummy);
      const f = Math.max(0, Math.min(1, (te - FADE_FROM) / (END_S - FADE_FROM)));
      bookMat.opacity = 1 - (1 - (1 - f) ** 2); petalMat.opacity = bookMat.opacity;
      return te < END_S;
    },
    dispose() { [bookGeo, petalGeo, bookMat, petalMat].forEach((x) => x.dispose()); books.dispose(); petals.dispose(); },
  };
}

const el = document.querySelector('.three-burst[data-three-scene="paid-burst"]');
let fired = false;
/** Báo celebrate.js mưa sách DOM thay. @returns void */
const fallback = () => document.dispatchEvent(new CustomEvent('hep:burst-fallback'));

if (el) {
  const idle = window.requestIdleCallback || ((cb) => setTimeout(cb, 300));
  idle(() => prepareThree(el).then((THREE) => {
    if (THREE && !fired) ROOT.dataset.threeBurst = 'ready';
  }));
  document.addEventListener('hep:paid', () => {
    if (fired) return;
    fired = true;
    if (ROOT.dataset.threeBurst !== 'ready') return;
    const t0 = performance.now();
    mountStage(el, (THREE, ctx) => buildBurst(THREE, ctx, t0), { lazy: false, once: true, maxDpr: [1.25, 1], onFail: fallback });
  });
}
