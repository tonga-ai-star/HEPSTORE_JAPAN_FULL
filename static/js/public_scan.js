/* Public ISBN / SKU scanner. Browser-first native BarcodeDetector, ZXing fallback.
   Scan 1D barcode data, NOT a barcode URL. Only navigates to the product result URL. */
'use strict';
(() => {
  const root = document.getElementById('public-scanner');
  if (!root) return;
  const video = document.getElementById('barcode-video');
  const status = document.getElementById('scan-status');
  const container = document.getElementById('scan-camera');
  const startButton = document.getElementById('start-barcode-scan');
  const stopButton = document.getElementById('stop-barcode-scan');
  const input = document.getElementById('isbn-value');
  const form = document.getElementById('scan-manual-form');
  let live = false;
  let processing = false;
  let stream = null;
  let reader = null;
  let timer = null;
  let started = 0;

  const validCode = (value) => /^[0-9a-zA-Z._-]{3,30}$/.test(value);
  function report(message, isError = false) {
    status.textContent = message;
    status.classList.toggle('error', isError);
  }
  function cameraControls(on) {
    container.classList.toggle('is-live', on);
    stopButton.disabled = !on;
    startButton.disabled = on;
  }
  function stop() {
    live = false;
    processing = false;
    if (timer !== null) { clearTimeout(timer); timer = null; }
    if (reader) { try { reader.reset(); } catch (_) { /* already stopped */ } reader = null; }
    if (stream) { stream.getTracks().forEach(track => track.stop()); stream = null; }
    if (video.srcObject) {
      try { video.srcObject.getTracks().forEach(track => track.stop()); } catch (_) { /* ok */ }
      video.srcObject = null;
    }
    cameraControls(false);
  }
  function result(code) {
    if (!live || processing) return;
    const raw = String(code || '').trim();
    if (!validCode(raw)) return;
    processing = true;
    input.value = raw;
    report(`Đã nhận mã ${raw}. Đang mở trang thông tin sách...`);
    stop();
    // The server independently validates the code and queries Book by ISBN / SKU.
    window.location.assign(`/quet-ma/sach/${encodeURIComponent(raw)}/`);
  }
  function ensureZXing() {
    if (window.ZXing && window.ZXing.BrowserMultiFormatReader) return Promise.resolve();
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/@zxing/library@0.21.3/umd/index.min.js';
      script.onload = () => (window.ZXing && window.ZXing.BrowserMultiFormatReader) ? resolve() : reject(new Error('Không tải được thư viện quét mã'));
      script.onerror = () => reject(new Error('Không tải được thư viện ZXing. Kiểm tra Internet.'));
      document.head.appendChild(script);
    });
  }
  async function startZXing() {
    report('Đang tải bộ nhận diện mã vạch ZXing...');
    await ensureZXing();
    if (!live) return;
    reader = new window.ZXing.BrowserMultiFormatReader();
    report('Đưa mã vạch ISBN vào vùng quét và giữ yên vài giây.');
    // ZXing handles camera and continuous decoding, no Python or API key required.
    await reader.decodeFromVideoDevice(null, video, (decoded) => {
      if (decoded && decoded.getText) result(decoded.getText());
    });
  }
  async function startNative() {
    if (!('BarcodeDetector' in window)) return false;
    const preferred = ['ean_13', 'ean_8', 'upc_a', 'upc_e', 'code_128', 'code_39'];
    try {
      const supported = typeof BarcodeDetector.getSupportedFormats === 'function'
        ? await BarcodeDetector.getSupportedFormats() : preferred;
      const formats = preferred.filter(f => supported.includes(f));
      if (!formats.length) return false;
      const detector = new BarcodeDetector({ formats });
      const media = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
      if (!live) { media.getTracks().forEach(track => track.stop()); return true; }
      stream = media;
      video.srcObject = stream;
      await video.play();
      report('Camera đã bật. Đưa mã vạch ISBN vào khung hình.');
      const loop = async () => {
        if (!live) return;
        try {
          if (video.readyState >= 2) {
            const codes = await detector.detect(video);
            if (codes.length) {
              const matching = codes.find(c => validCode(String(c.rawValue || '').trim()));
              if (matching) { result(matching.rawValue); return; }
            }
          }
        } catch (_) { /* transient frame error: keep scanning */ }
        if (live) timer = setTimeout(loop, 200);
      };
      loop();
      return true;
    } catch (err) {
      if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
      video.srcObject = null;
      // BarcodeDetector may be exposed but not work with this device. Try ZXing.
      return false;
    }
  }
  async function start() {
    if (live) return;
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      report('Không thể mở camera: cần localhost hoặc HTTPS. Có thể nhập ISBN bên cạnh.', true);
      return;
    }
    live = true;
    started = Date.now();
    cameraControls(true);
    try {
      report('Đang bật camera...');
      if (!await startNative()) await startZXing();
    } catch (err) {
      stop();
      report(`Không thể quét bằng camera: ${err.message}. Hãy kiểm tra quyền camera hoặc nhập ISBN.`, true);
    }
  }
  startButton.addEventListener('click', start);
  stopButton.addEventListener('click', () => { stop(); report('Camera đã tắt.'); });
  form.addEventListener('submit', (event) => {
    const code = input.value.trim();
    if (!validCode(code)) {
      event.preventDefault();
      report('ISBN/SKU không hợp lệ. Chỉ dùng chữ, số, gạch nối, dấu chấm (3 đến 30 ký tự).', true);
      input.focus();
      return;
    }
    stop();
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) stop(); });
  window.addEventListener('pagehide', stop);
})();
