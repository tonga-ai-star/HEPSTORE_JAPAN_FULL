"""All stock-changing operations live here. Never trust client prices or mark QR paid automatically."""
from collections import Counter
from datetime import timedelta
from django.conf import settings
import logging
import re

from django.db import OperationalError, transaction
from django.db.models import F
from django.utils import timezone
from .models import Book, Customer, Order, OrderItem, StockMovement, PurchaseOrder

log=logging.getLogger(__name__)

def phone_key(phone):
    """Comparable form of a Vietnamese phone number: digits only, +84/84 prefix folded to 0."""
    digits=re.sub(r'\D','',phone or '')
    if digits.startswith('00'):digits=digits[2:]               # 0084 ...
    if digits.startswith('84') and len(digits)>=11:
        rest=digits[2:]
        digits=rest if rest.startswith('0') else '0'+rest       # +84 (0)9... and +84 9...
    return digits

class BusinessError(ValueError):
    pass

def validated_lines(raw_lines):
    counts=Counter()
    for key,quantity in raw_lines:
        try:
            pk=int(key); qty=int(quantity)
        except (TypeError,ValueError):raise BusinessError('Mã sách hoặc số lượng không hợp lệ.')
        if qty < 1 or qty > 1000:raise BusinessError('Số lượng phải từ 1 đến 1000.')
        counts[pk]+=qty
    if not counts:raise BusinessError('Giỏ hàng đang trống.')
    if len(counts)>100:raise BusinessError('Một đơn tối đa 100 dòng sách.')
    return counts

def split_preorder(books, counts, allow_preorder):
    """Return {pk: (from_stock, waiting)} and the expected date, or raise when a short line cannot wait."""
    plan, wait_days = {}, 0
    for pk, qty in counts.items():
        book = books[pk]
        from_stock = min(book.stock, qty)
        waiting = qty - from_stock
        if waiting and not (allow_preorder and book.allow_preorder):
            raise BusinessError(f'{book.title_vi}: chỉ còn {book.stock} cuốn.')
        if waiting:
            wait_days = max(wait_days, book.restock_days)
        plan[pk] = (from_stock, waiting)
    expected = timezone.localdate() + timedelta(days=wait_days) if wait_days else None
    return plan, expected

@transaction.atomic
def create_order(*, raw_lines, source, payment_method, full_name, phone, email='', address='',note='',user=None,shipping_fee=0, paid=False, allow_preorder=False):
    if source not in dict(Order.SOURCES):raise BusinessError('Kênh bán không hợp lệ.')
    if payment_method not in dict(Order.METHODS):raise BusinessError('Phương thức thanh toán không hợp lệ.')
    if paid and (source!='pos' or payment_method!='cash' or not user or not user.is_staff):
        raise BusinessError('Chỉ nhân viên thu tiền mặt tại POS mới được xác nhận đã thu.')
    if not full_name.strip() or not phone.strip():raise BusinessError('Vui lòng nhập tên và số điện thoại.')
    counts=validated_lines(raw_lines)
    books={book.id:book for book in Book.objects.select_for_update().filter(id__in=counts,active=True).order_by('pk')}
    if len(books)!=len(counts):raise BusinessError('Có sách không còn được bán hoặc không tồn tại.')
    plan,expected=split_preorder(books,counts,allow_preorder and not paid)
    subtotal=sum(books[pk].price*qty for pk,qty in counts.items())
    if shipping_fee is None:
        fee=0 if subtotal>=350000 else 25000
    else:
        try:fee=int(shipping_fee)
        except (ValueError,TypeError):raise BusinessError('Phí giao hàng không hợp lệ.')
        if fee < 0 or fee > 500000:raise BusinessError('Phí vận chuyển không hợp lệ.')
    customer=None
    if user and user.is_authenticated and not user.is_staff:
        customer=Customer.objects.filter(user=user).first()
        if not customer:
            customer=Customer.objects.create(user=user,full_name=full_name,email=email,phone=phone,address=address)
    elif source!='pos' or (phone.strip() and phone.strip()!='0000000000'):
        # CRM profile for guest / social / POS with a real phone. Never attach this
        # profile to a registered account by phone alone (prevents data leakage).
        customer=Customer.objects.filter(user__isnull=True,phone=phone.strip()[:30]).first()
        if not customer:
            customer=Customer.objects.create(full_name=full_name.strip()[:150],phone=phone.strip()[:30],
                email=email.strip()[:254],address=address.strip(),note='Hồ sơ phát sinh từ đơn '+dict(Order.SOURCES)[source])
    order=Order.objects.create(customer=customer,source=source,payment_method=payment_method,
       full_name=full_name.strip()[:150],phone=phone.strip()[:30],email=email.strip(),address=address.strip(),note=note.strip(),
       subtotal=subtotal,shipping_fee=fee,total=subtotal+fee,created_by=user if user and user.is_authenticated and user.is_staff else None,
       payment_status='paid' if paid else 'unpaid',paid_at=timezone.now() if paid else None,
       payment_confirmed_by=user if paid else None,paid_via='pos_cash' if paid else '',
       status='completed' if paid else 'new',is_preorder=expected is not None,expected_date=expected)
    for pk,qty in sorted(counts.items()):
        book=books[pk];from_stock,waiting=plan[pk]
        OrderItem.objects.create(order=order,book=book,title_snapshot=book.title_vi,sku_snapshot=book.isbn,
           unit_price=book.price,quantity=qty,line_total=book.price*qty,preorder_qty=waiting)
        if not from_stock:continue
        updated=Book.objects.filter(pk=pk,active=True,stock__gte=from_stock).update(stock=F('stock')-from_stock)
        if updated!=1:raise BusinessError(f'Sách {book.title_vi} vừa hết hàng, vui lòng thử lại.')
        StockMovement.objects.create(book=book,delta=-from_stock,reason='Xuất bán '+dict(Order.SOURCES)[source],reference=order.order_code,
           actor=user if user and user.is_authenticated and user.is_staff else None)
    return order

@transaction.atomic
def change_order_status(order_id,new_status,actor):
    if new_status not in dict(Order.STATUSES):raise BusinessError('Trạng thái không hợp lệ.')
    order=Order.objects.select_for_update().get(pk=order_id)
    transitions={
      'new':{'confirmed','cancelled'},
      'confirmed':{'packing','completed','cancelled'},
      'packing':{'shipped','completed','cancelled'},
      'shipped':{'completed'},
      'completed':set(), 'cancelled':set(),
    }
    if new_status not in transitions[order.status]:raise BusinessError('Không thể chuyển từ trạng thái hiện tại sang trạng thái này.')
    if new_status in ('packing','shipped','completed') and order.payment_method=='bank' and order.payment_status!='paid':
        raise BusinessError('Đơn chuyển khoản chưa nhận tiền: chỉ đóng gói, giao hoặc hoàn tất sau khi tiền về.')
    if new_status=='cancelled' and order.payment_status=='paid':
        raise BusinessError('Đơn đã thu tiền phải xử lý hoàn tiền riêng; bản demo không cho hủy trực tiếp để tránh lệch đối soát.')
    if new_status=='cancelled':
        return_stock(order,actor,'Hoàn kho do hủy đơn')
    elif new_status in ('packing','shipped','completed'):
        take_waiting_stock(order,actor)
    order.status=new_status
    order.save(update_fields=['status','updated_at'])
    return order

def return_stock(order,actor,reason):
    """Put back the books this order actually took, then let waiting pre-orders claim them."""
    returned=[]
    for line in order.items.order_by('book_id'):
        taken=line.quantity-line.preorder_qty
        if not taken:continue
        Book.objects.filter(pk=line.book_id).update(stock=F('stock')+taken)
        StockMovement.objects.create(book_id=line.book_id,delta=taken,reason=reason,reference=order.order_code,actor=actor)
        returned.append(line.book_id)
    if returned:
        # The cancelled order's own lines must not claim the books back.
        OrderItem.objects.filter(order=order).update(preorder_qty=0)
        allocate_arrivals(returned,actor)

@transaction.atomic
def cancel_with_refund(order_id,actor,note):
    """Manager cancels a paid order after refunding the customer outside the system."""
    note=(note or '').strip()[:300]
    if not note:raise BusinessError('Ghi rõ đã hoàn tiền thế nào (ví dụ: CK trả lại 2.000đ, mã GD ...).')
    order=Order.objects.select_for_update().get(pk=order_id)
    if order.payment_status!='paid':raise BusinessError('Chỉ dùng cho đơn đã thu tiền. Đơn chưa thu thì hủy bình thường.')
    if order.status in ('shipped','completed','cancelled'):raise BusinessError('Đơn đã giao, hoàn tất hoặc đã hủy thì không hủy kèm hoàn tiền ở đây.')
    return_stock(order,actor,'Hoàn kho do hủy đơn đã hoàn tiền')
    stamp=timezone.localtime().strftime('%d/%m/%Y %H:%M')
    order.status='cancelled';order.payment_status='refunded'
    order.note=(order.note+'\n' if order.note else '')+f'[Hoàn tiền {stamp} bởi {actor.get_username()}] {note}'
    order.save(update_fields=['status','payment_status','note','updated_at'])
    return order

def _unmatched_transfer_could_be(order):
    from .models import PaymentTransaction
    return PaymentTransaction.objects.filter(order__isnull=True,status='unmatched',amount=order.total,
                                             received_at__gte=order.created_at).exists()

def expire_stale_orders(now=None):
    """Cancel unconfirmed, unpaid web orders that have held stock longer than ORDER_HOLD_DAYS."""
    now=now or timezone.now()
    hold=timedelta(days=settings.ORDER_HOLD_DAYS)
    # Orders with any bank transfer attached (short payment, wrong note being reconciled) are never
    # auto-cancelled: money is involved, so a person decides.
    stale=(Order.objects.filter(source='web',status='new',payment_status='unpaid',created_at__lt=now-hold)
           .filter(transactions__isnull=True))
    expired=0
    for order in stale.only('pk','is_preorder','expected_date','payment_method','total','created_at'):
        if order.is_preorder and order.expected_date and timezone.localdate(now)<order.expected_date+hold:
            continue
        if order.payment_method=='bank' and _unmatched_transfer_could_be(order):
            continue  # right amount arrived with a wrong note: staff must reconcile it, never auto-cancel
        try:
            change_order_status(order.pk,'cancelled',None)
            expired+=1
        except BusinessError:
            continue
        except OperationalError:
            # SQLite busy (two staff opening the dashboard together): try again on the next page load.
            log.warning('expire_stale_orders: CSDL đang bận, để lần sau')
            break
    return expired

def allocate_arrivals(book_ids,actor):
    """Hand newly arrived books to waiting pre-orders, oldest order first, before anyone else can buy them."""
    for book in Book.objects.select_for_update().filter(pk__in=book_ids).order_by('pk'):
        stock=book.stock
        waiting=(OrderItem.objects.select_related('order').filter(book=book,preorder_qty__gt=0)
                 .exclude(order__status='cancelled').order_by('order__payment_status','order__created_at','pk'))
        for line in waiting:
            if stock<=0:break
            give=min(stock,line.preorder_qty)
            stock-=give
            line.preorder_qty-=give
            line.save(update_fields=['preorder_qty'])
            StockMovement.objects.create(book=book,delta=-give,reason='Giữ cho đơn đặt trước',
               reference=line.order.order_code,actor=actor)
        if stock!=book.stock:
            Book.objects.filter(pk=book.pk).update(stock=stock)

def take_waiting_stock(order,actor):
    """Before a pre-order leaves the shop, take the books that have arrived since it was placed."""
    for line in order.items.select_related('book').filter(preorder_qty__gt=0).order_by('book_id'):
        updated=Book.objects.filter(pk=line.book_id,stock__gte=line.preorder_qty).update(stock=F('stock')-line.preorder_qty)
        if updated!=1:
            raise BusinessError(f'{line.title_snapshot}: chưa đủ {line.preorder_qty} cuốn trong kho cho đơn đặt trước. Nhập hàng trước khi giao.')
        StockMovement.objects.create(book_id=line.book_id,delta=-line.preorder_qty,
           reason='Xuất cho đơn đặt trước',reference=order.order_code,actor=actor)
        line.preorder_qty=0
        line.save(update_fields=['preorder_qty'])

@transaction.atomic
def mark_paid(order_id, actor, via='manual'):
    order=Order.objects.select_for_update().get(pk=order_id)
    if order.status=='cancelled':raise BusinessError('Không xác nhận thanh toán cho đơn đã hủy.')
    if order.payment_status=='paid':raise BusinessError('Đơn này đã được xác nhận thanh toán.')
    order.payment_status='paid';order.payment_confirmed_by=actor;order.paid_at=timezone.now();order.paid_via=via
    fields=['payment_status','payment_confirmed_by','paid_at','paid_via','updated_at']
    if order.status=='new':
        order.status='confirmed';fields.append('status')
    order.save(update_fields=fields)
    return order

@transaction.atomic
def receive_purchase(purchase_id,actor):
    purchase=PurchaseOrder.objects.select_for_update().get(pk=purchase_id)
    if purchase.status!='draft':raise BusinessError('Phiếu này đã được nhập kho.')
    items=list(purchase.items.select_related('book'))
    if not items:raise BusinessError('Phiếu nhập cần có ít nhất một dòng sách.')
    for item in items:
        Book.objects.filter(pk=item.book_id).update(stock=F('stock')+item.quantity,cost_price=item.unit_cost)
        StockMovement.objects.create(book_id=item.book_id,delta=item.quantity,
          reason=f'Nhập từ {purchase.supplier.name}',reference=f'PN-{purchase.pk}',actor=actor)
    allocate_arrivals([item.book_id for item in items],actor)
    purchase.status='received';purchase.received_at=timezone.now()
    purchase.save(update_fields=['status','received_at'])
    return purchase
