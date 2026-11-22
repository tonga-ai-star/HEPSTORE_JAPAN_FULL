#!/usr/bin/env python3
"""Generate docs/ERD_Hep_Bookstore.md, docs/erd.mmd and docs/ERD_Hep_Bookstore.html from shop/models.py."""
import html
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT)); os.chdir(ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hepstore.settings')
import django  # noqa: E402
django.setup()
from django.apps import apps  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402

User = get_user_model()
ORDER = ['Category', 'Supplier', 'Book', 'Customer', 'Order', 'OrderItem', 'PaymentTransaction', 'StockMovement',
         'PurchaseOrder', 'PurchaseItem', 'StaffProfile', 'ContactMessage']
VN = {'Category': 'Danh mục sách', 'Supplier': 'Nhà cung cấp', 'Book': 'Sách', 'Customer': 'Khách hàng',
      'Order': 'Đơn hàng (web, Facebook, Instagram, POS)', 'OrderItem': 'Dòng đơn',
      'PaymentTransaction': 'Giao dịch tiền vào (SePay)', 'StockMovement': 'Nhật ký biến động kho',
      'PurchaseOrder': 'Phiếu nhập hàng', 'PurchaseItem': 'Dòng phiếu nhập', 'StaffProfile': 'Hồ sơ nhân viên, vai trò',
      'ContactMessage': 'Lời nhắn liên hệ', 'User': 'Tài khoản đăng nhập (Django auth)'}
TYPES = {'BigAutoField': 'bigint', 'AutoField': 'int', 'CharField': 'varchar', 'SlugField': 'varchar', 'TextField': 'text',
         'EmailField': 'varchar', 'PositiveIntegerField': 'int', 'IntegerField': 'int', 'BigIntegerField': 'bigint',
         'BooleanField': 'bool', 'DateField': 'date', 'PositiveSmallIntegerField': 'smallint', 'DateTimeField': 'datetime', 'JSONField': 'json'}
USER_FIELDS = ('id', 'username', 'first_name', 'email', 'is_staff', 'is_superuser', 'is_active')

models = sorted(apps.get_app_config('shop').get_models(), key=lambda m: ORDER.index(m.__name__) if m.__name__ in ORDER else 99)


def fields_of(m):
    if m is User:
        return [User._meta.get_field(n) for n in USER_FIELDS]
    return [f for f in m._meta.get_fields() if getattr(f, 'concrete', False)]


def typ(f):
    return 'bigint' if f.is_relation else TYPES.get(f.get_internal_type(), f.get_internal_type().lower())


def key(f):
    return 'PK' if f.primary_key else 'FK' if f.is_relation else 'UK' if getattr(f, 'unique', False) else ''


lines, rels = ['erDiagram'], []
for m in [User] + models:
    lines.append(f'  {m.__name__} {{')
    for f in fields_of(m):
        lines.append(f'    {typ(f)} {f.column if f.is_relation else f.name}{" " + key(f) if key(f) else ""}')
    lines.append('  }')
    if m is User:
        continue
    for f in fields_of(m):
        if f.is_relation and (f.many_to_one or f.one_to_one):
            rels.append(f'  {f.related_model.__name__} {"|o" if f.null else "||"}--{"o|" if f.one_to_one else "o{"} {m.__name__} : "{f.name}"')
mermaid = '\n'.join(lines + rels)

md = ['# ERD Hép Bookstore', '', 'Sinh tự động từ `shop/models.py`. Chạy lại: `python3 docs/gen_erd.py`.', '',
      'Ký hiệu: PK khoá chính, FK khoá ngoại, UK duy nhất. `||--o{` một-nhiều, `|o--o{` một-nhiều phía cha có thể rỗng, `||--o|` một-một.',
      '', '```mermaid', mermaid, '```', '', '## Mô tả bảng', '']
tables_html = []
for m in [User] + models:
    md += [f'### {m.__name__}: {VN.get(m.__name__, "")}', '', '| Trường | Kiểu | Khoá | Ghi chú |', '| --- | --- | --- | --- |']
    rows = []
    for f in fields_of(m):
        note = str(f.verbose_name) if str(f.verbose_name) != f.name.replace('_', ' ') else ''
        if f.is_relation:
            note = (note + '; ' if note else '') + f'tham chiếu {f.related_model.__name__}' + (', có thể rỗng' if f.null else '')
        if f.choices:
            note = (note + '; ' if note else '') + ', '.join(str(c[0]) for c in f.choices)
        name = f.column if f.is_relation else f.name
        md.append(f'| {name} | {typ(f)} | {key(f)} | {note} |')
        rows.append(f'<tr><td>{name}</td><td>{typ(f)}</td><td>{key(f)}</td><td>{html.escape(note)}</td></tr>')
    md.append('')
    tables_html.append(f'<h3>{m.__name__} <span>{VN.get(m.__name__, "")}</span></h3><table><tr><th>Trường</th><th>Kiểu</th><th>Khoá</th><th>Ghi chú</th></tr>{"".join(rows)}</table>')
md += ['## Ràng buộc nghiệp vụ', '',
       '- `PaymentTransaction (provider, provider_txn_id)` duy nhất: SePay gửi lại không ghi trùng.',
       '- `Order.order_code` duy nhất, dạng `HEP` + ngày + 8 ký tự, là nội dung chuyển khoản để khớp tiền.',
       '- Tồn kho `Book.stock` chỉ đổi qua service, mỗi lần đổi ghi một `StockMovement`.',
       '- `StaffProfile.role`: manager (toàn quyền), sales (đơn, POS, tiền vào), warehouse (sách, kho, nhập hàng).',
       '- Đặt trước: sách hết hàng có `Book.allow_preorder` vẫn nhận đơn web/Facebook/Instagram. Phần thiếu ghi vào `OrderItem.preorder_qty`, '
       '`Order.is_preorder` bật và `Order.expected_date` = ngày đặt + `Book.restock_days` lớn nhất. Kho chỉ trừ phần thiếu khi đơn chuyển sang đóng gói.', '']
(ROOT / 'docs/ERD_Hep_Bookstore.md').write_text('\n'.join(md), encoding='utf-8')
(ROOT / 'docs/erd.mmd').write_text(mermaid, encoding='utf-8')
page = f'''<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>ERD Hép Bookstore</title>
<style>@page{{size:A3 landscape;margin:12mm}}body{{font-family:Arial,"DejaVu Sans",sans-serif;color:#1f2547;font-size:10pt}}
h1{{color:#2c3a7e;margin:0}}p.sub{{color:#4f5679;margin:2px 0 10px}}h3{{margin:14px 0 4px;color:#2c3a7e;page-break-after:avoid}}h3 span{{font-weight:400;color:#a8501a;font-size:10pt}}
table{{border-collapse:collapse;width:100%;font-size:9pt;page-break-inside:avoid}}td,th{{border:1px solid #d9c9b2;padding:3px 6px;text-align:left}}th{{background:#f4ece0}}
.diagram{{page-break-after:always;text-align:center}}.diagram img{{height:240mm;width:auto}}.cols{{columns:2;column-gap:18px}}.cols>div{{break-inside:avoid}}</style></head><body>
<h1>ERD Hép Bookstore</h1><p class="sub">Sinh tự động từ shop/models.py. 13 bảng, {len(rels)} quan hệ.</p>
<div class="diagram"><pre class="mermaid">{html.escape(mermaid)}</pre></div>
<div class="cols">{"".join(f"<div>{t}</div>" for t in tables_html)}</div>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10.9.1/dist/mermaid.min.js"></script>
<script>mermaid.initialize({{startOnLoad:true,theme:"base",er:{{useMaxWidth:true}},themeVariables:{{primaryColor:"#f4ece0",primaryBorderColor:"#2c3a7e",lineColor:"#2c3a7e",primaryTextColor:"#1f2547",fontFamily:"Arial"}}}});</script>
</body></html>'''
(ROOT / 'docs/ERD_Hep_Bookstore.html').write_text(page, encoding='utf-8')
print(f'{len(models) + 1} bảng, {len(rels)} quan hệ -> docs/ERD_Hep_Bookstore.md, .html, erd.mmd')
