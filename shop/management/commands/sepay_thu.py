"""Simulate SePay reporting a transfer, for the test environment without public hosting.

    python manage.py sepay_thu HEP261121A1B2C3D4            # đúng số tiền của đơn
    python manage.py sepay_thu HEP261121A1B2C3D4 --amount 50000
"""
import secrets

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from shop.payments import find_order, record_sepay


class Command(BaseCommand):
    help = 'Giả lập SePay báo một khoản chuyển khoản vào cho đơn hàng (chỉ dùng khi kiểm thử).'

    def add_arguments(self, parser):
        parser.add_argument('order_code')
        parser.add_argument('--amount', type=int, default=None)

    def handle(self, order_code, amount, **_):
        order = find_order(order_code)
        if order is None:
            raise CommandError(f'Không tìm thấy đơn {order_code}.')
        payload = {'id': 'TEST-' + secrets.token_hex(6), 'gateway': 'MBBank',
                   'transactionDate': timezone.localtime().strftime('%Y-%m-%d %H:%M:%S'),
                   'accountNumber': '', 'content': f'{order.order_code} chuyen khoan thu', 'transferType': 'in',
                   'transferAmount': amount if amount is not None else order.total, 'referenceCode': 'THU-NGHIEM'}
        txn, _ = record_sepay(payload)
        order.refresh_from_db()
        self.stdout.write(self.style.SUCCESS(f'Giao dịch {txn.provider_txn_id}: {txn.get_status_display()}. '
                                             f'Đơn {order.order_code}: {order.get_payment_status_display()}.'))
