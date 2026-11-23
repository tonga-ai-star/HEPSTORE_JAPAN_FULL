"""Release stock held by stale, unconfirmed, unpaid web orders (also runs when staff open the dashboard)."""
from django.conf import settings
from django.core.management.base import BaseCommand

from shop.services import expire_stale_orders


class Command(BaseCommand):
    help = 'Hủy đơn web chưa xác nhận, chưa trả tiền quá HEPSTORE_ORDER_HOLD_DAYS ngày và trả sách về kho.'

    def handle(self, *args, **options):
        n = expire_stale_orders()
        self.stdout.write(f'Đã hủy {n} đơn quá {settings.ORDER_HOLD_DAYS} ngày.')
