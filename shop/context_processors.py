from django.conf import settings
from .models import Category
from .roles import allowed_pages, role_of

def site_context(request):
    host,_,port=request.get_host().lower().partition(':')
    on_admin_host=bool(settings.ADMIN_HOST and settings.SHOP_HOST and host==settings.ADMIN_HOST.lower())
    cart=request.session.get('hep_cart',{})
    return {
       'on_admin_host':on_admin_host,
       'shop_url':f"{request.scheme}://{settings.SHOP_HOST}{':'+port if port else ''}/" if on_admin_host else '/',
       'nav_categories':Category.objects.all()[:7],
       'cart_count':sum(int(v) for v in cart.values() if str(v).isdigit()),
       'bank_configured':bool(settings.BANK_BIN and settings.BANK_ACCOUNT and settings.BANK_OWNER),
       'bank_owner':settings.BANK_OWNER,
       'bank_account':settings.BANK_ACCOUNT,
       'bank_bin':settings.BANK_BIN,
       'staff_role':role_of(request.user) if hasattr(request,'user') else None,
       'allowed_pages':allowed_pages(request.user) if hasattr(request,'user') else frozenset(),
    }
