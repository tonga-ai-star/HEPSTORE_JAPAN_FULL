from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from .models import Book,Category,Supplier,PurchaseOrder,PurchaseItem,Order,StockMovement
from .services import create_order,change_order_status,receive_purchase,mark_paid,BusinessError
class CoreCommerceTests(TestCase):
    def setUp(self):
        self.category=Category.objects.create(name_vi='Văn hóa',slug='van-hoa')
        self.book=Book.objects.create(category=self.category,title_vi='Sách mẫu',slug='sach-mau',isbn='DEMO-001',price=90000,stock=5,min_stock=1)
        self.admin=get_user_model().objects.create_user(username='staff1',password='StrongPassword123!',is_staff=True)
    def make_order(self,**kw):
        return create_order(raw_lines=[(self.book.id,2)],source='web',payment_method='cod',full_name='Khách A',phone='0123456789',address='Địa chỉ mẫu',shipping_fee=25000,**kw)
    def test_order_decreases_stock_and_creates_movement(self):
        order=self.make_order();self.book.refresh_from_db()
        self.assertEqual(self.book.stock,3);self.assertEqual(order.total,205000)
        self.assertEqual(order.items.count(),1);self.assertEqual(StockMovement.objects.filter(book=self.book).count(),1)
    def test_out_of_stock_rolls_back(self):
        self.make_order()
        with self.assertRaises(BusinessError):
            create_order(raw_lines=[(self.book.id,4)],source='web',payment_method='cod',full_name='Khách B',phone='0123456789',shipping_fee=25000)
        self.assertEqual(Order.objects.count(),1)
    def test_cancel_restores_once(self):
        o=self.make_order();change_order_status(o.id,'cancelled',self.admin)
        self.book.refresh_from_db();self.assertEqual(self.book.stock,5)
        with self.assertRaises(BusinessError):change_order_status(o.id,'cancelled',self.admin)
        self.book.refresh_from_db();self.assertEqual(self.book.stock,5)
    def test_purchase_receipt_once(self):
        s=Supplier.objects.create(name='Nhà cung A');p=PurchaseOrder.objects.create(supplier=s,created_by=self.admin)
        PurchaseItem.objects.create(purchase=p,book=self.book,quantity=4,unit_cost=50000)
        receive_purchase(p.id,self.admin)
        with self.assertRaises(BusinessError):receive_purchase(p.id,self.admin)
        self.book.refresh_from_db();self.assertEqual(self.book.stock,9)
    def test_bank_order_is_not_paid_automatically(self):
        o=create_order(raw_lines=[(self.book.id,1)],source='web',payment_method='bank',full_name='Khách A',phone='0123456789',shipping_fee=0)
        self.assertEqual(o.payment_status,'unpaid');self.assertIsNone(o.paid_at)
        o=mark_paid(o.id,self.admin);self.assertEqual(o.payment_status,'paid')
    def test_staff_routes_private(self):
        response=self.client.get(reverse('dashboard'));self.assertEqual(response.status_code,302)
    def test_customer_cannot_create_social_order(self):
        u=get_user_model().objects.create_user('buyer',password='SecurePassword123!');self.client.force_login(u)
        self.assertEqual(self.client.get(reverse('social_order')).status_code,302)
    def test_public_catalog(self):
        self.assertContains(self.client.get(reverse('catalog')),'Sách mẫu')
