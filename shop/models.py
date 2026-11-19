import secrets
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


def order_code():
    return 'HEP-'+timezone.localdate().strftime('%y%m%d')+'-'+secrets.token_hex(4).upper()

class Category(models.Model):
    name_vi=models.CharField('Tên danh mục',max_length=100)
    name_ja=models.CharField('Tên tiếng Nhật',max_length=100,blank=True)
    slug=models.SlugField(unique=True)
    description=models.TextField(blank=True)
    sort_order=models.PositiveIntegerField(default=0)
    def __str__(self): return self.name_vi
    class Meta: ordering=['sort_order','name_vi']; verbose_name='Danh mục'; verbose_name_plural='Danh mục'

class Supplier(models.Model):
    name=models.CharField('Tên nguồn cung',max_length=180)
    contact_name=models.CharField(max_length=120,blank=True)
    phone=models.CharField(max_length=30,blank=True)
    email=models.EmailField(blank=True)
    address=models.CharField(max_length=300,blank=True)
    note=models.TextField(blank=True)
    active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.name
    class Meta: ordering=['name']; verbose_name='Nhà cung cấp'; verbose_name_plural='Nhà cung cấp'

class Book(models.Model):
    category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name='books')
    supplier=models.ForeignKey(Supplier,on_delete=models.SET_NULL,null=True,blank=True,related_name='books')
    title_vi=models.CharField('Tên sách tiếng Việt',max_length=200)
    title_ja=models.CharField('Tên tiếng Nhật',max_length=200,blank=True)
    slug=models.SlugField(unique=True,max_length=220)
    author_ja=models.CharField('Tác giả',max_length=140,blank=True)
    publisher=models.CharField(max_length=140,blank=True)
    isbn=models.CharField('ISBN / SKU',max_length=30,unique=True)
    description_vi=models.TextField('Mô tả',blank=True)
    price=models.PositiveIntegerField('Giá (VNĐ)',validators=[MinValueValidator(1)])
    cost_price=models.PositiveIntegerField('Giá nhập (VNĐ)',default=0)
    stock=models.PositiveIntegerField('Tồn kho',default=0)
    min_stock=models.PositiveIntegerField('Ngưỡng cảnh báo',default=5)
    cover=models.CharField('Tên ảnh trong static/img',max_length=180,default='cover-default.svg')
    featured=models.BooleanField(default=False)
    active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.title_vi
    class Meta:ordering=['-created_at'];verbose_name='Sách';verbose_name_plural='Sách'

class Customer(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='hep_customer')
    full_name=models.CharField(max_length=150)
    email=models.EmailField(blank=True)
    phone=models.CharField(max_length=30,blank=True)
    address=models.TextField(blank=True)
    note=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def __str__(self):return self.full_name
    class Meta:ordering=['-id'];verbose_name='Khách hàng';verbose_name_plural='Khách hàng'

class Order(models.Model):
    SOURCES=[('web','Website'),('facebook','Facebook'),('instagram','Instagram'),('pos','Tại quầy')]
    STATUSES=[('new','Mới tạo'),('confirmed','Đã xác nhận'),('packing','Đang đóng gói'),('shipped','Đang giao'),('completed','Hoàn tất'),('cancelled','Đã hủy')]
    METHODS=[('bank','QR chuyển khoản'),('cod','COD'),('cash','Tiền mặt')]
    PAYMENT_STATUSES=[('unpaid','Chưa thanh toán'),('paid','Đã xác nhận thanh toán')]
    order_code=models.CharField(max_length=32,unique=True,default=order_code)
    customer=models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,blank=True,related_name='orders')
    source=models.CharField(max_length=12,choices=SOURCES,default='web')
    status=models.CharField(max_length=12,choices=STATUSES,default='new')
    payment_method=models.CharField(max_length=8,choices=METHODS,default='bank')
    payment_status=models.CharField(max_length=8,choices=PAYMENT_STATUSES,default='unpaid')
    full_name=models.CharField(max_length=150)
    phone=models.CharField(max_length=30)
    email=models.EmailField(blank=True)
    address=models.TextField(blank=True)
    note=models.TextField(blank=True)
    subtotal=models.PositiveIntegerField(default=0)
    shipping_fee=models.PositiveIntegerField(default=0)
    total=models.PositiveIntegerField(default=0)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='created_orders')
    payment_confirmed_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='payments_confirmed')
    paid_at=models.DateTimeField(null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)
    updated_at=models.DateTimeField(auto_now=True)
    def __str__(self):return self.order_code
    class Meta:ordering=['-created_at'];verbose_name='Đơn hàng';verbose_name_plural='Đơn hàng'

class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    book=models.ForeignKey(Book,on_delete=models.PROTECT)
    title_snapshot=models.CharField(max_length=200)
    sku_snapshot=models.CharField(max_length=30)
    quantity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price=models.PositiveIntegerField()
    line_total=models.PositiveIntegerField()
    class Meta:verbose_name='Dòng đơn';verbose_name_plural='Dòng đơn'

class StockMovement(models.Model):
    book=models.ForeignKey(Book,on_delete=models.PROTECT,related_name='movements')
    delta=models.IntegerField()
    reason=models.CharField(max_length=140)
    reference=models.CharField(max_length=90,blank=True)
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:ordering=['-created_at'];verbose_name='Biến động kho';verbose_name_plural='Biến động kho'

class PurchaseOrder(models.Model):
    STATUSES=[('draft','Bản nháp'),('received','Đã nhập kho')]
    supplier=models.ForeignKey(Supplier,on_delete=models.PROTECT,related_name='purchase_orders')
    status=models.CharField(max_length=12,choices=STATUSES,default='draft')
    note=models.TextField(blank=True)
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    received_at=models.DateTimeField(null=True,blank=True)
    class Meta:ordering=['-created_at'];verbose_name='Phiếu mua hàng';verbose_name_plural='Phiếu mua hàng'

class PurchaseItem(models.Model):
    purchase=models.ForeignKey(PurchaseOrder,on_delete=models.CASCADE,related_name='items')
    book=models.ForeignKey(Book,on_delete=models.PROTECT)
    quantity=models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_cost=models.PositiveIntegerField(default=0)
    class Meta:verbose_name='Dòng nhập';verbose_name_plural='Dòng nhập'

class ContactMessage(models.Model):
    full_name=models.CharField(max_length=120)
    email=models.EmailField()
    subject=models.CharField(max_length=180)
    message=models.TextField()
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:ordering=['-created_at'];verbose_name='Liên hệ';verbose_name_plural='Liên hệ'
