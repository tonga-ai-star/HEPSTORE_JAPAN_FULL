from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import PaymentTransaction, StaffProfile

User = get_user_model()


def staff_user(username, role=None, superuser=False):
    u = User.objects.create_user(username, password='Hep-Staff-Pass-2026', is_staff=True, is_superuser=superuser)
    if role:
        StaffProfile.objects.create(user=u, role=role)
    return u


class RoleAccessTests(TestCase):
    def setUp(self):
        self.owner = staff_user('chu', superuser=True)
        self.sales = staff_user('banhang', 'sales')
        self.kho = staff_user('kho', 'warehouse')
        self.bare = staff_user('trong')  # staff without profile

    def code(self, user, name, *args):
        self.client.force_login(user)
        return self.client.get(reverse(name, args=args)).status_code

    def test_owner_opens_everything(self):
        for name in ('dashboard', 'manage_reports', 'manage_staff', 'manage_payments', 'manage_books', 'pos'):
            self.assertEqual(self.code(self.owner, name), 200, name)

    def test_sales_cannot_open_warehouse_or_manager_pages(self):
        for name in ('pos', 'social_order', 'manage_orders', 'manage_payments'):
            self.assertEqual(self.code(self.sales, name), 200, name)
        for name in ('manage_books', 'manage_purchases', 'manage_reports', 'manage_staff', 'export_orders'):
            self.assertEqual(self.code(self.sales, name), 403, name)

    def test_warehouse_cannot_sell_or_see_money(self):
        for name in ('manage_books', 'manage_inventory', 'manage_purchases'):
            self.assertEqual(self.code(self.kho, name), 200, name)
        for name in ('pos', 'manage_orders', 'manage_payments', 'manage_reports'):
            self.assertEqual(self.code(self.kho, name), 403, name)

    def test_staff_without_profile_gets_least_privilege(self):
        self.assertEqual(self.code(self.bare, 'pos'), 200)
        self.assertEqual(self.code(self.bare, 'manage_staff'), 403)

    def test_live_payment_feed_follows_role(self):
        self.client.force_login(self.sales)
        r = self.client.get(reverse('payments_latest'))
        self.assertEqual(r.status_code, 200); self.assertIn('items', r.json())
        self.client.force_login(self.kho)
        self.assertEqual(self.client.get(reverse('payments_latest')).status_code, 403)

    def test_post_actions_are_guarded_too(self):
        self.client.force_login(self.kho)
        self.assertEqual(self.client.post(reverse('payment_resolve', args=[1]), {'order_code': 'x'}).status_code, 403)

    def test_sidebar_hides_pages_outside_role(self):
        self.client.force_login(self.kho)
        html = self.client.get(reverse('dashboard')).content.decode()
        self.assertIn(reverse('manage_books'), html)
        self.assertNotIn(reverse('pos'), html)
        self.assertNotIn(reverse('manage_reports'), html)

    def test_customer_is_redirected_to_login(self):
        u = User.objects.create_user('khach', password='Khach-Pass-2026x')
        self.client.force_login(u)
        self.assertEqual(self.client.get(reverse('pos')).status_code, 302)

    def test_manager_creates_staff_with_role(self):
        self.client.force_login(self.owner)
        r = self.client.post(reverse('staff_add'), {'username': 'thungan1', 'first_name': 'Vũ Thu Ngân', 'role': 'sales',
                                                    'password1': 'Thu-Ngan-Pass-77', 'password2': 'Thu-Ngan-Pass-77'})
        self.assertEqual(r.status_code, 302)
        u = User.objects.get(username='thungan1')
        self.assertTrue(u.is_staff); self.assertFalse(u.is_superuser); self.assertEqual(u.staff_profile.role, 'sales')

    def test_manager_can_lock_staff(self):
        self.client.force_login(self.owner)
        self.client.post(reverse('staff_edit', args=[self.sales.pk]), {'role': 'sales'})
        self.sales.refresh_from_db(); self.assertFalse(self.sales.is_active)


@override_settings(SHOP_HOST='shop.localhost', ADMIN_HOST='quantri.localhost',
                   ALLOWED_HOSTS=['shop.localhost', 'quantri.localhost', 'testserver'])
class HostSplitTests(TestCase):
    def test_shop_host_sends_management_to_admin_host(self):
        r = self.client.get('/management/', HTTP_HOST='shop.localhost:8000')
        self.assertEqual(r.status_code, 302); self.assertEqual(r['Location'], 'http://quantri.localhost:8000/management/')

    def test_admin_host_root_goes_to_dashboard(self):
        r = self.client.get('/', HTTP_HOST='quantri.localhost:8000')
        self.assertEqual(r['Location'], '/management/')

    def test_admin_host_does_not_serve_shop_pages(self):
        r = self.client.get('/sach/', HTTP_HOST='quantri.localhost:8000')
        self.assertEqual(r.status_code, 301); self.assertEqual(r['Location'], 'http://shop.localhost:8000/sach/')

    def test_admin_host_serves_login(self):
        self.assertEqual(self.client.get('/tai-khoan/login/', HTTP_HOST='quantri.localhost').status_code, 200)

    def test_shop_host_serves_store(self):
        self.assertEqual(self.client.get('/', HTTP_HOST='shop.localhost').status_code, 200)

    def test_webhook_reachable_on_any_host(self):
        r = self.client.post('/api/sepay/webhook/', '{}', content_type='application/json', HTTP_HOST='shop.localhost')
        self.assertIn(r.status_code, (401, 503))

    def test_admin_host_pages_never_link_into_the_shop_session(self):
        # Shop links on the admin host jump to shop.localhost, which has its own login cookie,
        # so staff looked "logged out". The admin side must only offer admin links and its own logout.
        login = self.client.get('/tai-khoan/login/', HTTP_HOST='quantri.localhost:8000').content.decode()
        for shop_link in ('/tai-khoan-cua-toi/', '/gio-hang/', '/dang-ky/'):
            self.assertNotIn(f'href="{shop_link}"', login)
        self.client.force_login(staff_user('qtv', superuser=True))
        page = self.client.get('/management/', HTTP_HOST='quantri.localhost:8000').content.decode()
        self.assertNotIn('href="/tai-khoan-cua-toi/"', page)
        self.assertIn('action="/tai-khoan/logout/"', page)
        self.assertIn('href="http://shop.localhost:8000/"', page)

    def test_shop_host_keeps_account_menu(self):
        self.client.force_login(User.objects.create_user('khach', password='x-Pass-12345'))
        self.assertContains(self.client.get('/', HTTP_HOST='shop.localhost'), 'href="/tai-khoan-cua-toi/"')

    def test_unknown_host_keeps_single_site(self):
        self.client.force_login(User.objects.create_user('o', password='x-Pass-12345', is_staff=True, is_superuser=True))
        self.assertEqual(self.client.get('/management/').status_code, 200)


class StaffAdminGuardTests(TestCase):
    def setUp(self):
        self.owner = staff_user('chu2', superuser=True)
        self.mgr = staff_user('quanly', 'manager')
        self.mgr2 = staff_user('quanly2', 'manager')
        self.sales = staff_user('nv', 'sales')

    def test_manager_cannot_edit_another_manager(self):
        self.client.force_login(self.mgr)
        self.client.post(reverse('staff_edit', args=[self.mgr2.pk]), {'role': 'manager', 'new_password': 'Takeover-Pass-1'})
        self.mgr2.refresh_from_db(); self.assertTrue(self.mgr2.is_active)
        self.assertFalse(self.mgr2.check_password('Takeover-Pass-1'))

    def test_manager_cannot_edit_self(self):
        self.client.force_login(self.mgr)
        self.client.post(reverse('staff_edit', args=[self.mgr.pk]), {'role': 'sales'})
        self.mgr.refresh_from_db(); self.assertEqual(self.mgr.staff_profile.role, 'manager')

    def test_manager_cannot_grant_manager_role(self):
        self.client.force_login(self.mgr)
        self.client.post(reverse('staff_edit', args=[self.sales.pk]), {'role': 'manager', 'is_active': 'on'})
        self.sales.staff_profile.refresh_from_db(); self.assertEqual(self.sales.staff_profile.role, 'sales')

    def test_owner_can_promote(self):
        self.client.force_login(self.owner)
        self.client.post(reverse('staff_edit', args=[self.sales.pk]), {'role': 'manager', 'is_active': 'on'})
        self.sales.staff_profile.refresh_from_db(); self.assertEqual(self.sales.staff_profile.role, 'manager')
