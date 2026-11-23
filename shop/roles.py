"""Back-office roles: which management pages each role may open."""
SALES_PAGES = frozenset({
    'dashboard', 'manage_orders', 'manage_order_detail', 'order_status',
    'pos', 'social_order', 'manage_customers', 'customer_add', 'customer_edit', 'customer_detail',
    'manage_payments', 'payment_resolve', 'payments_latest',
})
WAREHOUSE_PAGES = frozenset({
    'dashboard', 'manage_books', 'manage_book_add', 'manage_book_edit', 'manage_inventory', 'adjust_stock',
    'manage_suppliers', 'supplier_add', 'supplier_edit', 'supplier_detail',
    'manage_purchases', 'purchase_new', 'purchase_detail', 'purchase_receive',
})
# Confirming money by hand (no SePay transaction behind it) and refunds stay with the manager, so the person
# who sells is never the only one who says the money arrived.
MANAGER_ONLY = frozenset({'manage_reports', 'export_orders', 'manage_staff', 'staff_add', 'staff_edit',
                          'payment_confirm', 'order_refund'})
ALL_PAGES = SALES_PAGES | WAREHOUSE_PAGES | MANAGER_ONLY
ROLE_PAGES = {'manager': ALL_PAGES, 'sales': SALES_PAGES, 'warehouse': WAREHOUSE_PAGES}


def role_of(user):
    """Role name for a staff user; None for customers and anonymous visitors."""
    if not getattr(user, 'is_authenticated', False) or not user.is_staff or not user.is_active:
        return None
    if user.is_superuser:
        return 'manager'
    profile = getattr(user, 'staff_profile', None)
    # Least privilege: a staff account created without a profile only gets sales pages.
    return profile.role if profile else 'sales'


def allowed_pages(user):
    return ROLE_PAGES.get(role_of(user), frozenset())
