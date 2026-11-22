"""Webhook edge cases and the manual 'attach this transfer to an order' flow used by sales staff."""
import json
from io import StringIO
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Book, Category, Order, PaymentTransaction, StaffProfile
from .payments import record_sepay
from .services import create_order
from .test_payments import KEY, sepay

User = get_user_model()


@override_settings(SEPAY_API_KEY=KEY)
class WebhookEdgeTests(TestCase):
    url = '/api/sepay/webhook/'

    def post(self, body, key=KEY):
        return self.client.post(self.url, body, content_type='application/json', HTTP_AUTHORIZATION=f'Apikey {key}')

    def test_oversized_payload_is_refused_without_saving(self):
        r = self.post('{"content":"' + 'x' * 70000 + '"}')
        self.assertEqual(r.status_code, 413)
        self.assertFalse(PaymentTransaction.objects.exists())

    def test_missing_transaction_id_is_bad_request(self):
        self.assertEqual(self.post(json.dumps({'transferType': 'in', 'transferAmount': 1000})).status_code, 400)

    def test_unexpected_error_returns_plain_json_500(self):
        with self.settings(DEBUG=True), mock.patch('shop.payment_views.record_sepay', side_effect=RuntimeError('boom')):
            r = self.post(json.dumps(sepay('HEP', 1000)))
        self.assertEqual(r.status_code, 500)
        self.assertEqual(r.json(), {'success': False})
        self.assertNotIn(KEY.encode(), r.content)

    def test_missing_server_key_disables_webhook(self):
        with self.settings(SEPAY_API_KEY=''):
            self.assertEqual(self.post(json.dumps(sepay('HEP', 1000)), key='').status_code, 503)


@override_settings(SEPAY_API_KEY=KEY)
class ManualResolveTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name_vi='VH', slug='vh')
        self.book = Book.objects.create(category=cat, title_vi='Sách', slug='s', isbn='PM-1', price=2000, stock=5)
        self.order = create_order(raw_lines=[(self.book.pk, 1)], source='pos', payment_method='bank', full_name='K',
                                  phone='0000000000', shipping_fee=0)
        # Customer typed the wrong transfer note, so SePay could not match it.
        self.txn, _ = record_sepay(sepay('', 2000, txn_id=77, content='chuyen tien sach'))
        self.seller = User.objects.create_user('ban', password='Hep-Staff-Pass-2026', is_staff=True)
        StaffProfile.objects.create(user=self.seller, role='sales')
        self.client.force_login(self.seller)

    def resolve(self, code, txn=None):
        return self.client.post(reverse('payment_resolve', args=[(txn or self.txn).pk]), {'order_code': code}, follow=True)

    def test_sales_attaches_unmatched_transfer_to_order(self):
        self.assertEqual(self.txn.status, 'unmatched')
        r = self.resolve(self.order.order_code.lower())
        self.assertContains(r, 'Đã gắn giao dịch')
        self.order.refresh_from_db(); self.txn.refresh_from_db()
        self.assertEqual((self.order.payment_status, self.order.paid_via), ('paid', 'manual'))
        self.assertEqual((self.txn.status, self.txn.order_id, self.txn.resolved_by), ('matched', self.order.pk, self.seller))
        self.assertContains(self.resolve(self.order.order_code), 'đã khớp đơn')

    def test_wrong_code_amount_or_missing_txn_is_refused(self):
        self.assertContains(self.resolve('HEP000000AAAAAAAA'), 'Không tìm thấy đơn')
        small, _ = record_sepay(sepay('', 1000, txn_id=78, content='thieu tien'))
        self.assertContains(self.resolve(self.order.order_code, small), 'khác tổng đơn')
        self.assertContains(self.client.post(reverse('payment_resolve', args=[9999]), {'order_code': 'x'}, follow=True),
                            'Không tìm thấy giao dịch')
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'unpaid')

    def test_payments_page_filters_by_status(self):
        self.assertContains(self.client.get(reverse('manage_payments'), {'status': 'unmatched'}), '2.000')
        self.assertEqual(self.client.get(reverse('manage_payments'), {'status': 'zzz'}).status_code, 200)

    def test_simulator_command_pays_order(self):
        call_command('sepay_thu', self.order.order_code, stdout=StringIO())
        self.order.refresh_from_db()
        self.assertEqual(self.order.paid_via, 'sepay')


class SeedCommandTests(TestCase):
    def test_seed_demo_is_idempotent(self):
        call_command('seed_demo', stdout=StringIO())
        n = Book.objects.count()
        self.assertGreater(n, 0)
        call_command('seed_demo', stdout=StringIO())
        self.assertEqual(Book.objects.count(), n)
        self.assertFalse(Order.objects.exists())
