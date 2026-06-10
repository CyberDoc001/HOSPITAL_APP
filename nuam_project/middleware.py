from django.http import HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.urls import reverse


class RequireLoginMiddleware:
    """Require login for all views except a small whitelist.

    Whitelisted paths include static files, the admin, auth URLs and the
    landing and doctor-login pages so unauthenticated users can sign in.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        # allow common public prefixes
        allowed_prefixes = (
            "/accounts/",
            "/static/",
            "/admin/",
            "/favicon.ico",
            "/robots.txt",
            "/doctor/login/",
            "/",
        )

        if not request.user.is_authenticated:
            for p in allowed_prefixes:
                if path.startswith(p):
                    return self.get_response(request)
            # otherwise redirect to landing page
            try:
                return redirect(reverse("patients:landing"))
            except Exception:
                return redirect("/")

        return self.get_response(request)


class LowercaseRedirectMiddleware:
    """Redirect requests with uppercase path segments to lowercase.

    This helps users who type `/DOCTOR/` instead of `/doctor/` and avoids
    404s caused by case-sensitive URL matching. It preserves the querystring.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        lower = path.lower()
        if path != lower:
            qs = request.META.get("QUERY_STRING", "")
            new = lower + ("?" + qs if qs else "")
            return HttpResponsePermanentRedirect(new)
        return self.get_response(request)
