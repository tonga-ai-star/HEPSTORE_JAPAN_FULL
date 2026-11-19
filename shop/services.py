"""All stock-changing operations live here. Never trust client prices or mark QR paid automatically."""
from collections import Counter
from django.db import transaction
from django.db.models import F
from django.utils import timezone
from .models import Book, Customer, Order, OrderItem, StockMovement, PurchaseOrder

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

@transaction.atomic
def create_order(*, raw_lines, source, payment_method, full_name, phone, email='', address='',note='',user=None,shipping_fee=0, paid=False):
    if source not in dict(Order.SOURCES):raise BusinessError('Kênh bán không hợp lệ.')
    if payment_method not in dict(Order.METHODS):raise BusinessError('Phương thức thanh toán không hợp lệ.')
    if paid and (source!='pos' or payment_method!='cash' or not user or not user.is_staff):
        raise BusinessError('Chỉ nhân viên thu tiền mặt tại POS mới được xác nhận đã thu.')
    if not full_name.strip() or not phone.strip():raise BusinessError('Vui lòng nhập tên và số điện thoại.')
    counts=validated_lines(raw_lines)
    books={book.id:book for book in Book.objects.select_for_update().filter(id__in=counts,active=True).order_by('pk')}
    if len(books)!=len(counts):raise BusinessError('Có sách không còn được bán hoặc không tồn tại.')
    for pk,qty in counts.items():
        if books[pk].stock<qty:raise BusinessError(f'{books[pk].title_vi}: chỉ còn {books[pk].stock} cuốn.')
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
       payment_confirmed_by=user if paid else None,
       status='completed' if paid else 'new')
    for pk,qty in sorted(counts.items()):
        book=books[pk]
        updated=Book.objects.filter(pk=pk,active=True,stock__gte=qty).update(stock=F('stock')-qty)
        if updated!=1:raise BusinessError(f'Sách {book.title_vi} vừa hết hàng, vui lòng thử lại.')
        OrderItem.objects.create(order=order,book=book,title_snapshot=book.title_vi,sku_snapshot=book.isbn,
           unit_price=book.price,quantity=qty,line_total=book.price*qty)
        StockMovement.objects.create(book=book,delta=-qty,reason='Xuất bán '+dict(Order.SOURCES)[source],reference=order.order_code,
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
    if new_status=='completed' and order.payment_method=='bank' and order.payment_status!='paid':
        raise BusinessError('Đơn chuyển khoản phải được nhân viên xác nhận đã nhận tiền trước khi hoàn tất.')
    if new_status=='cancelled' and order.payment_status=='paid':
        raise BusinessError('Đơn đã thu tiền phải xử lý hoàn tiền riêng; bản demo không cho hủy trực tiếp để tránh lệch đối soát.')
    if new_status=='cancelled':
        for line in order.items.select_related('book').order_by('book_id'):
            Book.objects.filter(pk=line.book_id).update(stock=F('stock')+line.quantity)
            StockMovement.objects.create(book_id=line.book_id,delta=line.quantity,
               reason='Hoàn kho do hủy đơn',reference=order.order_code,actor=actor)
    order.status=new_status
    order.save(update_fields=['status','updated_at'])
    return order

@transaction.atomic
def mark_paid(order_id, actor):
    order=Order.objects.select_for_update().get(pk=order_id)
    if order.status=='cancelled':raise BusinessError('Không xác nhận thanh toán cho đơn đã hủy.')
    if order.payment_status=='paid':raise BusinessError('Đơn này đã được xác nhận thanh toán.')
    order.payment_status='paid';order.payment_confirmed_by=actor;order.paid_at=timezone.now()
    order.save(update_fields=['payment_status','payment_confirmed_by','paid_at','updated_at'])
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
    purchase.status='received';purchase.received_at=timezone.now()
    purchase.save(update_fields=['status','received_at'])
    return purchase
