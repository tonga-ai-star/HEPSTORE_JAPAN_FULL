from collections import Counter
from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Book, Category, Customer, Order, OrderItem, Supplier, PurchaseOrder, PurchaseItem, StockMovement, PaymentTransaction
from .forms import SignUpForm, BookForm, SupplierForm, CustomerForm, ContactForm
from .services import (BusinessError, allocate_arrivals, cancel_with_refund, change_order_status, create_order, phone_key,
                       expire_stale_orders, mark_paid, receive_purchase)
from .utils import qr_url

def _session_cart(request,kind='hep_cart'):
    return request.session.get(kind,{})

def _cart_details(request,kind='hep_cart'):
    cart=_session_cart(request,kind)
    books={str(b.id):b for b in Book.objects.filter(id__in=[int(k) for k in cart if k.isdigit()])}
    rows=[]
    for key,qty in cart.items():
        if key not in books:continue
        try:quantity=int(qty)
        except (TypeError,ValueError):continue
        if quantity<=0:continue
        b=books[key];rows.append({'book':b,'qty':quantity,'line_total':quantity*b.price,'waiting':max(0,quantity-b.stock)})
    total=sum(row['line_total'] for row in rows)
    return rows,total

def home(request):
    return render(request,'shop/home.html',{
      'featured':Book.objects.filter(active=True,featured=True).select_related('category')[:8],
      'new_books':Book.objects.filter(active=True).select_related('category')[:8],
      'categories':Category.objects.annotate(total_books=Count('books')).order_by('sort_order')[:5],
    })

def catalog(request):
    books=Book.objects.filter(active=True).select_related('category')
    q=request.GET.get('q','').strip()[:100]
    if q:books=books.filter(Q(title_vi__icontains=q)|Q(title_ja__icontains=q)|Q(author_ja__icontains=q)|Q(isbn__icontains=q))
    cat=request.GET.get('category','').strip()
    if cat:books=books.filter(category__slug=cat)
    sort=request.GET.get('sort','new')
    if sort=='low':books=books.order_by('price','id')
    elif sort=='high':books=books.order_by('-price','id')
    elif sort=='name':books=books.order_by('title_vi')
    else:books=books.order_by('-id')
    page=Paginator(books,12).get_page(request.GET.get('page'))
    return render(request,'shop/catalog.html',{'page':page,'q':q,'cat':cat,'sort':sort,'categories':Category.objects.all()})

def book_detail(request,slug):
    book=get_object_or_404(Book.objects.select_related('category','supplier'),slug=slug,active=True)
    similar=Book.objects.filter(active=True,category=book.category).exclude(pk=book.pk).select_related('category')[:4]
    return render(request,'shop/detail.html',{'book':book,'similar':similar})

@require_POST
def cart_add(request,pk):
    book=get_object_or_404(Book,pk=pk,active=True)
    try:qty=int(request.POST.get('quantity',1))
    except (TypeError,ValueError):qty=0
    if not 1<=qty<=100:messages.error(request,'Số lượng không hợp lệ.');return redirect('book_detail',slug=book.slug)
    cart=_session_cart(request).copy();current=int(cart.get(str(pk),0))
    if qty+current>book.stock and not book.allow_preorder:
        messages.error(request,f'Không đủ tồn kho, hiện còn {book.stock} cuốn.')
    elif qty+current>100:
        messages.error(request,'Mỗi đầu sách đặt tối đa 100 cuốn.')
    else:
        cart[str(pk)]=current+qty;request.session['hep_cart']=cart
        if qty+current>book.stock:
            messages.success(request,f'Đã thêm {book.title_vi} dạng đặt trước, có hàng khoảng {book.restock_days} ngày.')
        else:
            messages.success(request,f'Đã thêm {book.title_vi} vào giỏ.')
    return redirect('cart')

@require_POST
def cart_update(request,pk):
    cart=_session_cart(request).copy()
    try:qty=int(request.POST.get('quantity',0))
    except (TypeError,ValueError):qty=-1
    if qty<0 or qty>1000:messages.error(request,'Số lượng không hợp lệ.');return redirect('cart')
    book=Book.objects.filter(pk=pk,active=True).first()
    if qty>0 and (not book or (qty>book.stock and not book.allow_preorder) or qty>100):
        messages.error(request,'Số lượng vượt tồn hiện có.');return redirect('cart')
    if qty==0:cart.pop(str(pk),None)
    else:cart[str(pk)]=qty
    request.session['hep_cart']=cart
    return redirect('cart')

def cart(request):
    rows,total=_cart_details(request)
    return render(request,'shop/cart.html',{'rows':rows,'subtotal':total,'shipping':0 if total>=350000 else 25000,'total':total+(0 if total>=350000 else 25000) if rows else 0})

def _waiting_days(rows):
    return max((r['book'].restock_days for r in rows if r['waiting']),default=0)

def _preorder_accepted(request,rows):
    """The customer saw (and accepted) a wait at least as long as the one this order would get now."""
    try:accepted=int(request.POST.get('accept_preorder','0'))
    except (TypeError,ValueError):return False
    return accepted>0 and accepted>=_waiting_days(rows)

def checkout(request):
    rows,total=_cart_details(request)
    if not rows:messages.info(request,'Giỏ hàng đang trống.');return redirect('catalog')
    shipping=0 if total>=350000 else 25000
    if request.method=='POST':
        name=request.POST.get('full_name','').strip()[:150]
        phone=request.POST.get('phone','').strip()[:30]
        email=request.POST.get('email','').strip()[:254]
        address=request.POST.get('address','').strip()[:1500]
        method=request.POST.get('payment_method','bank')
        if method not in ('cod','bank'):
            messages.error(request,'Phương thức thanh toán không hợp lệ.');return redirect('checkout')
        if method=='bank' and not all((settings.BANK_BIN,settings.BANK_ACCOUNT,settings.BANK_OWNER)):
            messages.error(request,'Chuyển khoản QR chưa được cấu hình. Vui lòng chọn COD.');return redirect('checkout')
        if not name or not phone or not address:
            messages.error(request,'Cần điền đầy đủ người nhận, số điện thoại, địa chỉ.');return redirect('checkout')
        key=phone_key(phone)
        open_orders=sum(1 for p in Order.objects.filter(source='web',status='new',payment_status='unpaid')
                        .values_list('phone',flat=True) if phone_key(p)==key)
        if open_orders>=settings.MAX_OPEN_WEB_ORDERS:
            messages.error(request,f'Số điện thoại này đang có {open_orders} đơn chưa xác nhận. Thanh toán hoặc chờ Hép gọi xác nhận trước khi đặt thêm.')
            return redirect('checkout')
        try:
            order=create_order(raw_lines=[(r['book'].pk,r['qty']) for r in rows],source='web',
              payment_method=method,full_name=name,phone=phone,email=email,address=address,
              note=request.POST.get('note','')[:1200],user=request.user,shipping_fee=shipping,
              allow_preorder=_preorder_accepted(request,rows))
        except BusinessError as exc:
            if any(r['waiting'] for r in _cart_details(request)[0]) and not _preorder_accepted(request,_cart_details(request)[0]):
                messages.warning(request,'Một số sách vừa hết hàng nên đơn sẽ thành đặt trước. Xem ngày dự kiến bên dưới rồi bấm đặt hàng lại.')
                return redirect('checkout')
            messages.error(request,str(exc));return redirect('cart')
        request.session['hep_cart']={}
        codes=request.session.get('hep_recent_orders',[])
        request.session['hep_recent_orders']=(codes+[order.order_code])[-20:]
        return redirect('order_success',code=order.order_code)
    initial={'full_name':request.user.get_full_name(),'email':request.user.email} if request.user.is_authenticated else {}
    return render(request,'shop/checkout.html',{'waiting_days':_waiting_days(rows),'rows':rows,'subtotal':total,'shipping':shipping,'total':total+shipping,'initial':initial})

def order_success(request,code):
    order=get_object_or_404(Order.objects.prefetch_related('items'),order_code=code)
    allowed=code in request.session.get('hep_recent_orders',[])
    if not allowed and (not request.user.is_authenticated or not order.customer or order.customer.user_id!=request.user.pk):raise Http404()
    return render(request,'shop/order_success.html',{'order':order,'qr':qr_url(order)})

def track_order(request):
    order=None
    if request.method=='POST':
        code=request.POST.get('order_code','').strip()[:32].upper()
        phone=request.POST.get('phone','').strip()[:30]
        if code and phone:
            order=Order.objects.filter(order_code=code).first()
            if order and phone_key(order.phone)!=phone_key(phone):order=None
        if not order:messages.error(request,'Không tìm thấy đơn phù hợp với mã và số điện thoại.')
        else:
            codes=request.session.get('hep_recent_orders',[])
            if order.order_code not in codes:request.session['hep_recent_orders']=(codes+[order.order_code])[-20:]
    return render(request,'shop/track.html',{'order':order,'qr':qr_url(order) if order else ''})

def signup(request):
    if request.user.is_authenticated:return redirect('home')
    form=SignUpForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        user=form.save();Customer.objects.create(user=user,full_name=user.first_name,email=user.email)
        login(request,user);messages.success(request,'Đăng ký thành công!');return redirect('home')
    return render(request,'registration/signup.html',{'form':form})

@login_required
def account(request):
    customer=Customer.objects.filter(user=request.user).first()
    orders=Order.objects.filter(customer=customer) if customer else Order.objects.none()
    return render(request,'shop/account.html',{'customer':customer,'orders':orders[:30]})

def about(request):return render(request,'shop/about.html')
def policies(request):return render(request,'shop/policies.html')

def contact(request):
    form=ContactForm(request.POST or None)
    if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Đã nhận được lời nhắn của bạn.');return redirect('contact')
    return render(request,'shop/contact.html',{'form':form})

# ---------- BACK OFFICE ----------
staff=lambda fn: staff_member_required(fn,login_url='/tai-khoan/login/')

@staff
def dashboard(request):
    expire_stale_orders()
    start=timezone.localdate()-timedelta(days=6)
    graph=(Order.objects.filter(created_at__date__gte=start,status='completed')
        .annotate(day=TruncDate('created_at')).values('day').annotate(total=Sum('total')).order_by('day'))
    graph_data={x['day'].isoformat():x['total'] for x in graph}
    chart=[]
    for i in range(7):
        date=start+timedelta(days=i);chart.append({'day':date.strftime('%d/%m'),'total':graph_data.get(date.isoformat(),0)})
    top=(OrderItem.objects.filter(order__status='completed').values('title_snapshot').annotate(qty=Sum('quantity')).order_by('-qty')[:5])
    return render(request,'management/dashboard.html',{
       'total_books':Book.objects.filter(active=True).count(),
       'low_count':Book.objects.filter(stock__lte=F('min_stock')).count(),
       'customer_count':Customer.objects.count(),
       'order_count':Order.objects.count(),
       'new_count':Order.objects.filter(status='new').count(),
       'revenue':Order.objects.filter(status='completed').aggregate(s=Sum('total'))['s'] or 0,
       'collected':Order.objects.filter(payment_status='paid').aggregate(s=Sum('total'))['s'] or 0,
       'latest':Order.objects.select_related('customer')[:8],
       'alerts':Book.objects.filter(stock__lte=F('min_stock')).order_by('stock')[:6],
       'top_books':top,'chart':chart,
       'open_payments':PaymentTransaction.objects.exclude(status__in=('matched','duplicate_paid')).count(),
       'recent_payments':PaymentTransaction.objects.select_related('order')[:5],
    })

@staff
def manage_books(request):
    q=request.GET.get('q','').strip()[:80]
    books=Book.objects.select_related('category','supplier').order_by('title_vi')
    if q:books=books.filter(Q(title_vi__icontains=q)|Q(isbn__icontains=q))
    return render(request,'management/books.html',{'books':books[:150],'q':q})

@staff
def manage_book_edit(request,pk=None):
    book=get_object_or_404(Book,pk=pk) if pk else None
    form=BookForm(request.POST or None,instance=book,actor=request.user)
    if request.method=='POST' and form.is_valid():
        new=form.save();messages.success(request,'Đã lưu sách.');return redirect('manage_books')
    return render(request,'management/form.html',{'form':form,'heading':'Chỉnh sửa sách' if book else 'Thêm sách','back':'manage_books'})

@staff
def manage_inventory(request):
    movements=StockMovement.objects.select_related('book','actor')[:35]
    books=Book.objects.select_related('category').order_by('stock','title_vi')[:150]
    return render(request,'management/inventory.html',{'books':books,'movements':movements})

@staff
@require_POST
def adjust_stock(request,pk):
    book=get_object_or_404(Book,pk=pk)
    try:delta=int(request.POST.get('delta',''))
    except (TypeError,ValueError):messages.error(request,'Vui lòng nhập số lượng thay đổi.');return redirect('manage_inventory')
    reason=request.POST.get('reason','').strip()[:140]
    if not reason or delta==0 or abs(delta)>10000:
        messages.error(request,'Cần nhập lý do và lượng điều chỉnh hợp lệ.');return redirect('manage_inventory')
    with transaction.atomic():
        updated=Book.objects.filter(pk=pk,stock__gte=-delta).update(stock=F('stock')+delta) if delta<0 else Book.objects.filter(pk=pk).update(stock=F('stock')+delta)
        if not updated:messages.error(request,'Không thể điều chỉnh xuống số âm.');return redirect('manage_inventory')
        StockMovement.objects.create(book=book,delta=delta,reason=reason,reference='DIEU-CHINH',actor=request.user)
        if delta>0:allocate_arrivals([book.pk],request.user)
    messages.success(request,'Đã điều chỉnh tồn kho và ghi nhật ký.');return redirect('manage_inventory')

@staff
def manage_suppliers(request):
    return render(request,'management/suppliers.html',{'suppliers':Supplier.objects.annotate(book_count=Count('books')).all()})

@staff
def supplier_edit(request,pk=None):
    obj=get_object_or_404(Supplier,pk=pk) if pk else None
    form=SupplierForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Đã lưu nhà cung cấp.');return redirect('manage_suppliers')
    return render(request,'management/form.html',{'form':form,'heading':'Nhà cung cấp','back':'manage_suppliers'})

@staff
def supplier_detail(request,pk):
    supplier=get_object_or_404(Supplier,pk=pk)
    return render(request,'management/supplier_detail.html',{'supplier':supplier,'books':supplier.books.all(),'purchases':supplier.purchase_orders.all()[:20]})

@staff
def manage_purchases(request):
    return render(request,'management/purchases.html',{'purchases':PurchaseOrder.objects.select_related('supplier','created_by').all()[:100]})

@staff
def purchase_new(request):
    if request.method=='POST':
        try:
            supplier=Supplier.objects.get(pk=int(request.POST.get('supplier','0')),active=True)
            book_ids=request.POST.getlist('book');qtys=request.POST.getlist('quantity');costs=request.POST.getlist('unit_cost')
            if not book_ids or len(book_ids)!=len(qtys) or len(book_ids)!=len(costs) or len(book_ids)>100:raise BusinessError('Dữ liệu dòng nhập không hợp lệ.')
            rows=[]
            for bid,q,c in zip(book_ids,qtys,costs):
                try:bid=int(bid);q=int(q);c=int(c)
                except (TypeError,ValueError):raise BusinessError('Số lượng hoặc giá nhập không hợp lệ.')
                if q<1 or q>10000 or c<0 or c>100000000:raise BusinessError('Số lượng / giá nhập vượt phạm vi.')
                if not Book.objects.filter(pk=bid).exists():raise BusinessError('Không tìm thấy sách.')
                rows.append((bid,q,c))
            with transaction.atomic():
                po=PurchaseOrder.objects.create(supplier=supplier,note=request.POST.get('note','')[:1200],created_by=request.user)
                PurchaseItem.objects.bulk_create([PurchaseItem(purchase=po,book_id=bid,quantity=q,unit_cost=c) for bid,q,c in rows])
            messages.success(request,f'Đã tạo phiếu PN-{po.id}; chưa cộng kho trước khi nhận hàng.')
            return redirect('purchase_detail',pk=po.pk)
        except (Supplier.DoesNotExist,ValueError,BusinessError) as exc:messages.error(request,str(exc) or 'Nhà cung cấp không hợp lệ.')
    return render(request,'management/purchase_new.html',{'suppliers':Supplier.objects.filter(active=True),'books':Book.objects.all().order_by('title_vi')})

@staff
def purchase_detail(request,pk):
    po=get_object_or_404(PurchaseOrder.objects.select_related('supplier','created_by').prefetch_related('items__book'),pk=pk)
    return render(request,'management/purchase_detail.html',{'po':po})

@staff
@require_POST
def purchase_receive(request,pk):
    try:receive_purchase(pk,request.user);messages.success(request,'Đã nhập kho và ghi biến động từng sách.')
    except BusinessError as exc:messages.error(request,str(exc))
    return redirect('purchase_detail',pk=pk)

@staff
def manage_customers(request):
    q=request.GET.get('q','').strip()[:80]
    objs=Customer.objects.annotate(orders_count=Count('orders'))
    if q:objs=objs.filter(Q(full_name__icontains=q)|Q(phone__icontains=q)|Q(email__icontains=q))
    return render(request,'management/customers.html',{'customers':objs[:150],'q':q})

@staff
def customer_edit(request,pk=None):
    obj=get_object_or_404(Customer,pk=pk) if pk else None
    form=CustomerForm(request.POST or None,instance=obj)
    if request.method=='POST' and form.is_valid():form.save();messages.success(request,'Đã cập nhật khách hàng.');return redirect('manage_customers')
    return render(request,'management/form.html',{'form':form,'heading':'Thông tin khách hàng','back':'manage_customers'})

@staff
def customer_detail(request,pk):
    obj=get_object_or_404(Customer,pk=pk)
    return render(request,'management/customer_detail.html',{'person':obj,'orders':obj.orders.all()[:50]})

@staff
def manage_orders(request):
    expire_stale_orders()
    orders=Order.objects.select_related('customer').all()
    q=request.GET.get('q','').strip()[:80]
    source=request.GET.get('source','')
    status=request.GET.get('status','')
    if q:orders=orders.filter(Q(order_code__icontains=q)|Q(phone__icontains=q)|Q(full_name__icontains=q))
    if source in dict(Order.SOURCES):orders=orders.filter(source=source)
    if status in dict(Order.STATUSES):orders=orders.filter(status=status)
    return render(request,'management/orders.html',{'orders':orders[:200],'q':q,'source':source,'status':status,'sources':Order.SOURCES,'statuses':Order.STATUSES})

@staff
def manage_order_detail(request,pk):
    order=get_object_or_404(Order.objects.select_related('customer','created_by').prefetch_related('items__book'),pk=pk)
    transitions={ 'new':['confirmed','cancelled'],'confirmed':['packing','completed','cancelled'],
         'packing':['shipped','completed','cancelled'],'shipped':['completed'] }
    nexts=transitions.get(order.status,[])
    if order.payment_method=='bank' and order.payment_status!='paid':
        nexts=[k for k in nexts if k not in ('packing','shipped','completed')]  # blocked until the money arrives
    if order.payment_status=='paid':
        nexts=[k for k in nexts if k!='cancelled']  # paid orders are cancelled only through the refund form
    return render(request,'management/order_detail.html',{'order':order,'qr':qr_url(order),'next_statuses':[(k,dict(Order.STATUSES)[k]) for k in nexts]})

@staff
@require_POST
def order_status(request,pk):
    try:change_order_status(pk,request.POST.get('status',''),request.user);messages.success(request,'Đã cập nhật trạng thái.')
    except BusinessError as exc:messages.error(request,str(exc))
    return redirect('manage_order_detail',pk=pk)

@staff
@require_POST
def order_refund(request,pk):
    try:
        cancel_with_refund(pk,request.user,request.POST.get('note',''))
        messages.success(request,'Đã hủy đơn, ghi nhận hoàn tiền và trả sách về kho.')
    except BusinessError as exc:messages.error(request,str(exc))
    return redirect('manage_order_detail',pk=pk)

@staff
@require_POST
def payment_confirm(request,pk):
    try:mark_paid(pk,request.user);messages.success(request,'Đã ghi nhận nhân viên xác nhận tiền thực thu.');
    except BusinessError as exc:messages.error(request,str(exc))
    return redirect('manage_order_detail',pk=pk)

def _input_lines(request):
    ids=request.POST.getlist('book');qtys=request.POST.getlist('quantity')
    if not ids or len(ids)!=len(qtys):raise BusinessError('Vui lòng chọn sách và số lượng.')
    return list(zip(ids,qtys))

@staff
def social_order(request):
    if request.method=='POST':
        source=request.POST.get('source','')
        if source not in ('facebook','instagram'):messages.error(request,'Chỉ nhận đơn Facebook / Instagram.');return redirect('social_order')
        try:
            fee=int(request.POST.get('shipping_fee','0'))
            order=create_order(raw_lines=_input_lines(request),source=source,payment_method=request.POST.get('payment_method','cod'),
               full_name=request.POST.get('full_name',''),phone=request.POST.get('phone',''),email=request.POST.get('email',''),
               address=request.POST.get('address',''),note=request.POST.get('note',''),user=request.user,shipping_fee=fee,allow_preorder=True)
            messages.success(request,'Đã tạo đơn đặt trước, dự kiến có hàng '+order.expected_date.strftime('%d/%m')+'.' if order.is_preorder else 'Đã tạo đơn đa kênh, tồn kho đã cập nhật.');return redirect('manage_order_detail',pk=order.pk)
        except (BusinessError,ValueError) as exc:messages.error(request,str(exc))
    return render(request,'management/manual_order.html',{'kind':'social','books':Book.objects.filter(active=True).order_by('title_vi'),'sources':Order.SOURCES})

@staff
def pos(request):
    lookup=None
    q=request.GET.get('isbn','').strip()[:30]
    if q:lookup=Book.objects.filter(isbn__iexact=q,active=True).first()
    if request.method=='POST':
        try:
            method=request.POST.get('payment_method','cash')
            if method=='bank' and not all((settings.BANK_BIN,settings.BANK_ACCOUNT,settings.BANK_OWNER)):
                raise BusinessError('Chưa cấu hình tài khoản ngân hàng để tạo QR.')
            paid=(method=='cash' and request.POST.get('received_cash')=='on')
            order=create_order(raw_lines=_input_lines(request),source='pos',payment_method=method,
              full_name=request.POST.get('full_name','Khách tại quầy') or 'Khách tại quầy',
              phone=request.POST.get('phone','0000000000') or '0000000000',user=request.user,
              shipping_fee=0,paid=paid,note=request.POST.get('note',''))
            messages.success(request,'Đơn POS đã tạo; đối soát tiền trước khi xác nhận nếu chưa thu.');return redirect('manage_order_detail',pk=order.pk)
        except BusinessError as exc:messages.error(request,str(exc))
    return render(request,'management/pos.html',{'books':Book.objects.filter(active=True).order_by('title_vi'),'lookup':lookup,'isbn':q,'tm_model_url':settings.TM_MODEL_URL})

@staff
def manage_reports(request):
    by_source=Order.objects.exclude(status='cancelled').values('source').annotate(count=Count('id'),total=Sum('total')).order_by('source')
    by_status=Order.objects.values('status').annotate(count=Count('id')).order_by('status')
    best=OrderItem.objects.filter(order__status='completed').values('title_snapshot').annotate(qty=Sum('quantity'),sales=Sum('line_total')).order_by('-qty')[:20]
    return render(request,'management/reports.html',{'by_source':by_source,'by_status':by_status,'best':best,
        'paid_total':Order.objects.filter(payment_status='paid').aggregate(s=Sum('total'))['s'] or 0})

@staff
def export_orders(request):
    import csv
    from django.utils.encoding import smart_str
    r=HttpResponse(content_type='text/csv; charset=utf-8')
    r['Content-Disposition']='attachment; filename="hepstore_orders.csv"'
    r.write('\ufeff')
    w=csv.writer(r);w.writerow(['Mã đơn','Kênh','Khách','SĐT','Trạng thái','Thanh toán','Tổng (VND)','Ngày tạo'])
    for o in Order.objects.all().iterator():
        w.writerow([o.order_code,o.get_source_display(),o.full_name,o.phone,o.get_status_display(),o.get_payment_status_display(),o.total,timezone.localtime(o.created_at).strftime('%Y-%m-%d %H:%M')])
    return r
