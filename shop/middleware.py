"""Host split (shop link vs. admin link) and role-based access to /management/."""
from django.conf import settings
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render

from .roles import ALL_PAGES, allowed_pages, role_of

ADMIN_PREFIXES = ('/management/', '/admin/')
SHARED_PREFIXES = ('/static/', '/tai-khoan/', '/api/', '/favicon')


def _split(host_header):
    host, _, port = host_header.partition(':')
    return host.lower(), (':' + port if port else '')


class HostSplitMiddleware:
    """When SHOP_HOST and ADMIN_HOST are set, each link only serves its own side.

    Any other host (127.0.0.1, testserver) keeps the old single-site behaviour.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.shop = (getattr(settings, 'SHOP_HOST', '') or '').lower()
        self.admin = (getattr(settings, 'ADMIN_HOST', '') or '').lower()
        self.tunnels = [h.lower() for h in getattr(settings, 'TUNNEL_HOSTS', [])]

    def _is_tunnel(self, host):
        return any(host == t.lstrip('.') or (t.startswith('.') and host.endswith(t)) for t in self.tunnels)

    def __call__(self, request):
        host, _ = _split(request.get_host())
        if self.tunnels and self._is_tunnel(host) and request.path != '/api/sepay/webhook/':
            # The public tunnel exists only so SePay can reach the webhook; never expose the site or admin there.
            return HttpResponseNotFound('Not found')
        if self.shop and self.admin:
            host, port = _split(request.get_host())
            path = request.get_full_path()
            scheme = 'https' if request.is_secure() else 'http'
            if host == self.shop and request.path.startswith(ADMIN_PREFIXES):
                return HttpResponseRedirect(f'{scheme}://{self.admin}{port}{path}')
            if host == self.admin:
                if request.path == '/':
                    return HttpResponseRedirect('/management/')
                if not request.path.startswith(ADMIN_PREFIXES + SHARED_PREFIXES):
                    return HttpResponsePermanentRedirect(f'{scheme}://{self.shop}{port}{path}')
        return self.get_response(request)


class RoleAccessMiddleware:
    """Staff may only open the management pages of their role. Runs after authentication."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = request.resolver_match
        name = match.url_name if match else None
        if name not in ALL_PAGES or role_of(request.user) is None:
            return None  # customers/anonymous: staff_member_required handles the redirect
        if name in allowed_pages(request.user):
            return None
        return render(request, 'management/forbidden.html', {'page_name': name}, status=403)
