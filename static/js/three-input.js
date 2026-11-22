// three-input: con trỏ và cuộn cho vòng render của three-stage.js. Chỉ nghe pointermove passive trên window,
// không nghe scroll (scrollY đọc trong vòng render đang chạy).
const FINE = matchMedia('(hover: hover) and (pointer: fine)');
/** Vị trí con trỏ chuột cuối cùng (bỏ qua cảm ứng). */
export const pointer = { cx: -1, cy: -1, active: false, at: 0 };

window.addEventListener('pointermove', (e) => {
  if (!FINE.matches || e.pointerType === 'touch') return;
  pointer.cx = e.clientX; pointer.cy = e.clientY; pointer.active = true; pointer.at = performance.now();
}, { passive: true });
window.addEventListener('pointerout', (e) => { if (!e.relatedTarget) pointer.active = false; }, { passive: true });

/** Con trỏ chuẩn hoá -1..1 theo một hình chữ nhật, kẹp. @param {DOMRect} r @returns {{x:number,y:number,inside:boolean}} */
function normPointer(r) {
  if (!pointer.active) return { x: 0, y: 0, inside: false };
  const x = ((pointer.cx - r.left) / r.width) * 2 - 1;
  const y = ((pointer.cy - r.top) / r.height) * 2 - 1;
  const pad = 120;
  const inside = pointer.cx > r.left - pad && pointer.cx < r.right + pad && pointer.cy > r.top - pad && pointer.cy < r.bottom + pad;
  return { x: Math.max(-1, Math.min(1, x)), y: Math.max(-1, Math.min(1, y)), inside };
}

/** Đầu vào cho mỗi khung hình. @param {HTMLElement} el @returns {object} */
export function readInput(el) {
  const vw = { left: 0, top: 0, width: innerWidth, height: innerHeight };
  return { fine: FINE.matches, active: pointer.active, pointer: normPointer(el.getBoundingClientRect()), windowPointer: normPointer(vw), scrollY: window.scrollY };
}
