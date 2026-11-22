from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Book, Category, Order, StockMovement
from .services import BusinessError, change_order_status, create_order


@override_settings(BANK_BIN='970422', BANK_ACCOUNT='0011002233445', BANK_OWNER='NGUYEN VAN MAU')
class PreorderFixture(TestCase):
    def setUp(self):
        cat = Category.objects.create(name_vi='Văn hóa', slug='van-hoa')
        self.book = Book.objects.create(category=cat, title_vi='Sách còn 2', slug='con-2', isbn='PRE-1',
                                        price=100000, stock=2, restock_days=12)
        self.gone = Book.objects.create(category=cat, title_vi='Sách hết', slug='het', isbn='PRE-2',
                                        price=50000, stock=0, restock_days=7)
        self.closed = Book.objects.create(category=cat, title_vi='Không nhận đặt', slug='khong-dat', isbn='PRE-3',
                                          price=50000, stock=0, allow_preorder=False)
        self.staff = get_user_model().objects.create_user('kho1', password='StrongPassword123!', is_staff=True)

    def order(self, lines, **kw):
        return create_order(raw_lines=lines, source='web', payment_method='cod', full_name='Khách',
                            phone='0901234567', address='Huế', shipping_fee=0, allow_preorder=True, **kw)


class PreorderTests(PreorderFixture):

    def test_short_line_takes_stock_and_waits_for_rest(self):
        o = self.order([(self.book.pk, 5), (self.gone.pk, 1)])
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 0)
        self.assertTrue(o.is_preorder)
        self.assertEqual(o.expected_date, timezone.localdate() + timedelta(days=12))
        waits = {i.book_id: i.preorder_qty for i in o.items.all()}
        self.assertEqual(waits, {self.book.pk: 3, self.gone.pk: 1})

    def test_in_stock_order_is_not_preorder(self):
        o = self.order([(self.book.pk, 2)])
        self.assertFalse(o.is_preorder)
        self.assertIsNone(o.expected_date)

    def test_book_closed_to_preorder_is_refused(self):
        with self.assertRaises(BusinessError):
            self.order([(self.closed.pk, 1)])

    def test_pos_never_preorders(self):
        with self.assertRaises(BusinessError):
            create_order(raw_lines=[(self.gone.pk, 1)], source='pos', payment_method='cash',
                         full_name='Khách', phone='0000000000', user=self.staff, shipping_fee=0)

    def test_cancel_returns_only_books_actually_taken(self):
        o = self.order([(self.book.pk, 5)])
        change_order_status(o.pk, 'cancelled', self.staff)
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 2)

    def test_packing_needs_the_books_to_have_arrived(self):
        o = self.order([(self.gone.pk, 2)])
        change_order_status(o.pk, 'confirmed', self.staff)
        with self.assertRaises(BusinessError):
            change_order_status(o.pk, 'packing', self.staff)
        Book.objects.filter(pk=self.gone.pk).update(stock=3)
        change_order_status(o.pk, 'packing', self.staff)
        self.gone.refresh_from_db()
        self.assertEqual(self.gone.stock, 1)
        self.assertEqual(o.items.get().preorder_qty, 0)
        self.assertTrue(StockMovement.objects.filter(reference=o.order_code, delta=-2).exists())
        change_order_status(o.pk, 'cancelled', self.staff)
        self.gone.refresh_from_db()
        self.assertEqual(self.gone.stock, 3)

    def test_guest_can_preorder_through_the_shop(self):
        self.client.post(reverse('cart_add', args=[self.gone.pk]), {'quantity': 1})
        page = self.client.get(reverse('checkout'))
        self.assertContains(page, 'khoảng 7 ngày')
        resp = self.client.post(reverse('checkout'), {'full_name': 'Khách', 'phone': '0901234567',
                                                      'address': 'Huế', 'payment_method': 'bank',
                                                      'accept_preorder': '7'})
        o = Order.objects.get()
        self.assertRedirects(resp, reverse('order_success', args=[o.order_code]))
        done = self.client.get(resp.url)
        self.assertContains(done, 'Dự kiến có hàng')
        self.assertContains(done, o.expected_date.strftime('%d/%m/%Y'))

    def test_shop_shows_preorder_button_only_when_allowed(self):
        page = self.client.get(reverse('catalog')).content.decode()
        self.assertIn('Đặt trước Sách hết', page)
        self.assertNotIn('Đặt trước Không nhận đặt', page)
        resp = self.client.post(reverse('cart_add', args=[self.closed.pk]), {'quantity': 1})
        self.assertEqual(self.client.session.get('hep_cart', {}), {})
        self.assertEqual(resp.status_code, 302)


class PreorderAuditFixTests(PreorderFixture):
    """Regression tests for the auditor's HIGH findings (06_auditor_report.md)."""

    def test_arrivals_go_to_waiting_preorders_before_new_buyers(self):
        from .models import PurchaseItem, PurchaseOrder, Supplier
        first = self.order([(self.gone.pk, 1)])
        sup = Supplier.objects.create(name='NCC')
        po = PurchaseOrder.objects.create(supplier=sup, created_by=self.staff)
        PurchaseItem.objects.create(purchase=po, book=self.gone, quantity=1, unit_cost=30000)
        from .services import receive_purchase
        receive_purchase(po.pk, self.staff)
        self.gone.refresh_from_db()
        self.assertEqual(self.gone.stock, 0, 'Sách vừa về phải giữ cho đơn đặt trước')
        self.assertEqual(first.items.get().preorder_qty, 0)
        later = self.order([(self.gone.pk, 1)])
        self.assertTrue(later.is_preorder, 'Khách sau phải xếp hàng, không lấy mất sách của đơn trước')
        change_order_status(first.pk, 'confirmed', self.staff)
        change_order_status(first.pk, 'packing', self.staff)

    def test_manual_stock_increase_also_feeds_preorders(self):
        o = self.order([(self.gone.pk, 2)])
        self.client.force_login(get_user_model().objects.create_superuser('boss', password='StrongPassword123!'))
        self.client.post(reverse('adjust_stock', args=[self.gone.pk]), {'delta': 3, 'reason': 'Hàng về'})
        self.gone.refresh_from_db()
        self.assertEqual(self.gone.stock, 1)
        self.assertEqual(o.items.get().preorder_qty, 0)

    def test_unpaid_bank_order_cannot_be_packed_or_shipped(self):
        o = create_order(raw_lines=[(self.book.pk, 1)], source='web', payment_method='bank', full_name='Khách',
                         phone='0901234567', address='Huế', shipping_fee=0)
        change_order_status(o.pk, 'confirmed', self.staff)
        for status in ('packing', 'completed'):
            with self.assertRaises(BusinessError):
                change_order_status(o.pk, status, self.staff)

    def test_checkout_never_silently_turns_into_preorder(self):
        self.client.post(reverse('cart_add', args=[self.book.pk]), {'quantity': 2})
        Book.objects.filter(pk=self.book.pk).update(stock=0)  # sold out between cart and checkout
        form = {'full_name': 'Khách', 'phone': '0901234567', 'address': 'Huế', 'payment_method': 'cod'}
        resp = self.client.post(reverse('checkout'), form)
        self.assertRedirects(resp, reverse('checkout'))
        self.assertFalse(Order.objects.exists())
        self.assertContains(self.client.get(reverse('checkout')), 'name="accept_preorder" value="12"')
        self.client.post(reverse('checkout'), {**form, 'accept_preorder': '12'})
        self.assertTrue(Order.objects.get().is_preorder)
