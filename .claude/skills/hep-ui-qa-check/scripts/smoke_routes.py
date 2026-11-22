#!/usr/bin/env python3
"""Render every shop and management page against a throwaway test database.

Usage: python3 smoke_routes.py <repo_root> <out_dir>
Writes <out_dir>/routes.json and one HTML snapshot per page (static paths made
absolute so headless Chrome can open them as files). Exit code 1 if any page
returns 5xx or raises.
"""
import json
import os
import sys
from pathlib import Path

repo = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(repo))
os.chdir(repo)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hepstore.settings')

import django  # noqa: E402
django.setup()
from django.conf import settings  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connection  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402

setup_test_environment()
settings.ALLOWED_HOSTS = ['testserver', 'localhost']
connection.creation.create_test_db(verbosity=0, keepdb=False)

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402
from shop.models import Book, Customer, Order, Supplier, PurchaseOrder, PurchaseItem  # noqa: E402
from shop.services import create_order  # noqa: E402

results = []
try:
    call_command('seed_demo', verbosity=0)
    staff = get_user_model().objects.create_user('qa_staff', password='QaStaff-Pass-2026', is_staff=True, is_superuser=True)
    book = Book.objects.filter(active=True).first()
    order = create_order(raw_lines=[(book.id, 1)], source='web', payment_method='cod', full_name='Lê Thu Hà',
                         phone='0912447381', address='12 Ngõ Huế, Hà Nội', shipping_fee=25000)
    supplier = Supplier.objects.first() or Supplier.objects.create(name='Nhà sách Kim Đồng')
    po = PurchaseOrder.objects.create(supplier=supplier, created_by=staff)
    PurchaseItem.objects.create(purchase=po, book=book, quantity=3, unit_cost=52000)
    customer = Customer.objects.first()
    bank_order = create_order(raw_lines=[(book.id, 1)], source='web', payment_method='bank', full_name='Trịnh Bảo Ngọc',
                              phone='0934556712', address='7 Hàng Bài, Hà Nội', shipping_fee=25000)
    from shop.payments import record_sepay
    record_sepay({'id': 'SMOKE-1', 'gateway': 'Vietcombank', 'transferType': 'in', 'transferAmount': bank_order.total,
                  'content': f'{bank_order.order_code} ck', 'referenceCode': 'FT0001'})
    record_sepay({'id': 'SMOKE-2', 'gateway': 'Vietcombank', 'transferType': 'in', 'transferAmount': 123000,
                  'content': 'chuyen tien mua sach', 'referenceCode': 'FT0002'})
    pending = create_order(raw_lines=[(book.id, 1)], source='web', payment_method='bank', full_name='Mạc Thảo Vy',
                           phone='0915002367', address='Hải Phòng', shipping_fee=25000)

    guest = [
        ('home', '/'), ('catalog', '/sach/'), ('catalog_search', '/sach/?q=a&sort=low'),
        ('book_detail', f'/sach/{book.slug}/'), ('cart_empty', '/gio-hang/'), ('track', '/tra-cuu-don/'),
        ('signup', '/dang-ky/'), ('login', '/tai-khoan/login/'), ('about', '/ve-hep/'),
        ('policies', '/chinh-sach/'), ('contact', '/lien-he/'), ('scan', '/quet-ma/'),
        ('scan_found', f'/quet-ma/sach/{book.isbn}/'), ('scan_missing', '/quet-ma/sach/9786049999999/'),
        ('not_found_404', '/khong-ton-tai/'),
    ]
    staff_pages = [
        ('m_dashboard', '/management/'), ('m_books', '/management/books/'), ('m_book_add', '/management/books/add/'),
        ('m_book_edit', f'/management/books/{book.pk}/edit/'), ('m_inventory', '/management/inventory/'),
        ('m_suppliers', '/management/suppliers/'), ('m_supplier_detail', f'/management/suppliers/{supplier.pk}/'),
        ('m_purchases', '/management/purchases/'), ('m_purchase_new', '/management/purchases/new/'),
        ('m_purchase_detail', f'/management/purchases/{po.pk}/'), ('m_customers', '/management/customers/'),
        ('m_customer_detail', f'/management/customers/{customer.pk}/'), ('m_orders', '/management/orders/'),
        ('m_order_detail', f'/management/orders/{order.pk}/'), ('m_social', '/management/social/new/'),
        ('m_pos', '/management/pos/'), ('m_pos_lookup', f'/management/pos/?isbn={book.isbn}'),
        ('m_reports', '/management/reports/'), ('m_payments', '/management/payments/'),
        ('m_staff', '/management/staff/'), ('m_staff_add', '/management/staff/add/'),
    ]

    def snap(name, client, url, expect_ok=True):
        try:
            r = client.get(url)
            body = r.content.decode('utf-8', 'replace')
            ok = r.status_code < 500
            if r.status_code == 200 or name == 'not_found_404':
                html = body.replace('href="/static/', f'href="file://{repo}/static/').replace('src="/static/', f'src="file://{repo}/static/')
                (out / f'{name}.html').write_text(html, encoding='utf-8')
            results.append({'name': name, 'url': url, 'status': r.status_code, 'ok': ok, 'bytes': len(body)})
        except Exception as exc:  # template errors surface here
            results.append({'name': name, 'url': url, 'status': 'EXC', 'ok': False, 'error': f'{type(exc).__name__}: {exc}'[:400]})

    c = Client()
    for n, u in guest:
        snap(n, c, u)
    c.post(f'/gio-hang/them/{book.pk}/', {'quantity': 1})
    snap('cart_full', c, '/gio-hang/')
    snap('checkout', c, '/thanh-toan/')
    s = c.session; s['hep_recent_orders'] = [order.order_code, pending.order_code, bank_order.order_code]; s.save()
    snap('order_success', c, f'/dat-hang-thanh-cong/{order.order_code}/')
    settings.BANK_BIN, settings.BANK_ACCOUNT, settings.BANK_OWNER = '970436', '0011002233445', 'NGUYEN VAN MAU'
    snap('order_bank_pending', c, f'/dat-hang-thanh-cong/{pending.order_code}/')
    snap('order_bank_paid', c, f'/dat-hang-thanh-cong/{bank_order.order_code}/')
    sc = Client(); sc.force_login(staff)
    for n, u in staff_pages:
        snap(n, sc, u)
finally:
    connection.creation.destroy_test_db(settings.DATABASES['default']['NAME'], verbosity=0)

(out / 'routes.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
bad = [r for r in results if not r['ok']]
for r in results:
    print(f"{'OK ' if r['ok'] else 'ERR'} {r['status']!s:>4} {r['name']:<20} {r['url']}" + (f"  {r.get('error','')}" if not r['ok'] else ''))
print(f'\n{len(results)} trang, {len(bad)} lỗi')
sys.exit(1 if bad else 0)
