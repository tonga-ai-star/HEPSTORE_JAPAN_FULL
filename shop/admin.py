from django.contrib import admin
from .models import Book,Category,Supplier,Customer,Order,OrderItem,StockMovement,PurchaseOrder,PurchaseItem,ContactMessage
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display=['title_vi','isbn','price','stock','min_stock','active']
    search_fields=['title_vi','title_ja','isbn']
    list_filter=['category','active','featured']
    prepopulated_fields={'slug':('title_vi',)}
    readonly_fields=['stock','created_at']
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=['name_vi','name_ja'];prepopulated_fields={'slug':('name_vi',)}
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):list_display=['name','phone','email','active']
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):list_display=['full_name','phone','email']
class OrderItemInline(admin.TabularInline):
    model=OrderItem;extra=0;readonly_fields=['book','title_snapshot','sku_snapshot','quantity','unit_price','line_total'];can_delete=False
    def has_add_permission(self,request,obj=None):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=['order_code','source','status','payment_status','total','created_at']
    list_filter=['source','status','payment_status'];search_fields=['order_code','full_name','phone'];inlines=[OrderItemInline]
    readonly_fields=['order_code','customer','source','status','payment_method','payment_status','full_name','phone','email','address','note','subtotal','shipping_fee','total','created_by','payment_confirmed_by','paid_at','created_at','updated_at']
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display=['book','delta','reason','reference','created_at'];readonly_fields=['book','delta','reason','reference','actor','created_at']
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
class PurchaseItemInline(admin.TabularInline):
    model=PurchaseItem;extra=0;readonly_fields=['purchase','book','quantity','unit_cost'];can_delete=False
    def has_add_permission(self,request,obj=None):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display=['id','supplier','status','created_at','received_at']
    readonly_fields=['supplier','status','note','created_by','created_at','received_at']
    inlines=[PurchaseItemInline]
    def has_add_permission(self,request):return False
    def has_change_permission(self,request,obj=None):return False
    def has_delete_permission(self,request,obj=None):return False
@admin.register(ContactMessage)
class ContactAdmin(admin.ModelAdmin):list_display=['full_name','email','subject','created_at'];readonly_fields=['full_name','email','subject','message','created_at']
