"""Incoming bank transfers reported by SePay.

SePay posts one JSON document per transaction with ``Authorization: Apikey <key>``.
We store every incoming transfer, then try to match it to an unpaid bank order by the
order code inside the transfer content and the exact amount. Only an exact match marks
the order paid; everything else is left for staff to resolve by hand.
"""
import hmac
import re
from datetime import datetime

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Value
from django.db.models.functions import Replace, Upper
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from .models import Order, PaymentTransaction
from .services import BusinessError, mark_paid

ORDER_CODE_RE = re.compile(r'HEP\d{6}[0-9A-F]{8}')
MAX_AMOUNT = 10 ** 12  # far above any book order; rejects absurd values before int overflow paths


class PayloadError(ValueError):
    pass


@sensitive_variables('expected', 'supplied')
def api_key_valid(header_value):
    """Constant-time check of ``Authorization: Apikey <key>`` against settings.

    Compares bytes: hmac.compare_digest raises TypeError on non-ASCII str, which used to
    surface as a 500 debug page containing the key.
    """
    expected = getattr(settings, 'SEPAY_API_KEY', '')
    if not expected or not isinstance(header_value, str) or not header_value:
        return False
    scheme, _, supplied = header_value.strip().partition(' ')
    if scheme.lower() != 'apikey':
        return False
    return hmac.compare_digest(supplied.strip().encode('utf-8'), expected.encode('utf-8'))


def normalize(text):
    return re.sub(r'[^0-9A-Z]', '', (text or '').upper())


def find_orders(content, code=None):
    """All distinct orders whose code appears in the transfer content (separators ignored)."""
    candidates = list(dict.fromkeys(ORDER_CODE_RE.findall(normalize(str(code or ''))) +
                                    ORDER_CODE_RE.findall(normalize(str(content or '')))))
    if not candidates:
        return []
    qs = Order.objects.annotate(code_norm=Upper(Replace('order_code', Value('-'), Value(''))))
    return list(qs.filter(code_norm__in=candidates))


def find_order(content, code=None):
    """The single order referenced by the content, or None when zero or several match."""
    orders = find_orders(content, code)
    return orders[0] if len(orders) == 1 else None


def _parse_time(raw):
    if not raw:
        return None
    try:
        return timezone.make_aware(datetime.strptime(str(raw), '%Y-%m-%d %H:%M:%S'))
    except (ValueError, TypeError):
        return None


def _amount(raw):
    """Whole VND only: int (not bool) or a digit string. Floats like 100.9 are rejected, not truncated."""
    if isinstance(raw, bool):
        raise PayloadError('transferAmount không hợp lệ.')
    if isinstance(raw, int):
        value = raw
    elif isinstance(raw, str) and raw.strip().isdigit() and len(raw.strip()) <= 13:
        value = int(raw.strip())
    else:
        raise PayloadError('transferAmount phải là số nguyên VND.')
    if not 0 < value <= MAX_AMOUNT:
        raise PayloadError('transferAmount ngoài phạm vi.')
    return value


def _clean(payload):
    txn_id = str(payload.get('id', '')).strip()
    if not txn_id or len(txn_id) > 64:
        raise PayloadError('Thiếu id giao dịch.')
    return txn_id, _amount(payload.get('transferAmount'))


def record_sepay(payload):
    """Store and apply one SePay transaction. Idempotent on SePay's id.

    Returns (transaction, created). Raises PayloadError for malformed input.
    Outgoing transfers (transferType != 'in') are ignored and return (None, False).
    """
    if not isinstance(payload, dict):
        raise PayloadError('Payload phải là object JSON.')
    if str(payload.get('transferType', 'in')).lower() != 'in':
        return None, False
    txn_id, amount = _clean(payload)
    existing = PaymentTransaction.objects.filter(provider='sepay', provider_txn_id=txn_id).first()
    if existing:
        return existing, False
    content = str(payload.get('content') or payload.get('description') or '')[:2000]
    try:
        with transaction.atomic():
            orders = find_orders(content, payload.get('code'))
            order = orders[0] if len(orders) == 1 else None
            if len(orders) > 1:
                status = 'multiple_orders'
            elif order is None or order.payment_method != 'bank' or order.status == 'cancelled':
                status = 'unmatched'
            elif order.payment_status == 'paid':
                status = 'duplicate_paid'
            elif amount != order.total:
                status = 'amount_mismatch'
            else:
                status = 'matched'
            txn = PaymentTransaction.objects.create(
                order=order, provider='sepay', provider_txn_id=txn_id,
                reference_code=str(payload.get('referenceCode') or '')[:64],
                gateway=str(payload.get('gateway') or '')[:40],
                account_number=str(payload.get('accountNumber') or '')[:30],
                amount=amount, content=content, status=status, raw_payload=payload,
                transaction_at=_parse_time(payload.get('transactionDate')))
            if status == 'matched':
                try:
                    with transaction.atomic():
                        mark_paid(order.pk, None, via='sepay')
                except BusinessError:
                    # Order was cancelled or paid between lookup and lock: keep the money record.
                    order.refresh_from_db()
                    txn.status = 'duplicate_paid' if order.payment_status == 'paid' else 'unmatched'
                    txn.save(update_fields=['status'])
    except IntegrityError:  # concurrent retry of the same SePay id
        return PaymentTransaction.objects.get(provider='sepay', provider_txn_id=txn_id), False
    return txn, True


@transaction.atomic
def resolve_manually(txn_id, order_code, actor):
    """Staff attaches an unmatched transfer to an order and confirms payment."""
    txn = PaymentTransaction.objects.select_for_update().get(pk=txn_id)
    if txn.status == 'matched':
        raise BusinessError('Giao dịch này đã khớp đơn.')
    order = find_order(order_code)
    if order is None:
        raise BusinessError('Không tìm thấy đơn với mã này.')
    if txn.amount != order.total:
        raise BusinessError(f'Số tiền nhận ({txn.amount:,}đ) khác tổng đơn ({order.total:,}đ). '
                            'Kiểm tra lại với khách rồi xác nhận thủ công trong trang đơn.'.replace(',', '.'))
    mark_paid(order.pk, actor, via='manual')
    txn.order = order; txn.status = 'matched'; txn.resolved_by = actor
    txn.save(update_fields=['order', 'status', 'resolved_by'])
    return txn
