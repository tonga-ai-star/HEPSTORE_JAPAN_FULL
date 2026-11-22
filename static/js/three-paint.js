// three-paint: màu từ token, ánh sáng giấy, hình cánh hoa; three-stage.js xuất lại các hàm này cho mọi cảnh.
// Không có mã hex: mọi màu đọc từ token CSS lúc chạy (references/threejs-recipes.md mục 5).
const ROOT = document.documentElement;

/** Đọc token màu CSS lúc chạy. @param {string} name ví dụ '--navy' @returns {string} */
export function readToken(name) { return getComputedStyle(ROOT).getPropertyValue(name).trim(); }

let probe2d = null;
/** Chuẩn hoá chuỗi màu CSS về [r,g,b] 0..255 bằng canvas 2D. @param {string} css @returns {number[]} */
function rgbOf(css) {
  probe2d = probe2d || document.createElement('canvas').getContext('2d');
  probe2d.fillStyle = css;
  const v = probe2d.fillStyle;
  if (v.startsWith('#')) return [1, 3, 5].map((i) => parseInt(v.slice(i, i + 2), 16));
  return (v.match(/[\d.]+/g) || [0, 0, 0]).slice(0, 3).map(Number);
}

/** Token màu thành chuỗi rgba có độ mờ. @param {string} name token @param {number} a alpha @returns {string} */
export function tokenRgba(name, a) { const [r, g, b] = rgbOf(readToken(name)); return `rgba(${r},${g},${b},${a})`; }

/** Nền --bg có độ sáng tương đối < .2 thì là chế độ tối. @returns {boolean} */
export function isDarkTheme() {
  const lin = rgbOf(readToken('--bg')).map((c) => { const s = c / 255; return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; });
  return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2] < 0.2;
}

/** Màu three từ token. @param {object} THREE @param {string} name @returns {object} THREE.Color */
export function tokenColor(THREE, name) { return new THREE.Color().setStyle(readToken(name)); }

/** Hình cánh anh đào dùng chung cho sakura-drift và paid-burst. @param {object} THREE @returns {object} geometry */
export function petalGeometry(THREE) {
  const s = new THREE.Shape();
  s.moveTo(0, 0); s.bezierCurveTo(0.5, 0.15, 0.55, 0.75, 0.18, 1); s.lineTo(0, 0.88);
  s.lineTo(-0.18, 1); s.bezierCurveTo(-0.55, 0.75, -0.5, 0.15, 0, 0);
  return new THREE.ShapeGeometry(s, 5).center();
}

/** Màu từng cánh hoa: lerp từ be (sáng: --surface-2, tối: --ink) sang --orange. @param {object} THREE @returns {function(number):object} */
export function petalPalette(THREE) {
  const base = tokenColor(THREE, isDarkTheme() ? '--ink' : '--surface-2');
  const orange = tokenColor(THREE, '--orange');
  return (k) => base.clone().lerp(orange, k);
}

/** Một HemisphereLight be/navy và một DirectionalLight ấm, không bóng đổ. @param {object} THREE @param {object} scene @param {string} [ground] token màu đất, mặc định --navy (cánh hoa dùng be cho khỏi xám) @returns {object} hemisphere light */
export function paperLights(THREE, scene, ground = '--navy') {
  const hemi = new THREE.HemisphereLight(tokenColor(THREE, '--bg'), tokenColor(THREE, ground), 1.5);
  scene.add(hemi);
  const sun = new THREE.DirectionalLight(tokenColor(THREE, '--surface'), 1.6);
  sun.position.set(2.5, 4, 6);
  scene.add(sun);
  return hemi;
}
