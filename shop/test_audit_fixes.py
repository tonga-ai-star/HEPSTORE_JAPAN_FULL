"""Regression tests for the MEDIUM/LOW findings in _workspace/06_auditor_report.md."""
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Book, Category, Order, StaffProfile, StockMovement
from .services import BusinessError, cancel_with_refund, change_order_status, create_order, expire_stale_orders, mark_paid

User = get_user_model()
PW = 'Hep-Staff-Pass-2026'


def staff(username, role=None, superuser=False):
    u = User.objects.create_user(username, password=PW, is_staff=True, is_superuser=superuser)
    if role:
        StaffProfile.objects.create(user=u, role=role)
    return u


class Base(TestCase):
    def setUp(self):
        cat = Category.objects.create(name_vi='Văn hóa', slug='van-hoa')
        self.book = Book.objects.create(category=cat, title_vi='Sách A', slug='a', isbn='AF-1', price=100000, stock=3)
        self.gone = Book.objects.create(category=cat, title_vi='Sách hết', slug='het', isbn='AF-2', price=50000,
                                        stock=0, restock_days=5)
        self.boss = staff('boss', superuser=True)
        self.seller = staff('ban', 'sales')
        self.keeper = staff('kho', 'warehouse')

    def web_order(self, lines, method='cod', phone='0901234567', **kw):
        return create_order(raw_lines=lines, source='web', payment_method=method, full_name='Khách', phone=phone,
                            address='Huế', shipping_fee=0, allow_preorder=True, **kw)


class RefundTests(Base):
    def paid_preorder(self):
        o = self.web_order([(self.book.pk, 1), (self.gone.pk, 2)], method='bank')
        mark_paid(o.pk, self.boss, via='sepay')
        return o

    def test_manager_cancels_paid_preorder_with_refund_note(self):
        o = self.paid_preorder()
        cancel_with_refund(o.pk, self.boss, 'CK trả lại, mã GD FT123')
        o.refresh_from_db(); self.book.refresh_from_db()
        self.assertEqual((o.status, o.payment_status), ('cancelled', 'refunded'))
        self.assertIn('FT123', o.note)
        self.assertEqual(self.book.stock, 3, 'Sách đã trừ phải về kho')
        self.assertEqual(o.items.get(book=self.gone).preorder_qty, 0, 'Đơn đã hủy không còn chờ hàng')

    def test_refund_requires_note_paid_and_not_shipped(self):
        o = self.paid_preorder()
        with self.assertRaises(BusinessError):
            cancel_with_refund(o.pk, self.boss, '  ')
        unpaid = self.web_order([(self.book.pk, 1)])
        with self.assertRaises(BusinessError):
            cancel_with_refund(unpaid.pk, self.boss, 'x')

    def test_returned_books_go_to_next_waiting_preorder(self):
        waiting = self.web_order([(self.book.pk, 3)], phone='0911111111')  # takes all 3
        later = self.web_order([(self.book.pk, 2)], phone='0922222222')     # waits for 2
        self.assertEqual(later.items.get().preorder_qty, 2)
        change_order_status(waiting.pk, 'cancelled', self.boss)
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock, 1)
        self.assertEqual(later.items.get().preorder_qty, 0)

    def test_only_manager_sees_and_uses_refund(self):
        o = self.paid_preorder()
        url = reverse('order_refund', args=[o.pk])
        self.client.force_login(self.seller)
        self.assertEqual(self.client.post(url, {'note': 'x'}).status_code, 403)
        self.assertNotContains(self.client.get(reverse('manage_order_detail', args=[o.pk])), url)
        self.client.force_login(self.boss)
        self.assertContains(self.client.get(reverse('manage_order_detail', args=[o.pk])), url)
        self.client.post(url, {'note': 'Đã CK trả'})
        o.refresh_from_db()
        self.assertEqual(o.payment_status, 'refunded')
        self.assertContains(self.client.get(reverse('manage_orders')), 'Đã hoàn tiền')

    def test_refunded_order_cannot_be_marked_paid_again(self):
        o = self.paid_preorder()
        cancel_with_refund(o.pk, self.boss, 'trả')
        with self.assertRaises(BusinessError):
            mark_paid(o.pk, self.boss)


class StaleHoldTests(Base):
    def age(self, order, days):
        Order.objects.filter(pk=order.pk).update(created_at=timezone.now() - timedelta(days=days))

    @override_settings(ORDER_HOLD_DAYS=3)
    def test_old_unconfirmed_orders_release_stock(self):
        old = self.web_order([(self.book.pk, 3)])
        fresh = self.web_order([(self.book.pk, 1)], phone='0933333333')  # pre-order, stock is 0
        self.age(old, 4)
        self.assertEqual(expire_stale_orders(), 1)
        old.refresh_from_db(); self.book.refresh_from_db()
        self.assertEqual(old.status, 'cancelled')
        self.assertEqual(fresh.items.get().preorder_qty, 0, 'Sách nhả ra phải về đơn đang chờ')
        self.assertEqual(self.book.stock, 2)

    @override_settings(ORDER_HOLD_DAYS=3)
    def test_confirmed_paid_pos_and_waiting_preorders_are_kept(self):
        confirmed = self.web_order([(self.book.pk, 1)])
        change_order_status(confirmed.pk, 'confirmed', self.boss)
        paid = self.web_order([(self.book.pk, 1)], method='bank', phone='0944444444')
        mark_paid(paid.pk, self.boss)
        pre = self.web_order([(self.gone.pk, 1)], phone='0955555555')  # expected in 5 days
        for o in (confirmed, paid, pre):
            self.age(o, 4)
        self.assertEqual(expire_stale_orders(), 0)
        self.age(pre, 9)
        Order.objects.filter(pk=pre.pk).update(expected_date=timezone.localdate() - timedelta(days=4))
        self.assertEqual(expire_stale_orders(), 1)

    @override_settings(ORDER_HOLD_DAYS=3)
    def test_dashboard_and_command_run_expiry(self):
        old = self.web_order([(self.book.pk, 1)])
        self.age(old, 5)
        out = StringIO()
        call_command('huy_don_qua_han', stdout=out)
        self.assertIn('1 đơn', out.getvalue())
        again = self.web_order([(self.book.pk, 1)], phone='0966666666')
        self.age(again, 5)
        self.client.force_login(self.boss)
        self.client.get(reverse('dashboard'))
        again.refresh_from_db()
        self.assertEqual(again.status, 'cancelled')
        self.assertTrue(StockMovement.objects.filter(reference=again.order_code, delta=1).exists())

    @override_settings(MAX_OPEN_WEB_ORDERS=2)
    def test_one_phone_cannot_hold_unlimited_cod_orders(self):
        for _ in range(2):
            self.web_order([(self.book.pk, 1)])
        self.client.post(reverse('cart_add', args=[self.book.pk]), {'quantity': 1})
        resp = self.client.post(reverse('checkout'), {'full_name': 'Khách', 'phone': '0901234567',
                                                      'address': 'Huế', 'payment_method': 'cod'}, follow=True)
        self.assertContains(resp, 'đơn chưa xác nhận')
        self.assertEqual(Order.objects.count(), 2)


class DutySplitTests(Base):
    def edit_url(self):
        return reverse('manage_book_edit', args=[self.book.pk])

    def book_post(self, **over):
        data = {'category': self.book.category_id, 'title_vi': 'Sách A', 'slug': 'a', 'isbn': 'AF-1',
                'price': 1000, 'cost_price': 0, 'min_stock': 1, 'restock_days': 10, 'cover': 'cover-default.svg',
                'active': 'on', 'allow_preorder': 'on'}
        data.update(over)
        return data

    def test_warehouse_cannot_change_price_of_existing_book(self):
        self.client.force_login(self.keeper)
        self.client.post(self.edit_url(), self.book_post(title_vi='Sách A mới'))
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, 100000, 'Giá phải giữ nguyên')
        self.assertEqual(self.book.title_vi, 'Sách A mới', 'Các trường khác vẫn sửa được')

    def test_manager_can_change_price(self):
        self.client.force_login(self.boss)
        self.client.post(self.edit_url(), self.book_post(price=120000))
        self.book.refresh_from_db()
        self.assertEqual(self.book.price, 120000)

    def test_sales_cannot_mark_money_received_by_hand(self):
        o = self.web_order([(self.book.pk, 1)], method='bank')
        self.client.force_login(self.seller)
        self.assertEqual(self.client.post(reverse('payment_confirm', args=[o.pk])).status_code, 403)
        page = self.client.get(reverse('manage_order_detail', args=[o.pk]))
        self.assertNotContains(page, reverse('payment_confirm', args=[o.pk]))
        self.assertContains(page, 'báo quản lý xác nhận')
        o.refresh_from_db()
        self.assertEqual(o.payment_status, 'unpaid')

    def test_sales_still_sells_cash_at_pos(self):
        o = create_order(raw_lines=[(self.book.pk, 1)], source='pos', payment_method='cash', full_name='Khách',
                         phone='0000000000', user=self.seller, shipping_fee=0, paid=True)
        self.assertEqual(o.payment_status, 'paid')

    def test_books_list_shows_preorder_setting(self):
        self.client.force_login(self.keeper)
        self.assertContains(self.client.get(reverse('manage_books')), 'Đặt trước 5 ngày')


class RecheckFixTests(Base):
    """Findings from _workspace/09_auditor_recheck.md."""

    @override_settings(ORDER_HOLD_DAYS=3, SEPAY_API_KEY='k')
    def test_orders_with_a_transfer_attached_are_never_auto_cancelled(self):
        from .payments import record_sepay
        short = self.web_order([(self.book.pk, 1)], method='bank')
        record_sepay({'id': 'T1', 'transferType': 'in', 'transferAmount': 1000, 'content': short.order_code})
        Order.objects.filter(pk=short.pk).update(created_at=timezone.now() - timedelta(days=5))
        self.assertEqual(expire_stale_orders(), 0)
        short.refresh_from_db()
        self.assertEqual(short.status, 'new')

    def test_cancelled_order_page_hides_qr_and_warns(self):
        o = self.web_order([(self.book.pk, 1)], method='bank')
        change_order_status(o.pk, 'cancelled', None)
        with self.settings(BANK_BIN='970422', BANK_ACCOUNT='0011002233445', BANK_OWNER='NGUYEN VAN MAU'):
            session = self.client.session; session['hep_recent_orders'] = [o.order_code]; session.save()
            for page in (self.client.get(reverse('order_success', args=[o.order_code])),
                         self.client.post(reverse('track_order'), {'order_code': o.order_code, 'phone': o.phone})):
                self.assertContains(page, 'Đơn này đã hủy')
                self.assertNotContains(page, 'img.vietqr.io')
                self.assertNotContains(page, 'data-payment-poll')

    @override_settings(MAX_OPEN_WEB_ORDERS=2)
    def test_order_cap_ignores_phone_formatting(self):
        self.web_order([(self.book.pk, 1)], phone='0911111111')
        self.web_order([(self.book.pk, 1)], phone='+84 911 111 111')
        self.client.post(reverse('cart_add', args=[self.book.pk]), {'quantity': 1})
        self.client.post(reverse('checkout'), {'full_name': 'K', 'phone': '0911.111.111', 'address': 'Huế',
                                               'payment_method': 'cod'})
        self.assertEqual(Order.objects.count(), 2)

    def test_customer_must_accept_the_actual_wait(self):
        Book.objects.filter(pk=self.gone.pk).update(restock_days=30)
        self.client.post(reverse('cart_add', args=[self.gone.pk]), {'quantity': 1})
        form = {'full_name': 'K', 'phone': '0912345678', 'address': 'Huế', 'payment_method': 'cod'}
        resp = self.client.post(reverse('checkout'), {**form, 'accept_preorder': '5'})  # saw 5 days, now 30
        self.assertRedirects(resp, reverse('checkout'))
        self.assertFalse(Order.objects.exists())
        self.client.post(reverse('checkout'), {**form, 'accept_preorder': 'x'})
        self.assertFalse(Order.objects.exists())
        self.client.post(reverse('checkout'), {**form, 'accept_preorder': '30'})
        self.assertEqual(Order.objects.get().expected_date, timezone.localdate() + timedelta(days=30))

    def test_paid_preorders_get_arrivals_before_unpaid_ones(self):
        unpaid = self.web_order([(self.gone.pk, 1)], phone='0911111111')
        paid = self.web_order([(self.gone.pk, 1)], method='bank', phone='0922222222')
        mark_paid(paid.pk, self.boss)
        self.client.force_login(self.boss)
        self.client.post(reverse('adjust_stock', args=[self.gone.pk]), {'delta': 1, 'reason': 'Hàng về'})
        self.assertEqual(paid.items.get().preorder_qty, 0)
        self.assertEqual(unpaid.items.get().preorder_qty, 1)

    def test_unpaid_bank_order_detail_offers_no_shipping_buttons(self):
        o = self.web_order([(self.book.pk, 1)], method='bank')
        change_order_status(o.pk, 'confirmed', self.boss)
        self.client.force_login(self.boss)
        page = self.client.get(reverse('manage_order_detail', args=[o.pk])).content.decode()
        self.assertNotIn('value="packing"', page)
        self.assertNotIn('value="completed"', page)
        self.assertIn('value="cancelled"', page)

    def test_busy_database_does_not_break_dashboard(self):
        from unittest import mock
        from django.db import OperationalError
        old = self.web_order([(self.book.pk, 1)])
        Order.objects.filter(pk=old.pk).update(created_at=timezone.now() - timedelta(days=9))
        with mock.patch('shop.services.change_order_status', side_effect=OperationalError('database is locked')):
            self.assertEqual(expire_stale_orders(), 0)


class FullAuditFixTests(Base):
    """Findings from _workspace/13_auditor_full.md."""

    @override_settings(ORDER_HOLD_DAYS=3)
    def test_right_amount_with_wrong_note_keeps_order_alive(self):
        from .payments import record_sepay
        o = self.web_order([(self.book.pk, 1)], method='bank')
        record_sepay({'id': 'W1', 'transferType': 'in', 'transferAmount': o.total, 'content': 'chuyen tien mua sach'})
        Order.objects.filter(pk=o.pk).update(created_at=timezone.now() - timedelta(days=5))
        self.assertEqual(expire_stale_orders(), 0)
        other = self.web_order([(self.book.pk, 2)], method='bank', phone='0977777777')  # different total
        Order.objects.filter(pk=other.pk).update(created_at=timezone.now() - timedelta(days=5))
        self.assertEqual(expire_stale_orders(), 1)

    def test_phone_key_folds_every_vietnamese_format(self):
        from .services import phone_key
        for raw in ('0912 345 678', '+84 912 345 678', '84912345678', '0084 912345678', '+84 (0)912.345.678'):
            self.assertEqual(phone_key(raw), '0912345678', raw)

    def test_track_order_accepts_differently_formatted_phone(self):
        o = self.web_order([(self.book.pk, 1)], phone='0912 345 678')
        r = self.client.post(reverse('track_order'), {'order_code': o.order_code, 'phone': '+84912345678'})
        self.assertContains(r, o.order_code)
        r = self.client.post(reverse('track_order'), {'order_code': o.order_code, 'phone': '0912345679'})
        self.assertContains(r, 'Không tìm thấy')

    def test_paid_order_detail_has_no_plain_cancel_button(self):
        o = self.web_order([(self.book.pk, 1)], method='bank')
        mark_paid(o.pk, self.boss)
        self.client.force_login(self.boss)
        page = self.client.get(reverse('manage_order_detail', args=[o.pk])).content.decode()
        self.assertNotIn('value="cancelled"', page)
        self.assertIn(reverse('order_refund', args=[o.pk]), page)

    def test_book_lists_do_not_query_category_per_book(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        for i in range(6):
            Book.objects.create(category=self.book.category, title_vi=f'S{i}', slug=f's{i}', isbn=f'NQ-{i}',
                                price=1000, stock=1, featured=True)
        for url in (reverse('home'), reverse('book_detail', args=[self.book.slug])):
            with CaptureQueriesContext(connection) as ctx:
                self.client.get(url)
            cat_queries = [q for q in ctx.captured_queries if 'FROM "shop_category"' in q['sql']
                           and 'WHERE "shop_category"."id" =' in q['sql']]
            self.assertLessEqual(len(cat_queries), 1, url)
