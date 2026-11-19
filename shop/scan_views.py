"""Trang quét mã vạch công khai, độc lập quản trị và không thay đổi dữ liệu bán hàng."""
import re
from django.db.models import Value
from django.db.models.functions import Replace
from django.http import Http404
from django.shortcuts import render, redirect
from .models import Book

# ---------- PUBLIC ISBN SCANNER (NO STAFF LOGIN REQUIRED) ----------
# This module is read-only; it NEVER creates orders, alters stock or registers payments.
_ISBN_SKU_PATTERN = re.compile(r'[A-Za-z0-9._-]{3,30}\Z')


def public_scan(request):
    """Public scanner UI: https://site/quet-ma/ (localhost works in development)."""
    return render(request, 'shop/public_scan.html')


def public_scan_lookup(request):
    """Convert an ISBN or SKU entered by hand into a shareable result URL."""
    code = request.GET.get('isbn', '').strip()
    if not _ISBN_SKU_PATTERN.fullmatch(code):
        return render(request, 'shop/public_scan.html', {
            'scan_error': 'Vui lòng nhập ISBN / SKU hợp lệ (3–30 ký tự, chữ, số, dấu gạch hoặc chấm).',
            'scan_value': code[:30],
        }, status=400)
    return redirect('public_scan_result', code=code)


def public_scan_result(request, code):
    """Show the price of an ACTIVE book without exposing supplier/private information."""
    if not _ISBN_SKU_PATTERN.fullmatch(code):
        raise Http404('Mã ISBN / SKU không hợp lệ')
    books = Book.objects.filter(active=True).select_related('category')
    book = books.filter(isbn__iexact=code).first()
    # EAN-13 barcodes are digits, while some publishers store hyphenated ISBNs.
    if book is None and code.replace('-', '').isdigit():
        canonical = code.replace('-', '')
        book = books.annotate(
            canonical_isbn=Replace(Replace('isbn', Value('-'), Value('')), Value(' '), Value('')),
        ).filter(canonical_isbn=canonical).first()
    return render(request, 'shop/public_scan_result.html', {
        'book': book,
        'scanned_code': code,
    }, status=200 if book is not None else 404)


