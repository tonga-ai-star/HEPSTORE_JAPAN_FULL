from django.test import TestCase
from django.urls import reverse
from .models import Book, Category, Order

class PublicBarcodeScanTests(TestCase):
    """Public scanner must be independent from dashboard and read actual prices."""
    def setUp(self):
        category = Category.objects.create(name_vi='Văn hóa Nhật', slug='van-hoa-nhat')
        self.book = Book.objects.create(category=category, title_vi='Sách test ISBN',
            slug='sach-test-isbn', isbn='9786041234567', price=129000, stock=3, active=True)

    def test_scanner_public_not_staff(self):
        self.assertContains(self.client.get(reverse('public_scan')), 'Quét mã vạch', status_code=200)

    def test_lookup_redirects_to_shareable_url(self):
        response = self.client.get(reverse('public_scan_lookup'), {'isbn':'9786041234567'})
        self.assertRedirects(response, reverse('public_scan_result', args=['9786041234567']))

    def test_scan_result_shows_price_and_title(self):
        self.assertContains(self.client.get(reverse('public_scan_result', args=[self.book.isbn])), '129.000', status_code=200)
        self.assertContains(self.client.get(reverse('public_scan_result', args=[self.book.isbn])), 'Sách test ISBN', status_code=200)

    def test_hyphenated_isbn_in_database(self):
        self.book.isbn='978-604-123456-7'; self.book.save(update_fields=['isbn'])
        self.assertContains(self.client.get(reverse('public_scan_result', args=['9786041234567'])), 'Sách test ISBN', status_code=200)

    def test_unknown_isbn_returns_friendly_404(self):
        response = self.client.get(reverse('public_scan_result', args=['9786049999999']))
        self.assertEqual(response.status_code,404)
        self.assertContains(response, 'Chưa tìm thấy sách', status_code=404)

    def test_inactive_book_not_exposed(self):
        self.book.active=False; self.book.save(update_fields=['active'])
        response=self.client.get(reverse('public_scan_result',args=['9786041234567']))
        self.assertEqual(response.status_code,404)

    def test_scan_does_not_reduce_stock_or_create_order(self):
        self.client.get(reverse('public_scan_result',args=['9786041234567']))
        self.book.refresh_from_db()
        self.assertEqual(self.book.stock,3)
        self.assertEqual(Order.objects.count(),0)
