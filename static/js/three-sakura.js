// sakura-drift: cánh anh đào rơi chậm phía sau hero trang chủ (05_designer_three_spec.md mục 2.2).
// Một InstancedMesh qua three-stage.js; tắt thì hero giữ nền --bg như cũ.
import { mountStage, petalGeometry, petalPalette, paperLights, tokenColor, isDarkTheme } from './three-stage.js';

const rand = (lo, hi) => lo + Math.random() * (hi - lo);
const CAM_Z = 10;
const FOV = 40;

/** Số cánh theo máy: desktop 120, CPU ≤ 4 nhân 72, dưới 768px 48. @param {boolean} mobile @returns {number} */
function petalCount(mobile) {
  if (mobile) return 48;
  return (navigator.hardwareConcurrency || 8) <= 4 ? 72 : 120;
}

/** Trạng thái ngẫu nhiên một cánh. @param {object} box vùng sống @param {boolean} top đặt ở đỉnh @returns {object} */
function spawn(box, top) {
  return {
    x: rand(-box.w, box.w), y: top ? box.h : rand(-box.h, box.h), z: rand(-3, 2),
    vy: rand(0.28, 0.6), amp: rand(0.15, 0.35), freq: rand(0.25, 0.6), ph: rand(0, 6.28),
    rx: rand(0, 6.28), ry: rand(0, 6.28), rz: rand(0, 6.28),
    wx: rand(0.6, 1.6), wy: rand(0.4, 1.2), wz: rand(0.2, 0.8), s: rand(0.09, 0.16), k: rand(0.15, 0.45),
  };
}

/** Dựng cảnh sakura-drift. @param {object} THREE @param {object} ctx {scene, camera, mobile} @returns {object} api cảnh */
function buildSakura(THREE, { scene, camera, el, mobile }) {
  camera.fov = FOV; camera.position.set(0, 0, CAM_Z); camera.lookAt(0, 0, 0);
  const hemi = paperLights(THREE, scene);
  const n = petalCount(mobile);
  const geo = petalGeometry(THREE);
  const mat = new THREE.MeshStandardMaterial({ roughness: 0.8, metalness: 0, side: THREE.DoubleSide, forceSinglePass: true, transparent: true, opacity: 0.6, depthWrite: false });
  const mesh = new THREE.InstancedMesh(geo, mat, n);
  mesh.frustumCulled = false;
  scene.add(mesh);
  const box = { w: 6, h: 3 };
  const fit = (w, h) => { box.h = Math.tan((FOV * Math.PI) / 360) * CAM_Z + 0.5; box.w = (box.h - 0.5) * (w / h) + 0.5; };
  fit(el.clientWidth || 1, el.clientHeight || 1);
  const petals = Array.from({ length: n }, () => spawn(box, false));
  const paint = () => {
    const mix = petalPalette(THREE);
    hemi.groundColor.copy(tokenColor(THREE, isDarkTheme() ? '--ink' : '--surface-2'));
    petals.forEach((p, i) => mesh.setColorAt(i, mix(p.k)));
    mesh.instanceColor.needsUpdate = true;
  };
  paint();
  const dummy = new THREE.Object3D();
  let wind = 0.08; let boost = 0; let lastScroll = null;
  return {
    resize: fit,
    update(t, dt, input) {
      const target = input.fine && input.active ? 0.08 + 0.45 * input.windowPointer.x : 0.08;
      wind += (target - wind) * (1 - Math.exp(-1.5 * dt));
      const v = lastScroll === null || dt <= 0 ? 0 : Math.abs(input.scrollY - lastScroll) / dt;
      lastScroll = input.scrollY;
      boost = Math.max(boost * Math.exp(-2 * dt), Math.min(v * 0.0015, 1.2));
      petals.forEach((p, i) => {
        p.y -= (p.vy + boost) * dt; p.x += wind * dt;
        p.rx += p.wx * dt; p.ry += p.wy * dt; p.rz += p.wz * dt;
        if (p.y < -box.h || Math.abs(p.x) > box.w + 0.6) Object.assign(p, spawn(box, true), { k: p.k });
        dummy.position.set(p.x + p.amp * Math.sin(2 * Math.PI * p.freq * t + p.ph), p.y, p.z);
        dummy.rotation.set(p.rx, p.ry, p.rz);
        dummy.scale.setScalar(p.s);
        dummy.updateMatrix();
        mesh.setMatrixAt(i, dummy.matrix);
      });
      mesh.instanceMatrix.needsUpdate = true;
      return true;
    },
    onTheme: paint,
    degrade() { mesh.count = Math.floor(n / 2); },
    dispose() { geo.dispose(); mat.dispose(); mesh.dispose(); },
  };
}

const el = document.querySelector('.hero-sakura[data-three-scene="sakura-drift"]');
if (el) mountStage(el, buildSakura, { lazy: true, maxDpr: [1.5, 1.25] });
