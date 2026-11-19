from django.conf import settings
from .models import Category

def site_context(request):
    cart=request.session.get('hep_cart',{})
    return {
       'nav_categories':Category.objects.all()[:7],
       'cart_count':sum(int(v) for v in cart.values() if str(v).isdigit()),
       'bank_configured':bool(settings.BANK_BIN and settings.BANK_ACCOUNT and settings.BANK_OWNER),
       'bank_owner':settings.BANK_OWNER,
       'bank_account':settings.BANK_ACCOUNT,
       'bank_bin':settings.BANK_BIN,
    }
