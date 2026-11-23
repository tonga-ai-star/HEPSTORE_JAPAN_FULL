"""Hép Store — Django demo. Configure secrets/hosts and HTTPS before production."""
import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(path):
    """Minimal .env reader: KEY=VALUE lines; real environment variables win."""
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_env_file(BASE_DIR / '.env')
SECRET_KEY = os.environ.get('HEPSTORE_SECRET_KEY', 'dev-only-change-before-deployment-7e2d9cc1b4f14780a1f1')
DEBUG = os.environ.get('HEPSTORE_DEBUG', '0') == '1'  # safe default; .env turns it on for local testing
# Two links: SHOP_HOST serves the store, ADMIN_HOST serves /management/ (login + role required).
# *.localhost resolves to 127.0.0.1 in browsers, so this works locally without hosting.
SHOP_HOST = os.environ.get('HEPSTORE_SHOP_HOST', 'shop.localhost').strip()
ADMIN_HOST = os.environ.get('HEPSTORE_ADMIN_HOST', 'quantri.localhost').strip()
ALLOWED_HOSTS = [x.strip() for x in os.environ.get('HEPSTORE_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if x.strip()]
ALLOWED_HOSTS += [h for h in (SHOP_HOST, ADMIN_HOST) if h and h not in ALLOWED_HOSTS]
# Public tunnel host for SePay during testing (ngrok / cloudflared), e.g. abc.ngrok-free.app
TUNNEL_HOSTS = [x.strip() for x in os.environ.get('HEPSTORE_TUNNEL_HOSTS', '').split(',') if x.strip()]
ALLOWED_HOSTS += TUNNEL_HOSTS
CSRF_TRUSTED_ORIGINS = [x.strip() for x in os.environ.get('HEPSTORE_CSRF_ORIGINS', '').split(',') if x.strip()]
INSTALLED_APPS = [
 'django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions',
 'django.contrib.messages','django.contrib.staticfiles','shop',
]
MIDDLEWARE = [
 'django.middleware.security.SecurityMiddleware','django.contrib.sessions.middleware.SessionMiddleware',
 'django.middleware.common.CommonMiddleware','shop.middleware.HostSplitMiddleware','django.middleware.csrf.CsrfViewMiddleware',
 'django.contrib.auth.middleware.AuthenticationMiddleware','shop.middleware.RoleAccessMiddleware','django.contrib.messages.middleware.MessageMiddleware',
 'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'hepstore.urls'
TEMPLATES = [{
 'BACKEND':'django.template.backends.django.DjangoTemplates',
 'DIRS':[BASE_DIR/'templates'], 'APP_DIRS':True,
 'OPTIONS':{'context_processors':[
 'django.template.context_processors.debug','django.template.context_processors.request',
 'django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',
 'shop.context_processors.site_context',
 ]},
}]
WSGI_APPLICATION = 'hepstore.wsgi.application'
DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':BASE_DIR/'db.sqlite3','OPTIONS':{'timeout':20}}}
AUTH_PASSWORD_VALIDATORS = [
 {'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
 {'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},
 {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},
 {'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE='vi'
TIME_ZONE='Asia/Ho_Chi_Minh'
USE_I18N=True
USE_TZ=True
STATIC_URL='static/'
STATICFILES_DIRS=[BASE_DIR/'static']
STATIC_ROOT=BASE_DIR/'staticfiles'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
LOGIN_URL='login'
LOGIN_REDIRECT_URL='home'
LOGOUT_REDIRECT_URL='home'
SESSION_COOKIE_HTTPONLY=True
CSRF_COOKIE_HTTPONLY=True
X_FRAME_OPTIONS='DENY'
# Unconfirmed, unpaid web orders release their stock after this many days; each phone may hold at most this many open web orders.
ORDER_HOLD_DAYS=int(os.environ.get('HEPSTORE_ORDER_HOLD_DAYS','3'))
MAX_OPEN_WEB_ORDERS=int(os.environ.get('HEPSTORE_MAX_OPEN_WEB_ORDERS','3'))
# Bank configuration; leave unconfigured until you replace with YOUR real details.
BANK_BIN=os.environ.get('HEPSTORE_BANK_BIN','').strip()
BANK_ACCOUNT=os.environ.get('HEPSTORE_BANK_ACCOUNT','').strip()
BANK_OWNER=os.environ.get('HEPSTORE_BANK_OWNER','').strip()
TM_MODEL_URL=os.environ.get('HEPSTORE_TM_MODEL_URL','').strip()
# SePay webhook: the same random key is pasted into SePay > Webhooks > "API Key".
SEPAY_API_KEY=os.environ.get('HEPSTORE_SEPAY_API_KEY','').strip()
