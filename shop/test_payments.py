import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Book, Category, Order, PaymentTransaction
from .services import create_order

KEY = 'test-sepay-key-4f1c'


def sepay(order_code='', amount=0, txn_id=1, **extra):
    data = {'id': txn_id, 'gateway': 'Vietcombank', 'transactionDate': '2026-11-21 10:15:02',
            'accountNumber': '0011002233445', 'code': None, 'content': f'MBVCB.123 {order_code} chuyen tien',
            'transferType': 'in', 'transferAmount': amount, 'accumulated': 0, 'subAccount': None,
            'referenceCode': f'FT{txn_id:08d}', 'description': ''}
    data.update(extra)
    return data


@override_settings(SEPAY_API_KEY=KEY)
class SepayWebhookTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name_vi='Học tiếng Nhật', slug='hoc-tieng-nhat')
        self.book = Book.objects.create(category=cat, title_vi='Katakana mỗi ngày', slug='katakana', isbn='HEP-T-001', price=72000, stock=5)
        self.order = create_order(raw_lines=[(self.book.id, 1)], source='web', payment_method='bank',
                                  full_name='Đỗ Minh Khuê', phone='0903118274', address='Đà Nẵng', shipping_fee=25000)

    def post(self, payload, key=KEY, content_type='application/json'):
        body = json.dumps(payload) if content_type == 'application/json' else payload
        return self.client.post(reverse('sepay_webhook'), body, content_type=content_type,
                                HTTP_AUTHORIZATION=f'Apikey {key}')

    def test_new_order_code_has_no_separators(self):
        self.assertRegex(self.order.order_code, r'^HEP\d{6}[0-9A-F]{8}$')

    def test_matching_transfer_marks_order_paid_and_confirmed(self):
        r = self.post(sepay(self.order.order_code, self.order.total))
        self.assertEqual(r.status_code, 200); self.assertEqual(r.json(), {'success': True})
        self.order.refresh_from_db()
        self.assertEqual(self.order.payment_status, 'paid')
        self.assertEqual(self.order.paid_via, 'sepay')
        self.assertEqual(self.order.status, 'confirmed')
        self.assertEqual(PaymentTransaction.objects.get().status, 'matched')

    def test_bank_lowercase_and_spaces_in_content_still_match(self):
        code = self.order.order_code.lower()
        r = self.post(sepay('', self.order.total, content=f'ck {code[:5]} {code[5:]} cam on'))
        self.assertEqual(r.status_code, 200)
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'paid')

    def test_old_hyphenated_codes_still_match(self):
        Order.objects.filter(pk=self.order.pk).update(order_code='HEP-261121-ABCD1234')
        self.post(sepay('HEP261121ABCD1234', self.order.total))
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'paid')

    def test_wrong_api_key_is_rejected_and_nothing_stored(self):
        r = self.post(sepay(self.order.order_code, self.order.total), key='guess')
        self.assertEqual(r.status_code, 401)
        self.assertFalse(PaymentTransaction.objects.exists())
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')

    def test_missing_authorization_is_rejected(self):
        r = self.client.post(reverse('sepay_webhook'), json.dumps(sepay(self.order.order_code, self.order.total)), content_type='application/json')
        self.assertEqual(r.status_code, 401)

    @override_settings(SEPAY_API_KEY='')
    def test_unconfigured_key_returns_503(self):
        self.assertEqual(self.post(sepay(self.order.order_code, self.order.total), key='').status_code, 503)

    def test_retry_of_same_id_is_idempotent(self):
        payload = sepay(self.order.order_code, self.order.total, txn_id=77)
        self.post(payload); r = self.post(payload)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(PaymentTransaction.objects.count(), 1)

    def test_amount_mismatch_does_not_mark_paid(self):
        self.post(sepay(self.order.order_code, self.order.total - 1000))
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')
        self.assertEqual(PaymentTransaction.objects.get().status, 'amount_mismatch')

    def test_unknown_code_is_stored_as_unmatched(self):
        r = self.post(sepay('HEP261121FFFFFFFF', 50000))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(PaymentTransaction.objects.get().status, 'unmatched')

    def test_second_payment_for_paid_order_is_flagged(self):
        self.post(sepay(self.order.order_code, self.order.total, txn_id=1))
        self.post(sepay(self.order.order_code, self.order.total, txn_id=2))
        self.assertEqual(PaymentTransaction.objects.get(provider_txn_id='2').status, 'duplicate_paid')

    def test_outgoing_transfer_is_ignored(self):
        self.post(sepay(self.order.order_code, self.order.total, transferType='out'))
        self.assertFalse(PaymentTransaction.objects.exists())

    def test_malformed_amount_returns_400(self):
        self.assertEqual(self.post(sepay(self.order.order_code, 'abc')).status_code, 400)

    def test_form_encoded_payload_is_accepted(self):
        payload = {k: ('' if v is None else v) for k, v in sepay(self.order.order_code, self.order.total).items()}
        r = self.client.post(reverse('sepay_webhook'), payload, HTTP_AUTHORIZATION=f'Apikey {KEY}')
        self.assertEqual(r.status_code, 200)
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'paid')

    def test_cancelled_order_is_not_paid(self):
        Order.objects.filter(pk=self.order.pk).update(status='cancelled')
        self.post(sepay(self.order.order_code, self.order.total))
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')


class PaymentStatusEndpointTests(TestCase):
    def setUp(self):
        cat = Category.objects.create(name_vi='Văn hóa', slug='van-hoa')
        book = Book.objects.create(category=cat, title_vi='Trà đạo', slug='tra-dao', isbn='HEP-T-002', price=90000, stock=3)
        self.order = create_order(raw_lines=[(book.id, 1)], source='web', payment_method='bank',
                                  full_name='Ngô Hải Yến', phone='0377120456', address='Huế', shipping_fee=0)
        self.url = reverse('order_payment_status', args=[self.order.order_code])

    def test_stranger_cannot_read_status(self):
        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_buyer_session_reads_status_and_sees_paid(self):
        s = self.client.session; s['hep_recent_orders'] = [self.order.order_code]; s.save()
        self.assertFalse(self.client.get(self.url).json()['paid'])
        Order.objects.filter(pk=self.order.pk).update(payment_status='paid', paid_via='sepay')
        r = self.client.get(self.url)
        self.assertTrue(r.json()['paid']); self.assertIn('no-cache', r['Cache-Control'])

    def test_track_lookup_grants_status_access(self):
        self.client.post(reverse('track_order'), {'order_code': self.order.order_code, 'phone': '0377120456'})
        self.assertEqual(self.client.get(self.url).status_code, 200)

    def test_order_page_contains_poller_for_unpaid_bank_order(self):
        s = self.client.session; s['hep_recent_orders'] = [self.order.order_code]; s.save()
        with self.settings(BANK_BIN='970436', BANK_ACCOUNT='0011002233445', BANK_OWNER='NGUYEN VAN MAU'):
            r = self.client.get(reverse('order_success', args=[self.order.order_code]))
        self.assertContains(r, 'data-payment-poll'); self.assertContains(r, 'payment_poll.js')


class SimulatorCommandTests(TestCase):
    def test_sepay_thu_marks_order_paid(self):
        from io import StringIO
        from django.core.management import call_command
        cat = Category.objects.create(name_vi='Văn học', slug='van-hoc')
        book = Book.objects.create(category=cat, title_vi='Mùa hạ', slug='mua-ha', isbn='HEP-T-003', price=60000, stock=2)
        order = create_order(raw_lines=[(book.id, 1)], source='facebook', payment_method='bank',
                             full_name='Lý Mai Chi', phone='0868221905', address='Cần Thơ', shipping_fee=20000)
        out = StringIO(); call_command('sepay_thu', order.order_code, stdout=out)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid'); self.assertIn('Đã khớp', out.getvalue())


@override_settings(SEPAY_API_KEY=KEY, DEBUG=True)
class SecurityRegressionTests(TestCase):
    """Findings of the 2026-11-21 security review."""
    def setUp(self):
        cat = Category.objects.create(name_vi='Ngôn ngữ', slug='ngon-ngu')
        self.book = Book.objects.create(category=cat, title_vi='Kanji N5', slug='kanji-n5', isbn='HEP-T-010', price=100000, stock=9)
        self.order = create_order(raw_lines=[(self.book.id, 1)], source='web', payment_method='bank',
                                  full_name='Hà Gia Linh', phone='0961773025', address='Vinh', shipping_fee=0)

    def raw(self, body, auth=f'Apikey {KEY}'):
        return self.client.post(reverse('sepay_webhook'), body, content_type='application/json', HTTP_AUTHORIZATION=auth)

    def test_non_ascii_key_is_401_not_500_and_never_leaks_key(self):
        r = self.raw(json.dumps(sepay(self.order.order_code, self.order.total)), auth='Apikey é')
        self.assertEqual(r.status_code, 401)
        self.assertNotIn(KEY, r.content.decode())

    def test_non_object_json_is_400(self):
        for body in ('[1]', '"x"', '42', 'not json'):
            r = self.raw(body)
            self.assertEqual(r.status_code, 400, body); self.assertNotIn(KEY, r.content.decode())

    def test_huge_float_and_bool_amounts_rejected(self):
        for amount in (10 ** 30, 100000.9, True, -5, '12a'):
            r = self.raw(json.dumps(sepay(self.order.order_code, amount)))
            self.assertEqual(r.status_code, 400, amount)
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')

    def test_digit_string_amount_accepted(self):
        self.raw(json.dumps(sepay(self.order.order_code, str(self.order.total))))
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'paid')

    def test_cod_order_is_not_auto_paid(self):
        Order.objects.filter(pk=self.order.pk).update(payment_method='cod')
        self.raw(json.dumps(sepay(self.order.order_code, self.order.total)))
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')
        self.assertEqual(PaymentTransaction.objects.get().status, 'unmatched')

    def test_two_codes_in_one_transfer_go_to_staff(self):
        other = create_order(raw_lines=[(self.book.id, 1)], source='web', payment_method='bank',
                             full_name='Hà Gia Linh', phone='0961773025', address='Vinh', shipping_fee=0)
        self.raw(json.dumps(sepay('', self.order.total + other.total, content=f'{self.order.order_code} {other.order_code}')))
        self.assertEqual(PaymentTransaction.objects.get().status, 'multiple_orders')
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')

    def test_race_with_cancel_still_records_money(self):
        from unittest import mock
        from .services import BusinessError
        with mock.patch('shop.payments.mark_paid', side_effect=BusinessError('Không xác nhận thanh toán cho đơn đã hủy.')):
            r = self.raw(json.dumps(sepay(self.order.order_code, self.order.total, txn_id=900)))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(PaymentTransaction.objects.get(provider_txn_id='900').status, 'unmatched')

    def test_manual_resolve_requires_matching_amount(self):
        from .payments import record_sepay, resolve_manually
        from .services import BusinessError
        txn, _ = record_sepay(sepay('', 10000, txn_id=901, content='chuyen tien'))
        staff = get_user_model().objects.create_user('ketoan', password='Ke-Toan-Pass-88', is_staff=True)
        with self.assertRaises(BusinessError):
            resolve_manually(txn.pk, self.order.order_code, staff)
        self.order.refresh_from_db(); self.assertEqual(self.order.payment_status, 'unpaid')

    @override_settings(TUNNEL_HOSTS=['.trycloudflare.com'], ALLOWED_HOSTS=['.trycloudflare.com', 'testserver'])
    def test_tunnel_host_only_exposes_webhook(self):
        h = 'abc.trycloudflare.com'
        self.assertEqual(self.client.get('/management/', HTTP_HOST=h).status_code, 404)
        self.assertEqual(self.client.get('/admin/', HTTP_HOST=h).status_code, 404)
        self.assertEqual(self.client.get('/', HTTP_HOST=h).status_code, 404)
        with self.settings(DEBUG=True):  # the debug 404 page would list every URL pattern
            r = self.client.get('/api/sepay/khong-co/', HTTP_HOST=h)
            self.assertEqual(r.status_code, 404)
            self.assertNotIn(b'management', r.content)
        r = self.client.post('/api/sepay/webhook/', json.dumps(sepay(self.order.order_code, self.order.total)),
                             content_type='application/json', HTTP_AUTHORIZATION=f'Apikey {KEY}', HTTP_HOST=h)
        self.assertEqual(r.status_code, 200)
