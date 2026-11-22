"""SePay webhook, customer payment-status polling and the staff transactions page."""
import json
import logging

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_GET, require_POST

from .models import Order, PaymentTransaction
from .payments import PayloadError, api_key_valid, record_sepay, resolve_manually
from .services import BusinessError

log = logging.getLogger('hepstore.payments')
staff = lambda fn: staff_member_required(fn, login_url='/tai-khoan/login/')  # noqa: E731
MAX_BODY = 64 * 1024


@csrf_exempt
@require_POST
@sensitive_post_parameters()
def sepay_webhook(request):
    """Receive one SePay transaction. 2xx tells SePay to stop retrying."""
    from django.conf import settings
    if not settings.SEPAY_API_KEY:
        return JsonResponse({'success': False, 'message': 'webhook chưa cấu hình'}, status=503)
    if not api_key_valid(request.headers.get('Authorization', '')):
        log.warning('SePay webhook: sai API key từ %s', request.META.get('REMOTE_ADDR'))
        return JsonResponse({'success': False}, status=401)
    if len(request.body) > MAX_BODY:
        return JsonResponse({'success': False, 'message': 'payload quá lớn'}, status=413)
    try:
        if request.content_type == 'application/json':
            payload = json.loads(request.body.decode('utf-8'))
        else:
            payload = request.POST.dict()
        txn, created = record_sepay(payload)
    except (PayloadError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        log.warning('SePay webhook: payload lỗi: %s', exc)
        return JsonResponse({'success': False, 'message': str(exc)}, status=400)
    except Exception:  # never let a webhook error render Django's debug page (it would leak settings)
        log.exception('SePay webhook: lỗi xử lý')
        return JsonResponse({'success': False}, status=500)
    if txn is not None:
        log.info('SePay txn %s -> %s (mới=%s)', txn.provider_txn_id, txn.status, created)
    return JsonResponse({'success': True})


def _can_view_order(request, order):
    if order.order_code in request.session.get('hep_recent_orders', []):
        return True
    user = request.user
    if user.is_authenticated and (user.is_staff or (order.customer and order.customer.user_id == user.pk)):
        return True
    return False


@never_cache
@require_GET
def order_payment_status(request, code):
    """Polled by the order page every few seconds while a QR transfer is pending."""
    order = Order.objects.filter(order_code=code).first()
    if order is None or not _can_view_order(request, order):
        raise Http404()
    return JsonResponse({
        'paid': order.payment_status == 'paid',
        'via': order.paid_via,
        'status': order.get_status_display(),
        'state': order.status,
        'paid_at': order.paid_at.isoformat() if order.paid_at else None,
    })


@staff
def manage_payments(request):
    status = request.GET.get('status', '')
    txns = PaymentTransaction.objects.select_related('order', 'resolved_by')
    if status in dict(PaymentTransaction.STATUSES):
        txns = txns.filter(status=status)
    return render(request, 'management/payments.html', {
        'txns': txns[:200], 'status': status, 'statuses': PaymentTransaction.STATUSES,
        'open_count': PaymentTransaction.objects.exclude(status__in=('matched', 'duplicate_paid')).count(),
    })


@staff
@require_POST
def payment_resolve(request, pk):
    try:
        txn = resolve_manually(pk, request.POST.get('order_code', '')[:40], request.user)
        messages.success(request, f'Đã gắn giao dịch vào đơn {txn.order.order_code} và xác nhận thu tiền.')
    except PaymentTransaction.DoesNotExist:
        messages.error(request, 'Không tìm thấy giao dịch.')
    except BusinessError as exc:
        messages.error(request, str(exc))
    return redirect('manage_payments')


@never_cache
@staff
def payments_latest(request):
    """Last transfers for live admin notifications. Role check runs in RoleAccessMiddleware."""
    rows = PaymentTransaction.objects.select_related('order')[:10]
    return JsonResponse({'items': [{
        'id': t.pk, 'amount': t.amount, 'status': t.status, 'status_label': t.get_status_display(),
        'order_code': t.order.order_code if t.order else None,
        'order_url': f'/management/orders/{t.order_id}/' if t.order_id else None,
        'received_at': t.received_at.isoformat(),
    } for t in rows]})
