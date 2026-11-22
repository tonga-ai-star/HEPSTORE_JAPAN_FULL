"""Request-level tests for shop and back-office views that only had render smoke coverage."""
import csv
import io

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import (Book, Category, ContactMessage, Customer, Order, PurchaseOrder, StockMovement,
                     Supplier)
from .services import create_order
from .templatetags.shop_extras import money, mul
from .utils import qr_url

User = get_user_model()
BANK = dict(BANK_BIN='970422', BANK_ACCOUNT='0011002233445', BANK_OWNER='NGUYEN VAN MAU')


@override_settings(**BANK)
class ShopViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name_vi='Văn học', slug='van-hoc')
        self.book = Book.objects.create(category=self.cat, title_vi='Rừng Na Uy', title_ja='ノルウェイの森', slug='rung',
                                        isbn='VF-1', price=120000, stock=4, author_ja='Murakami')
        self.cheap = Book.objects.create(category=self.cat, title_vi='Bento', slug='bento', isbn='VF-2', price=30000,
                                         stock=2, allow_preorder=False)

    def test_catalog_search_filter_and_sort(self):
        for q in ('Murakami', 'ノルウェイ', 'VF-2'):
            self.assertEqual(self.client.get(reverse('catalog'), {'q': q}).status_code, 200)
        page = self.client.get(reverse('catalog'), {'category': 'van-hoc', 'sort': 'low'}).content.decode()
        self.assertLess(page.index('Bento'), page.index('Rừng Na Uy'))
        for sort in ('high', 'name', 'new'):
            self.assertEqual(self.client.get(reverse('catalog'), {'sort': sort}).status_code, 200)
        self.assertNotContains(self.client.get(reverse('catalog'), {'q': 'không có'}), 'Bento')

    def test_cart_add_rejects_bad_quantities(self):
        url = reverse('cart_add', args=[self.cheap.pk])
        self.client.post(url, {'quantity': 'abc'})
        self.client.post(url, {'quantity': 0})
        self.client.post(url, {'quantity': 3})  # only 2 left and no pre-order
        self.assertEqual(self.client.session.get('hep_cart', {}), {})
        self.client.post(reverse('cart_add', args=[self.book.pk]), {'quantity': 100})
        self.client.post(reverse('cart_add', args=[self.book.pk]), {'quantity': 1})  # over the 100 per title cap
        self.assertEqual(self.client.session['hep_cart'], {str(self.book.pk): 100})

    def test_cart_update_changes_removes_and_validates(self):
        self.client.post(reverse('cart_add', args=[self.cheap.pk]), {'quantity': 1})
        url = reverse('cart_update', args=[self.cheap.pk])
        self.client.post(url, {'quantity': 2})
        self.assertEqual(self.client.session['hep_cart'], {str(self.cheap.pk): 2})
        for bad in ('x', -1, 5, 2000):
            self.client.post(url, {'quantity': bad})
            self.assertEqual(self.client.session['hep_cart'], {str(self.cheap.pk): 2})
        self.client.post(url, {'quantity': 0})
        self.assertEqual(self.client.session['hep_cart'], {})
        self.assertContains(self.client.get(reverse('cart')), 'Giỏ', status_code=200)

    def test_checkout_validation_paths(self):
        self.assertRedirects(self.client.get(reverse('checkout')), reverse('catalog'))
        self.client.post(reverse('cart_add', args=[self.book.pk]), {'quantity': 1})
        base = {'full_name': 'Khách', 'phone': '0901234567', 'address': 'Huế'}
        self.client.post(reverse('checkout'), {**base, 'payment_method': 'cash'})
        self.client.post(reverse('checkout'), {**base, 'address': '', 'payment_method': 'cod'})
        with self.settings(BANK_BIN=''):
            self.client.post(reverse('checkout'), {**base, 'payment_method': 'bank'})
        self.assertFalse(Order.objects.exists())
        r = self.client.post(reverse('checkout'), {**base, 'payment_method': 'cod'})
        order = Order.objects.get()
        self.assertEqual(order.shipping_fee, 25000)
        self.assertRedirects(r, reverse('order_success', args=[order.order_code]))

    def test_order_success_is_private(self):
        o = create_order(raw_lines=[(self.book.pk, 1)], source='web', payment_method='bank', full_name='A',
                         phone='0901234567', address='Huế', shipping_fee=0)
        self.assertEqual(self.client.get(reverse('order_success', args=[o.order_code])).status_code, 404)

    def test_track_order_needs_matching_phone(self):
        o = create_order(raw_lines=[(self.book.pk, 1)], source='web', payment_method='bank', full_name='A',
                         phone='0901234567', address='Huế', shipping_fee=0)
        self.assertContains(self.client.post(reverse('track_order'), {'order_code': o.order_code, 'phone': '0999'}),
                            'Không tìm thấy')
        r = self.client.post(reverse('track_order'), {'order_code': o.order_code.lower(), 'phone': '0901234567'})
        self.assertContains(r, o.order_code)
        self.assertContains(r, 'img.vietqr.io')

    def test_signup_login_account_and_contact(self):
        r = self.client.post(reverse('signup'), {'username': 'thu', 'first_name': 'Thư', 'email': 'thu@example.com',
                                                 'password1': 'Sach-Hep-2026!', 'password2': 'Sach-Hep-2026!'})
        self.assertRedirects(r, reverse('home'))
        self.assertTrue(Customer.objects.filter(user__username='thu').exists())
        self.assertRedirects(self.client.get(reverse('signup')), reverse('home'))
        self.assertContains(self.client.get(reverse('account')), 'Thư')
        self.client.post(reverse('contact'), {'full_name': 'Thư', 'email': 'thu@example.com', 'subject': 'Hỏi sách',
                                              'message': 'Còn sách không?'})
        self.assertEqual(ContactMessage.objects.count(), 1)
        for name in ('about', 'policies', 'contact'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_account_requires_login(self):
        self.assertEqual(self.client.get(reverse('account')).status_code, 302)

    def test_qr_and_filters(self):
        o = Order(order_code='HEP2611220000ABCD', total=2000)
        self.assertIn('970422-0011002233445', qr_url(o))
        with self.settings(BANK_BIN='97A422'):
            self.assertEqual(qr_url(o), '')
        with self.settings(BANK_OWNER=''):
            self.assertEqual(qr_url(o), '')
        self.assertEqual(money(1234567), '1.234.567 ₫')
        self.assertEqual(money(None), '0 ₫')
        self.assertEqual(mul('3', 4), 12)
        self.assertEqual(mul('x', 4), 0)


@override_settings(**BANK)
class BackOfficeViewTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(name_vi='Văn học', slug='van-hoc')
        self.book = Book.objects.create(category=self.cat, title_vi='Rừng Na Uy', slug='rung', isbn='BO-1',
                                        price=120000, stock=4)
        self.boss = User.objects.create_superuser('boss', password='Hep-Staff-Pass-2026')
        self.client.force_login(self.boss)

    def test_supplier_create_edit_detail(self):
        self.client.post(reverse('supplier_add'), {'name': 'Nhã Nam', 'active': 'on'})
        sup = Supplier.objects.get()
        self.client.post(reverse('supplier_edit', args=[sup.pk]), {'name': 'Nhã Nam HN', 'active': 'on'})
        sup.refresh_from_db()
        self.assertEqual(sup.name, 'Nhã Nam HN')
        self.assertContains(self.client.get(reverse('supplier_detail', args=[sup.pk])), 'Nhã Nam HN')
        self.assertContains(self.client.get(reverse('manage_suppliers')), 'Nhã Nam HN')

    def test_purchase_validation_create_and_receive(self):
        sup = Supplier.objects.create(name='NCC')
        url = reverse('purchase_new')
        self.assertEqual(self.client.get(url).status_code, 200)
        bad = [{'supplier': 999, 'book': [self.book.pk], 'quantity': [1], 'unit_cost': [1]},
               {'supplier': sup.pk, 'book': [self.book.pk], 'quantity': [1, 2], 'unit_cost': [1]},
               {'supplier': sup.pk, 'book': [self.book.pk], 'quantity': ['x'], 'unit_cost': [1]},
               {'supplier': sup.pk, 'book': [self.book.pk], 'quantity': [0], 'unit_cost': [1]},
               {'supplier': sup.pk, 'book': [9999], 'quantity': [1], 'unit_cost': [1]}]
        for data in bad:
            self.client.post(url, data)
        self.assertFalse(PurchaseOrder.objects.exists())
        r = self.client.post(url, {'supplier': sup.pk, 'book': [self.book.pk], 'quantity': [6], 'unit_cost': [70000]})
        po = PurchaseOrder.objects.get()
        self.assertRedirects(r, reverse('purchase_detail', args=[po.pk]))
        self.assertContains(self.client.get(reverse('manage_purchases')), f'PN-{po.pk}')
        self.client.post(reverse('purchase_receive', args=[po.pk]))
        self.client.post(reverse('purchase_receive', args=[po.pk]))  # second time is refused
        self.book.refresh_from_db()
        self.assertEqual((self.book.stock, self.book.cost_price), (10, 70000))

    def test_customer_crud_and_search(self):
        self.client.post(reverse('customer_add'), {'full_name': 'Lê Hạ Vy', 'phone': '0912345678'})
        c = Customer.objects.get()
        self.client.post(reverse('customer_edit', args=[c.pk]), {'full_name': 'Lê Hạ Vy', 'phone': '0912000000'})
        c.refresh_from_db()
        self.assertEqual(c.phone, '0912000000')
        self.assertContains(self.client.get(reverse('manage_customers'), {'q': '0912000'}), 'Lê Hạ Vy')
        self.assertContains(self.client.get(reverse('customer_detail', args=[c.pk])), 'Lê Hạ Vy')

    def test_orders_filters_and_status_change(self):
        o = create_order(raw_lines=[(self.book.pk, 1)], source='web', payment_method='cod', full_name='Vy',
                         phone='0912345678', address='Huế', shipping_fee=0)
        for params in ({'q': 'Vy'}, {'source': 'web'}, {'status': 'new'}, {'source': 'zzz'}):
            self.assertContains(self.client.get(reverse('manage_orders'), params), 'Đơn', status_code=200)
        self.client.post(reverse('order_status', args=[o.pk]), {'status': 'completed'})  # not allowed from new
        o.refresh_from_db(); self.assertEqual(o.status, 'new')
        self.client.post(reverse('order_status', args=[o.pk]), {'status': 'confirmed'})
        o.refresh_from_db(); self.assertEqual(o.status, 'confirmed')
        self.assertContains(self.client.get(reverse('manage_order_detail', args=[o.pk])), 'Đang đóng gói')

    def test_social_order_view(self):
        url = reverse('social_order')
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.post(url, {'source': 'web', 'book': [self.book.pk], 'quantity': [1]})
        self.client.post(url, {'source': 'facebook', 'full_name': 'FB', 'phone': '0911', 'book': [], 'quantity': []})
        self.assertFalse(Order.objects.exists())
        self.client.post(url, {'source': 'facebook', 'full_name': 'FB', 'phone': '0911', 'shipping_fee': '20000',
                               'payment_method': 'cod', 'book': [self.book.pk], 'quantity': [2]})
        o = Order.objects.get()
        self.assertEqual((o.source, o.total), ('facebook', 260000))

    def test_social_preorder_message(self):
        Book.objects.filter(pk=self.book.pk).update(stock=0)
        r = self.client.post(reverse('social_order'), {'source': 'instagram', 'full_name': 'IG', 'phone': '0911',
                                                        'shipping_fee': '0', 'payment_method': 'cod',
                                                        'book': [self.book.pk], 'quantity': [1]}, follow=True)
        self.assertContains(r, 'đặt trước')

    def test_pos_lookup_cash_and_bank(self):
        self.assertContains(self.client.get(reverse('pos'), {'isbn': 'bo-1'}), 'Rừng Na Uy')
        self.client.post(reverse('pos'), {'book': [self.book.pk], 'quantity': [1], 'payment_method': 'cash',
                                          'received_cash': 'on'})
        self.client.post(reverse('pos'), {'book': [self.book.pk], 'quantity': [1], 'payment_method': 'bank'})
        cash, bank = Order.objects.order_by('pk')
        self.assertEqual((cash.status, cash.payment_status), ('completed', 'paid'))
        self.assertEqual((bank.status, bank.payment_status, bank.shipping_fee), ('new', 'unpaid', 0))
        with self.settings(BANK_BIN=''):
            self.client.post(reverse('pos'), {'book': [self.book.pk], 'quantity': [1], 'payment_method': 'bank'})
        self.assertEqual(Order.objects.count(), 2)

    def test_reports_and_csv_export(self):
        create_order(raw_lines=[(self.book.pk, 1)], source='pos', payment_method='cash', full_name='A',
                     phone='0000000000', user=self.boss, shipping_fee=0, paid=True)
        self.assertContains(self.client.get(reverse('manage_reports')), 'Rừng Na Uy')
        r = self.client.get(reverse('export_orders'))
        rows = list(csv.reader(io.StringIO(r.content.decode('utf-8-sig'))))
        self.assertEqual(rows[0][0], 'Mã đơn')
        self.assertEqual(rows[1][6], '120000')

    def test_inventory_adjust_validation(self):
        url = reverse('adjust_stock', args=[self.book.pk])
        for data in ({'delta': 'x', 'reason': 'a'}, {'delta': 0, 'reason': 'a'}, {'delta': 2, 'reason': ''},
                     {'delta': -10, 'reason': 'mất'}):
            self.client.post(url, data)
        self.book.refresh_from_db(); self.assertEqual(self.book.stock, 4)
        self.client.post(url, {'delta': -1, 'reason': 'Rách'})
        self.book.refresh_from_db(); self.assertEqual(self.book.stock, 3)
        self.assertTrue(StockMovement.objects.filter(reason='Rách', delta=-1).exists())
        self.assertContains(self.client.get(reverse('manage_inventory')), 'Rừng Na Uy')

    def test_book_add_and_list(self):
        self.client.post(reverse('manage_book_add'), {'category': self.cat.pk, 'title_vi': 'Sách mới', 'slug': 'Sách Mới',
                                                      'isbn': 'BO-2', 'price': 50000, 'cost_price': 0, 'min_stock': 1,
                                                      'restock_days': 10, 'cover': 'cover-default.svg', 'active': 'on'})
        self.assertEqual(Book.objects.get(isbn='BO-2').slug, 'sach-moi')
        self.client.post(reverse('manage_book_add'), {'category': self.cat.pk, 'title_vi': 'Đắc nhân tâm', 'slug': 'Đắc nhân tâm',
                                                      'isbn': 'BO-3', 'price': 50000, 'cost_price': 0, 'min_stock': 1,
                                                      'restock_days': 10, 'cover': 'cover-default.svg', 'active': 'on'})
        self.assertEqual(Book.objects.get(isbn='BO-3').slug, 'dac-nhan-tam')
        self.assertContains(self.client.get(reverse('manage_books')), 'Sách mới')
