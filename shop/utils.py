import re
from urllib.parse import urlencode
from django.conf import settings
from django.utils.http import url_has_allowed_host_and_scheme

def qr_url(order):
    if not all((settings.BANK_BIN,settings.BANK_ACCOUNT,settings.BANK_OWNER)):
        return ''
    if not re.fullmatch(r'\d{6}', settings.BANK_BIN) or not re.fullmatch(r'\d{6,19}',settings.BANK_ACCOUNT):
        return ''
    params=urlencode({'amount':order.total,'addInfo':order.order_code,'accountName':settings.BANK_OWNER})
    return f'https://img.vietqr.io/image/{settings.BANK_BIN}-{settings.BANK_ACCOUNT}-compact2.png?{params}'

def safe_next(request,default='home'):
    next_url=request.GET.get('next','')
    if next_url and url_has_allowed_host_and_scheme(next_url,allowed_hosts={request.get_host()},require_https=request.is_secure()):
        return next_url
    return default
