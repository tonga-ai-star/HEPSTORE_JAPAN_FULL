import re
from urllib.parse import urlencode
from django.conf import settings

def qr_url(order):
    if not all((settings.BANK_BIN,settings.BANK_ACCOUNT,settings.BANK_OWNER)):
        return ''
    if not re.fullmatch(r'\d{6}', settings.BANK_BIN) or not re.fullmatch(r'\d{6,19}',settings.BANK_ACCOUNT):
        return ''
    params=urlencode({'amount':order.total,'addInfo':order.order_code,'accountName':settings.BANK_OWNER})
    return f'https://img.vietqr.io/image/{settings.BANK_BIN}-{settings.BANK_ACCOUNT}-compact2.png?{params}'
