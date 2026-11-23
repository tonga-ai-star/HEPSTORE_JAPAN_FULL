#!/usr/bin/env python3
"""Check Hép Bookstore brand rules mechanically.

Usage: python3 lint_ui.py <repo_root>
Levels: CHẶN (blocks release) and CẢNH BÁO (should fix). Exit 1 if any CHẶN.
"""
import re
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
css_path = repo / 'static/css/app.css'
templates = sorted((repo / 'templates').rglob('*.html'))
scripts = sorted((repo / 'static/js').glob('*.js'))
issues = []

def add(level, where, msg):
    issues.append((level, where, msg))

# --- contrast -------------------------------------------------------------
def hex_rgb(h):
    h = h.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))

def lum(rgb):
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = map(f, rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = sorted((lum(hex_rgb(a)), lum(hex_rgb(b))), reverse=True)
    return (la + 0.05) / (lb + 0.05)

PAIRS = [('--ink', '--bg'), ('--ink-soft', '--bg'), ('--navy', '--bg'), ('--orange-ink', '--bg'),
         ('--on-orange', '--orange'), ('--on-navy', '--navy'), ('--ink', '--surface'), ('--ink-soft', '--surface-2')]
REQUIRED = {'--bg', '--surface', '--surface-2', '--line', '--ink', '--ink-soft', '--navy', '--orange', '--orange-ink', '--on-orange', '--on-navy'}

css = css_path.read_text(encoding='utf-8') if css_path.exists() else ''
blocks = {'sáng': {}, 'tối': {}}
for sel, body in re.findall(r'([^{}]*:root[^{}]*)\{([^{}]*)\}', css):
    mode = 'tối' if 'dark' in sel else 'sáng'
    for k, v in re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b', body):
        blocks[mode].setdefault(k, v)
# media-query dark blocks: :root inside @media (prefers-color-scheme: dark)
for media in re.finditer(r'@media[^{]*prefers-color-scheme:\s*dark[^{]*\{(.*?)\}\s*\}', css, re.S):
    for k, v in re.findall(r'(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b', media.group(1)):
        blocks['tối'].setdefault(k, v)

missing = REQUIRED - set(blocks['sáng'])
if missing:
    add('CHẶN', 'app.css', f'Thiếu token bắt buộc: {", ".join(sorted(missing))}')
if not blocks['tối']:
    add('CẢNH BÁO', 'app.css', 'Chưa có token chế độ tối')
contrast_rows = []
for mode, toks in blocks.items():
    for fg, bg in PAIRS:
        if fg in toks and bg in toks:
            r = ratio(toks[fg], toks[bg])
            contrast_rows.append((mode, fg, bg, r))
            if r < 4.5:
                add('CHẶN', f'app.css ({mode})', f'Tương phản {fg} trên {bg} = {r:.2f}:1 < 4.5')

# --- hex outside token blocks ----------------------------------------------
css_wo_tokens = re.sub(r'[^{}]*:root[^{}]*\{[^{}]*\}', '', css)
stray = re.findall(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', re.sub(r'url\([^)]*\)', '', css_wo_tokens))
if stray:
    add('CẢNH BÁO', 'app.css', f'{len(stray)} mã màu hex nằm ngoài khối token (vd {", ".join(sorted(set(stray))[:6])})')
for extra in (repo / 'static/css').glob('*.css'):
    if extra.name != 'app.css':
        n = len(re.findall(r'#[0-9a-fA-F]{6}\b', extra.read_text(encoding='utf-8')))
        if n:
            add('CẢNH BÁO', extra.name, f'{n} mã màu hex cứng, nên chuyển sang var(--...)')
if 'prefers-reduced-motion' not in css:
    add('CHẶN', 'app.css', 'Không có khối prefers-reduced-motion')
if re.search(r'z-index\s*:\s*\d{4,}', css):
    add('CẢNH BÁO', 'app.css', 'z-index từ 1000 trở lên, dùng thang trong skill')
for banned in ('Inter', 'Fraunces', 'Instrument Serif', 'Noto Serif', 'Georgia'):
    if re.search(rf"font-family[^;]*{banned}", css):
        add('CẢNH BÁO', 'app.css', f'Font không thuộc thương hiệu: {banned}')

# --- templates --------------------------------------------------------------
for t in templates:
    rel = t.relative_to(repo)
    text = t.read_text(encoding='utf-8')
    visible = re.sub(r'\{[%#].*?[%#]\}|<script.*?</script>|<style.*?</style>', '', text, flags=re.S)
    if '—' in visible or '–' in visible:
        add('CHẶN', str(rel), f'Có {visible.count(chr(0x2014)) + visible.count(chr(0x2013))} ký tự gạch ngang dài/vừa')
    if 'Hép Store' in text or 'HÉP STORE' in text:
        add('CHẶN', str(rel), 'Còn tên cũ "Hép Store"')
    n_inline = len(re.findall(r'\sstyle="(?!--)', text))
    if n_inline:
        add('CẢNH BÁO', str(rel), f'{n_inline} thuộc tính style nội tuyến (chỉ cho phép biến CSS kiểu style="--i:..")')
    sections = max(1, len(re.findall(r'<section\b', text)))
    eyebrows = len(re.findall(r'class="[^"]*\beyebrow\b', text))
    if eyebrows > -(-sections // 3) and 'base.html' not in t.name and not t.name.startswith('_'):
        add('CẢNH BÁO', str(rel), f'{eyebrows} eyebrow cho {sections} section (tối đa {-(-sections // 3)})')
    for line in visible.splitlines():
        if line.count('·') > 1:
            add('CẢNH BÁO', str(rel), 'Hơn 1 dấu chấm giữa (·) trên một dòng')
            break
    for img in re.findall(r'<img\b[^>]*>', text):
        if 'alt=' not in img:
            add('CHẶN', str(rel), 'Ảnh thiếu alt')

base = (repo / 'templates/base.html').read_text(encoding='utf-8')
if 'fonts.googleapis.com' not in base or 'Baloo' not in base:
    add('CHẶN', 'templates/base.html', 'Chưa nạp font thương hiệu (Baloo 2, Be Vietnam Pro)')
if 'skip' not in base.lower():
    add('CẢNH BÁO', 'templates/base.html', 'Thiếu liên kết bỏ qua tới nội dung')

# --- scripts ----------------------------------------------------------------
for s in scripts:
    code = s.read_text(encoding='utf-8')
    for fn in ('alert(', 'confirm(', 'prompt('):
        hits = len(re.findall(r'(?<![\w.])' + re.escape(fn), code)) + len(re.findall(r'window\.' + re.escape(fn), code))
        if hits:
            add('CHẶN', f'static/js/{s.name}', f'{hits} lần gọi {fn[:-1]}()')
    if re.search(r"addEventListener\(\s*['\"]scroll['\"]", code):
        add('CHẶN', f'static/js/{s.name}', 'Dùng sự kiện scroll, đổi sang IntersectionObserver hoặc CSS scroll-timeline')
motion = repo / 'static/js/motion.js'
if not motion.exists():
    add('CHẶN', 'static/js/motion.js', 'Chưa có file hiệu ứng')
elif 'prefers-reduced-motion' not in motion.read_text(encoding='utf-8'):
    add('CHẶN', 'static/js/motion.js', 'motion.js không kiểm prefers-reduced-motion')

# --- three.js (references/threejs-recipes.md of hep-brand-ui) -------------------
VENDOR = 'vendor/three/three.module.min.js'
if not (repo / 'static' / VENDOR).exists():
    add('CHẶN', f'static/{VENDOR}', 'Thiếu bản three.js vendor')
for s in scripts:
    code = s.read_text(encoding='utf-8')
    if re.search(r"(cdn\.jsdelivr|unpkg|esm\.sh|skypack|cdnjs)[^'\"]*three", code):
        add('CHẶN', f'static/js/{s.name}', 'Nạp three.js từ CDN, phải dùng bản vendor')
    if s.name.startswith('three-'):
        if s.name != 'three-stage.js' and 'mountStage' not in code and 'three-stage' not in code:
            add('CHẶN', f'static/js/{s.name}', 'Cảnh 3D không đi qua three-stage.js (mất kiểm tra tắt, nạp lười, dọn dẹp)')
        if s.name == 'three-stage.js':
            for need, msg in (('prefers-reduced-motion', 'không kiểm prefers-reduced-motion'),
                              ('dispose', 'không dispose renderer khi rời trang'),
                              ('IntersectionObserver', 'không nạp lười bằng IntersectionObserver'),
                              ('saveData', 'không tắt khi bật tiết kiệm dữ liệu')):
                if need not in code:
                    add('CHẶN', 'static/js/three-stage.js', msg)
        if re.search(r'#[0-9a-fA-F]{6}\b', code):
            add('CẢNH BÁO', f'static/js/{s.name}', 'Có mã hex trong cảnh 3D, nên đọc màu từ token CSS')
for t in templates:
    rel = t.relative_to(repo)
    if 'management' in rel.parts or rel.name in ('pos.html', 'checkout.html', 'login.html'):
        txt = t.read_text(encoding='utf-8')
        if 'data-three' in txt or 'three-' in txt and '.js' in txt and re.search(r"three-[a-z-]+\.js", txt):
            add('CHẶN', str(rel), 'Không dùng 3D ở trang quản trị, POS, thanh toán, đăng nhập')

# --- đợt wa (hep-brand-ui mục 6b) ------------------------------------------------
for extra in (repo / 'static/css').glob('*.css'):
    code = extra.read_text(encoding='utf-8')
    # The handwritten face is only for POP cards and hand notes; anywhere else it reads as a gimmick.
    for sel, body in re.findall(r'([^{}]+)\{([^{}]*var\(--font-hand\)[^{}]*)\}', code):
        if not re.search(r'\.(pop|hand)\b', sel):
            add('CẢNH BÁO', extra.name, f'--font-hand dùng ngoài .pop/.hand: {sel.strip()[:60]}')
for t in templates:
    rel = t.relative_to(repo)
    txt = t.read_text(encoding='utf-8')
    pops = len(re.findall(r'class="[^"]*\bpop\b', txt))
    if pops > 6:
        add('CẢNH BÁO', str(rel), f'{pops} thẻ POP, tối đa 6 mỗi trang')
    if rel.name == 'checkout.html' and re.search(r'data-swing|class="[^"]*\bpop\b', txt):
        add('CHẶN', str(rel), 'Checkout không dùng POP hay data-swing (không gây xao nhãng khi trả tiền)')
    if rel.name in ('home.html', 'detail.html') and 'section-top' in txt:
        add('CHẶN', str(rel), 'Còn khuôn .section-top (tiêu đề + link + lưới thẻ), mục 6b cấm ở trang này')

# --- report -----------------------------------------------------------------
print('## Tương phản')
for mode, fg, bg, r in contrast_rows:
    print(f"- [{'OK' if r >= 4.5 else 'FAIL'}] {mode}: {fg} / {bg} = {r:.2f}:1")
print('\n## Vi phạm')
for lvl in ('CHẶN', 'CẢNH BÁO'):
    for level, where, msg in issues:
        if level == lvl:
            print(f'- {level} | {where} | {msg}')
n_block = sum(1 for i in issues if i[0] == 'CHẶN')
print(f'\nTổng: {n_block} CHẶN, {len(issues) - n_block} CẢNH BÁO')
sys.exit(1 if n_block else 0)
